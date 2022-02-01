from sqlalchemy import create_engine
from config import DATABASE_URI
from db_tables import metadata

engine = create_engine(DATABASE_URI)


def recreate_db():
    metadata.drop_all(engine)
    metadata.create_all(engine)
