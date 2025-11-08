import os, joblib
MODEL_PATH = os.path.join(os.path.dirname(__file__), 'models', 'anomaly.joblib')

class AnomalyDetector:
    def __init__(self):
        self.model = None
        if os.path.exists(MODEL_PATH):
            try:
                self.model = joblib.load(MODEL_PATH)
            except Exception as e:
                print('Failed to load anomaly model:', e)

    def score(self, cpu, mem, threads):
        if not self.model:
            val = (cpu/100.0)*0.6 + (mem/100.0)*0.3 + (threads/50.0)*0.1
            return int(min(100, max(0, val*100)))
        try:
            s = self.model.decision_function([[cpu,mem,threads]])[0]
            score = (1 - (s - (-0.5)) / (1.5 - (-0.5))) * 100
            return int(min(100, max(0, score)))
        except Exception as e:
            return 0
