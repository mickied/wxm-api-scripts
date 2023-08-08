import base_functions as bf
from datetime import datetime as dt

# WeatherXM Device Info
# Leave the username and password fields blank if the public API is desired.
WXM_USERNAME = ""
WXM_PASSWORD = ""
WXM_STATION_NAME = "Stormy Basil Cirrocumulus"

# Create a Tago.io "Custom HTTPS" device and enter the token here.
TAGOIO_DEVICE_TOKEN = ""

# Conversion Options
C_TO_F = False
METERSPERSECOND_TO_MPH = False
MM_TO_INCH = False
HPA_TO_INHG = False


tago_url = "https://api.tago.io/data"


def get_tago_timestamp():
    tago_query = tago_url + "?query=last_item&variable=temperature"
    tago_query_headers = {'device-token': TAGOIO_DEVICE_TOKEN}
    query_response = bf.requests.get(tago_query, headers=tago_query_headers)
    tago_query_data = query_response.json()
    if query_response.status_code != 200:
        print(f"Tago.io query failed with code: {query_response.status_code}")
        exit()

    # The iso8601 timetamps from Tago.io and WeatherXM are in different timezone formats so we need to
    # parse them into a datatime object that can be compared.
    if tago_query_data["result"]:
        iso_datetime = tago_query_data["result"][0]["time"]
        # The fromisoformat method in Python versions <= 3.10 cannot parse the Zulu "Z" specifier at the
        # end of an ISO6801 time string, so replace it with "+00:00".
        return dt.fromisoformat(iso_datetime.replace('Z', '+00:00'))
    else:
        return None


def main():
    if WXM_STATION_NAME == "":
        print("A WeatherXM station name is required. Please follow the instructions in the readme to "
              "add an ID to the script and try again.")
        exit()

    weatherxm_data = None
    if WXM_USERNAME != "" and WXM_PASSWORD != "":
        token = bf.wxm_login(WXM_USERNAME, WXM_PASSWORD)
        weatherxm_data = bf.wxm_private_request(WXM_STATION_NAME, token)
        bf.wxm_logout(token)
    else:
        station_IDs = bf.wxm_public_ids_from_name(WXM_STATION_NAME)
        weatherxm_data = bf.wxm_public_request(station_IDs[0], station_IDs[1])

    # Compare timestamps from last dataset and current dataset and exit if they are the same.
    datetime_last = get_tago_timestamp()
    datetime = dt.fromisoformat(weatherxm_data["timestamp"])
    if datetime == datetime_last:
        print("Duplicate weather data received. Try again later.")
        exit()

    # Parse Data
    timestamp = weatherxm_data["timestamp"]
    temperature_C = weatherxm_data["temperature"]
    humidity = weatherxm_data["humidity"]
    wind_speed_mps = weatherxm_data["wind_speed"]
    wind_gust_mps = weatherxm_data["wind_gust"]
    wind_direction_deg = weatherxm_data["wind_direction"]
    uv_index = weatherxm_data["uv_index"]
    precipitation_mm = weatherxm_data["precipitation"]
    pressure_hPa = weatherxm_data["pressure"]
    icon = weatherxm_data["icon"]
    feels_like_C = weatherxm_data["feels_like"]
    precipitation_mm_accumulated = weatherxm_data["precipitation_accumulated"]
    solar_irradiance_wm2 = weatherxm_data["solar_irradiance"]
    dew_point_C = weatherxm_data["dew_point"]

    # Perform Conversions
    if C_TO_F:
        temperature = bf.c_to_f(temperature_C)
        feels_like = bf.c_to_f(feels_like_C)
        dew_point = bf.c_to_f(dew_point_C)
        temp_unit = "°F"
    else:
        temperature = temperature_C
        feels_like = feels_like_C
        dew_point = dew_point_C
        temp_unit = "°C"

    if METERSPERSECOND_TO_MPH:
        wind_speed = bf.mps_to_mph(wind_speed_mps)
        wind_gust = bf.mps_to_mph(wind_gust_mps)
        wind_unit = "MPH"
    else:
        wind_speed = wind_speed_mps
        wind_gust = wind_gust_mps
        wind_unit = "m/s"

    wind_direction_card = bf.deg_to_cardinal(wind_direction_deg)

    if MM_TO_INCH:
        precipitation = bf.mm_to_inch(precipitation_mm)
        precipitation_accumulated = bf.mm_to_inch(precipitation_mm_accumulated)
        precip_unit = "in"
    else:
        precipitation = precipitation_mm
        precipitation_accumulated = precipitation_mm_accumulated
        precip_unit = "mm"

    if HPA_TO_INHG:
        pressure = bf.hpa_to_inhg(pressure_hPa)
        pressure_unit = "inHg"
    else:
        pressure = pressure_hPa
        pressure_unit = "hPa"

    # Build the payload for Tago.io.
    tago_payload = bf.json.dumps([
        {
            "variable": "temperature",
            "value": f"{temperature:.2f}",
            "unit": temp_unit,
            "time": timestamp
        },
        {
            "variable": "humidity",
            "value": humidity,
            "unit": "%",
            "time": timestamp
        },
        {
            "variable": "wind_speed",
            "value": f"{wind_speed:.2f}",
            "unit": wind_unit,
            "time": timestamp
        },
        {
            "variable": "wind_gust",
            "value": f"{wind_gust:.2f}",
            "unit": wind_unit,
            "time": timestamp
        },
        {
            "variable": "wind_direction",
            "value": wind_direction_deg,
            "unit": "°",
            "time": timestamp
        },
        {
            "variable": "wind_direction_cardinal",
            "value": wind_direction_card,
            "time": timestamp
        },
        {
            "variable": "uv_index",
            "value": uv_index,
            "time": timestamp
        },
        {
            "variable": "precipitation",
            "value": f"{precipitation:.2f}",
            "unit": precip_unit + "/h",
            "time": timestamp
        },
        {
            "variable": "precipitation_accumulated",
            "value": f"{precipitation_accumulated:.2f}",
            "unit": precip_unit,
            "time": timestamp
        },
        {
            "variable": "pressure",
            "value": f"{pressure:.2f}",
            "unit": pressure_unit,
            "time": timestamp
        },
        {
            "variable": "feels_like",
            "value": f"{feels_like:.2f}",
            "unit": temp_unit,
            "time": timestamp
        },
        {
            "variable": "solar_irradiance",
            "value": f"{solar_irradiance_wm2:.2f}",
            "unit": "w/m²",
            "time": timestamp
        },
        {
            "variable": "dew_point",
            "value": f"{dew_point:.2f}",
            "unit": temp_unit,
            "time": timestamp
        },
        {
            "variable": "icon",
            "value": icon,
            "time": timestamp
        }
    ])

    tago_headers = {
        'device-token': TAGOIO_DEVICE_TOKEN,
        'Content-Type': 'application/json'
    }

    tago_response = bf.requests.post(
        tago_url, tago_payload, headers=tago_headers)

    print(tago_response.text)


if __name__ == '__main__':
    main()
