
import logging
import os
from datetime import date

from dotenv import load_dotenv
from pymongo import MongoClient, UpdateOne
from pymongo.errors import PyMongoError

load_dotenv()

logger = logging.getLogger(__name__)

_client = None
_collection = None
_index_ready = False


def _get_collection():
    """Lazily initialize the MongoDB weather cache."""
    global _client, _collection, _index_ready

    uri = os.getenv("MONGODB_URI")
    if not uri:
        return None

    try:
        if _collection is None:
            _client = MongoClient(
                uri,
                serverSelectionTimeoutMS=3000,
                connectTimeoutMS=3000,
            )
            _collection = _client["climate_hazard_analyzer"][
                "daily_weather"
            ]

        _client.admin.command("ping")

        if not _index_ready:
            _collection.create_index(
                [
                    ("latitude", 1),
                    ("longitude", 1),
                    ("date", 1),
                ],
                unique=True,
                name="location_date_unique",
            )
            _index_ready = True

        return _collection

    except PyMongoError:
        logger.warning(
            "MongoDB cache unavailable; weather data cannot be cached.",
            exc_info=True,
        )
        return None


def get_cached_observations(
    latitude: float,
    longitude: float,
    start_date: date,
    end_date: date,
):
    """Return cached records; None means the database is unavailable."""
    collection = _get_collection()

    if collection is None:
        return None

    lat = round(latitude, 4)
    lon = round(longitude, 4)

    try:
        return list(
            collection.find(
                {
                    "latitude": lat,
                    "longitude": lon,
                    "date": {
                        "$gte": start_date.isoformat(),
                        "$lte": end_date.isoformat(),
                    },
                },
                {
                    "_id": 0,
                    "date": 1,
                    "temperature_max": 1,
                },
            ).sort("date", 1)
        )
    except PyMongoError:
        logger.warning(
            "MongoDB cache read failed.",
            exc_info=True,
        )
        return None


def save_observations(
    latitude: float,
    longitude: float,
    observations: list[dict],
) -> bool:
    """Upsert observations and report whether the write succeeded."""
    collection = _get_collection()

    if collection is None:
        return False

    if not observations:
        return True

    lat = round(latitude, 4)
    lon = round(longitude, 4)

    operations = [
        UpdateOne(
            {
                "latitude": lat,
                "longitude": lon,
                "date": item["date"],
            },
            {
                "$set": {
                    "latitude": lat,
                    "longitude": lon,
                    "date": item["date"],
                    "temperature_max": item["temperature_max"],
                }
            },
            upsert=True,
        )
        for item in observations
    ]

    try:
        collection.bulk_write(operations, ordered=False)
        return True
    except PyMongoError:
        logger.warning(
            "MongoDB cache write failed.",
            exc_info=True,
        )
        return False
