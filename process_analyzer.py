import psutil
import time
from datetime import datetime

class ProcessAnalyzer:
    def __init__(self, config):
        self.config = config
        self.crash_history = []
        self.process_lifetimes = {}
    
    def analyze_process_health(self, process_info):
        """Analyze process health and detect issues"""
        analysis = {
            'is_crashing': False,
            'battery_impact': 'low',
            'network_activity': 'low',
            'recommendation': 'none'
        }
        
        # Crash detection (simplified)
        if self._detect_crash(process_info):
            analysis['is_crashing'] = True
            analysis['recommendation'] = 'restart'
        
        # Battery impact estimation
        cpu_usage = process_info.get('cpu_percent', 0)
        if cpu_usage > 50:
            analysis['battery_impact'] = 'high'
        elif cpu_usage > 20:
            analysis['battery_impact'] = 'medium'
        
        # Network activity
        connections = process_info.get('network_connections', 0)
        if connections > 10:
            analysis['network_activity'] = 'high'
            if 'suspicious' in process_info.get('categories', []):
                analysis['recommendation'] = 'investigate'
        
        return analysis
    
    def _detect_crash(self, process_info):
        """Detect if process is crashing frequently"""
        pid = process_info['pid']
        current_time = time.time()
        
        if pid not in self.process_lifetimes:
            self.process_lifetimes[pid] = []
        
        # Track process restarts
        self.process_lifetimes[pid].append(current_time)
        
        # If process restarted more than 3 times in 60 seconds, consider it crashing
        recent_restarts = [t for t in self.process_lifetimes[pid] if current_time - t < 60]
        if len(recent_restarts) > 3:
            self.crash_history.append({
                'pid': pid,
                'name': process_info['name'],
                'timestamp': datetime.now()
            })
            return True
        
        return False
    
    def calculate_battery_impact(self, process_info):
        """Estimate battery impact of process"""
        cpu_usage = process_info.get('cpu_percent', 0)
        memory_usage = process_info.get('memory_percent', 0)
        
        # Simple formula for battery impact estimation
        battery_impact = (cpu_usage * 0.6) + (memory_usage * 0.4)
        
        if battery_impact > 60:
            return "very_high"
        elif battery_impact > 40:
            return "high"
        elif battery_impact > 20:
            return "medium"
        else:
            return "low"