from flask import Flask
app = Flask(__name__, static_folder='../static', template_folder='../templates')
app.config['SECRET_KEY'] = 'dev-key'
