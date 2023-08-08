# WeatherXM API Python Scripts
A collection of scripts that use the [WeatherXM API](https://api.weatherxm.com/api/v1/docs/) to get weather station data for various purposes.  

This repository is not affiliated with or endorsed by [WeatherXM](https://weatherxm.com/).

## Dependancies
Python of course.  [Python 3](https://www.python.org/downloads/) is required to run these python scripts.  

Additionally, use pip (Python Package Manager that should come with Python) to install the following Python libraries:
``` bash
$ pip install requests json pytz
```

## Instructions
These Python scripts are designed to be run on a schedule.  On Linux and Windows you can use built-in tools like Cron and Task Scheduler.  On macOS you may need to download and install a 3rd party task scheduler. 

There are two methods to access weather station data from the WeatherXM API.  

#### __1. Public WeatherXM Explorer__
Anyone can access data via the public WeatherXM explorer API.  New data accessed via this method is available about every 6 minutes.  
To do this, enter your weather station 3-word name into the constant near the top of the script:
``` python
# WeatherXM Device Info
# Leave the username and password fields blank if the public API is desired.
WXM_USERNAME = ""
WXM_PASSWORD = ""
WXM_STATION_NAME = "Stormy Basil Cirrocumulus"
```

#### __2. Private WeatherXM Account__
If you are a weather station owner with a WeatherXM account, your device data can be accessed with your username and password.  New data accessed via this method is availabel about every 3 minutes.  
Enter your weather station 3-word name, along with your username and password, into the constant variables near the top of the script:
``` python
# WeatherXM Device Info
# Leave the username and password fields blank if the public API is desired.
WXM_USERNAME = "yourusername"
WXM_PASSWORD = "yoursecretpassword1"
WXM_STATION_NAME = "Stormy Basil Cirrocumulus"
```
___IMPORTANT___  
Note that while the secure HTTPS protocal is used and therefore your username and password IS encrypted when transmitted, it is NOT encrypted while at rest in this script on whatever machine you use to execute it.  Ideally WeatherXM would provide a way to generate a revocable API key with limited permission that could be used for this purpose.  As of yet, I am not aware of this ability.  Ensure you trust the machine you are using to execute this script and USE AT YOUR OWN RISK!  

### __wxm_to_tagoio.py Script__
To send the data to a Tago.io device using this script a Tago.io device token is required.  Within the Tago.io admin login, create a "Custom HTTPS" device.  Then either generate a new token or use the default one created with the device.  Enter this token into the constant "TAGOIO_DEVICE_TOKEN".
``` python
# Create a Tago.io "Custom HTTPS" device and enter the token here.
TAGOIO_DEVICE_TOKEN = "4a4ca431-f267-483a-92b7-735fe5be1b80"
```

In order to prevent duplicate entries, this script first queries the Tago.io device's last temperature entry and compares its timestamp against the data retrieved from the weather station.  If the timestamps match then no data is sent to Tago.io.    

Any metrics you are not interested in can be commented out from the tago_payload.

### __wxm_to_mysql.py Script__
This script can be used to send WeatherXM weather station data to a MySQL Server.  For convenience a SQL script for creating a compatable table is included (create_table.sql).  

This script depends on the MySQL Connector which can be installed with the Python Package installer by running:
``` bash
$ pip install mysql-connector-python
```

To be able to connect to your MySQL database be sure to fill in the following information near the top of the script:
``` python
# MySQL Database Info
DB_HOST = "192.168.1.201"
DB_PORT = "6603"
DB_USER = "dbusername"
DB_PASSWORD = "dbpassword"
DB_DATABASE = "dbname"
```  

No instructions are provided for how to properly setup a MySQL database server, enabled remote connections, create databases, or create tables.  

## Conversion Options
If you wish to convert from the default WeatherXM units, this script provides the same alternative units as WeatherXM does in their app and web app.  You can enable these conversions near the top of the script.  
``` python
# Conversion Options
C_TO_F = True
METERSPERSECOND_TO_MPH = False
MM_TO_INCH = False
HPA_TO_INHG = False
```
Additionally, converting from wind direction in degrees to cardinal directions is provided by default and included as a seperate variable (wind_direction_cardinal).  While seeing the wind direction displayed in cardinal form is easier to interpret, having it in degrees is useful if you want to be able to show a directional arrow.  

## Schedule Examples
### Cron
On Debian/Ubuntu systems, cron can be used to schedule the excution of the script.  
Open a terminal and enter the following command to edit the cron table:
``` bash
$ crontab -e
```
To run a script every 3 minutes add the following line:
``` bash
*/3 * * * * /usr/bin/python3 /home/yourusername/path/to/scripts/wxm_to_tagoio.py >/dev/null 2>&1
```
Save when exiting and the cron job will start being executed.  

### Windows Task Scheduler
On Windows operating systems you can use the Task Scheduler to schedule the execution of Python scripts.  

	Search for and open Task Scheduler.  
	Create Task...  
	Name the task.  
	Create a new trigger, begin the task on a schedule, daily, every 1 day, repeat task every - manually type "3 minutes", for a duration of "indefinitely".  
	Create a new action, action: "Start a program", "Programs/Script" input the path to python.exe, "Add Arguments" input the script file name, "Start in" input the path to where the script file is saved.  
	Add any "Conditions" or "Settings" you prefer.

For example:  
Path to Python: C:\Users\yourusername\AppData\Local\Programs\Python\Python311\python.exe  
Script File Name: ./wxm_to_tagoio.py  
Path to Location where Script is Saved: C:\path\to\scripts\