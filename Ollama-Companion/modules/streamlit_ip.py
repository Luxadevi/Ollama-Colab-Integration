""""
# Old code for building a cloudflare tunnel

import subprocess
import psutil
import re

def is_tunnel_running():
    for process in psutil.process_iter(['pid', 'name']):
        try:
            if 'cloudflared' in process.info['name'].lower():
                return True
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue
    return False

def start_tunnel():
    if not is_tunnel_running():
        process = subprocess.Popen(['pycloudflared', 'tunnel', '--url', 'http://127.0.0.1:8501'],
                                   stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)

        print("Starting Cloudflare Tunnel...")
        for line in iter(process.stdout.readline, ''):
            if '.trycloudflare.com' in line:
                print(f"Tunnel URL: {line.strip()}")
                break

if __name__ == "__main__":
    start_tunnel()
"""""