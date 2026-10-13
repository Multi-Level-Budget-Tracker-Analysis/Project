import os
import sys
import webbrowser
import threading
import time

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

from backend.app import app

def open_browser():
    time.sleep(1.5)
    webbrowser.open("http://127.0.0.1:5000")

if __name__ == "__main__":
    print("=" * 70)
    print("  MULTI-LEVEL BUDGET TRACKER ANALYTICS")
    print("  Data Visualization Lab Project — NIE Mysuru")
    print("  Starting Flask Fullstack Server on http://127.0.0.1:5000 ...")
    print("=" * 70)
    
    # Auto launch web browser in background
    threading.Thread(target=open_browser, daemon=True).start()
    app.run(host="0.0.0.0", port=5000, debug=False)
