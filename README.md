![GitHub Release](https://img.shields.io/github/v/release/Domochip/gardena2mqtt)
![Docker Pulls](https://img.shields.io/docker/pulls/domochip/gardena2mqtt)
[![Publish Docker image](https://github.com/Domochip/gardena2mqtt/actions/workflows/docker-publish-release.yml/badge.svg)](https://github.com/Domochip/gardena2mqtt/actions/workflows/docker-publish-release.yml)
[![Publish Docker Dev image](https://github.com/Domochip/gardena2mqtt/actions/workflows/docker-publish-dev.yml/badge.svg)](https://github.com/Domochip/gardena2mqtt/actions/workflows/docker-publish-dev.yml)

# gardena2mqtt

Gateway to control and monitor Gardena Smart System devices via MQTT.

---

# About this fork

This fork focuses on a **simple, robust and generic MQTT integration**.

Compared to the original project:

- ❌ Home Assistant MQTT discovery support has been removed  
- ✅ Plain MQTT topics are published (no abstraction layer)  
- ✅ Designed for custom integrations (e.g. Domoticz via bridge)  
- ✅ Improved stability with WebSocket supervisor (Python 3.12 compatible)

This makes the project easier to integrate into **non-Home Assistant environments**.

---

# Prerequisites

You need one or more Gardena Smart system devices:  
https://www.gardena.com/int/products/smart-system/smart-system  

Get API credentials from:  
https://developer.husqvarnagroup.cloud/docs/get-started  

---

# How it works


Gardena Cloud → gardena2mqtt → MQTT → your system (Domoticz, etc.)


The application connects to Gardena Cloud and publishes all device updates to MQTT in real time.

---

# Installation

## 🔧 Recommended: Docker Compose + `.env`

### 1. Create configuration

```bash
cp .env.example .env
nano .env

Example:

# Gardena API
GARDENA_CLIENT_ID=your-client-id
GARDENA_CLIENT_SECRET=your-client-secret

# MQTT
MQTT_HOST=127.0.0.1
MQTT_PORT=1883
MQTT_PREFIX=gardena2mqtt

# Optional
MQTT_CLIENTID=gardena2mqtt
MQTT_USER=
MQTT_PASSWORD=
2. Docker Compose
services:
  gardena2mqtt:
    container_name: gardena2mqtt
    image: domochip/gardena2mqtt:latest
    env_file:
      - ../.env
    restart: always
    network_mode: host
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
GARDENA_CLIENT_ID	Gardena API client ID
GARDENA_CLIENT_SECRET	Gardena API secret
MQTT_HOST	MQTT broker hostname/IP
MQTT_PORT	MQTT port (default: 1883)
MQTT_PREFIX	MQTT topic prefix
MQTT_CLIENTID	MQTT client ID
MQTT_USER	MQTT username
MQTT_PASSWORD	MQTT password
MQTT Topics
Status

Topic:

gardena2mqtt/connected

Payload:

Value	Meaning
0	Disconnected
1	Connected to MQTT only
2	Connected to MQTT + Gardena Cloud
Device state

Topic:

gardena2mqtt/<DeviceName>

Example:

gardena2mqtt/MySileno

Published when:

Startup
Reconnection
Device update

Payload: JSON with all device attributes.

Device control

Command topic:

gardena2mqtt/<DeviceName>/control

Result topic:

gardena2mqtt/<DeviceName>/result
Domoticz integration example

This fork publishes plain MQTT data, so integration with Domoticz requires a bridge.

An example is provided:

examples/domoticz_bridge_example.py
Architecture
Gardena → MQTT → bridge script → Domoticz
What the bridge does
subscribes to gardena2mqtt/#
parses JSON payloads
maps values to Domoticz IDX
updates devices via Domoticz API
Configuration

Edit:

IDX_MAP = {
    "DeviceName": {
        "temperature": 123,
        "humidity": 124
    }
}

You must adapt this mapping to your own Domoticz devices.

Logs
docker logs gardena2mqtt
Update
docker compose pull
docker compose up -d
Security

⚠️ Never commit your .env file
✔ Use .env.example as template

Troubleshooting
Check logs: docker logs gardena2mqtt
Verify MQTT connectivity
Ensure Gardena API credentials are valid
Check WebSocket status in logs
Thanks

This project is based on:

https://github.com/py-smart-gardena/py-smart-gardena