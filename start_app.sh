#!/bin/bash

# スクリプトを実行するディレクトリに移動
cd /home/bitnami/Stamp-rally-Digital/app

# Pythonスクリプトをnohupで実行し、ログを出力
nohup python run.py > app.log 2>&1 &
echo "Application started and running in the background. Logs are being saved to app.log"
