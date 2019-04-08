#!/bin/bash
set -e
sudo apt-get install libbluetooth-dev python-virtualenv >> LEGO.log
virtualenv -p python2 venv2 >> LEGO.log
. ./venv2/bin/activate >> LEGO.log
wget https://github.com/Eelviny/nxt-python/archive/v2.2.2.zip >> LEGO.log
unzip v2.2.2.zip >> LEGO.log
cd nxt-python-2.2.2
python setup.py install >> ../LEGO.log
cd ..
pip install -r requirements.txt >> LEGO.log
python setup.py install >> LEGO.log
