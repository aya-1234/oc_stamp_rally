#!/bin/bash

# ログファイルの設定
LOG_DIR="/home/bitnami/Stamp-rally-Digital/logs"
LOG_FILE="$LOG_DIR/app.log"

# ログディレクトリの作成
mkdir -p "$LOG_DIR"

# ログ出力関数
log_message() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# アプリケーションディレクトリに移動
cd /home/bitnami/Stamp-rally-Digital/app || {
    log_message "Failed to change directory"
    exit 1
}

# 環境情報のログ出力
log_message "Current directory: $(pwd)"
log_message "Python version: $(/opt/bitnami/python/bin/python --version 2>&1)"
log_message "PYTHONPATH: $PYTHONPATH"

# 既存のプロセスをすべて終了
pkill -f "python run_prod.py"
sleep 5

# 環境変数の設定
export PYTHONPATH=/home/bitnami/Stamp-rally-Digital/app
export FLASK_ENV=production
export PATH="/opt/bitnami/python/bin:$PATH"

# アプリケーションの起動（エラー出力を詳細に記録）
log_message "Starting application..."
/opt/bitnami/python/bin/python /home/bitnami/Stamp-rally-Digital/app/run_prod.py >> "$LOG_FILE" 2>&1 &
APP_PID=$!

# プロセスの起動確認（より詳細なチェック）
sleep 5
if ps -p $APP_PID > /dev/null; then
    if netstat -tuln | grep ":8888 " > /dev/null; then
        log_message "Application started successfully (PID: $APP_PID)"
        log_message "Port 8888 is now listening"
        exit 0
    else
        log_message "Process is running but port 8888 is not listening"
        log_message "Last 10 lines of application log:"
        tail -n 10 "$LOG_FILE" >> "$LOG_FILE"
        kill $APP_PID
        exit 1
    fi
else
    log_message "Process failed to start. Last 10 lines of application log:"
    tail -n 10 "$LOG_FILE" >> "$LOG_FILE"
    log_message "Process status: $(ps aux | grep python)"
    exit 1
fi
