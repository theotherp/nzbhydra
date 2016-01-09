import os
import sys
from flask import Flask
app = Flask(__name__)

@app.route('/')
def hello_world():
    return 'Hello World!'

@app.route('/restart')
def restart():
    print("Restarting with os.execl")
    os.execl(sys.executable, *([sys.executable] + sys.argv))

@app.route('/respawn')
def respawn():
    print("Restarting with os.spawnv")
    os.spawnl(os.P_NOWAIT, sys.executable, *([sys.executable] + sys.argv))

if __name__ == '__main__':
    print("Starting")
    app.run()