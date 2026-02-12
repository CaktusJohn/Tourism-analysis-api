from flask import Flask, jsonify, request
from analysis import calculate_kpi

app = Flask(__name__)

@app.route("/health", methods=["GET"])
def health():
    return {"status": "ok"}

@app.route("/kpi", methods=["GET"])
def get_kpi():
    data = calculate_kpi()
    return jsonify(data)

@app.route("/kpi", methods=["POST"])
def get_kpi_by_period():
    body = request.get_json()

    start_date = body.get("start_date")
    end_date = body.get("end_date")

    data = calculate_kpi(start_date=start_date, end_date=end_date)

    return jsonify(data)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
