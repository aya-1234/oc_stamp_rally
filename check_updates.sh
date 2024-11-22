#!/bin/bash

# Log file settings
LOG_FILE="/home/bitnami/deploy.log"

# Function to log messages with timestamp
log_message() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_FILE"
}

# Move to application directory
cd /home/bitnami/Stamp-rally-Digital

# Check remote changes
git fetch origin initial

UPSTREAM=${1:-'@{u}'}
LOCAL=$(git rev-parse @)
REMOTE=$(git rev-parse "$UPSTREAM")

if [ $LOCAL != $REMOTE ]; then
    log_message "Updates detected. Starting deployment..."
    
    # Pull changes
    git pull origin initial
    if [ $? -eq 0 ]; then
        log_message "git pull successful"
        
        # Restart application
        bash app/start_app.sh
        if [ $? -eq 0 ]; then
            log_message "Application restart successful"
        else
            log_message "Application restart failed"
        fi
    else
        log_message "git pull failed"
    fi
else
    log_message "No updates detected"
fi 