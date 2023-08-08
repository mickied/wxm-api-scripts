import base_functions as bf
from datetime import datetime as dt
import pytz
import mysql.connector

# WeatherXM Device Info
# Leave the username and password fields blank if the public API is desired.
WXM_USERNAME = ""
WXM_PASSWORD = ""
WXM_HEX_ID = "871969c99ffffff"
WXM_DEVICE_ID = "6ebe4520-3c10-11ed-9972-4f669f2d96bd"

# MySQL Database Info
DB_HOST = "192.168.1.201"
DB_PORT = "6603"
DB_USER = "dbusername"
DB_PASSWORD = "dbpassword"
DB_DATABASE = "dbname"

# Conversion Options
C_TO_F = True
METERSPERSECOND_TO_MPH = True
MM_TO_INCH = True
HPA_TO_INHG = True


def main():
    if WXM_DEVICE_ID == "":
        print("A WeatherXM device ID is required. Please follow the instructions in the readme to "
              "add an ID to the script and try again.")
        exit()

    weatherxm_data = None
    if WXM_USERNAME != "" and WXM_PASSWORD != "":
        token = bf.wxm_login(WXM_USERNAME, WXM_PASSWORD)
        weatherxm_data = bf.wxm_private_request(WXM_DEVICE_ID, token)
        bf.wxm_logout(token)
    else:
        if WXM_HEX_ID == "":
            print("A WeatherXM hex ID is required when using the public API. Please follow the "
                  "instructions in the readme to add a hex ID to the script and try again.")
            exit()

        weatherxm_data = bf.wxm_public_request(
            WXM_HEX_ID, WXM_DEVICE_ID)

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
    conditions = weatherxm_data["icon"]
    feels_like_C = weatherxm_data["feels_like"]
    precipitation_mm_accumulated = weatherxm_data["precipitation_accumulated"]
    solar_irradiance_wm2 = weatherxm_data["solar_irradiance"]
    dew_point_C = weatherxm_data["dew_point"]

    # Convert to UTC time zone.
    # The WeatherXM date is formated ISO 8601 which includes a timezone offset (e.g. "2023-04-11T08:59:46-05:00").
    # However, mysql cannot intrepret the offset and only wants to store UTC time (e.g. "2023-04-11T13:59:46").
    timestamp = dt.fromisoformat(timestamp).astimezone(tz=pytz.utc)

    # Perform Conversions
    temperature = bf.c_to_f(temperature_C) if C_TO_F else temperature_C
    feels_like = bf.c_to_f(feels_like_C) if C_TO_F else feels_like_C
    dew_point = bf.c_to_f(dew_point_C) if C_TO_F else dew_point_C

    wind_speed = bf.mps_to_mph(
        wind_speed_mps) if METERSPERSECOND_TO_MPH else wind_speed_mps

    wind_gust = bf.mps_to_mph(
        wind_gust_mps) if METERSPERSECOND_TO_MPH else wind_gust_mps

    wind_direction_card = bf.deg_to_cardinal(wind_direction_deg)

    precipitation = bf.mm_to_inch(
        precipitation_mm) if MM_TO_INCH else precipitation_mm

    precipitation_accumulated = bf.mm_to_inch(
        precipitation_mm_accumulated) if MM_TO_INCH else precipitation_mm_accumulated

    pressure = bf.hpa_to_inhg(
        pressure_hPa) if HPA_TO_INHG else pressure_hPa

    # This is the sql command will all the values inserted with their formatters.
    sqlcmd = ("INSERT INTO WeatherStationDL (datetime, temperature, feels_like, humidity, wind_speed, "
              "wind_gust, wind_direction, wind_direction_degrees, uv_index, precipitation, pressure, "
              "conditions, precipitation_accumulated, solar_irradiance, dew_point) "
              f"VALUES ('{timestamp}', {temperature:.2f}, {feels_like:.2f}, {humidity}, {wind_speed:.2f}, "
              f"{wind_gust:.2f}, '{wind_direction_card}', {wind_direction_deg}, {uv_index}, {precipitation:.2f}, {pressure:.2f}, "
              f"'{conditions}', {precipitation_accumulated:.2f}, {solar_irradiance_wm2:.2f}, {dew_point:.2f})")

    # Uncomment to see the statement printed out for debugging.
    # print(sqlcmd)

    try:
        # Connect to the database.
        db = mysql.connector.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_DATABASE
        )

        # Attempt to execute the sql command on the database to insert the record.
        dbcursor = db.cursor()
        dbcursor.execute(sqlcmd)
        db.commit()
    except Exception as e:
        print('Error: ', e)
    else:
        print(dbcursor.rowcount, "record inserted.")


if __name__ == '__main__':
    main()
