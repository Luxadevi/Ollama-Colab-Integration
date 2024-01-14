import subprocess
import threading
import time
import logging.handlers
import sys
import os

def create_logger(name, filename, level, formatter):
    logger = logging.getLogger(name)
    handler = logging.handlers.RotatingFileHandler(filename, maxBytes=5*1024*1024, backupCount=5)
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(level)
    return logger

status_formatter = logging.Formatter('[%(asctime)s] [%(levelname)s] [%(name)s] - %(message)s')
error_formatter = logging.Formatter('[%(asctime)s] [%(levelname)s] [%(name)s] - %(message)s')

loggers = {
    "Status": create_logger("Status", "status.log", logging.INFO, status_formatter),
    "OllamaStatus": create_logger("OllamaStatus", "ollama.log", logging.INFO, status_formatter),
    "Error": create_logger("Error", "error.log", logging.ERROR, error_formatter),
    "OllamaError": create_logger("OllamaError", "ollama_error.log", logging.ERROR, error_formatter)
}

class ProcessMonitor:
    def __init__(self):
        self.processes = {}
        self.is_monitoring = True

    def handle_output(self, process_name):
        process = self.processes[process_name]
        logger_status = loggers[f"{process_name.capitalize()}Status"]
        for line in iter(process.stdout.readline, b''):
            logger_status.info(line.decode().strip())

    def run_ollama(self):
        os.environ["OLLAMA_HOST"] = "0.0.0.0:11434"
        os.environ["OLLAMA_ORIGINS"] = "http://0.0.0.0:*"

        cmd = "ollama serve"
        # Redirect subprocess output to /dev/null
        with open(os.devnull, 'wb') as devnull:
            self.processes['ollama'] = subprocess.Popen(cmd, shell=True, stdout=devnull, stderr=devnull)
        loggers["OllamaStatus"].info(f"Started ollama with command: {cmd}")

    def monitor_process(self, process_name):
        while self.is_monitoring:
            if self.processes[process_name].poll() is not None:
                loggers["Status"].warning(f"{process_name} process has stopped. Restarting...")
                self.run_ollama()
            time.sleep(5)

    def start(self):
        self.run_ollama()
        threading.Thread(target=self.monitor_process, args=('ollama',)).start()

    def stop(self):
        self.is_monitoring = False
        for p in self.processes.values():
            p.terminate()

if __name__ == '__main__':
    monitor = ProcessMonitor()
    monitor.start()
