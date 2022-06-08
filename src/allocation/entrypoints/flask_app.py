from datetime import datetime

from flask import Flask
from flask import request
from flask import jsonify

from allocation.domain import commands
from allocation.adapters import orm
from allocation.service_layer import messagebus
from allocation.service_layer import unit_of_work
from allocation.service_layer import handlers
from allocation import views

app = Flask(__name__)
orm.start_mappers()


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
    uow = unit_of_work.SqlAlchemyUnitOfWork()
    messagebus.handle(cmd, uow)
    return  "OK", 201

@app.route("/allocate", methods=["POST"])
def allocate_endpoint():
    try:
        cmd = commands.Allocate(
            request.json["orderid"],
            request.json["sku"],
            request.json["qty"],
        )

        uow = unit_of_work.SqlAlchemyUnitOfWork()
        messagebus.handle(cmd, uow)

    except (handlers.InvalidSku) as e:
        return {"message": str(e)}, 400

    return "OK", 202


@app.route("/allocations/<orderid>", methods=["GET"])
def allocations_view_endpoint(orderid):
    uow = unit_of_work.SqlAlchemyUnitOfWork()
    result = views.allocations(orderid, uow)
    if not result:
        return "not found", 404
    return jsonify(result), 200
