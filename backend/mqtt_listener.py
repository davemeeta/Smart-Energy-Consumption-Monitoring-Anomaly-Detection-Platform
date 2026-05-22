import paho.mqtt.client as mqtt
import json, os
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS
from dotenv import load_dotenv
from models.isolation_forest import EnergyAnomalyDetector
from models.autoencoder import AutoencoderDetector
from co2_calculator import calculate

load_dotenv()

influx = InfluxDBClient(
    url=os.getenv("INFLUX_URL", "http://localhost:8086"),
    token=os.getenv("INFLUX_TOKEN", "my-super-secret-token"),
    org=os.getenv("INFLUX_ORG", "energyorg"),
)
write_api = influx.write_api(write_options=SYNCHRONOUS)

iso_detector = EnergyAnomalyDetector()
ae_detector  = AutoencoderDetector()
latest_events = []

def on_message(client, userdata, msg):
    data = json.loads(msg.payload)
    kwh     = data["kwh"]
    voltage = data["voltage"]
    temp    = data["temperature"]

    # Train models
    iso_detector.add_reading(kwh, voltage, temp)
    ae_detector.add_and_train(kwh, voltage, temp)

    # Get predictions
    iso = iso_detector.predict(kwh, voltage, temp)
    ae  = ae_detector.predict(kwh, voltage, temp)
    co2 = calculate(kwh)

    # Smart ensemble:
    # - If neither model is ready yet, no anomaly
    # - If only one model is ready, trust it alone
    # - If both ready, require BOTH to agree (reduces false positives)
    both_ready = iso["iso_ready"] and ae["ae_ready"]
    one_ready  = iso["iso_ready"] or ae["ae_ready"]

    if both_ready:
        is_anomaly = iso["iso_anomaly"] and ae["ae_anomaly"]
    elif one_ready:
        is_anomaly = iso["iso_anomaly"] or ae["ae_anomaly"]
    else:
        is_anomaly = False

    # Write to InfluxDB
    point = (
        Point("energy_reading")
        .tag("sensor_id", data["sensor_id"])
        .field("kwh", kwh)
        .field("voltage", voltage)
        .field("temperature", temp)
        .field("anomaly", int(is_anomaly))
        .field("iso_score", iso["iso_score"])
        .field("ae_error", ae["reconstruction_error"])
        .field("ae_threshold", ae["ae_threshold"] or 0.0)
        .field("co2_kg", co2["co2_kg"])
        .field("cost_eur", co2["cost_eur"])
    )
    write_api.write(bucket=os.getenv("INFLUX_BUCKET", "energy"), record=point)

    event = {
        **data,
        "is_anomaly":          is_anomaly,
        "iso_anomaly":         iso["iso_anomaly"],
        "iso_score":           iso["iso_score"],
        "iso_ready":           iso["iso_ready"],
        "ae_anomaly":          ae["ae_anomaly"],
        "reconstruction_error": ae["reconstruction_error"],
        "ae_threshold":        ae["ae_threshold"],
        "ae_ready":            ae["ae_ready"],
        **co2
    }
    latest_events.append(event)
    if len(latest_events) > 100:
        latest_events.pop(0)

    # Status line
    iso_status = f"ISO={'🚨' if iso['iso_anomaly'] else '✅'}" if iso["iso_ready"] else "ISO=⏳"
    ae_status  = f"AE={'🚨' if ae['ae_anomaly'] else '✅'}(err={ae['reconstruction_error']})" if ae["ae_ready"] else "AE=⏳"
    print(f"{'🚨 ANOMALY' if is_anomaly else '✅ Normal'} | kWh={kwh} | {iso_status} | {ae_status} | CO2={co2['co2_kg']}kg")

def start_listener():
    client = mqtt.Client()
    client.on_message = on_message
    client.connect(
        os.getenv("MQTT_BROKER", "localhost"),
        int(os.getenv("MQTT_PORT", 1883)),
    )
    client.subscribe(os.getenv("MQTT_TOPIC", "energy/sensors"))
    print("MQTT listener started")
    client.loop_forever()