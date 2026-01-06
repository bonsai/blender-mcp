import os
import json
from flask import Flask, jsonify, render_template

app = Flask(__name__)

LOG_FILE = "server_status_log.json"

# Ensure log file exists
if not os.path.exists(LOG_FILE):
    with open(LOG_FILE, "w") as f:
        json.dump([], f)

@app.route("/")
def index():
    return render_template("server_status.html")

@app.route("/api/status", methods=["GET"])
def get_status():
    # Read log file
    with open(LOG_FILE, "r") as f:
        logs = json.load(f)
    return jsonify(logs)

@app.route("/api/log", methods=["POST"])
def log_status():
    # Example log entry
    log_entry = {
        "timestamp": "2026-01-06T21:23:14",
        "cpu": "15%",
        "memory": "45%",
        "disk": "60%"
    }

    # Append to log file
    with open(LOG_FILE, "r") as f:
        logs = json.load(f)
    logs.append(log_entry)
    with open(LOG_FILE, "w") as f:
        json.dump(logs, f, indent=2)

    return jsonify({"status": "success"})

if __name__ == "__main__":
    app.run(debug=True)