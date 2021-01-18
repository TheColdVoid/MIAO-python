from .scheme import call, get_scheme, HashcodeNotFound
from quart_cors import *
from quart import Quart, request, abort, redirect, jsonify
import json
import os
import webbrowser
import uvicorn
import logging

# Meta info ,such as title,author,authentication,etc
META_INFO: {str: str} = {}

dir_path = os.path.dirname(os.path.realpath(__file__))
app = Quart("MIAO", static_url_path="", static_folder=os.path.join(dir_path, 'static'))
cors(app, allow_origin="*")


@app.route('/scheme')
async def scheme():
    return json.dumps(get_scheme(), default=lambda info: info.get_dict())


@app.route('/call/<int:method_hash>', methods=['POST'])
async def call_func(method_hash: int):
    parameters = await request.get_json()
    try:
        return_val = call(method_hash, *parameters)
        return json.dumps(return_val)
    except(HashcodeNotFound):
        abort(412)


@app.route('/meta-info')
async def meta_info():
    return jsonify(META_INFO)


@app.route('/')
async def index():
    return redirect("/index.html")


# start MIAO server and block current python file
def start(title="MIAO", port: int = 2333, host: str = "0.0.0.0"):
    # TODO:add a logger
    print("MIAO's server is starting...")
    META_INFO['title'] = title
    print_startup_done_message(host, port)

    @app.before_serving
    async def open_browser():
        webbrowser.open(get_hostname(host, port))

    @app.after_serving
    async def close_server():
        print("The MIAO's server is stopping")

    uvicorn.run(app, host=host, port=port, log_level='error')


def get_hostname(host, port):
    url = "http://"
    if host == "0.0.0.0":
        url += "localhost"
    else:
        url += host
    url += ":" + str(port) + "/"
    return url


def print_startup_done_message(host, port):
    print("The MIAO's server started,\n" +
          "please enter this URL in your browser to access this application:\n"
          + get_hostname(host, port))
