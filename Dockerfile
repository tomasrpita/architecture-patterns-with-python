FROM python:3.9-slim-buster

# RUN apt install gcc libpq (no longer needed bc we use psycopg2-binary)

COPY requirements.txt /tmp/
RUN pip install -r /tmp/requirements.txt

RUN mkdir -p /src
RUN mkdir -p /tests
COPY src/ /src/
COPY tests/ /tests/

WORKDIR /src
