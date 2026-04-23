#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import time
import requests
import paho.mqtt.client as mqtt

# ----------------------------
# Configuration
# ----------------------------
MQTT_HOST = "127.0.0.1"
MQTT_PORT = 1883
MQTT_TOPIC = "gardena2mqtt/#"

DOMOTICZ_URL = "http://127.0.0.1:8080/json.htm"

# Mapping example:
# topic suffix -> Domoticz idx
IDX_MAP = {
    "Mower": {
        "battery_level": 123,
        "activity": 124,
        "state": 125,
    },
    "humidity": {
        "battery_level": 126,
        "temperature": 127,
        "humidity": 128,
    },
    "Dual Water Control": {
        "activity": 129,
        "state": 130,
    },
}


def domoticz_update(idx, value, svalue=""):
    params = {
        "type": "command",
        "param": "udevice",
        "idx": idx,
        "nvalue": value,
        "svalue": svalue,
    }
    try:
        r = requests.get(DOMOTICZ_URL, params=params, timeout=10)
        r.raise_for_status()
    except Exception as e:
        print(f"[ERROR] Domoticz update failed idx={idx}: {e}")


def handle_device_payload(device_name, payload):
    if device_name not in IDX_MAP:
        return

    mapping = IDX_MAP[device_name]

    # battery_level example
    if "battery_level" in payload and "battery_level" in mapping:
        domoticz_update(mapping["battery_level"], 0, str(payload["battery_level"]))

    # temperature example
    if "temperature" in payload and "temperature" in mapping:
        domoticz_update(mapping["temperature"], 0, str(payload["temperature"]))

    # humidity example
    if "humidity" in payload and "humidity" in mapping:
        domoticz_update(mapping["humidity"], 0, str(payload["humidity"]))

    # string state examples
    if "activity" in payload and "activity" in mapping:
        domoticz_update(mapping["activity"], 0, str(payload["activity"]))

    if "state" in payload and "state" in mapping:
        domoticz_update(mapping["state"], 0, str(payload["state"]))


def on_connect(client, userdata, flags, reason_code, properties=None):
    print(f"[INFO] Connected to MQTT rc={reason_code}")
    client.subscribe(MQTT_TOPIC)


def on_message(client, userdata, msg):
    topic = msg.topic

    # Ignore status topic and control/result topics
    if topic.endswith("/connected") or topic.endswith("/control") or topic.endswith("/result"):
        return

    try:
        payload = json.loads(msg.payload.decode("utf-8"))
    except Exception as e:
        print(f"[ERROR] Invalid JSON on {topic}: {e}")
        return

    # Expected topic: gardena2mqtt/<device_name>
    parts = topic.split("/", 1)
    if len(parts) != 2:
        return

    device_name = parts[1]
    handle_device_payload(device_name, payload)


def main():
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.on_connect = on_connect
    client.on_message = on_message

    while True:
        try:
            client.connect(MQTT_HOST, MQTT_PORT, 60)
            client.loop_forever()
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"[ERROR] MQTT loop crashed: {e}")
            time.sleep(10)


if __name__ == "__main__":
    main()