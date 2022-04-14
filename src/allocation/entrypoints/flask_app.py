from datetime import datetime

from flask import Flask
from flask import request

from src.allocation.adapters import orm
from src.allocation.domain import commands
from src.allocation.service_layer import handlers
from src.allocation.service_layer import messagebus
from src.allocation.service_layer import unit_of_work

orm.start_mappers()
app = Flask(__name__)


@app.route("/allocate", methods=["POST"])
def allocate_endpoint():
    try:
        event = commands.Allocate(
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

    event = commands.CreateBatch(
        request.json["batchref"],
        request.json["sku"],
        request.json["qty"],
        eta,
    )

    messagebus.handle(event, unit_of_work.SqlAlchemyUnitOfWork())

    return {"message": "ok"}, 201
