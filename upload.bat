Rem Remove auxiliary files
rd /s /q build 
rd /s /q dist
rd /s /q simpler.egg-info
for /d %%x in (simpler-*) do rd /s /q %%x

Rem Commit changes
git add *
git commit
git push origin master

Rem Update library
python setup.py sdist bdist_wheel
python -m twine upload dist/* -u juancroldan

Rem Reinstall it
pip uninstall simpler
pip install simpler -U
pause

Rem Remove auxiliary files again
rd /s /q build 
rd /s /q dist
rd /s /q simpler.egg-info
for /d %%x in (simpler-*) do rd /s /q %%x