# ⚡ Smart Energy Consumption Monitoring & Anomaly Detection Platform

> **Originally created by [Meeta Dave](https://github.com/davemeeta)**

A production-grade, real-time IoT energy monitoring system that detects anomalous power consumption using machine learning, calculates CO₂ emissions impact, and visualizes everything through live dashboards.

Built to demonstrate end-to-end data engineering and ML skills relevant to the green energy sector 
---

## 🎯 What it does

- **Ingests** real household energy data (UCI dataset, 2M+ readings) via MQTT broker
- **Detects anomalies** in real time using an ensemble of Isolation Forest + PyTorch Autoencoder
- **Calculates CO₂ impact** using the German grid emission factor (0.380 kg CO₂/kWh)
- **Estimates cost savings** based on German electricity prices (€0.32/kWh)
- **Visualizes** everything through a live React dashboard and Grafana ops panels
- **Stores** all time-series data in InfluxDB for historical analysis

---

## 📸 Screenshots

### React Live Dashboard
![React Dashboard](/dashboard.png)

### Grafana Live Dashboard
![Grafana Dashboard](/grafana.png)

> 🔗 **[View Live Grafana Snapshot](http://localhost:3000/dashboard/snapshot/dmfgGeleZ3Iu8m03NCgoNMukideAhdx5)**
---

## 🏗️ Architecture

```
UCI Dataset / IoT Sensors
        │
        ▼
  MQTT Broker (Mosquitto)
        │
        ▼
  MQTT Subscriber (Python)
        │
        ├──► Isolation Forest (scikit-learn)
        ├──► Autoencoder (PyTorch)
        └──► CO₂ Calculator
        │
        ▼
  InfluxDB (time-series storage)
        │
        ├──► FastAPI + WebSocket
        │         │
        │         ▼
        │    React Dashboard
        │    (live kWh + anomaly feed)
        │
        └──► Grafana Dashboards
             (ops panels + alerts)
```

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| **Data source** | UCI Household Electric Power Consumption dataset (Kaggle) |
| **IoT protocol** | MQTT (Eclipse Mosquitto) |
| **ML — anomaly detection** | Isolation Forest (scikit-learn) + Autoencoder (PyTorch) |
| **Backend API** | FastAPI + WebSocket (Python) |
| **Time-series DB** | InfluxDB 2.7 |
| **Frontend** | React + Vite + Recharts |
| **Ops dashboard** | Grafana 10.4 |
| **Infrastructure** | Docker + Docker Compose |

---

## 🤖 ML Models

### Isolation Forest
- Unsupervised anomaly detection via random feature partitioning
- Contamination factor: 5% (expected anomaly rate)
- Retrains every 50 samples to adapt to consumption patterns
- Returns anomaly flag + decision score

### Autoencoder (PyTorch)
- 3-layer encoder → 2D bottleneck → 3-layer decoder
- Online training with rolling 500-sample buffer
- Dynamic threshold using 3-sigma rule on reconstruction errors
- Normalized inputs to prevent scale sensitivity

### Ensemble Strategy
- Both models warm up on first 50 readings before flagging
- When both ready: requires **both** to agree (reduces false positives)
- When only one ready: trusts the single available model

---

## 📊 Key Features

- **Real-time WebSocket streaming** — React dashboard updates every 500ms
- **3-sensor simulation** — kitchen, HVAC, laundry tracked independently
- **CO₂ impact calculator** — converts kWh → kg CO₂ → € cost → potential savings
- **German grid constants** — 0.380 kg CO₂/kWh, €0.32/kWh (2024 values)
- **Grafana panels** — Live kWh, CO₂ trends, anomaly events, total cost per sensor
- **InfluxDB Flux queries** — time-windowed aggregations for dashboard panels

---

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- Node.js 18+
- Docker Desktop

### 1. Clone the repo
```bash
git clone https://github.com/davemeeta/Smart-Energy-Consumption-Monitoring-Anomaly-Detection-Platform.git
cd Smart-Energy-Consumption-Monitoring-Anomaly-Detection-Platform
```

### 2. Download the dataset
Download from [Kaggle UCI Electric Power Consumption](https://www.kaggle.com/datasets/uciml/electric-power-consumption-data-set) and place `household_power_consumption.txt` in the `simulator/` folder.

### 3. Start infrastructure
```bash
docker compose up -d
```

### 4. Start backend
```bash
cd backend
source .venv/bin/activate      # Windows: .venv\Scripts\activate
uvicorn main:app --reload
```

### 5. Start simulator
```bash
cd simulator
python sensor_simulator.py
```

### 6. Start frontend
```bash
cd frontend
npm install
npm run dev
```

---

## 🌐 Service URLs

| Service | URL | Credentials |
|---------|-----|-------------|
| React Dashboard | http://localhost:5173 | — |
| FastAPI Docs | http://localhost:8000/docs | — |
| InfluxDB | http://localhost:8086 | admin / password123 |
| Grafana | http://localhost:3001 | admin / admin |

---

## 📁 Project Structure

```
├── docker-compose.yml          # Mosquitto + InfluxDB + Grafana
├── .env                        # Environment variables
├── simulator/
│   ├── sensor_simulator.py     # UCI dataset MQTT publisher
│   └── household_power_consumption.txt
├── backend/
│   ├── main.py                 # FastAPI app + WebSocket
│   ├── mqtt_listener.py        # MQTT subscriber + ML pipeline
│   ├── co2_calculator.py       # kWh → CO₂ → € calculator
│   ├── models/
│   │   ├── isolation_forest.py # Isolation Forest detector
│   │   └── autoencoder.py      # PyTorch Autoencoder detector
│   └── requirements.txt
├── frontend/
│   └── src/
│       └── App.jsx             # React live dashboard
└── mosquitto/
    └── config/
        └── mosquitto.conf
```

---

## 📈 Grafana Dashboard Panels

1. **Total Cost (€)** — stat panel, cost per sensor over time window
2. **CO₂ Emitted (kg)** — time series, all 3 sensors
3. **Anomaly Events** — time series bars, anomaly count per minute
4. **Live kWh Readings** — time series, real-time consumption per sensor

---

## 🌍 Why this matters

Germany's energy transition (Energiewende) requires intelligent monitoring of household and industrial consumption. This platform demonstrates:

- How **ML can flag wasteful consumption spikes** before they become costly
- How **real-time CO₂ accounting** helps consumers and grid operators make better decisions
- How **open-source IoT stack** (MQTT + InfluxDB + Grafana) can replace expensive proprietary SCADA systems

---

## 👩‍💻 Author

**Meeta Dave**
- GitHub: [@davemeeta](https://github.com/davemeeta)
- LinkedIn: [Meeta Dave](https://linkedin.com/in/meetadave)

*This project was originally conceived, designed, and built by Meeta Dave as a portfolio project targeting roles in the green energy and IoT analytics space.*

---

## 📄 License

MIT License — free to use, modify, and distribute with attribution.

---

## Acknowledgements

- [UCI ML Repository](https://archive.ics.uci.edu/ml/datasets/Individual+household+electric+power+consumption) — for the household energy dataset
- [Umweltbundesamt](https://www.umweltbundesamt.de) — for German grid CO₂ emission factors
- [Eclipse Mosquitto](https://mosquitto.org) — open-source MQTT broker
