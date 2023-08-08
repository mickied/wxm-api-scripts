import requests
import json

# The private API urls.
base_url = "https://api.weatherxm.com/api/v1"
url_login = base_url + "/auth/login"
url_logout = base_url + "/auth/logout"


# Conversion function for converting direction in degrees to a cardinal direction.
def deg_to_cardinal(deg):
    dirs = ['N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE', 'SSE',
            'S', 'SSW', 'SW', 'WSW', 'W', 'WNW', 'NW', 'NNW']
    ix = round(deg / (360. / len(dirs)))
    return dirs[ix % len(dirs)]


# Celcius to Farenheit
def c_to_f(temp):
    return temp * 9/5 + 32


# Meters per second to miles per hour.
def mps_to_mph(mps):
    return mps * 2.236936


# Millimeters to Inches
def mm_to_inch(mm):
    return mm * 0.0393700787


# Hectopascals to Inches of Murcery
def hpa_to_inhg(hpa):
    return hpa * 0.02952998307


# Login to WeatherXM
def wxm_login(username, password):
    payload = json.dumps(
        {"username": username, "password": password}
    )
    headers = {
        'accept': 'application/json',
        'Content-Type': 'application/json'
    }
    response = requests.post(url_login, payload, headers=headers)

    if response.status_code != 200:
        print(f"Login failed with code: {response.status_code}")
        exit()

    jsonData = response.json()
    return jsonData["token"]


# Logout
def wxm_logout(bearer_token):
    payload = json.dumps(
        {"accessToken": bearer_token}
    )
    headers = {
        'accept': '*/*',
        'Content-Type': 'application/json'
    }
    response = requests.post(url_logout, payload, headers=headers)

    if response.status_code != 205:
        print(f"Logout failed with code: {response.status_code}")


# GET Private HTTP Request
def wxm_private_request(device_id, bearer_token):
    headers = {
        'accept': 'application/json',
        'Authorization': 'Bearer ' + bearer_token
    }
    url_device = base_url + f"/me/devices/{device_id}"
    response = requests.get(url_device, headers=headers)

    if response.status_code != 200:
        print(f"Query failed with code: {response.status_code}")
        wxm_logout(bearer_token)
        exit()

    # Get the data as a JSON Object
    jsonData = response.json()
    return jsonData["current_weather"]


# GET Public HTTP Request
def wxm_public_request(hex_id, device_id):
    url = f"https://api.weatherxm.com/api/v1/cells/{hex_id}/devices/{device_id}"
    response = requests.get(url)

    if response.status_code != 200:
        print(f"Query failed with code: {response.status_code}")
        exit()

    # Get the data as a JSON Object
    jsonData = response.json()
    return jsonData["current_weather"]
