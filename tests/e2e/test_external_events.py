import json

import pytest
from tenacity import Retrying
from tenacity import stop_after_delay

from tests import api_client
from tests import redis_client
from tests.random_refs import random_batchref
from tests.random_refs import random_orderid
from tests.random_refs import random_sku


@pytest.mark.usefixtures("postgres_db")
@pytest.mark.usefixtures("restart_api")
@pytest.mark.usefixtures("restart_redis_pubsub")
def test_change_batch_quantity_leading_to_realocation():
    # start with two batches and an order allocated to one of them
    order_id, sku = random_orderid(), random_sku()
    earlier_batch, later_batch = random_batchref("old"), random_batchref("newer")
    api_client.post_to_add_batch(earlier_batch, sku, qty=10, eta="2011-01-01")
    api_client.post_to_add_batch(later_batch, sku, qty=10, eta="2011-01-02")
    api_client.post_to_allocate(order_id, sku, 10)
    response = api_client.get_allocation(order_id)
    assert response.json()[0]["batchref"] == earlier_batch

    subscription = redis_client.subscribe_to("line_allocated")

    # change quantity on allocated batch so it's less than our order
    redis_client.publish_message(
        "change_batch_quantity", {"batchref": earlier_batch, "qty": 3}
    )

    # wait unitl we see a message saying the order has been realocated
    messages = []
    for attempt in Retrying(stop=stop_after_delay(3), reraise=True):
        with attempt:
            message = subscription.get_message(timeout=1)
            if message:
                messages.append(message)
                print(messages)
            data = json.loads(messages[-1]["data"])
            assert data["orderid"] == order_id
            assert data["batchref"] == later_batch
