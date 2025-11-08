import threading, time, csv, os
import psutil
from datetime import datetime
LOG_PATH = os.path.join(os.path.dirname(__file__), '..', 'logs', 'system_data.csv')

HEADER = ['timestamp','pid','name','user','cpu','memory','threads','create_time']

class Collector(threading.Thread):
    def __init__(self, interval=3):
        super().__init__(daemon=True)
        self.interval = interval
        self.running = False
        os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
        if not os.path.exists(LOG_PATH):
            with open(LOG_PATH,'w',newline='',encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(HEADER)

    def gather(self):
        rows = []
        for p in psutil.process_iter(['pid','name','username','cpu_percent','memory_percent','num_threads','create_time']):
            try:
                info = p.info
                rows.append([datetime.utcnow().isoformat(), info.get('pid'), info.get('name'), info.get('username'),
                             info.get('cpu_percent') or 0, round(info.get('memory_percent') or 0,2),
                             info.get('num_threads') or 0, info.get('create_time') or 0])
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return rows

    def run(self):
        self.running = True
        while self.running:
            rows = self.gather()
            with open(LOG_PATH,'a',newline='',encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerows(rows)
            time.sleep(self.interval)

    def stop(self):
        self.running = False
