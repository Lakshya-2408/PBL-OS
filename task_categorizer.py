import os
import psutil

class TaskCategorizer:
    def __init__(self, config):
        self.config = config
    
    def categorize_process(self, process_info):
        """Categorize process into types - Safe version"""
        try:
            categories = []
            
            # Get values safely
            username = str(process_info.get('username', ''))
            name = str(process_info.get('name', ''))
            exe = str(process_info.get('exe', ''))
            status = str(process_info.get('status', ''))
            ppid = process_info.get('ppid', 0)
            cpu_usage = process_info.get('cpu_percent', 0)
            memory_usage = process_info.get('memory_percent', 0)
            
            # System Process Check
            if (username in ['SYSTEM', 'root', 'NT AUTHORITY\\SYSTEM'] or 
                ppid == 1 or
                'system32' in exe.lower()):
                categories.append("system")
            
            # User Process Check
            elif username and username not in ['SYSTEM', 'root', 'NT AUTHORITY\\SYSTEM']:
                categories.append("user")
            else:
                categories.append("unknown")
            
            # Zombie Process
            if status == 'zombie':
                categories.append("zombie")
            
            # High Resource Usage
            if (cpu_usage > self.config.config['cpu_threshold'] or 
                memory_usage > self.config.config['memory_threshold']):
                categories.append("high_usage")
            
            return categories
            
        except Exception as e:
            # If anything fails, return basic category
            return ["unknown"]