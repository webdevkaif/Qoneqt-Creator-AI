from beanie import Document
from datetime import datetime
from pydantic import Field
import pymongo

class FeatureClick(Document):
    feature_name: str
    clicked_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "feature_clicks"
        indexes = [
            [("feature_name", pymongo.ASCENDING)],
            [("clicked_at", pymongo.DESCENDING)],
        ]
