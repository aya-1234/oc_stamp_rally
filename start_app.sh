#!/bin/bash

# スクリプトを実行するディレクトリに移動
cd /home/bitnami/Stamp-rally-Digital/app

# 既存のプロセスを確認
PID=$(pgrep -f "python run.py")

if [ ! -z "$PID" ]; then
    echo "既存のアプリケーションを停止します (PID: $PID)"
    kill $PID
    sleep 2  # プロセスが完全に終了するまで少し待機
fi

# Pythonスクリプトをnohupで実行し、ログを出力
nohup python run.py > app.log 2>&1 &
echo "アプリケーションを再起動しました。ログは app.log に保存されています。"
