# pylint: disable=redefined-outer-name
import shutil
import subprocess
import time
from pathlib import Path

import pytest
import redis
import requests
from requests.exceptions import ConnectionError
from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import clear_mappers
from sqlalchemy.orm import sessionmaker
from tenacity import retry
from tenacity import stop_after_delay

from allocation import config
from allocation.adapters.orm import metadata
from allocation.adapters.orm import start_mappers


@pytest.fixture
def in_memory_db():
    engine = create_engine("sqlite:///:memory:")
    metadata.create_all(engine)
    return engine


@pytest.fixture
def session_factory(in_memory_db):
    start_mappers()
    yield sessionmaker(bind=in_memory_db)
    clear_mappers()


@pytest.fixture
def session(session_factory):
    return session_factory()


# def wait_for_postgres_to_come_up(engine):
#     deadline = time.time() + 10
#     while time.time() < deadline:
#         try:
#             return engine.connect()
#         except OperationalError:
#             time.sleep(0.5)
#     pytest.fail("Postgres never came up")
@retry(stop=stop_after_delay(10))
def wait_for_postgres_to_come_up(engine):
        return engine.connect()


# def wait_for_webapp_to_come_up():
#     deadline = time.time() + 10
#     url = config.get_api_url()
#     while time.time() < deadline:
#         try:
#             return requests.get(url)
#         except ConnectionError:
#             time.sleep(0.5)
#     pytest.fail("API never came up")
@retry(stop=stop_after_delay(10))
def wait_for_webapp_to_come_up():
        return requests.get(config.get_api_url())


@retry(stop=stop_after_delay(10))
def wait_for_redis_to_come_up():
    r = redis.Redis(**config.get_redis_host_and_port())
    return r.ping()


@pytest.fixture(scope="session")
def postgres_db():
    engine = create_engine(config.get_postgres_uri())
    wait_for_postgres_to_come_up(engine)
    metadata.create_all(engine)
    return engine


@pytest.fixture
def postgres_session_factory(postgres_db):
    start_mappers()
    yield sessionmaker(bind=postgres_db)
    clear_mappers()


@pytest.fixture
def postgres_session(postgres_session_factory):
    return postgres_session_factory()


@pytest.fixture
def restart_api():
    # What does this line do?
    # If I comment it out it still works the same
    # (Path(__file__).parent / "../entrypoints/flask_app.py").touch()
    # (Path(__file__).parent / "../src/allocation/entrypoints/flask_app.py").touch()
    time.sleep(0.5)
    wait_for_webapp_to_come_up()


@pytest.fixture
def restart_redis_pubsub():
    wait_for_redis_to_come_up()
    if not shutil.which("docker-compose"):
        print("skipping restart, assumes running in container")
        return
    subprocess.run(
        ["docker-compose", "restart", "-t", "0", "redis_pubsub"],
        check=True,
    )
