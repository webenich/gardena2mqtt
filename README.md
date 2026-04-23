![GitHub Release](https://img.shields.io/github/v/release/Domochip/gardena2mqtt)
![Docker Pulls](https://img.shields.io/docker/pulls/domochip/gardena2mqtt)
[![Publish Docker image](https://github.com/Domochip/gardena2mqtt/actions/workflows/docker-publish-release.yml/badge.svg)](https://github.com/Domochip/gardena2mqtt/actions/workflows/docker-publish-release.yml)
[![Publish Docker Dev image](https://github.com/Domochip/gardena2mqtt/actions/workflows/docker-publish-dev.yml/badge.svg)](https://github.com/Domochip/gardena2mqtt/actions/workflows/docker-publish-dev.yml)

# Prerequisites

You need one or more Gardena Smart system devices:  
https://www.gardena.com/int/products/smart-system/smart-system  

Follow the official documentation to get API access:  
https://developer.husqvarnagroup.cloud/docs/get-started  

This application connects to both Authentication API and Gardena Smart System API:

![Application](application.png)

---

# How it works

![Diagram](gardena2mqtt.svg)

This application uses the Gardena Cloud WebSocket API to receive real-time updates from your devices.

---

# Installation

## 🔧 Recommended: Docker Compose + `.env`

### 1. Create your configuration file

```bash
cp .env.example .env
nano .env

Example .env:

# Gardena API
GARDENA_CLIENT_ID=your-client-id
GARDENA_CLIENT_SECRET=your-client-secret

# MQTT
MQTT_HOST=192.168.1.x
MQTT_PORT=1883
MQTT_PREFIX=gardena2mqtt
MQTT_CLIENTID=gardena2mqtt
MQTT_USER=mqtt_user
MQTT_PASSWORD=mqtt_password
2. Docker Compose
version: '3'

services:
  gardena2mqtt:
    container_name: gardena2mqtt
    image: domochip/gardena2mqtt:latest
    env_file:
      - ../.env
    restart: always
3. Start
docker compose up -d
🐳 Alternative: Docker CLI
docker run -d \
  --name gardena2mqtt \
  --restart=always \
  --env-file .env \
  domochip/gardena2mqtt:latest
Configuration
Environment variables
Variable	Description
GARDENA_CLIENT_ID	Gardena Application key
GARDENA_CLIENT_SECRET	Gardena Application secret
MQTT_HOST	MQTT broker address
MQTT_PORT	MQTT port (default: 1883)
MQTT_PREFIX	MQTT topic prefix
MQTT_CLIENTID	MQTT client ID
MQTT_USER	MQTT username
MQTT_PASSWORD	MQTT password
Topics
Status

Topic:

gardena2mqtt/connected

Payload:

Value	Meaning
0	Disconnected
1	Connected to MQTT only
2	Connected to MQTT + Gardena
Device state

Topic:

gardena2mqtt/<DeviceName>

Example:

gardena2mqtt/MySileno

Published when:

Startup
Reconnection
Device update
Device control

Command topic:

gardena2mqtt/<DeviceName>/control

Result topic:

gardena2mqtt/<DeviceName>/result
Mower
{"command":"start_seconds_to_override","duration":3600}
{"command":"start_dont_override"}
{"command":"park_until_next_task"}
{"command":"park_until_further_notice"}
Power Socket
{"command":"start_seconds_to_override","duration":3600}
{"command":"start_override"}
{"command":"stop_until_next_task"}
{"command":"pause"}
{"command":"unpause"}
Irrigation Control
{"command":"start_seconds_to_override","duration":3600,"valve_id":"id"}
{"command":"stop_until_next_task","valve_id":"id"}
{"command":"pause","valve_id":"id"}
{"command":"unpause","valve_id":"id"}
Water Control
{"command":"start_seconds_to_override","duration":3600}
{"command":"stop_until_next_task"}
{"command":"pause"}
{"command":"unpause"}
Logs
docker logs gardena2mqtt
Update
docker compose pull
docker compose up -d
Security

⚠️ Never commit your .env file

Use .env.example as template.

Thanks

Based on:
https://github.com/py-smart-gardena/py-smart-gardena