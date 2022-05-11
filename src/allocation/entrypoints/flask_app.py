from datetime import datetime

from flask import Flask
from flask import request

from allocation.adapters import orm
from allocation.domain import commands
from allocation.service_layer import handlers
from allocation.service_layer import messagebus
from allocation.service_layer import unit_of_work

orm.start_mappers()
app = Flask(__name__)


@app.route("/allocate", methods=["POST"])
def allocate_endpoint():
    try:
        cmd = commands.Allocate(
            request.json["orderid"],
            request.json["sku"],
            request.json["qty"],
        )
        results = messagebus.handle(cmd, unit_of_work.SqlAlchemyUnitOfWork())
        batchref = results.pop(0)

    except (handlers.InvalidSku) as e:
        return {"message": str(e)}, 400

    return {"batchref": batchref}, 201


@app.route("/batches", methods=["POST"])
def add_batch_endpoint():

    eta = request.json["eta"]
    if eta is not None:
        eta = datetime.fromisoformat(eta).date()

    cmd = commands.CreateBatch(
        request.json["batchref"],
        request.json["sku"],
        request.json["qty"],
        eta,
    )

    messagebus.handle(cmd, unit_of_work.SqlAlchemyUnitOfWork())

    return {"message": "ok"}, 201
