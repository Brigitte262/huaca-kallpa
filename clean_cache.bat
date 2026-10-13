@echo off
echo Limpiando cache de Python...
for /d /r . %%d in (__pycache__) do @if exist "%%d" rd /s /q "%%d"
del /s /q *.pyc 2>nul
echo Cache limpiado. Ejecuta main.py nuevamente.
pause
