import pytest
import requests
from allocation.adapters import notifications
from allocation.service_layer import unit_of_work
from src.allocation import bootstrap, config
from sqlalchemy.orm import clear_mappers


@pytest.fixture
def bus(sqlite_session_factory):
	bus = bootstrap.bootstrap(
		start_orm=True,
		uow=unit_of_work.SqlAlchemyUnitOfWork(sqlite_session_factory),
		notifications=notifications.EmailNotifications(),
		publsh=lambda *args: None
	)
	yield bus
	clear_mappers()


def get_email_from_mailhog(sku):
	host, port = map(
		config.get_email_host_and_port().get,
		["host", "http_port"]
	)
	all_emails = requests.get(
			f"http://{host}:{port}/api/v2/messages"
		).json()
	return next(m for m in all_emails["items"] if sku in str(m))


