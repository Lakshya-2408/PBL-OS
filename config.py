import json
import os

class Config:
    def __init__(self):
        self.config_file = "config.json"
        self.default_config = {
            "whitelist": ["explorer.exe", "System", "python.exe"],
            "blacklist": [],
            "suspicious_keywords": ["cryptominer", "malware", "virus"],
            "cpu_threshold": 80,
            "memory_threshold": 80,
            "auto_terminate_zombies": True,
            "battery_saver_mode": False,
            "gaming_mode": False
        }
        self.load_config()
    
    def load_config(self):
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r') as f:
                self.config = json.load(f)
        else:
            self.config = self.default_config
            self.save_config()
    
    def save_config(self):
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=4)