import os
import signal
import base_functions as bf
from datetime import datetime as dt
from datetime import timezone as tz
import time
import mysql.connector

# WeatherXM Device Info
# DO NOT CHANGE! All these are read from the system environment variables set in the .env file!
WXM_USERNAME = os.environ.get("WXM_USERNAME")
WXM_PASSWORD = os.environ.get("WXM_PASSWORD")
WXM_STATION_NAMES = bf.json.loads(os.environ.get("WXM_STATIONS"))

UPDATE_RATE_SECONDS = 60 * int(os.environ.get("UPDATE_RATE_MINUTES"))

# MySQL Database Info
# DO NOT CHANGE! All these are read from the system environment variables set in the .env file!
DB_HOST = "mysql-server"
DB_PORT = "3306"
DB_USER = os.environ.get("MYSQL_USER")
DB_PASSWORD = os.environ.get("MYSQL_PASSWORD")
DB_DATABASE = os.environ.get("MYSQL_DATABASE")

# Conversion Options
# DO NOT CHANGE! All these are read from the system environment variables set in the .env file!
C_TO_F = os.getenv('C_TO_F', 'False').lower() in ('true', '1', 't')
METERSPERSECOND_TO_MPH = os.getenv('METERSPERSECOND_TO_MPH', 'False').lower() in ('true', '1', 't')
MM_TO_INCH = os.getenv('MM_TO_INCH', 'False').lower() in ('true', '1', 't')
HPA_TO_INHG = os.getenv('HPA_TO_INHG', 'False').lower() in ('true', '1', 't')

# Create a signal handler to process a shutdown signal and shutdown the program only when it is sleeping (between updates).
asleep = False
def signal_handler(sig, frame):
    bf.logging.critical("Shutdown signal received!")
    while not asleep:
        time.sleep(0.1)
    exit(0)

# Main function.
def main():
    # Catch shutdown signals.
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    runLoop = True
    while runLoop:
        scanStartTime = time.monotonic()  # Get the time at the start of this scan.

        # Connect to the database.
        try:
            db = mysql.connector.connect(
                host=DB_HOST,
                port=DB_PORT,
                user=DB_USER,
                password=DB_PASSWORD,
                database=DB_DATABASE
            )
        except Exception as e:
            bf.logging.error('MySQL DB Connection Error: %s\n\tTrying again in 3 seconds.', e)
            time.sleep(3)
            continue

        for station in WXM_STATION_NAMES:
            weatherxm_data = None
            if WXM_USERNAME != "" and WXM_PASSWORD != "":
                token = bf.wxm_login(WXM_USERNAME, WXM_PASSWORD)
                weatherxm_data = bf.wxm_private_request(station, token)
                bf.wxm_logout(token)
            else:
                station_IDs = bf.wxm_public_ids_from_name(station)
                weatherxm_data = bf.wxm_public_request(station_IDs[0], station_IDs[1])

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
            timestamp = dt.fromisoformat(timestamp).astimezone(tz=tz.utc)

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

            # Replace spaces in the station name with underscores.
            dbName = station.replace(" ", "_")

            # This is the sql command to create the table for this particular weather station.
            createTableSqlCmd = (f"CREATE TABLE IF NOT EXISTS `{DB_DATABASE}`.`{dbName}` ("
                "`datetime` DATETIME NOT NULL,"
                "`temperature` DECIMAL(5,2) NULL DEFAULT NULL,"
                "`feels_like` DECIMAL(5,2) NULL DEFAULT NULL,"
                "`dew_point` DECIMAL(5,2) NULL DEFAULT NULL,"
                "`humidity` INT NULL DEFAULT NULL,"
                "`wind_speed` DECIMAL(5,2) NULL DEFAULT NULL,"
                "`wind_gust` DECIMAL(5,2) NULL DEFAULT NULL,"
                "`wind_direction` VARCHAR(8) NULL DEFAULT NULL,"
                "`wind_direction_degrees` INT NULL DEFAULT NULL,"
                "`uv_index` INT NULL DEFAULT NULL,"
                "`solar_irradiance` DECIMAL(6,2) NULL DEFAULT NULL,"
                "`precipitation` DECIMAL(5,2) NULL DEFAULT NULL,"
                "`precipitation_accumulated` DECIMAL(5,2) NULL DEFAULT NULL,"
                "`pressure` DECIMAL(6,2) NULL DEFAULT NULL,"
                "`conditions` VARCHAR(45) NULL DEFAULT NULL,"
                "PRIMARY KEY (`datetime`));")
            
            try:
                # Attempt to execute the sql command on the database to create the table if it doesn't exist.
                dbcursor = db.cursor()
                dbcursor.execute(createTableSqlCmd)
                db.commit()
            except Exception as e:
                bf.logging.error('MySQL DB Create Table Error: %s', e)

            # This is the sql command will all the values inserted with their formatters.
            sqlcmd = (f"INSERT INTO {dbName} (datetime, temperature, feels_like, humidity, wind_speed, "
                    "wind_gust, wind_direction, wind_direction_degrees, uv_index, precipitation, pressure, "
                    "conditions, precipitation_accumulated, solar_irradiance, dew_point) "
                    f"VALUES ('{timestamp}', {temperature:.2f}, {feels_like:.2f}, {humidity}, {wind_speed:.2f}, "
                    f"{wind_gust:.2f}, '{wind_direction_card}', {wind_direction_deg}, {uv_index}, {precipitation:.2f}, {pressure:.2f}, "
                    f"'{conditions}', {precipitation_accumulated:.2f}, {solar_irradiance_wm2:.2f}, {dew_point:.2f})")

            # If the bf.logging mode is set to "debug" then log the SQL Insert statement.
            bf.logging.debug(sqlcmd)

            try:
                # Attempt to execute the sql command on the database to insert the record.
                dbcursor = db.cursor()
                dbcursor.execute(sqlcmd)
                db.commit()
            except Exception as e:
                bf.logging.error('MySQL DB Insert Error: %s', e)
            else:
                bf.logging.info(f"{dbcursor.rowcount} record inserted into {dbName}.")

        scanEndTime = time.monotonic()  # Get the time at the end of this scan.
        scanTime = scanEndTime - scanStartTime
        bf.logging.debug("Scan time: %s seconds", scanTime)

        # Sleep for the remaining time left after processing the code
        sleepTime = UPDATE_RATE_SECONDS - scanTime
        if sleepTime < 0:
            bf.logging.warning("Program process time took longer than the update rate time. Considering increasing the update rate time.")
        else:
            try:
                global asleep
                asleep = True
                time.sleep(sleepTime)
                asleep = False
            except (SystemExit):
                bf.logging.info("Shutting down...")
                runLoop = False


if __name__ == '__main__':
    main()
