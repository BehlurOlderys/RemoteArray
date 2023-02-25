#!/bin/bash

sudo apt-get update
sudo apt-get install python3-venv
mkdir workspace
cd workspace
git clone https://github.com/BehlurOlderys/RemoteArray.git
mkdir samyang_app
mv RemoteArray samyang_app/samyang_app
cd samyang_app; python3 -m venv .venv
pip install -r samyang_app/requirements.txt
# something about zwo libs
mv samyang_app/on_boot.sh .
chmod +x on_boot.sh
(sudo crontab -l ; cat samyang_app/crontab_line.txt)| sudo crontab -