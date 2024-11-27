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
BASE=$(git merge-base @ "$UPSTREAM")

if [ $LOCAL = $REMOTE ]; then
    log_message "No updates detected"
elif [ $LOCAL = $BASE ]; then
    log_message "Updates detected. Starting deployment..."
    
    # Pull changes with error handling
    if git pull origin main; then
        log_message "git pull successful"
        
        # Restart application with timeout
        timeout 300 bash start_app.sh
        if [ $? -eq 0 ]; then
            log_message "Application restart successful"
        elif [ $? -eq 124 ]; then
            log_message "Application restart timed out after 5 minutes"
        else
            log_message "Application restart failed with error code $?"
        fi
    else
        log_message "git pull failed with error code $?"
    fi
else
    log_message "Diverged from remote. Manual intervention required"
fi 