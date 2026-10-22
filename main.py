"""
AI Content & Plagiarism Intelligence Suite
Main application entry point.

Run via:
    python main.py
or double-click:
    run.bat
"""
import socket
import sys
import time
import urllib.request
import webbrowser


def is_port_in_use(host: str, port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(1.0)
        return s.connect_ex((host, port)) == 0


def main():
    port = 8000
    host = "127.0.0.1"

    print("=" * 65)
    print(" Multi-Vector Forensic AI & Plagiarism Consensus Suite")
    print("=" * 65)

    if is_port_in_use(host, port):
        # Verify if it's our server responding on /health
        try:
            req = urllib.request.Request(f"http://{host}:{port}/health")
            with urllib.request.urlopen(req, timeout=2) as response:
                if response.status == 200:
                    print(f"\n[INFO] Server is ALREADY RUNNING and healthy on http://localhost:{port}!")
                    print(f"[INFO] Opening http://localhost:{port} in your web browser...")
                    webbrowser.open(f"http://localhost:{port}")
                    print("\nYou can keep this window open or close it at any time.")
                    print("=" * 65)
                    return
        except Exception:
            print(f"\n[WARNING] Port {port} is occupied by another process.")
            print(f"Please terminate any process using port {port} and try again.")
            return

    # Port is free: start uvicorn directly
    print(f"\n[INFO] Starting uvicorn server on http://localhost:{port} ...")
    print(f"[INFO] Health check: http://localhost:{port}/health")
    print("=" * 65)

    import uvicorn
    # Open browser after a slight delay
    def open_ui():
        time.sleep(2.0)
        webbrowser.open(f"http://localhost:{port}")

    import threading
    threading.Thread(target=open_ui, daemon=True).start()

    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=False)


if __name__ == "__main__":
    main()
