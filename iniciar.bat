@echo off
title System Auto JK - Web-IA v6.1 (Macro Controller)
echo Iniciando...
python -m pip install --upgrade pip
pip install -r requirements.txt
python main_ui.py
pause
