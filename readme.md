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

`20;37;Acurite;ID=cbd5;TEMP=0066;HUM=79;WINSP=001a;BAT=OK`

### ASCII
```
/data/RFLINK/Acurite/cbd5/READ/TEMP 10.2
/data/RFLINK/Acurite/cbd5/READ/HUM 73
/data/RFLINK/Acurite/cbd5/READ/WINSP 2.6
/data/RFLINK/Acurite/cbd5/READ/BAT OK
```

### JSON
```json
/data/RFLINK/Acurite/cbd5/READ/TEMP {"value": 10.2}
/data/RFLINK/Acurite/cbd5/READ/HUM {"value": 73}
/data/RFLINK/Acurite/cbd5/READ/WINSP {"value": 2.6}
/data/RFLINK/Acurite/cbd5/READ/BAT {"value": "OK"}
```

Every message received on particular MQTT topic is translated to
RFLink Gateway and sent to 433 MHz.

## Installation
Install the dependencies with the following commands:

`pip install -r requirements.txt `



## Configuration

Whole configuration is located in config.json file. You can copy and edit `config.json.sample`.

```json
{
  "mqtt_host": "your_mqtt_host",
  "mqtt_port": 1883,
  "mqtt_prefix": "/data/RFLINK",
  "mqtt_format": "json",
  "mqtt_message_timeout": 60,
  "mqtt_user":"your_mqtt_user",
  "mqtt_password":"your_mqtt_password",
  "rflink_tty_device": "/dev/ttyUSB0",
  "rflink_direct_output_params": [
    "BAT",
    "CMD",
    "SET_LEVEL",
    "SWITCH",
    "HUM",
    "CHIME",
    "PIR",
    "SMOKEALERT"
  ],
  "rflink_signed_output_params": [
    "TEMP",
    "WINCHL",
    "WINTMP"
  ],
  "rflink_wdir_output_params": [
    "WINDIR"
  ]
}
```

config param  | meaning
------------- |---------
 mqtt_host    | MQTT broker host |
 mqtt_port    | MQTT broker port|
 mqtt_prefix  | prefix for publish and subscribe topic|
 mqtt_format  | publish and subscribe topic as `json` or `ascii` |
 rflink_tty_device | Serial device |
 rflink_direct_output_params | Parameters transferred to MQTT without any processing |
 rflink_signed_output_params | Parameters with signed values |
 rflink_wdir_output_params | Parameters with wind direction values |



## Running

Scripts assume script directory located at: `/opt/scripts/RFLinkGateway`, and virtualenv was used. If not, use system Python binary, not the virtualenv'ed one.

### Running in Supervisor

```Shell
vim supervisor_RFLinkGateway
cp supervisor_RFLinkGateway /etc/supervisor/conf.d/
supervisorctl reread
supervisorctl update
supervisorctl start RFLinkGateway
```

### Start as a Service

```Shell
vim RFLinkGateway.service
cp RFLinkGateway.service /lib/systemd/system/RFLinkGateway.service
sudo systemctl daemon-reload
sudo systemctl enable RFLinkGateway.service
```

### Logging
Script logs to STDOUT, it can be redirected through supervisord to files or syslog.


## Output data

Application pushes informations to MQTT broker in following format:
`[mqtt_prefix]/[device_type]/[device_id]/READ/[parameter]`

`/data/RFLINK/TriState/8556a8/READ/1 OFF`

Except if there its a CMD (Normally a signal from a switch), it is pushed to the following topic:
`[mqtt_prefix]/[device_type]/[device_id]/[switch_id]/READ/[parameter]`

like this, you only have to read the command message to use with devices with two or more switches

`/data/RFLINK/NewKaku/0201e3fa/2/READ/CMD ON`

Every change should be published to topic:
`[mqtt_prefix]/[device_type]/[device_id]/WRITE/[switch_ID]`

`/data/RFLINK/TriState/8556a8/WRITE/1 ON`



## References
- RFLink Gateway project http://www.rflink.nl/
- RFLink Gateway protocol http://www.rflink.nl/blog2/protref
