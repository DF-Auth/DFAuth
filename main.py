import eventlet
eventlet.monkey_patch()

from flask import Flask, redirect, render_template, request, jsonify, Response
from flask_sock import Sock, Server
from werkzeug.exceptions import HTTPException, NotFound, BadRequest
from random import randint
from json import dumps
from uuid import uuid4
from dotenv import load_dotenv
from functools import wraps
from typing import Union
import os
import re
import io
import fireclient_auth
from eventlet import wsgi

load_dotenv()



VERSION = "1.1.2"


codes = {}

tokens = {}

def gen_code():
    return "{:06d}".format(randint(0, 999999))

def env_to_bool(env_result: str) -> bool:
    if env_result.lower() in ["false", "0", ""]:
        return False
    else:
        return True

def get_ws_address():
    external_address = os.getenv("EXTERNAL_ADDRESS")
    externally_secure = env_to_bool(os.getenv("EXTERNALLY_SECURE", ""))
    if externally_secure:
        return f"wss://{external_address}/auth_wait"
    else:
        return f"ws://{external_address}/auth_wait"

DF_USER_AGENT_REGEX = "DiamondFire/([0123456789\.]*) \(([0123456789]*), ([abcdefghijklmnopqrstuvxyzABCDEFGHIJKLMNOPQRSTUVXYZ0123456789_]*)\)"
DF_USER_AGENT_REGEX_DF_VERSION = 1
DF_USER_AGENT_REGEX_PLOT_ID = 2
DF_USER_AGENT_REGEX_PLOT_OWNER = 3
def decode_df_user_agent(user_agent: str) -> Union[tuple[str, str, str], None]:
    match: re.Match = re.search(DF_USER_AGENT_REGEX, user_agent)
    if match == None:
        return None
    if match.groups() == ():
        return None
    df_version = match.group(DF_USER_AGENT_REGEX_DF_VERSION)
    plot_id = match.group(DF_USER_AGENT_REGEX_PLOT_ID)
    plot_owner = match.group(DF_USER_AGENT_REGEX_PLOT_OWNER)
    return df_version, plot_id, plot_owner

def ip_snatcher(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        ip = request.remote_addr
        proxy_ip_header = os.getenv("PROXY_IP_HEADER")
        if not proxy_ip_header == None:
            ip = request.headers.get(proxy_ip_header, ip)
        #print(ip)
        return f(ip, *args, **kwargs)
    return decorated_function

app = Flask(__name__)
sock = Sock(app)

app.jinja_env.globals.update(plot_id=os.getenv("PLOT_ID"), plot_id_beta=os.getenv("PLOT_ID_BETA"), plot_owner=os.getenv("PLOT_OWNER"), ws_address=get_ws_address(), version=VERSION, fca_key=fireclient_auth.get_public_der_base64())

@app.errorhandler(HTTPException)
def error(e: HTTPException):
    if request.path.startswith("/api"):
        return Response(dumps({
            "code": e.code,
            "name": e.name,
            "message": e.description
        }), e.code, mimetype="application/json")
    else:
        return Response(render_template("error.html", code=e.code, name=e.name, message=e.description), e.code)

@app.route("/")
def home():
    return render_template("home.html")

@app.route("/auth")
@ip_snatcher
def auth(ip):
    appid = request.args.get("appid", 0, int)
    appname = "Unknown" # APPS[appid]["name"]
    redirloc = request.args.get("redirect", "/try_it_out_response") # APPS[appid]["redirect"]
    code = gen_code()
    codes[code] = {
        "ip": ip,
        "ready": False
    }
    return render_template("auth.html", application_name=appname, appid=appid, redirect=redirloc, code=code)

@app.route("/.plot/complete_auth/<string:code>/<string:uuid>/<string:username>")
@ip_snatcher
def plot_complete_auth(ip, code, uuid, username):
    SPOOF_MSG = "imagine somebody actually trying to spoof their login xD"
    if ip in os.getenv("DF_IPS", "51.222.245.229,54.39.29.75").split(","):
        user_agent = decode_df_user_agent(request.headers.get("User-Agent", ""))
        if user_agent == None:
            return SPOOF_MSG
        _, plot_id, plot_owner = user_agent
        if not plot_id in [os.getenv("PLOT_ID"), os.getenv("PLOT_ID_BETA", "_")]:
            return SPOOF_MSG
        if not plot_owner == os.getenv("PLOT_OWNER"):
            return SPOOF_MSG
        #print(f"Logging in {username} ({uuid}) with code {code}.")
        if code in codes.keys():
            codes[code]["uuid"] = uuid
            codes[code]["username"] = username
            codes[code]["ready"] = True
        return ""
    else:
        return SPOOF_MSG

@app.route("/try_it_out_response")
def try_it_out_response():
    token = request.args.get("token")
    if token in tokens.keys():
        return render_template("try_it_out_response.html", response=tokens[token])
    else:
        raise BadRequest()

@app.route("/api/get_token/<string:token>")
def api_get_token(token):
    if token in tokens.keys():
        return jsonify(tokens[token])
    else:
        raise NotFound("Invalid token supplied.")

@app.route("/my_ip")
@ip_snatcher
def my_ip(ip):
    return ip

@app.route("/.fireclient_auth_finish")
@ip_snatcher
def fireclient_auth_finish(ip):
    secretKey = request.args.get("secretKey")
    username = request.args.get("username")

    uuid = fireclient_auth.auth_finish(secretKey, username)

    retrievaltoken = uuid4().hex
    tokens[retrievaltoken] = {
        "uuid": uuid,
        "username": username,
        "ip": ip
    }

    return jsonify({
        "token": retrievaltoken
    })


@sock.route("/auth_wait")
def auth_wait(ws: Server):
    code = ws.receive()
    #print("Waiting for auth with code", code)
    while True:
        data = ws.receive(.01)
        data = ws.receive(1)
        if not ws.connected:
            return
        ws.send(dumps({"type": "ping"}))
        if codes[code]["ready"]:
            retrievaltoken = uuid4().hex
            rdata = codes[code]
            del rdata["ready"]
            tokens[retrievaltoken] = rdata
            del codes[code]
            ws.send(dumps({"type": "ready", "token": retrievaltoken}))
            ws.close()
            return

class DeadEnd(io.BufferedWriter):

    def __init__(self) -> None:
        pass

    def write(self, __buffer) -> int:
        pass


if __name__ == "__main__":
    wsgi.server(eventlet.listen((os.getenv("HOST"), int(os.getenv("PORT")))), app, log=DeadEnd())