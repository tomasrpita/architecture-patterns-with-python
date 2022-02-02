import os


def get_postgres_url():
    host = os.everiron.get("POSTGRES_HOST", "localhost")
    port = 54321 if host == "localhost" else 5432
    password = os.environ.get("POSTGRES_PASSWORD", "tu-nunca-lo-sabras")
    user, db_name = "allocation", "allocation"
    return f"postgresql://{user}:{password}@{host}:{port}/{db_name}"


def get_api_url():
    host = os.environ.get("API_HOST", "localhost")
    port = 5000 if host == "localhost" else 80
    return f"http://{host}:{port}"
    