import subprocess
import threading
import re

def start_tunnel():
    print("Starting Cloudflare Tunnel...")
    process = subprocess.Popen(['pycloudflared', 'tunnel', '--url', 'http://127.0.0.1:8501'],
                               stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)

    for line in iter(process.stdout.readline, ''):
        if '.trycloudflare.com' in line:
            url = re.search(r'https://[a-zA-Z0-9-]+\.trycloudflare\.com', line)
            if url:
                print(f"Tunnel URL: {url.group()}")
                break

def run_streamlit():
    print("Starting Streamlit App...")
    subprocess.call(['streamlit', 'run', '/content/Ollama-Companion/main.py'])

def main():
    tunnel_thread = threading.Thread(target=start_tunnel)
    streamlit_thread = threading.Thread(target=run_streamlit)

    tunnel_thread.start()
    streamlit_thread.start()

    tunnel_thread.join()
    streamlit_thread.join()

if __name__ == "__main__":
    main()
