#!/bin/bash

# Function to clean up background processes on script exit
cleanup() {
    echo "[*] Cleaning up..."
    kill $(jobs -p) 2>/dev/null
    sudo docker stop hugo-container >/dev/null 2>&1
    sudo docker rm hugo-container >/dev/null 2>&1
    exit
}

# Set up trap to call cleanup function on script exit
trap cleanup EXIT

# Function to build and run the Docker container
build_and_run() {
    echo "[*] Redeploying..."
    
    # Build Docker image
    sudo docker build -t hugo-image . >/dev/null 2>&1

    # Stop and remove previous container if it exists
    sudo docker stop hugo-container >/dev/null 2>&1
    sudo docker rm hugo-container >/dev/null 2>&1

    # Start new container
    sudo docker run --name hugo-container -d -p 1313:1313 -v $(pwd):/site hugo-image server -D --bind 0.0.0.0 >/dev/null 2>&1

    echo "[+] Container redeployed"
}

# Initial build and run
build_and_run

# Loop to rebuild and rerun every 5 seconds
while true; do
    sleep 5
    build_and_run
done