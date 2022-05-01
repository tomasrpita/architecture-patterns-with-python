import json
import logging
import redis
from dataclasses import asdict
from src.allocation import config
from src.allocation.domain import events

logger = logging.getLogger(__name__)


r = redis.Redis(**config.get_redis_host_and_port())


# We take a hardcoded channel here, but you could also store a mapping between
# event classes/names and the appropriate channel, allowing one or more message
# types to go to different channels.
def publish(channel, event: events.Event):
    logger.debug("publishing: channel=%s, event=%s", channel, event)
    r.publish(channel, json.dumps(asdict(event)))
