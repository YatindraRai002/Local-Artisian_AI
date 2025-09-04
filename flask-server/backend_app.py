from flask import Flask, request, jsonify

# Import helpers (no sys.path hacks needed if folder structure is correct)
from helpers.chat_utils import handle_chat
from helpers.search_utils import apply_filters
from helpers.stats_utils import get_stats
from helpers.similar_utils import find_similar

app = Flask(__name__)

@app.route("/chat", methods=["POST"])
def chat_route():
    body = request.json or {}
    return jsonify(handle_chat(body))

@app.route("/search", methods=["POST"])
def search_route():
    filters = request.json or {}
    return jsonify(apply_filters(filters))

@app.route("/stats", methods=["GET"])
def stats_route():
    return jsonify(get_stats())

@app.route("/similar", methods=["GET"])
def similar_route():
    args = request.args
    return jsonify(find_similar(args))

if __name__ == "__main__":
    app.run(debug=True, port=5000)
