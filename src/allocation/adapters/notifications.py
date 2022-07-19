import abc
import smtplib


DEFAULT_HOST = ""
DEFAULT_PORT = ""



class AbstractNotifications(abc.ABC):
	@abc.abstractmethod
	def send(self, destination, message):
		raise NotImplementedError()


class EmailNotifications(AbstractNotifications):
	def __init__(self, smtp_host=DEFAULT_HOST, port=DEFAULT_PORT) -> None:
		self.server = smtplib.SMTP(smtp_host, port)
		self.server.noop()


	def send(self, destination, message):
		msg = f"Subject: allocation service notification\n{message}"
		self.server.sendmail(
			from_addr="allocation@example.com",
			to_addrs=[destination]
			msg=msg
		)

