import os, joblib
MODEL_PATH = os.path.join(os.path.dirname(__file__), 'models', 'categorizer.joblib')

KEYWORD_MAP = {
    'system': ['svchost','wininit','services','system','csrss','lsass'],
    'browser': ['chrome','firefox','edge','brave','safari','opera'],
    'ide': ['code','pycharm','idea','sublime','notepad++','vscode'],
    'database': ['mysql','mongod','postgres','redis','sqlservr'],
    'media': ['vlc','spotify','mpv','obs','discord'],
    'security': ['defender','avp','kaspersky','antivirus','firewall'],
    'game': ['steam','valorant','epic','game','fortnite'],
    'utility': ['onedrive','updater','backup','update','installer'],
    'script': ['python','node','bash','powershell','sh','cmd'],
    'other': []
}

def heuristic(name):
    n = (name or '').lower()
    for cat, keys in KEYWORD_MAP.items():
        for k in keys:
            if k in n:
                return cat
    return 'other'

class Categorizer:
    def __init__(self):
        self.model = None
        if os.path.exists(MODEL_PATH):
            try:
                self.model = joblib.load(MODEL_PATH)
            except Exception as e:
                print('Failed to load categorizer model:', e)

    def predict(self, name):
        if not name:
            return 'other'
        if self.model:
            try:
                pred = self.model.predict([name])[0]
                return pred
            except Exception as e:
                return heuristic(name)
        return heuristic(name)
