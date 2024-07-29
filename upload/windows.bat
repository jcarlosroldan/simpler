@ECHO OFF

Rem Remove auxiliary files
rd /s /q build 
rd /s /q dist
rd /s /q simpler.egg-info
for /d %%x in (simpler-*) do rd /s /q %%x

Rem Commit changes
git add *
git commit
git push origin master

Rem Build docs
sphinx-apidoc -o docs simpler -f --separate

Rem Update library
python setup.py sdist bdist_wheel
python -m twine upload dist/* -u juancroldan

Rem Remove auxiliary files again
rd /s /q build 
rd /s /q dist
rd /s /q simpler.egg-info
for /d %%x in (simpler-*) do rd /s /q %%x

timeout /t 5

Rem Reinstall it
ipconfig /flushdns
pip uninstall simpler -y
pip install simpler -U

pause