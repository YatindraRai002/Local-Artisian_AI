import sys
import os

# Add project root to path (so "backend" becomes importable)
current_dir = os.path.dirname(os.path.abspath(__file__))  # api/
project_root = os.path.abspath(os.path.join(current_dir, ".."))  # flask-server
sys.path.insert(0, project_root)

from backend import final_server
from backend import data_processor
from backend import lightweight_chatbot

from flask import Flask
from flask_cors import CORS

app = Flask(__name__)
CORS(app)


# ✅ Register routes from backend/final_server
if hasattr(final_server, "app"):  # if final_server itself has a Flask app
    app.register_blueprint(final_server.app)  
elif hasattr(final_server, "bp"):  # or if you used a Blueprint
    app.register_blueprint(final_server.bp)


@app.route("/ping")
def ping():
    return {"msg": "Flask API is alive 🚀"}
