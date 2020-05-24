# RFLink Gateway to MQTT

## Purpose
Bridge between RFLink Gateway and MQTT broker.

## Current features
Forwarding messages received on TTY port from RFLink Gateway Arduino board
to MQTT broker in both directions.

Every message received from RFLinkGateway is split into single parameters
and published to different MQTT topics.
Example:
Message:
`20;83;Oregon Rain2;ID=2a19;RAIN=002a;RAINTOT=0054;BAT=OK;`

 is translated to following topics:

 `/data/RFLINK/Oregon Rain2/2a19/R/RAIN 002a`

 `/data/RFLINK/Oregon Rain2/2a19/R/RAINTOT 0054`

 `/data/RFLINK/Oregon Rain2/2a19/R/BAT OK`
  
`20;37;Acurite;ID=cbd5;TEMP=0066;HUM=79;WINSP=001a;BAT=OK`  
  
```ascii```
```
/data/RFLINK/Acurite/cbd5/R/TEMP 10.2
/data/RFLINK/Acurite/cbd5/R/HUM 73
/data/RFLINK/Acurite/cbd5/R/WINSP 2.6
/data/RFLINK/Acurite/cbd5/R/BAT OK
```
  
```json```
```
/data/RFLINK/Acurite/cbd5/R/TEMP {"value": 10.2}
/data/RFLINK/Acurite/cbd5/R/HUM {"value": 73}
/data/RFLINK/Acurite/cbd5/R/WINSP {"value": 2.6}
/data/RFLINK/Acurite/cbd5/R/BAT {"value": "OK"}
```
  
Every message received on particular MQTT topic is translated to
RFLink Gateway and sent to 433 MHz.

## Dependencies
Install the dependencies with the following commands:

sudo python3 -m pip install pyserial paho-mqtt tornado

## Start as a Service

sudo nano /lib/systemd/system/rfLink2mqtt.service

[Unit]
Description=RFLink2MQTTBridge
After=multi-user.target
Conflicts=getty@tty1.service

[Service]
Type=simple
WorkingDirectory=/home/pi/RFLinkGateway/
ExecStart=/usr/bin/python3 /home/pi/RFLinkGateway/RFLinkGateway.py
User=root

[Install]
WantedBy=multi-user.target

sudo systemctl daemon-reload
sudo systemctl enable rfLink2mqtt.service


## Configuration

Whole configuration is located in config.json file.

```json
{
  "mqtt_host": "your.mqtt.host",
  "mqtt_port": 1883,
  "mqtt_prefix": "/data/RFLINK",
  "mqtt_format": "json",
  "rflink_tty_device": "/dev/ttyUSB0",
  "rflink_direct_output_params": ["BAT", "CMD", "SET_LEVEL", "SWITCH", "HUM", "CHIME", "PIR", "SMOKEALERT"],
  "rflink_signed_output_params": ["TEMP", "WINCHL", "WINTMP"],
  "rflink_wdir_output_params": ["WINDIR"]
}
```

config param | meaning
-------------|---------
| mqtt_host | MQTT broker host |
| mqtt_port | MQTT broker port|
| mqtt_prefix | prefix for publish and subscribe topic|
| mqtt_format | publish and subscribe topic as json |
| rflink_tty_device | Arduino tty device |
| rflink_direct_output_params | Parameters transferred to MQTT without any processing |
| rflink_signed_output_params | Parameters with signed values |
| rflink_wdir_output_params | Parameters with wind direction values |

## Output data
Application pushes informations to MQTT broker in following format:
[mqtt_prefix]/[device_type]/[device_id]/R/[parameter]

`/data/RFLINK/TriState/8556a8/R/1 OFF`

Except if there its a CMD (Normally a signal from a switch), it is pushed to the following Topic:
[mqtt_prefix]/[device_type]/[device_id]/[switch_id]/R/[parameter]
like this, you only have to read the command message to use with devices with two or more switches

`/data/RFLINK/NewKaku/0201e3fa/2/READ/CMD ON`

Every change should be published to topic:
[mqtt_prefix]/[device_type]/[device_id]/W/[switch_ID]

`/data/RFLINK/TriState/8556a8/W/1 ON`


## References
- RFLink Gateway project http://www.rflink.nl/
- RFLink Gateway protocol http://www.rflink.nl/blog2/protref
