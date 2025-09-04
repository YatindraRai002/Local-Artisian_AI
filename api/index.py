import sys, os

# Add backend folder to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.join(current_dir, "..", "backend")
sys.path.append(backend_dir)

from flask import Flask
from flask_cors import CORS

# now this works because backend is on the path
import final_server  

app = Flask(__name__)
CORS(app)
