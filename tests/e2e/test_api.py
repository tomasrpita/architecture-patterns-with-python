import uuid
import pytest
import requests

import config


def random_suffix():
    return str(uuid.uuid4())[:6]


def random_sku(name=""):
    return f"sku-{name}-{random_suffix()}"


def random_batchref(name=""):
    return f"batch-{name}-{random_suffix()}"


def random_orderid(name=""):
    return f"order-{name}-{random_suffix()}"

# Finally, we can confidently strip down our E2E tests to just two,
# one for the happy path and one for the unhappy path:
@pytest.mark.usefixtures("restart_api")
def test_happy_path_returns_201_and_allocated_batch(add_stock):
    sku, othersku = random_sku(), random_sku("other")
    earlybatch = random_batchref(1)
    laterbatch = random_batchref(2)
    otherbatch = random_batchref(3)
    # add_stock(
    #     [
    #         (laterbatch, sku, 100, "2011-02-02"),
    #         (otherbatch, othersku, 100, None),
    #         (earlybatch, sku, 100, "2011-01-01"),
    #     ]
    # )
    post_to_add_batch(earlybatch, sku, 100, "2011-01-01")
    post_to_add_batch(laterbatch, sku, 100, "2011-02-02")
    post_to_add_batch(otherbatch, othersku, 100, None)

    data = {"orderid": random_orderid(), "sku": sku, "qty": 3}
    url = config.get_api_url()

    r = requests.post(f"{url}/allocate", json=data)

    assert r.status_code == 201
    assert r.json()["batchref"] == earlybatch


@pytest.mark.usefixtures("restart_api")
def test_unhappy_path_returns_400_and_error_message():
    unknown_sku = random_sku()
    order = random_orderid()
    line = {"orderid": order, "sku": unknown_sku, "qty": 11}

    url = config.get_api_url()
    r = requests.post(f"{url}/allocate", json=line)

    assert r.status_code == 400
    assert r.json()["message"] == f"Invalid sku {unknown_sku}"


def post_to_add_batch(ref, sku, qty, eta):
    url = config.get_api_url()
    data = {"batchref": ref, "sku": sku, "qty": qty, "eta": eta}
    r = requests.post(f"{url}/add_batch", json=data)
    assert r.status_code == 201
