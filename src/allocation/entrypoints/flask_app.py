from datetime import datetime
from flask import Flask, request

from src.allocation.adapters import orm
from src.allocation.domain import model
from src.allocation.service_layer import services, unit_of_work

# import src.allocation.domain.model as model
# import src.allocation.adapters.orm as orm
# import src.allocation.service_layer.services as services
# # import src.allocation.service_layer.unit_of_work as unit_of_work
# import domain.model as model
# import adapters.orm as orm
# import service_layer.services as services
# import service_layer.unit_of_work as unit_of_work

# from ..domain import model
# from ..adapters import orm
# from ..service_layer import services
# from ..service_layer import unit_of_work

orm.start_mappers()
app = Flask(__name__)


@app.route("/allocate", methods=["POST"])
def allocate_endpoint():
    try:
        batchref = services.allocate(
            request.json["orderid"],
            request.json["sku"],
            request.json["qty"],
            unit_of_work.SqlAlchemnyUnitOfWork()
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
        unit_of_work.SqlAlchemnyUnitOfWork()
    )

    return {"message": "ok"}, 201
