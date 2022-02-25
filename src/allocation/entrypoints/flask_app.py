from datetime import datetime
from flask import Flask, request


import src.allocation.domain.model as model
import src.allocation.adapters.orm as orm
import src.allocation.service_layer.services as services
# import src.allocation.service_layer.unit_of_work as unit_of_work
from src.allocation.service_layer.unit_of_work import uow_maker

orm.start_mappers()
app = Flask(__name__)


@app.route("/allocate", methods=["POST"])
def allocate_endpoint():
    try:
        batchref = services.allocate(
            request.json["orderid"],
            request.json["sku"],
            request.json["qty"],
            uow_maker
        )

    except (model.OutOfStock, services.InvalidSku) as e:
        return {"message": str(e)}, 400

    return {"batchref": batchref}, 201


@app.route("/batches", methods=["POST"])
def add_batch_endpoint():

    eta = request.json["eta"]
    if eta is not None:
        eta = datetime.fromisoformat(eta).date()

    services.add_batch(
        request.json["batchref"],
        request.json["sku"],
        request.json["qty"],
        eta,
        uow_maker
    )

    return {"message": "ok"}, 201
