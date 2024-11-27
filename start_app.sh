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

# 既存のプロセスを確実に終了
cleanup_processes() {
    log_message "Cleaning up existing processes..."
    pkill -f "python.*run_prod.py"
    sleep 2
    
    # 強制終了が必要な場合
    if pgrep -f "python.*run_prod.py" > /dev/null; then
        log_message "Force killing remaining processes..."
        pkill -9 -f "python.*run_prod.py"
        sleep 3
    fi
}

# クリーンアップを実行
cleanup_processes

# アプリケーションディレクトリに移動
cd /home/bitnami/Stamp-rally-Digital/app || {
    log_message "Failed to change directory"
    exit 1
}

# 環境変数の設定
export PYTHONPATH=/home/bitnami/Stamp-rally-Digital/app
export FLASK_ENV=production
export PATH="/opt/bitnami/python/bin:$PATH"

# ポート8888が使用されていないことを確認
if netstat -tuln | grep ":8888 " > /dev/null; then
    log_message "Port 8888 is already in use. Waiting for it to be released..."
    sleep 10
fi

# アプリケーションの起動
log_message "Starting application..."
/opt/bitnami/python/bin/python /home/bitnami/Stamp-rally-Digital/app/run_prod.py > "$LOG_FILE" 2>&1 &
APP_PID=$!

# プロセスの起動確認
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
