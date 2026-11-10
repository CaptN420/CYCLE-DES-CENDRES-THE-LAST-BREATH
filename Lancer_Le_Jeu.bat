@echo off
chcp 65001 >nul
title CYCLE DES CENDRES
cd /d "%~dp0"
mode con: cols=84 lines=34 >nul 2>nul
color 0F
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8

where py >nul 2>nul
if not errorlevel 1 goto use_py
where python >nul 2>nul
if not errorlevel 1 goto use_python

echo.
echo  Python 3 est introuvable sur ce PC.
echo  Installe-le depuis https://www.python.org/downloads/ puis relance ce fichier.
echo.
pause
exit /b 1

:use_py
py -3 main.py
goto done

:use_python
python main.py
goto done

:done
if errorlevel 1 (
  echo.
  echo  Le jeu s'est arrete avec une erreur. Lis le message ci-dessus.
  pause
)
exit /b 0
