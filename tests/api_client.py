import requests
from allocation import config


def post_to_add_batch(ref, sku, qty, eta):
    url = config.get_api_url()
    data = {"batchref": ref, "sku": sku, "qty": qty, "eta": eta}
    r = requests.post(f"{url}/batches", json=data)
    assert r.status_code == 201


def post_to_allocate(order_id, sku, qty, expect_success=True):
	url = config.get_api_url()
	data = {"orderid": order_id, "sku":sku, "qty": qty}
	r = requests.post(f"{url}/allocate", json=data)
	if expect_success:
		assert r.status_code == 201
	return r


