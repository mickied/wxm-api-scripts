import requests
import json
import logging

# Setup logger
logging.basicConfig(format='%(asctime)s.%(msecs)03d [%(levelname)s] %(message)s', datefmt='%m/%d/%Y %H:%M:%S', level=logging.INFO)


# The private API urls.
base_url = "https://api.weatherxm.com/api/v1"
url_login = base_url + "/auth/login"
url_logout = base_url + "/auth/logout"
REQUEST_TIMEOUT = 15


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
def wxm_login(username, password, timeout=REQUEST_TIMEOUT):
    payload = json.dumps(
        {"username": username, "password": password}
    )
    headers = {
        'accept': 'application/json',
        'Content-Type': 'application/json'
    }

    try:
        response = requests.post(url_login, payload, headers=headers, timeout=timeout)
    except requests.exceptions.Timeout:
        logging.error(f"Login request timed out after {timeout} seconds")
        exit()
    except requests.exceptions.RequestException as e:
        logging.error(f"Login request failed: {e}")
        exit()

    if response.status_code != 200:
        logging.error(f"Login failed with code: {response.status_code}")
        exit()

    jsonData = response.json()
    return jsonData["token"]


# Logout
def wxm_logout(bearer_token, timeout=REQUEST_TIMEOUT):
    payload = json.dumps(
        {"accessToken": bearer_token}
    )
    headers = {
        'accept': '*/*',
        'Content-Type': 'application/json'
    }

    try:
        response = requests.post(url_logout, payload, headers=headers, timeout=timeout)
    except requests.exceptions.RequestException as e:
        logging.error(f"Logout request failed: {e}")
        return

    if response.status_code != 205:
        logging.error(f"Logout failed with code: {response.status_code}")


# GET Private HTTP Request
def wxm_private_request(name, bearer_token):
    headers = {
        'accept': 'application/json',
        'Authorization': 'Bearer ' + bearer_token
    }
    url_device = base_url + f"/me/devices"
    try:
        response = requests.get(url_device, headers=headers, timeout=REQUEST_TIMEOUT)
    except requests.exceptions.RequestException as e:
        logging.error(f"Device query request failed: {e}")
        wxm_logout(bearer_token)
        exit()

    if response.status_code != 200:
        logging.error(f"Query failed with code: {response.status_code}")
        wxm_logout(bearer_token)
        exit()

    # Get the data as a JSON Object
    jsonData = response.json()
    
    if not jsonData:
        logging.error("No stations associated with this account.")
        wxm_logout(bearer_token)
        exit()

    for device in jsonData:
        device_name = str(device["name"])

        if str(name).lower() == device_name.lower():
            device["current_weather"]["device_id"] = device["id"]
            return device["current_weather"]

    logging.error(f"No station found with name: {name}")
    wxm_logout(bearer_token)
    exit()


# GET Public Weather Station IDs
def wxm_public_ids_from_name(name):
    url = base_url + f"/network/search?query={name}"

    try:
        response = requests.get(url, timeout=REQUEST_TIMEOUT)
    except requests.exceptions.RequestException as e:
        logging.error(f"Station search request failed: {e}")
        exit()

    if response.status_code != 200:
        logging.error(f"Query failed with code: {response.status_code}")
        exit()

    # Get the data as a JSON Object
    jsonData = response.json()

    if not jsonData["devices"]:
        logging.error(f"Could not find station name: {name}")
        exit()

    queried_name = str(jsonData["devices"][0]["name"])

    if str(name).lower() == queried_name.lower():
        hex = jsonData["devices"][0]["cell_index"]
        id = jsonData["devices"][0]["id"]
        return (hex, id)
    else:
        logging.error(f"Could not find station name: {name}")
        exit()


# GET Public HTTP Request
def wxm_public_request(hex_id, device_id):
    url = base_url + f"/cells/{hex_id}/devices/{device_id}"
    try:
        response = requests.get(url, timeout=REQUEST_TIMEOUT)
    except requests.exceptions.RequestException as e:
        logging.error(f"Public device request failed: {e}")
        exit()

    if response.status_code != 200:
        logging.error(f"Query failed with code: {response.status_code}")
        exit()

    # Get the data as a JSON Object
    jsonData = response.json()
    return jsonData["current_weather"]

def wxm_device_info(device_id, bearer_token):
    headers = {
        'accept': 'application/json',
        'Authorization': 'Bearer ' + bearer_token
    }
    url_device = base_url + f"/me/devices/{device_id}/info"
    try:
        response = requests.get(url_device, headers=headers, timeout=REQUEST_TIMEOUT)
    except requests.exceptions.RequestException as e:
        logging.error(f"Device info request failed: {e}")
        wxm_logout(bearer_token)
        exit()

    if response.status_code != 200:
        logging.error(f"Device info query failed with code: {response.status_code}")
        wxm_logout(bearer_token)
        exit()

    # Get the data as a JSON Object
    jsonData = response.json()

    return jsonData["weather_station"]