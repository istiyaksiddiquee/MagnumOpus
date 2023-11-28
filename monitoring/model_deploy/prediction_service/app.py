import os
import math
import pickle
import requests
from flask import Blueprint, Flask, request, jsonify
from werkzeug.middleware.dispatcher import DispatcherMiddleware
from werkzeug.serving import run_simple
from pymongo import MongoClient
import prometheus_client as prom
from prometheus_client import make_wsgi_app
from flask_prometheus_metrics import register_metrics


MAIN = Blueprint("duration", __name__)
CONFIG = {"version": "v0.1.2", "config": "staging"}

pred_gaue = prom.Gauge("magnum::pred::gauge", "Tracking predicted duration")
mae_gaue = prom.Gauge("magnum::mae::gauge", "Tracking MAE of Magnum Opus Regression")
mape_gauge = prom.Gauge("magnum:mape::gauge", "Tracking MAPE of Magnum Opus Regression")
mse_gauge = prom.Gauge("magnum::mse::gauge", "Tracking MSE of Magnum Opus Regression")
rmse_gauge = prom.Gauge("magnum:rmse::gauge", "Tracking RMSE of Magnum Opus Regression")

MODEL_FILE = os.getenv("MODEL_FILE", "lin_reg.bin")
with open(MODEL_FILE, "rb") as f_in:
    dv, model = pickle.load(f_in)

EVIDENTLY_SERVICE_ADDRESS = os.getenv("EVIDENTLY_SERVICE", "http://127.0.0.1:5000")
MONGODB_ADDRESS = os.getenv("MONGODB_ADDRESS", "mongodb://127.0.0.1:27017")

mongo_client = MongoClient(MONGODB_ADDRESS)
db = mongo_client.get_database("prediction_service")
collection = db.get_collection("data")

sum_of_actual = 0
total_error = 0
total_abs_error = 0
total_squared_error = 0
observed_instances = 0

@MAIN.route("/predict", methods=["POST"])
def predict():
    record = request.get_json()

    record["PU_DO"] = "%s_%s" % (record["PULocationID"], record["DOLocationID"])

    X = dv.transform([record])
    y_pred = model.predict(X)
    pred_gaue.set(y_pred)

    result = {
        "duration": float(y_pred),
    }

    save_to_db(record, float(y_pred))
    send_to_evidently_service(record, float(y_pred))
    error_calculation(record["duration"], y_pred)

    return jsonify(result)


def error_calculation(actual, observed):
    observed_instances += 1
    sum_of_actual += actual
    error = actual - observed
    total_error += error
    total_abs_error += abs(error)
    total_squared_error += error**2

    mse = total_squared_error / observed_instances
    rmse = math.sqrt(mse)
    mae = total_abs_error / observed_instances
    mape = total_error / sum_of_actual * 100

    mae_gaue.set(mae)
    mape_gauge.set(mape)
    mse_gauge.set(mse)
    rmse_gauge.set(rmse)

    return


def save_to_db(record, prediction):
    rec = record.copy()
    rec["prediction"] = prediction
    collection.insert_one(rec)


def send_to_evidently_service(record, prediction):
    rec = record.copy()
    rec["prediction"] = prediction
    requests.post(f"{EVIDENTLY_SERVICE_ADDRESS}/iterate/taxi", json=[rec])


def create_dispatcher() -> DispatcherMiddleware:
    """
    App factory for dispatcher middleware managing multiple WSGI apps
    """
    app = Flask(__name__)

    app.register_blueprint(MAIN)
    register_metrics(app, app_version=CONFIG["version"], app_config=CONFIG["config"])

    return DispatcherMiddleware(app.wsgi_app, {"/metrics": make_wsgi_app()})


if __name__ == "__main__":
    run_simple(
        "0.0.0.0",
        9696,
        create_dispatcher(),
        use_reloader=True,
        use_debugger=True,
        use_evalex=True,
    )
