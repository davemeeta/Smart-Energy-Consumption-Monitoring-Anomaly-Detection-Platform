import torch
import torch.nn as nn
import numpy as np

class Autoencoder(nn.Module):
    def __init__(self):
        super().__init__()
        self.encoder = nn.Sequential(
            nn.Linear(3, 16), nn.ReLU(),
            nn.Linear(16, 8), nn.ReLU(),
            nn.Linear(8, 2)
        )
        self.decoder = nn.Sequential(
            nn.Linear(2, 8),  nn.ReLU(),
            nn.Linear(8, 16), nn.ReLU(),
            nn.Linear(16, 3)
        )

    def forward(self, x):
        return self.decoder(self.encoder(x))


class AutoencoderDetector:
    def __init__(self, warmup=50):
        self.model = Autoencoder()
        self.optimizer = torch.optim.Adam(self.model.parameters(), lr=1e-3)
        self.buffer = []
        self.warmup = warmup

        # Running stats for normalization (updated online)
        self.mean = np.zeros(3)
        self.std  = np.ones(3)

        # Dynamic threshold: mean + 3*std of recent errors
        self.recent_errors = []
        self.threshold = None

    def _normalize(self, arr: np.ndarray) -> np.ndarray:
        return (arr - self.mean) / (self.std + 1e-8)

    def _update_stats(self):
        data = np.array(self.buffer)
        self.mean = data.mean(axis=0)
        self.std  = data.std(axis=0)

    def add_and_train(self, kwh: float, voltage: float, temp: float):
        self.buffer.append([kwh, voltage, temp])

        # Keep a rolling window
        if len(self.buffer) > 500:
            self.buffer.pop(0)

        # Need at least warmup samples before training
        if len(self.buffer) < self.warmup:
            return

        self._update_stats()

        # Train on last 100 normalized samples
        raw = np.array(self.buffer[-100:])
        X   = torch.tensor(self._normalize(raw), dtype=torch.float32)

        self.optimizer.zero_grad()
        loss = nn.MSELoss()(self.model(X), X)
        loss.backward()
        self.optimizer.step()

        # Update dynamic threshold using recent reconstruction errors
        with torch.no_grad():
            errors = nn.MSELoss(reduction="none")(self.model(X), X)
            per_sample = errors.mean(dim=1).numpy()

        self.recent_errors.extend(per_sample.tolist())
        if len(self.recent_errors) > 200:
            self.recent_errors = self.recent_errors[-200:]

        # Threshold = mean + 3 standard deviations (3-sigma rule)
        err_arr = np.array(self.recent_errors)
        self.threshold = float(err_arr.mean() + 3 * err_arr.std())

    def predict(self, kwh: float, voltage: float, temp: float) -> dict:
        # Not enough data yet — don't flag anything
        if self.threshold is None or len(self.buffer) < self.warmup:
            return {
                "ae_anomaly": False,
                "reconstruction_error": 0.0,
                "ae_threshold": None,
                "ae_ready": False
            }

        raw = np.array([[kwh, voltage, temp]])
        x   = torch.tensor(self._normalize(raw), dtype=torch.float32)

        with torch.no_grad():
            error = float(nn.MSELoss()(self.model(x), x).item())

        return {
            "ae_anomaly":          error > self.threshold,
            "reconstruction_error": round(error, 4),
            "ae_threshold":         round(self.threshold, 4),
            "ae_ready":             True
        }