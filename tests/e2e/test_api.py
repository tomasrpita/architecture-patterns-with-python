import pytest
import requests

from allocation import config
from tests import api_client
from tests.random_refs import random_batchref
from tests.random_refs import random_orderid
from tests.random_refs import random_sku


# Finally, we can confidently strip down our E2E tests to just two,
# one for the happy path and one for the unhappy path:
# @pytest.mark.usefixtures("postgres_db")
# @pytest.mark.usefixtures("restart_api")
# def test_happy_path_returns_201_and_allocated_batch():
#     sku, othersku = random_sku(), random_sku("other")
#     earlybatch = random_batchref(1)
#     laterbatch = random_batchref(2)
#     otherbatch = random_batchref(3)

#     api_client.post_to_add_batch(earlybatch, sku, 100, "2011-01-01")
#     api_client.post_to_add_batch(laterbatch, sku, 100, "2011-02-02")
#     api_client.post_to_add_batch(otherbatch, othersku, 100, None)

#     data = {"orderid": random_orderid(), "sku": sku, "qty": 3}
#     url = config.get_api_url()

#     r = requests.post(f"{url}/allocate", json=data)

#     assert r.status_code == 201
#     assert r.json()["batchref"] == earlybatch

@pytest.mark.usefixtures("postgres_db")
@pytest.mark.usefixtures("restart_api")
def test_happy_path_returns_202_and_batch_is_allocated():
    orderid = random_orderid()
    sku, othersku = random_sku(), random_sku("other")
    earlybatch = random_batchref(1)
    laterbatch = random_batchref(2)
    otherbatch = random_batchref(3)

    api_client.post_to_add_batch(laterbatch, sku, 100, "2011-02-02")
    api_client.post_to_add_batch(earlybatch, sku, 100, "2011-01-01")
    api_client.post_to_add_batch(otherbatch, othersku, 100, None)

    response = api_client.post_to_allocate(random_orderid(), sku, qty=3)

    assert response.status_code == 201
    assert response.json()["batchref"] == earlybatch

# @pytest.mark.usefixtures("postgres_db")
# @pytest.mark.usefixtures("restart_api")
# def test_unhappy_path_returns_400_and_error_message():
#     unknown_sku = random_sku()
#     order = random_orderid()
#     line = {"orderid": order, "sku": unknown_sku, "qty": 11}

#     url = config.get_api_url()
#     r = requests.post(f"{url}/allocate", json=line)

#     assert r.status_code == 400
#     assert r.json()["message"] == f"Invalid sku {unknown_sku}"

@pytest.mark.usefixtures("postgres_db")
@pytest.mark.usefixtures("restart_api")
def test_unhappy_path_returns_400_and_error_message():
    unknown_sku = random_sku()
    order_id = random_orderid()
    response = api_client.post_to_allocate(
        order_id,
        unknown_sku,
        qty=20,
        expect_success=False,
    )

    assert response.status_code == 400
    assert response.json()["message"] == f"Invalid sku {unknown_sku}"
