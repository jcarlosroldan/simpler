#!/bin/bash

# Remove auxiliary files
rm -rf build dist simpler.egg-info
find . -type d -name 'simpler-*' -exec rm -rf {} +

# Commit changes
git add .
git commit
git push origin master

# Build docs
sphinx-apidoc -o docs simpler -f --separate

# Update library
python3 setup.py sdist bdist_wheel
python3 -m twine upload dist/* -u juancroldan

# Remove auxiliary files again
rm -rf build dist simpler.egg-info
find . -type d -name 'simpler-*' -exec rm -rf {} +

# Wait for 5 seconds
sleep 5

# Reinstall it
sudo dscacheutil -flushcache
sudo killall -HUP mDNSResponder
pip3 uninstall simpler -y
pip3 install simpler -U

echo "Script execution completed."