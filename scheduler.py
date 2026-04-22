import time
import subprocess
import os

# Get the path to your venv's python
if os.name == 'nt':  # For Windows
    venv_python = os.path.join(".venv", "Scripts", "python.exe")
else:  # For Mac/Linux
    venv_python = os.path.join(".venv", "bin", "python")

while True:
    print(f"\n{time.strftime('%H:%M:%S')} - Moving MinIO data to PostgreSQL...")
    try:
        # Force it to use the VENV Python
        subprocess.run([venv_python, "manual_bridge.py"], check=True)
        print("Ingestion cycle complete.")
    except Exception as e:
        print(f"Scheduler Error: {e}")

    print("Waiting 10 minutes for next cycle...")
    time.sleep(600)
