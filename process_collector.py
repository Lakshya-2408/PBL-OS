import psutil
import time
from datetime import datetime, timedelta

class ProcessCollector:
    def __init__(self):
        self.process_history = {}
    
    def get_all_processes(self):
        """Collect all running processes with detailed information"""
        processes = []
        
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 
                                       'status', 'username', 'create_time', 'exe', 'ppid']):
            try:
                process_info = proc.info
                process_info['cpu_percent'] = proc.cpu_percent()
                process_info['memory_percent'] = proc.memory_percent()
                
                # Get network connections count
                try:
                    process_info['network_connections'] = len(proc.connections())
                except:
                    process_info['network_connections'] = 0
                
                # Calculate process age
                create_time = process_info['create_time']
                if create_time:
                    age_seconds = time.time() - create_time
                    process_info['age'] = str(timedelta(seconds=int(age_seconds)))
                else:
                    process_info['age'] = "Unknown"
                
                processes.append(process_info)
                
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
        
        return processes
    
    def get_system_stats(self):
        """Get overall system statistics"""
        stats = {
            'cpu_percent': psutil.cpu_percent(interval=1),
            'memory_percent': psutil.virtual_memory().percent,
            'memory_used_gb': round(psutil.virtual_memory().used / (1024**3), 2),
            'memory_total_gb': round(psutil.virtual_memory().total / (1024**3), 2)
        }
        
        # Get battery info if available
        try:
            battery = psutil.sensors_battery()
            if battery:
                stats['battery_percent'] = battery.percent
            else:
                stats['battery_percent'] = None
        except:
            stats['battery_percent'] = None
            
        return stats