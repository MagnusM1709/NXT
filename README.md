# Installation

-Download bluetooth driver header files (to compile python bluetooth bindings)
-Create virtualenv
-Install last stable release of nxt python bindings into virtualenv
-Keep the releasse for possible modifications
-Install rest of the requirements into virtualenv via pip
-Install this python module into virtualenv

Somehting like this in bash (not yet tested!):
```
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
```

USB-Setup (udev-rule) and more:
https://github.com/Eelviny/nxt-python/wiki/Installation

Modify motor.py of this driver (nxt-python-2.2.2) to achieve higher accuracy
using bluetooth.

Test if everything works fine, from inside the repository:
```
nxt_direct -m bluetooth -g
```

Read the text from the console and follow instructions to continue.

# Bluetooth Pairing

Kudos to FancyChaos for the awesome nxt_pair module doing all the work!
