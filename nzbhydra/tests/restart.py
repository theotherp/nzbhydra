import os
import subprocess
import sys
from os.path import dirname, abspath, join
from time import sleep

from flask import Flask, request

app = Flask(__name__)

@app.route('/')
def hello_world():
    return 'Hello World!'

@app.route('/restart')
def restart():
    print("Restarting with os.execl")
    os.execl(sys.executable, *([sys.executable] + sys.argv))

@app.route('/shutdown')
def shutdown():
    os._exit(0)
    

@app.route('/respawn')
def respawn():
    print("Restarting with os.spawnv")
    os.spawnl(os.P_NOWAIT, sys.executable, *([sys.executable] + sys.argv))

@app.route('/popen')
def popen():
    print("Restarting with popen")
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        raise RuntimeError('Not running with the Werkzeug Server')
    func()
    print("Shutdown complete")
    sleep(5)
    print("Starting new instance")
    p = join(dirname(abspath(__file__)), "restart.py")
    subprocess.Popen([sys.executable, p], cwd=os.getcwd())
    os._exit(0)

@app.route('/foo')
def foo():
    print("Exiting with return code 3")
    os._exit(3)

if __name__ == '__main__':
    print("Starting")
    args = sys.argv[1:]
    if "foo" not in args:
        print("Initial start. Starting subprocess in loop")
        retcode = None
        p = join(dirname(abspath(__file__)), "restart.py")
        while retcode != 0:
            retcode = subprocess.call([sys.executable, p, "foo"])
            print("Subprocess returned with code %d" % retcode)
    else:
        print("Foo in args. We are in subprocess and want to start flask")
        app.run()
        
            
    