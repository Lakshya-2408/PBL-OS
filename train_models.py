import pandas as pd, os, joblib
from sklearn.pipeline import make_pipeline
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import IsolationForest

LOG_PATH = os.path.join('logs','system_data.csv')
MODEL_DIR = os.path.join('app','models')
os.makedirs(MODEL_DIR, exist_ok=True)

SAMPLE = [
    {'name':'chrome.exe','category':'browser','uptime':300,'cpu':5,'mem':1.2,'threads':30},
    {'name':'python.exe','category':'script','uptime':50,'cpu':20,'mem':2.3,'threads':5},
    {'name':'svchost.exe','category':'system','uptime':10000,'cpu':1,'mem':0.8,'threads':50},
    {'name':'vlc.exe','category':'media','uptime':500,'cpu':2,'mem':1.1,'threads':10},
    {'name':'mysqld.exe','category':'database','uptime':2000,'cpu':10,'mem':3.0,'threads':40},
    {'name':'code.exe','category':'ide','uptime':400,'cpu':3,'mem':2.0,'threads':25},
    {'name':'onedrive.exe','category':'utility','uptime':800,'cpu':1,'mem':0.5,'threads':8},
    {'name':'steam.exe','category':'game','uptime':600,'cpu':5,'mem':4.0,'threads':20},
    {'name':'defender.exe','category':'security','uptime':9000,'cpu':1,'mem':1.5,'threads':30},
]

def load_data():
    if os.path.exists(LOG_PATH):
        df = pd.read_csv(LOG_PATH)
        df['name_clean'] = df['name'].fillna('unknown').astype(str)
        def map_cat(n):
            n=n.lower()
            if 'chrome' in n or 'firefox' in n: return 'browser'
            if 'python' in n or 'node' in n: return 'script'
            if 'svchost' in n or 'system' in n or 'csrss' in n: return 'system'
            if 'vlc' in n or 'spotify' in n or 'obs' in n: return 'media'
            if 'mysql' in n or 'mongod' in n or 'sql' in n: return 'database'
            if 'code' in n or 'pycharm' in n or 'sublime' in n: return 'ide'
            if 'onedrive' in n or 'update' in n or 'backup' in n: return 'utility'
            if 'steam' in n or 'valorant' in n or 'epic' in n: return 'game'
            if 'defender' in n or 'avp' in n or 'kaspersky' in n: return 'security'
            return 'other'
        df['category'] = df['name_clean'].apply(map_cat)
        df['uptime'] = (pd.to_datetime('now') - pd.to_datetime(df['timestamp'])).dt.total_seconds().abs()
        df['cpu'] = df['cpu'].fillna(0)
        df['mem'] = df['memory'].fillna(0)
        df['threads'] = df['threads'].fillna(0)
        return df[['name_clean','category','uptime','cpu','mem','threads']]
    else:
        return pd.DataFrame(SAMPLE)

def train_categorizer(df):
    X = df['name_clean']
    y = df['category']
    pipe = make_pipeline(CountVectorizer(analyzer='char_wb', ngram_range=(3,5)), MultinomialNB())
    pipe.fit(X,y)
    joblib.dump(pipe, os.path.join(MODEL_DIR,'categorizer.joblib'))
    print('Saved categorizer model')

def train_lifetime(df):
    X = df[['uptime','cpu','mem','threads']].fillna(0)
    y = (X['uptime']*0.05 + (100 - X['cpu'])*10).clip(1,86400)
    lr = LinearRegression()
    lr.fit(X,y)
    joblib.dump(lr, os.path.join(MODEL_DIR,'lifetime.joblib'))
    print('Saved lifetime model')

def train_anomaly(df):
    X = df[['cpu','mem','threads']].fillna(0)
    iso = IsolationForest(n_estimators=100, contamination=0.05, random_state=42)
    iso.fit(X)
    joblib.dump(iso, os.path.join(MODEL_DIR,'anomaly.joblib'))
    print('Saved anomaly model')

if __name__ == '__main__':
    df = load_data()
    if df.shape[0]==0:
        print('No logs found; using sample data')
    train_categorizer(df)
    train_lifetime(df)
    train_anomaly(df)
    print('All models trained and saved to app/models/')
