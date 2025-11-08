import os, joblib, time
MODEL_PATH = os.path.join(os.path.dirname(__file__), 'models', 'lifetime.joblib')

class LifetimePredictor:
    def __init__(self):
        self.model = None
        if os.path.exists(MODEL_PATH):
            try:
                self.model = joblib.load(MODEL_PATH)
            except Exception as e:
                print('Failed to load lifetime model:', e)

    def predict(self, uptime, cpu, mem, threads):
        if not self.model:
            return int(max(60, min(86400, (uptime * 0.05) + (100 - cpu) * 10)))
        try:
            pred = self.model.predict([[uptime, cpu, mem, threads]])[0]
            return int(max(1, pred))
        except Exception as e:
            return int(max(60, min(86400, (uptime * 0.05) + (100 - cpu) * 10)))
