from flask import Flask, jsonify, request
from analysis import calculate_kpi

app = Flask(__name__)

@app.route("/health", methods=["GET"])
def health():
    return {"status": "ok"}

@app.route("/kpi", methods=["GET"])
def get_all():
    return jsonify(calculate_kpi())

@app.route("/kpi", methods=["POST"])
def get_by_period():
    data = request.get_json()
    start = data.get("start_date")
    end = data.get("end_date")
    return jsonify(calculate_kpi(start, end))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
