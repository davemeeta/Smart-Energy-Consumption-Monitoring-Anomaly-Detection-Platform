from sklearn.ensemble import IsolationForest
import numpy as np

class EnergyAnomalyDetector:
    def __init__(self, contamination=0.10, warmup=50):
        self.contamination = contamination
        self.warmup = warmup
        self.model  = IsolationForest(
            contamination=contamination,
            random_state=42,
            n_estimators=100,
            max_samples="auto"
        )
        self.buffer  = []
        self.trained = False
        self.retrain_every = 50   # retrain every N new samples
        self.samples_since_retrain = 0

    def add_reading(self, kwh: float, voltage: float, temp: float):
        self.buffer.append([kwh, voltage, temp])
        if len(self.buffer) > 500:
            self.buffer.pop(0)

        self.samples_since_retrain += 1

        # Initial train
        if len(self.buffer) >= self.warmup and not self.trained:
            self._train()

        # Periodic retrain to adapt to new patterns
        if self.trained and self.samples_since_retrain >= self.retrain_every:
            self._train()
            self.samples_since_retrain = 0

    def _train(self):
        self.model.fit(np.array(self.buffer))
        self.trained = True

    def predict(self, kwh: float, voltage: float, temp: float) -> dict:
        if not self.trained:
            return {
                "iso_anomaly": False,
                "iso_score":   0.0,
                "iso_ready":   False
            }
        X     = np.array([[kwh, voltage, temp]])
        score = float(self.model.score_samples(X)[0])
        is_anomaly = self.model.predict(X)[0] == -1
        return {
            "iso_anomaly": bool(is_anomaly),
            "iso_score":   round(score, 4),
            "iso_ready":   True
        }