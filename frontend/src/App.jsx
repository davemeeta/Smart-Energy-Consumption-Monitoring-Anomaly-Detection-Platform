import { useState, useEffect, useRef } from "react";
import {
  LineChart, Line, XAxis, YAxis, Tooltip,
  ReferenceLine, ResponsiveContainer, CartesianGrid,
} from "recharts";

const WS = "ws://localhost:8000/ws";
const API = "http://localhost:8000";

const KPICard = ({ label, value, color }) => (
  <div style={{
    flex: 1, background: "#1e1e2e", borderRadius: 12,
    padding: "16px 20px", minWidth: 130, border: "1px solid #2a2a3e"
  }}>
    <div style={{ fontSize: 12, color: "#888", marginBottom: 6 }}>{label}</div>
    <div style={{ fontSize: 28, fontWeight: 700, color: color || "#fff" }}>{value}</div>
  </div>
);

export default function App() {
  const [readings, setReadings] = useState([]);
  const [anomalies, setAnomalies] = useState([]);
  const [connected, setConnected] = useState(false);
  const wsRef = useRef(null);
  const fmt = (ts) => new Date(ts * 1000).toLocaleTimeString();

  useEffect(() => {
    fetch(`${API}/events`)
      .then(r => r.json())
      .then(data => {
        setReadings(data.map(d => ({ ...d, time: fmt(d.timestamp) })));
        setAnomalies(data.filter(d => d.is_anomaly));
      })
      .catch(() => {});

    wsRef.current = new WebSocket(WS);
    wsRef.current.onopen = () => setConnected(true);
    wsRef.current.onclose = () => setConnected(false);
    wsRef.current.onmessage = (e) => {
      const d = JSON.parse(e.data);
      const row = { ...d, time: fmt(d.timestamp) };
      setReadings(prev => [...prev.slice(-80), row]);
      if (d.is_anomaly === true || d.is_anomaly === 1) setAnomalies(prev => [row, ...prev].slice(0, 30));    };
    return () => wsRef.current?.close();
  }, []);

  const totalCo2    = readings.reduce((s, r) => s + (r.co2_kg || 0), 0).toFixed(3);
  const totalSaving = readings.reduce((s, r) => s + (r.potential_saving_eur || 0), 0).toFixed(2);

  return (
    <div style={{
      minHeight: "100vh", background: "#13131f",
      color: "#fff", fontFamily: "system-ui, sans-serif"
    }}>
      <div style={{ maxWidth: 1100, margin: "0 auto", padding: 28 }}>

        {/* Header */}
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 28 }}>
          <div>
            <h1 style={{ margin: 0, fontSize: 24, fontWeight: 700 }}>⚡ Energy Anomaly Monitor</h1>
            <p style={{ margin: "4px 0 0", color: "#666", fontSize: 13 }}>
              IoT sensors · Isolation Forest + Autoencoder · CO₂ impact
            </p>
          </div>
          <div style={{
            padding: "6px 14px", borderRadius: 20, fontSize: 12, fontWeight: 600,
            background: connected ? "#0f3d1f" : "#3d0f0f",
            color: connected ? "#4caf50" : "#f44336",
            border: `1px solid ${connected ? "#4caf50" : "#f44336"}`
          }}>
            {connected ? "🟢 Live" : "🔴 Disconnected"}
          </div>
        </div>

        {/* KPI row */}
        <div style={{ display: "flex", gap: 14, marginBottom: 28, flexWrap: "wrap" }}>
          <KPICard label="Total readings"      value={readings.length} />
          <KPICard label="Anomalies detected"  value={anomalies.length}   color="#f44336" />
          <KPICard label="CO₂ emitted (kg)"    value={totalCo2}           color="#4caf50" />
          <KPICard label="Potential saving"     value={`€${totalSaving}`}  color="#ff9800" />
        </div>

        {/* Live chart */}
        <div style={{ background: "#1e1e2e", borderRadius: 12, padding: 20, marginBottom: 24, border: "1px solid #2a2a3e" }}>
          <h2 style={{ margin: "0 0 16px", fontSize: 15, color: "#ccc" }}>Live kWh readings</h2>
          <ResponsiveContainer width="100%" height={220}>
            <LineChart data={readings}>
              <CartesianGrid strokeDasharray="3 3" stroke="#2a2a3e" />
              <XAxis dataKey="time" tick={{ fontSize: 11, fill: "#666" }} interval="preserveStartEnd" />
              <YAxis domain={["auto", "auto"]} tick={{ fontSize: 11, fill: "#666" }} />
              <Tooltip
                contentStyle={{ background: "#1e1e2e", border: "1px solid #2a2a3e", borderRadius: 8, fontSize: 12 }}
                labelStyle={{ color: "#aaa" }}
              />
              <ReferenceLine y={4} stroke="#f44336" strokeDasharray="4 2"
                label={{ value: "Anomaly threshold", position: "insideTopRight", fontSize: 11, fill: "#f44336" }} />
              <Line type="monotone" dataKey="kwh" stroke="#4fc3f7" dot={false} strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Anomaly feed */}
        <div style={{ background: "#1e1e2e", borderRadius: 12, padding: 20, border: "1px solid #2a2a3e" }}>
          <h2 style={{ margin: "0 0 16px", fontSize: 15, color: "#ccc" }}>🚨 Anomaly feed</h2>
          {anomalies.length === 0 ? (
            <p style={{ color: "#555", fontSize: 13, textAlign: "center", padding: "20px 0" }}>
              No anomalies detected yet — waiting for spikes…
            </p>
          ) : (
            <div style={{ overflowX: "auto" }}>
              <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13 }}>
                <thead>
                  <tr style={{ borderBottom: "1px solid #2a2a3e" }}>
                    {["Time","Sensor","kWh","ISO score","AE error","CO₂ kg","Cost €","Saving €"].map(h => (
                      <th key={h} style={{ padding: "8px 12px", textAlign: "left", color: "#666", fontWeight: 500 }}>{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {anomalies.map((a, i) => (
                    <tr key={i} style={{ borderBottom: "1px solid #1a1a2e" }}>
                      <td style={{ padding: "8px 12px", color: "#aaa" }}>{fmt(a.timestamp)}</td>
                      <td style={{ padding: "8px 12px", color: "#aaa" }}>{a.sensor_id}</td>
                      <td style={{ padding: "8px 12px", color: "#f44336", fontWeight: 700 }}>{a.kwh}</td>
                      <td style={{ padding: "8px 12px", color: "#aaa" }}>{a.score}</td>
                      <td style={{ padding: "8px 12px", color: "#aaa" }}>{a.reconstruction_error}</td>
                      <td style={{ padding: "8px 12px", color: "#4caf50" }}>{a.co2_kg}</td>
                      <td style={{ padding: "8px 12px", color: "#aaa" }}>{a.cost_eur}</td>
                      <td style={{ padding: "8px 12px", color: "#ff9800" }}>€{a.potential_saving_eur}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

      </div>
    </div>
  );
}