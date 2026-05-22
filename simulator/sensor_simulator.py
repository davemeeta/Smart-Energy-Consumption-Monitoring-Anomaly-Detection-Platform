import paho.mqtt.client as mqtt
import json, time, os, random
import pandas as pd
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))

BROKER = os.getenv("MQTT_BROKER", "localhost")
PORT   = int(os.getenv("MQTT_PORT", 1883))
TOPIC  = os.getenv("MQTT_TOPIC", "energy/sensors")
SPEED  = float(os.getenv("SIM_SPEED", 1.0))  # seconds between readings

# ── Load and clean the UCI dataset ───────────
DATA_FILE = os.path.join(os.path.dirname(__file__), "household_power_consumption.txt")

print("Loading UCI dataset...")
df = pd.read_csv(
    DATA_FILE,
    sep=";",
    parse_dates={"datetime": ["Date", "Time"]},
    infer_datetime_format=True,
    low_memory=False,
    na_values=["?"]
)

# Drop rows with missing values
df.dropna(inplace=True)

# Convert to numeric
df["Global_active_power"]   = pd.to_numeric(df["Global_active_power"])
df["Voltage"]               = pd.to_numeric(df["Voltage"])
df["Global_intensity"]      = pd.to_numeric(df["Global_intensity"])
df["Sub_metering_1"]        = pd.to_numeric(df["Sub_metering_1"])
df["Sub_metering_2"]        = pd.to_numeric(df["Sub_metering_2"])
df["Sub_metering_3"]        = pd.to_numeric(df["Sub_metering_3"])

# Convert Global_active_power (kW) to kWh per minute
df["kwh"] = df["Global_active_power"] / 60.0

print(f"Dataset loaded: {len(df):,} readings from {df['datetime'].min()} to {df['datetime'].max()}")
print(f"kWh range: {df['kwh'].min():.3f} – {df['kwh'].max():.3f}")
print(f"Starting replay...\n")

# ── Connect to MQTT ───────────────────────────
client = mqtt.Client()
client.connect(BROKER, PORT)
print(f"Connected to MQTT broker at {BROKER}:{PORT}")

# ── Replay dataset row by row ─────────────────
sensors = ["sensor_kitchen", "sensor_laundry", "sensor_hvac"]

for i, row in df.iterrows():
    # Map UCI columns to our schema
    reading = {
        "timestamp":    time.time(),
        "sensor_id":    random.choice(sensors),
        "kwh":          round(float(row["kwh"]), 4),
        "voltage":      round(float(row["Voltage"]), 1),
        "temperature":  round(20 + float(row["Global_intensity"]) * 0.3, 1),
        "sub_metering": round(float(row["Sub_metering_1"]) +
                              float(row["Sub_metering_2"]) +
                              float(row["Sub_metering_3"]), 2),
        # Keep original timestamp for reference
        "original_ts":  str(row["datetime"]),
    }

    client.publish(TOPIC, json.dumps(reading))
    print(f"[{row['datetime']}] kWh={reading['kwh']:.4f} | "
          f"V={reading['voltage']} | sensor={reading['sensor_id']}")

    time.sleep(SPEED)

print("Dataset replay complete.")