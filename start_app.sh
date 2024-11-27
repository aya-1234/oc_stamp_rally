#!/bin/bash

# Change to application directory
cd /home/bitnami/Stamp-rally-Digital/app

# Check existing process
PID=$(pgrep -f "python run_prod.py")

if [ ! -z "$PID" ]; then
    echo "Stopping existing application (PID: $PID)"
    kill $PID
    sleep 2  # Wait for process to terminate
fi

# Set PYTHONPATH to include current directory
export PYTHONPATH=$PYTHONPATH:/home/bitnami/Stamp-rally-Digital/app

# Run Python script with nohup and log output
nohup python run_prod.py > app.log 2>&1 &
echo "Application restarted. Logs saved to app.log"
