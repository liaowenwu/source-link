import os

from flask import Flask, request
from flask_cors import CORS
from api.routes import register_routes
from core.worker import start_worker
from config import PORT

app = Flask(__name__)

default_origins = "http://localhost:5173,http://127.0.0.1:5173,http://47.120.69.243:10000"
configured_origins = os.getenv("CORS_ALLOWED_ORIGINS", default_origins)
allowed_origins = [item.strip() for item in configured_origins.split(",") if item.strip()]

CORS(
    app,
    resources={r"/*": {"origins": allowed_origins or "*"}},
    methods=["GET", "POST", "OPTIONS"],
    allow_headers=[
        "Content-Type",
        "Authorization",
        "Access-Control-Request-Private-Network",
    ],
)


@app.after_request

# 添加privatenetworkheaders。
def add_private_network_headers(response):
    if request.headers.get("Access-Control-Request-Private-Network") == "true":
        response.headers["Access-Control-Allow-Private-Network"] = "true"
    return response


register_routes(app)
start_worker()

if __name__ == "__main__":
    # pyinstaller -F -w ./main.py  -n bbws
    app.run(port=PORT, threaded=True)
