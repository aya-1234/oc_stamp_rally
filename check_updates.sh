#!/bin/bash

# ログファイルの設定
LOG_FILE="/home/bitnami/deploy.log"

# タイムスタンプ付きでログを記録する関数
log_message() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_FILE"
}

# アプリケーションディレクトリに移動
cd /home/bitnami/Stamp-rally-Digital

# リモートの変更を確認
git fetch origin initial

UPSTREAM=${1:-'@{u}'}
LOCAL=$(git rev-parse @)
REMOTE=$(git rev-parse "$UPSTREAM")

if [ $LOCAL != $REMOTE ]; then
    log_message "更新を検出しました。デプロイを開始します..."
    
    # プル実行
    git pull origin initial
    if [ $? -eq 0 ]; then
        log_message "git pull が成功しました"
        
        # アプリケーションの再起動
        bash app/start_app.sh
        if [ $? -eq 0 ]; then
            log_message "アプリケーションの再起動が成功しました"
        else
            log_message "アプリケーションの再起動に失敗しました"
        fi
    else
        log_message "git pull に失敗しました"
    fi
else
    log_message "更新は検出されませんでした"
fi 