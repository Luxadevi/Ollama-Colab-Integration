from time import time
from flask import Flask, request, Response
import requests
from flask_cloudflared import run_with_cloudflared
import gradio as gr
from threading import Thread
import sys
import os
import logging
from flask import stream_with_context

# Add the parent directory (project) to the sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + '/../')

# Import shared module from the "modules" directory
from shared import shared

api_url = shared['api_endpoint']['url']
app = Flask(__name__)

# Define a chunk size for streaming
CHUNK_SIZE = 512  # 512 bytes

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH'])
def proxy(path):
    url = f'{api_url}/{path}'
    req_stream = request.stream  # Stream the incoming request data

    resp = requests.request(
        method=request.method,
        url=url,
        headers={key: value for (key, value) in request.headers if key != 'Host'},
        data=(chunk for chunk in req_stream),  # Stream request data in chunks
        cookies=request.cookies,
        allow_redirects=False,
        stream=True)  # Stream the response

    excluded_headers = ['content-encoding', 'content-length', 'transfer-encoding', 'connection']
    headers = [(name, value) for (name, value) in resp.raw.headers.items()
               if name.lower() not in excluded_headers]

    # Stream response back to client
    return Response(stream_with_context(resp.iter_content(chunk_size=CHUNK_SIZE)), 
                    resp.status_code, headers)

@app.route('/openai', defaults={'path': ''})
@app.route('/openai/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH'])
def openai_proxy(path):
    try:
        new_url = f'http://127.0.0.1:8000/{path}'
        logging.info(f"Proxying to URL: {new_url}")

        resp = requests.request(
            method=request.method,
            url=new_url,
            headers={key: value for (key, value) in request.headers if key != 'Host'},
            data=(chunk for chunk in request.stream),  # Stream request data in chunks
            cookies=request.cookies,
            allow_redirects=True,
            stream=True)  # Stream the response

        excluded_headers = ['content-encoding', 'content-length', 'transfer-encoding', 'connection']
        headers = [(name, value) for (name, value) in resp.raw.headers.items()
                   if name.lower() not in excluded_headers]

        # Stream response back to client
        return Response(stream_with_context(resp.iter_content(chunk_size=CHUNK_SIZE)), 
                        resp.status_code, headers)
    except Exception as e:
        logging.error(f"Error in openai_proxy: {e}")
        return Response(f"Error: {e}", status=500)

run_with_cloudflared(app)

if __name__ == '__main__':
    app.run(host='0.0.0.0')
