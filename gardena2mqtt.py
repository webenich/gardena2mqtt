#!/usr/bin/env python3

import asyncio
import logging
import time
import os
import signal
import json
from gardena.smart_system import SmartSystem
import paho.mqtt.client as mqtt


# Objets/états globaux
mqttclient = None
eventloop = None

location = None
smart_system = None

mqttclientconnected = False
smartsystemclientconnected = False
stopping = False

mqttprefix = None
mqtthost = None
mqttport = None
gardenaclientid = None
gardenaclientsecret = None


def publish_device(device):
    infos = {"datetime": time.strftime("%Y-%m-%d %H:%M:%S")}
    for attr_name in vars(device):
        if not attr_name.startswith('_') and attr_name not in ('location', 'callbacks'):
            infos[attr_name] = getattr(device, attr_name)
    mqttclient.publish(f"{mqttprefix}/{device.name}", json.dumps(infos))


def publish_everything():
    global location
    if location is None:
        return
    for device in location.devices.values():
        publish_device(device)


def subscribe_device(device):
    global mqttclientconnected
    if mqttclientconnected:
        mqttclient.subscribe(f"{mqttprefix}/{device.name}/control")


def subscribe_everything():
    global location
    if location is None:
        return
    for device in location.devices.values():
        subscribe_device(device)


def set_connected_state(ws_connected=None, mqtt_connected=None):
    global smartsystemclientconnected, mqttclientconnected

    if ws_connected is not None:
        smartsystemclientconnected = ws_connected
    if mqtt_connected is not None:
        mqttclientconnected = mqtt_connected

    if mqttclientconnected:
        mqttclient.publish(
            f"{mqttprefix}/connected",
            ("2" if smartsystemclientconnected else "1"),
            0,
            True
        )


def on_mqtt_connect(client, userdata, flags, reason_code, properties):
    logging.info("Connected to MQTT host")
    set_connected_state(mqtt_connected=True)
    subscribe_everything()

    if smartsystemclientconnected:
        publish_everything()


def on_mqtt_disconnect(client, userdata, disconnect_flags, reason_code, properties):
    logging.info("Disconnected from MQTT host")
    set_connected_state(mqtt_connected=False)


def on_mqtt_message(client, userdata, msg):
    global location, eventloop

    if location is None:
        logging.error("No Gardena location loaded")
        return

    splitted_topic = msg.topic.split('/')
    splitted_topic[-1] = 'result'
    result_topic = '/'.join(splitted_topic)

    try:
        decoded_payload = msg.payload.decode('utf-8')
    except Exception:
        logging.error("Invalid payload")
        mqttclient.publish(result_topic, json.dumps({"status": "error", "message": "invalid payload"}))
        return

    this_device_name = splitted_topic[-2]
    this_device = None
    for device in location.devices.values():
        if device.name == this_device_name:
            this_device = device
            break

    if this_device is None:
        logging.error(f"Unknown device: {this_device_name}")
        mqttclient.publish(result_topic, json.dumps({"status": "error", "message": f"unknown device: {this_device_name}"}))
        return

    try:
        parsed_payload = json.loads(decoded_payload)
    except Exception:
        logging.error("Invalid JSON")
        mqttclient.publish(result_topic, json.dumps({"status": "error", "message": "invalid json"}))
        return

    try:
        method = getattr(this_device, parsed_payload['command'])
    except Exception:
        logging.error("Invalid command")
        mqttclient.publish(result_topic, json.dumps({"status": "error", "message": "invalid command"}))
        return

    params = []
    for param in method.__code__.co_varnames:
        if param not in ('self', 'data'):
            if param in parsed_payload:
                params.append(parsed_payload[param])
            else:
                logging.error(f"Missing param {param}")
                mqttclient.publish(result_topic, json.dumps({"status": "error", "message": f"missing param {param}"}))
                return

    try:
        if not eventloop.is_running():
            logging.error("Loop not running")
            mqttclient.publish(result_topic, json.dumps({"status": "error", "message": "loop not running"}))
            return

        if len(params) == 0:
            future = asyncio.run_coroutine_threadsafe(method(), eventloop)
        elif len(params) == 1:
            future = asyncio.run_coroutine_threadsafe(method(params[0]), eventloop)
        elif len(params) == 2:
            future = asyncio.run_coroutine_threadsafe(method(params[0], params[1]), eventloop)
        else:
            logging.error("Too many params")
            mqttclient.publish(result_topic, json.dumps({"status": "error", "message": "too many params"}))
            return

        future.result(timeout=30)
        mqttclient.publish(result_topic, json.dumps({"status": "ok"}))

    except Exception as exc:
        logging.exception("Command failed")
        mqttclient.publish(result_topic, json.dumps({"status": "error", "message": str(exc)}))


