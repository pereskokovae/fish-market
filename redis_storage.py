import redis
import os


_database = None


def get_database_connection():
    global _database
    if _database is None:
        host = os.getenv("DATABASE_HOST")
        port = os.getenv("DATABASE_PORT")
        password = os.getenv("DATABASE_PASSWORD")

        _database = redis.Redis(host=host, port=int(port), password=password)
    return _database


def get_state(db, chat_id: int) -> str:
    raw = db.get(chat_id)
    return raw.decode("utf-8") if raw else "START"


def set_state(db, chat_id: int, state: str):
    db.set(chat_id, state)