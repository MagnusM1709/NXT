from flask import Flask
from flask import render_template
import subprocess
app = Flask(__name__)



@app.route('/')
def hello(name=None):
    lip = getip()
    return render_template('index.html', ip=str(lip))

def getip():
    ip = subprocess.check_output("hostname -I", shell=True).decode('utf-8') #get ip
    ip = ip[:-2] #eliminate unwanted characters
    return ip
