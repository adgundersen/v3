import os, re
from dotenv import load_dotenv
from peewee import PostgresqlDatabase
from urllib.parse import urlparse

load_dotenv()
_url = os.getenv("DATABASE_URL", "postgresql://localhost/crimata")
_url = re.sub(r'\+\w+', '', _url)   # strip +asyncpg etc.
_p = urlparse(_url)
db = PostgresqlDatabase(
    _p.path.lstrip('/'), host=_p.hostname, port=_p.port or 5432,
    user=_p.username or '', password=_p.password or '',
)
