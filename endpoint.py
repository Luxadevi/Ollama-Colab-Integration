from time import time
from flask import Flask, request, Response
import requests
from flask_cloudflared import run_with_cloudflared
import gradio as gr
from threading import Thread
import sys

app = Flask(__name__)

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH'])
def proxy(path):
    url = f'http://127.0.0.1:11434/{path}'
    resp = requests.request(
        method=request.method,
        url=url,
        headers={key: value for (key, value) in request.headers if key != 'Host'},
        data=request.get_data(),
        cookies=request.cookies,
        allow_redirects=False)

    excluded_headers = ['content-encoding', 'content-length', 'transfer-encoding', 'connection']
    headers = [(name, value) for (name, value) in resp.raw.headers.items()
               if name.lower() not in excluded_headers]
    return Response(resp.content, resp.status_code, headers)
run_with_cloudflared(app)



if __name__ == '__main__':
    app.run()
time.sleep(10)

sys.stdout.flush()