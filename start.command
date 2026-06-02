#!/bin/bash
# Double-click this file to start the Country History Explorer.
# It opens the server and your browser automatically.
# To stop the app: close this window, or press Ctrl+C here.

cd "$(dirname "$0")"
echo "Starting Country History Explorer…"
python3 server.py
