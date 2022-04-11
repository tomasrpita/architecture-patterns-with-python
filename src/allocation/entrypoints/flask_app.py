from datetime import datetime

from flask import Flask, request

import src.allocation.adapters.orm as orm
import src.allocation.service_layer.handlers as handlers
import src.allocation.service_layer.unit_of_work as unit_of_work
from src.allocation.domain import events
from src.allocation.service_layer import messagebus

orm.start_mappers()
app = Flask(__name__)


@app.route("/allocate", methods=["POST"])
def allocate_endpoint():
    try:
        event = events.AllocationRequired(
            request.json["orderid"],
            request.json["sku"],
            request.json["qty"],
        )
        results = messagebus.handle(event, unit_of_work.SqlAlchemyUnitOfWork())
        batchref = results.pop(0)

    except (handlers.InvalidSku) as e:
        return {"message": str(e)}, 400

    return {"batchref": batchref}, 201


@app.route("/batches", methods=["POST"])
def add_batch_endpoint():

    eta = request.json["eta"]
    if eta is not None:
        eta = datetime.fromisoformat(eta).date()

    event = events.BatchCreated(
        request.json["batchref"],
        request.json["sku"],
        request.json["qty"],
        eta,
    )

    messagebus.handle(event, unit_of_work.SqlAlchemyUnitOfWork())

    return {"message": "ok"}, 201
