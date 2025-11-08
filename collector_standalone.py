from app.collector import Collector
c = Collector(interval=3)
c.start()
print('Collector started. Logs at logs/system_data.csv. Press Ctrl+C to stop.')
try:
    while True:
        pass
except KeyboardInterrupt:
    c.stop()
    print('Stopped')    
