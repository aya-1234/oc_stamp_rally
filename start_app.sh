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

# 既存のプロセスをチェックして終了
PID=$(pgrep -f "python run_prod.py")
if [ ! -z "$PID" ]; then
    log_message "Stopping existing application (PID: $PID)"
    kill $PID
    sleep 5  # プロセスの終了を待つ時間を増やす
    
    # プロセスが終了したか確認
    if kill -0 $PID 2>/dev/null; then
        log_message "Force killing application"
        kill -9 $PID
    fi
fi

# 環境変数の設定
export PYTHONPATH=$PYTHONPATH:/home/bitnami/Stamp-rally-Digital/app
export FLASK_ENV=production

# アプリケーションの起動（絶対パスを使用）
log_message "Starting application..."
/opt/bitnami/python/bin/python /home/bitnami/Stamp-rally-Digital/app/run_prod.py > "$LOG_FILE" 2>&1 &

# プロセスの起動確認
sleep 5
NEW_PID=$(pgrep -f "python run_prod.py")
if [ ! -z "$NEW_PID" ]; then
    log_message "Application started successfully (PID: $NEW_PID)"
    exit 0
else
    log_message "Failed to start application"
    exit 1
fi
