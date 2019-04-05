#!/bin/bash

sudo apt-get install libbluetooth-dev python-virtualenv
virtualenv -p python2 venv2
. ./venv2/bin/activate
wget https://github.com/Eelviny/nxt-python/archive/v2.2.2.zip
unzip v2.2.2.zip
cd nxt-python-2.2.2
python setup.py install
cd ..
pip install -r requirements.txt
python setup.py install
