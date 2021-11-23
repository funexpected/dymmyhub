import os
import webbrowser
import requests
import threading
import logging
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import urlencode, urlparse, parse_qs

logger = logging.getLogger("dummyhub")


HOME = Path.home()
LOCAL = os.path.join(HOME, '.dummyhub')
KEYPATH = os.path.join(HOME, '.ssh/id_rsa.pub')
AUTH_CONFIG = os.path.join(LOCAL, "github.token")
# CLIENT_ID = "Iv1.a2f6ee543940fc18"
# CLIENT_SECRET = "8599d79eda0445ac05e06e12c69e496665c61b9a"
CLIENT_ID = "0b807a3307cb6474bd7d"
CLIENT_SECRET = "a17654a2ff86e30d57368a6bd41710206beb6c81"
GITHUB_AUTH_URL = "https://github.com/login/oauth/authorize"
GITHUB_ACCESS_URL = "https://github.com/login/oauth/access_token"


class GithubUnhappy(Exception):
    pass

def login() -> str:
    if os.path.exists(AUTH_CONFIG):
        with open(AUTH_CONFIG, "r") as f:
            return f.read().strip()

    auth_server = None
    port = 31337
    while not auth_server:
        try:
            auth_server = AuthServer(("localhost", port), Handler)
        except OSError:
            port += 1

    url = (
        GITHUB_AUTH_URL
        + "?"
        + urlencode(
            {
                "client_id": CLIENT_ID,
                "scope": "admin:public_key read:public_key write:public_key",
                "redirect_uri": "http://localhost:%s/dummyhub/login" % port
            }
        )
    )
    webbrowser.open(url, 2)
    auth_server.serve_forever()
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "user-agent": "dummyhub",
    }
    resp = requests.post(
        GITHUB_ACCESS_URL,
        headers=headers,
        json={
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "code": auth_server.code_token,
        },
    )
    print("auth response:", resp.json())
    access_token = resp.json()["access_token"]
    save_access_token(access_token)
    return access_token

def apicall(method: str, path: str, **kwargs: str):
    url = "https://api.github.com" + path
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": "fnx",
        "Authorization": "token %s" % login(),
    }
    jsonargs = None
    if method != "POST" and len(kwargs):
        url += "?" + urlencode(kwargs)
    elif len(kwargs):
        jsonargs = kwargs
    # print(method, url)
    resp = requests.request(method, url, headers=headers, json=jsonargs)
    if resp.status_code < 200 or resp.status_code >= 300:
        raise GithubUnhappy("Error while executing %s request for url %s: [%s] %s" % (method, url, resp.status_code, resp.text))
    try:
        return resp.json()
    except:
        return {}


def save_access_token(token: str):
    with open(AUTH_CONFIG, "w") as f:
        f.write(token)

def is_key_registered(active_key: str) -> bool:
    keys = apicall('GET', '/user/keys')
    for key in keys:
        if active_key.startswith(key['key']):
            return True
    return False


class AuthServer(HTTPServer):
    code_token: str = ""


class Handler(BaseHTTPRequestHandler):
    server: AuthServer
    LANDING_PAGE = """
        <!doctype html>
        <html lang="en">
            <head>
                <!-- Required meta tags -->
                <meta charset="utf-8">
                <meta name="viewport" content="width=device-width, initial-scale=1">
                <!-- Bootstrap CSS -->
                <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-utilities@4.1.3/bootstrap-utilities.css">
                <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.3.1/css/bootstrap.min.css" integrity="sha384-ggOyR0iXCbMQv3Xipma34MD+dH/1fQ784/j6cY/iJTQUOhcWr7x9JvoRxT2MZw1T" crossorigin="anonymous">
                <title>Hello, world!</title>
                <style>
                    html {
                        height: 100%!important;
                    }
                    body {
                        font-family: monospace!important;
                    }
                    .cover-container {
                        max-width: 42em;
                    }
                    .btn-secondary, .btn-secondary:hover, .btn-secondary:focus {
                        color: #333;
                        text-shadow: none;
                    }
                </style>
            </head>
            <body class="d-flex h-100 text-center text-white bg-dark" data-new-gr-c-s-check-loaded="14.1007.0" data-gr-ext-installed="" cz-shortcut-listen="true">
                <div class="cover-container d-flex w-100 h-100 p-3 mx-auto flex-column">
                    <header class="mb-auto"></header>
                    <main class="px-3">
                            <h1>dummyhub authorized</h1>
                            <p class="lead">close the page and come back to your favorite terminal.</p>
                            <p class="lead">good luck!</p>
                            <p class="lead">
                                    <a href="javascript: window.close()" class="btn btn-lg btn-secondary fw-bold border-white bg-white">close</a>
                            </p>
                    </main>
                    <footer class="mt-auto ml-auto text-white-50">
                            <p>cover template for <a href="https://getbootstrap.com/" class="text-white">bootstrap</a>, by <a href="https://twitter.com/mdo" class="text-white">@mdo</a>.</p>
                    </footer>
                </div>
                <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.0.0-beta3/dist/js/bootstrap.bundle.min.js" integrity="sha384-JEW9xMcG8R+pH31jmWH6WWP0WintQrMb4s7ZOdauHnUtxwoG2vI5DkLtS3qm9Ekf" crossorigin="anonymous"></script>
            </body>
        </html>
        </body></html>
    """

    def log_message(self, format: str, *args) -> None:
        logger.debug(format, *args)

    def do_GET(self) -> None:
        path = urlparse(self.path)
        params = parse_qs(path.query)
        if path.path == "/dummyhub/login":
            self.server.code_token = params.get("code", [""])[0]
            self.send_response(302, "Moved temporary")
            self.send_header("Location", "/dummyhub/success")
            self.end_headers()
            self.flush_headers()
        elif path.path == "/dummyhub/success":
            self.send_response(200, "OK")
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.flush_headers()
            self.wfile.write(self.LANDING_PAGE.encode("utf8"))
            self.wfile.flush()
            shutdown = threading.Thread(target=self.server.shutdown)
            shutdown.start()
        else:
            self.send_response(404, "Not found")
            self.end_headers()
            self.flush_headers()


login()
active_key = open(KEYPATH, 'r').read().strip()
if not is_key_registered(active_key):
    apicall('POST', '/user/keys', title='Generated by dymmyhub', key=active_key)
    print("New SSH key registered")
else:
    print("Existed ssh key is valid.")
