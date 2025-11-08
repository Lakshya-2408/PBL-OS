import os, time, psutil, math, threading, json
from flask import render_template, jsonify, request
from . import app
from .collector import Collector
from .categorizer import Categorizer
from .predictor import LifetimePredictor
from .anomaly_detector import AnomalyDetector
from pathlib import Path
import logging, pandas as pd
from subprocess import Popen, PIPE

LOG_DIR = Path(__file__).parent.parent / 'logs'
LOG_DIR.mkdir(parents=True, exist_ok=True)
logging.basicConfig(filename=LOG_DIR/'actions.log', level=logging.INFO,
                    format='%(asctime)s %(levelname)s %(message)s')

collector = Collector(interval=3)
collector.start()

categorizer = Categorizer()
predictor = LifetimePredictor()
anomaly = AnomalyDetector()

AUTO_KILL_ENABLED = False

@app.route('/')
def index():
    return render_template('index.html', auto_kill=str(AUTO_KILL_ENABLED).lower())

@app.route('/api/processes')
def processes():
    procs = []
    for p in psutil.process_iter(['pid','name','username','cpu_percent','memory_percent','num_threads','create_time']):
        try:
            info = p.info
            uptime = 0
            try:
                uptime = int(time.time() - info.get('create_time', time.time()))
            except:
                uptime = 0
            cpu = info.get('cpu_percent') or 0
            mem = round(info.get('memory_percent') or 0,2)
            threads = info.get('num_threads') or 0
            cat = categorizer.predict(info.get('name') or '')
            life = predictor.predict(uptime, cpu, mem, threads)
            a_score = anomaly.score(cpu, mem, threads)
            procs.append({'pid': info.get('pid'), 'name': info.get('name'), 'user': info.get('username'),
                          'cpu': cpu, 'memory': mem, 'threads': threads, 'uptime': uptime,
                          'category': cat, 'lifetime_pred': life, 'anomaly': a_score})
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    procs = sorted(procs, key=lambda x: x['cpu'], reverse=True)
    return jsonify(procs)

@app.route('/api/stats')
def stats():
    path = Path(__file__).parent.parent / 'logs' / 'system_data.csv'
    if not path.exists():
        return jsonify({'error':'no logs'}), 404
    try:
        df = pd.read_csv(path, parse_dates=['timestamp'])
        df2 = df.tail(500).groupby(pd.Grouper(key='timestamp', freq='10S')).agg({'cpu':'mean','memory':'mean'}).fillna(0).reset_index()
        times = df2['timestamp'].astype(str).tolist()
        cpu = df2['cpu'].round(2).tolist()
        mem = df2['memory'].round(2).tolist()
        return jsonify({'times':times,'cpu':cpu,'mem':mem})
    except Exception as e:
        return jsonify({'error':str(e)}),500

@app.route('/api/kill', methods=['POST'])
def kill_proc():
    data = request.get_json() or {}
    pid = int(data.get('pid', -1))
    try:
        p = psutil.Process(pid)
        name = p.name()
        p.terminate()
        gone, alive = psutil.wait_procs([p], timeout=3)
        if alive:
            p.kill()
        logging.info(f'KILLED pid={pid} name={name}')
        return jsonify({'status':'ok','msg':f'Killed {pid} - {name}'})
    except psutil.NoSuchProcess:
        return jsonify({'status':'error','msg':'No such process'}), 404
    except psutil.AccessDenied:
        return jsonify({'status':'error','msg':'Access denied - need elevated permissions'}), 403
    except Exception as e:
        return jsonify({'status':'error','msg':str(e)}), 500

@app.route('/api/retrain', methods=['POST'])
def retrain():
    try:
        proc = Popen(['python','train_models.py'], cwd=str(Path(__file__).parent.parent), stdout=PIPE, stderr=PIPE)
        out,err = proc.communicate(timeout=300)
        return jsonify({'status':'ok','out':out.decode('utf-8')[:1000],'err':err.decode('utf-8')[:1000]})
    except Exception as e:
        return jsonify({'status':'error','msg':str(e)}),500

@app.route('/api/toggle_autokill', methods=['POST'])
def toggle_autokill():
    global AUTO_KILL_ENABLED
    data = request.get_json() or {}
    AUTO_KILL_ENABLED = bool(data.get('enable', False))
    return jsonify({'status':'ok','auto_kill':AUTO_KILL_ENABLED})

if __name__ == '__main__':
    app.run(debug=True, port=5000)
