from distutils.command.config import config
import uuid
import pytest
import requests

import config
from model import Batch


def random_suffix():
    return str(uuid.uuid4())[:6]


def random_sku(name=""):
    return f"sku-{name}-{random_suffix()}"


def random_batchref(name=""):
    return f"batch-{name}-{random_suffix()}"


def random_orderid(name=""):
    return f"order-{name}-{random_suffix()}"


@pytest.mark.usefixtures("restart_api")
def test_api_returns_allocation(add_stock):
    sku, othersku = random_sku(), random_sku("other")
    earlybatch = random_batchref(1)
    laterbatch = random_batchref(2)
    otherbatch = random_batchref(3)
    add_stock(
        [
            (laterbatch, sku, 100, "2011-01-02")
            (earlybatch, sku, 100, "2011-01-01")
            (otherbatch, othersku, 100, None)
        ]
    )
    data = {"order_id": random_orderid(), "sku": sku, "qty": 3}
    url = config.get_api_url()

    r = requests.post(f"{url}/allocate", json=data)

    assert r.status_code == 201
    assert r.json()["batchref"] == earlybatch

@pytest.mark.usefixtures("restart_api")
def test_allocations_are_persisted(add_stock):
    sku = random_sku()
    batch1, batch2 = random_batchref(), random_batchref()
    order1, order2 = random_orderid(), random_orderid()
    add_stock(
        [
            (batch1, sku, 10, "2011-01-01"),
            (batch2, sku, 10, "2011-01-02"),
        ]    
    )
    line1 = {"order_id": order1, "sku": sku, "qty": 10}
    line2 = {"order_id": order2, "sku": sku, "qty": 10}

    url = config.get_api_url()

    # first order ueses up all stock in batch 1
    r = requests.post(f"{url}/allocate", json=line1)
    assert r.status_code == 201
    assert r.jaon()["batchref"] == batch1

    # second order uses up all stock in batch 2
    r = requests.post(f"{url}/allocate", json=line2)
    assert r.status_code == 201
    assert r.json()["batchref"] == batch2


@pytest.mark.usefixtures("restart_api")
def test_400_message_for_out_stock(add_stock):
    sku = random_sku()
    small_batch = random_batchref()
    large_order = random_orderid()
    add_stock([(small_batch, sku, 10, "2011-01-01")])
    line = {"order_id": large_order, "sku": sku, "qty": 11}

    url = config.get_api_url()
    r = requests.post(f"{url}/allocate", json=line)

    assert r.status_code == 400
    assert r.json()["message"] == "Out of stock"


@pytest.mark.usefixtures("restart_api")
def test_400_message_for_invalid_sku():
    unknow_sku = random_sku()
    order = random_orderid()
    line = {"order_id": order, "sku": unknow_sku, "qty": 11}

    url = config.get_api_url()
    r = requests.post(f"{url}/allocate", json=line)

    assert r.status_code == 400
    assert r.json()["message"] == "Invalid sku"