def on_ws_status_changed(status):
    logging.info(f"WebSocket status : {status}")
    set_connected_state(ws_connected=status)

    if status and mqttclientconnected:
        publish_everything()


def on_device_update(device):
    if mqttclientconnected:
        publish_device(device)


def shutdown(signum=None, frame=None):
    global stopping
    if stopping:
        return
    stopping = True
    logging.info("Shutdown requested")
    if eventloop.is_running():
        eventloop.call_soon_threadsafe(eventloop.stop)


async def init_gardena_session():
    global smart_system, location

    logging.info("Initializing Gardena session")
    smart_system = SmartSystem(
        client_id=gardenaclientid,
        client_secret=gardenaclientsecret
    )

    await smart_system.authenticate()
    await smart_system.update_locations()

    if not smart_system.locations:
        raise RuntimeError("No Gardena locations found")

    location = list(smart_system.locations.values())[0]
    await smart_system.update_devices(location)

    smart_system.add_ws_status_callback(on_ws_status_changed)

    for device in location.devices.values():
        device.add_callback(on_device_update)

    logging.info(f"Gardena location loaded: {location.name}")
    logging.info(f"Devices loaded: {len(location.devices)}")

    if mqttclientconnected:
        subscribe_everything()
        publish_everything()


async def ws_supervisor():
    global smart_system, location

    backoff = 15

    while not stopping:
        try:
            set_connected_state(ws_connected=False)
            location = None
            smart_system = None

            await init_gardena_session()

            logging.info("Starting Gardena websocket")
            await smart_system.start_ws(location)

            # Si on arrive ici sans exception, c'est que start_ws s'est terminé "proprement"
            logging.warning("start_ws() returned unexpectedly")

        except asyncio.CancelledError:
            logging.info("Websocket supervisor cancelled")
            raise

        except Exception:
            logging.exception("Websocket supervisor error")

        set_connected_state(ws_connected=False)

        if stopping:
            break

        logging.info(f"Reconnecting in {backoff} seconds")
        await asyncio.sleep(backoff)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s: %(message)s",
        datefmt="%H:%M:%S"
    )

    gardenaclientid = os.getenv("GARDENA_CLIENT_ID")
    gardenaclientsecret = os.getenv("GARDENA_CLIENT_SECRET")

    mqttprefix = os.getenv("MQTT_PREFIX", os.getenv("PREFIX", "gardena2mqtt"))
    mqtthost = os.getenv("MQTT_HOST", os.getenv("HOST", "localhost"))
    mqttport = int(os.getenv("MQTT_PORT", os.getenv("PORT", 1883)))

    mqttclient = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    mqttclient.on_connect = on_mqtt_connect
    mqttclient.on_disconnect = on_mqtt_disconnect
    mqttclient.on_message = on_mqtt_message
    mqttclient.will_set(f"{mqttprefix}/connected", "0", 0, True)

    eventloop = asyncio.new_event_loop()
    asyncio.set_event_loop(eventloop)

    try:
        eventloop.add_signal_handler(signal.SIGINT, shutdown)
        eventloop.add_signal_handler(signal.SIGTERM, shutdown)
    except NotImplementedError:
        signal.signal(signal.SIGINT, shutdown)
        signal.signal(signal.SIGTERM, shutdown)

    mqttclient.connect(mqtthost, mqttport)
    mqttclient.loop_start()

    supervisor_task = eventloop.create_task(ws_supervisor())

    try:
        eventloop.run_forever()
    finally:
        logging.info("Stopping cleanly")

        if not supervisor_task.done():
            supervisor_task.cancel()
            try:
                eventloop.run_until_complete(supervisor_task)
            except Exception:
                pass

        pending = [t for t in asyncio.all_tasks(eventloop) if not t.done()]
        for task in pending:
            task.cancel()

        if pending:
            try:
                eventloop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
            except Exception:
                pass

        mqttclient.disconnect()
        mqttclient.loop_stop()

        eventloop.close()