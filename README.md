![GitHub Release](https://img.shields.io/github/v/release/Domochip/gardena2mqtt)
![Docker Pulls](https://img.shields.io/docker/pulls/domochip/gardena2mqtt)
[![Publish Docker image](https://github.com/Domochip/gardena2mqtt/actions/workflows/docker-publish-release.yml/badge.svg)](https://github.com/Domochip/gardena2mqtt/actions/workflows/docker-publish-release.yml)
[![Publish Docker Dev image](https://github.com/Domochip/gardena2mqtt/actions/workflows/docker-publish-dev.yml/badge.svg)](https://github.com/Domochip/gardena2mqtt/actions/workflows/docker-publish-dev.yml)


gardena2mqtt

Gateway to control and monitor **Gardena Smart System devices via MQTT.

⚠️ Breaking change

This fork removes Home Assistant MQTT discovery support.

👉 The project now focuses on:

simple MQTT publishing
robustness
compatibility with any system (not only Home Assistant)
About this fork

This fork focuses on a simple, robust and generic MQTT integration.

Compared to the original project:

❌ Home Assistant MQTT discovery removed
✅ Plain MQTT topics (no abstraction layer)
✅ Designed for custom integrations (e.g. Domoticz via bridge)
✅ WebSocket supervisor for automatic reconnection
✅ Python 3.12+ compatibility

👉 Goal: make it reliable and usable in any MQTT-based system

Prerequisites

You need one or more Gardena Smart system devices:
https://www.gardena.com/int/products/smart-system/smart-system

Get API credentials from:
https://developer.husqvarnagroup.cloud/docs/get-started

How it works
Gardena Cloud → gardena2mqtt → MQTT → your system (Domoticz, etc.)

The application connects to Gardena Cloud and publishes all device updates to MQTT in real time.

Installation
🔧 Recommended: Docker Compose + .env
1. Create configuration
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
    build:
      context: .
    env_file:
      - .env
    restart: always
    network_mode: host
3. Start
docker compose up -d
🐳 Alternative: Docker CLI
docker run -d \
  --name gardena2mqtt \
  --restart=always \
  --env-file .env \
  --network host \
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
1	MQTT only
2	MQTT + Gardena
Device state

Topic:

gardena2mqtt/<DeviceName>

Example:

gardena2mqtt/MySileno

Published when:

startup
reconnection
device update

Payload: JSON with all device attributes.

Device control

Command topic:

gardena2mqtt/<DeviceName>/control

Result topic:

gardena2mqtt/<DeviceName>/result
🔌 Domoticz integration example

This fork publishes plain MQTT data, so integration with Domoticz requires a bridge.

👉 Example provided:

examples/domoticz_bridge_example.py
Architecture
Gardena → MQTT → bridge script → Domoticz
What the bridge does
subscribes to gardena2mqtt/#
parses JSON payloads
maps values to Domoticz IDX
updates devices via Domoticz API
Configuration example
IDX_MAP = {
    "DeviceName": {
        "temperature": 123,
        "humidity": 124
    }
}

👉 Adapt this mapping to your own Domoticz devices.

Logs
docker logs gardena2mqtt
Update
docker compose build --no-cache
docker compose up -d
Security

⚠️ Never commit your .env file
✔ Use .env.example as template

Troubleshooting
Check logs: docker logs gardena2mqtt
Verify MQTT connectivity
Ensure Gardena API credentials are valid
Check WebSocket status in logs
Development note

.devcontainer/ is only for development
Do not use it for deployment.

Thanks

This project is based on:

https://github.com/py-smart-gardena/py-smart-gardena
https://github.com/Domochip/gardena2mqtt
