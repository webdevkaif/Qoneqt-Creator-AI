from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from app.core.config import settings
from loguru import logger

_client: AsyncIOMotorClient = None


async def connect_db():
    global _client
    logger.info(f"Connecting to MongoDB at {settings.MONGODB_URL}")
    try:
        _client = AsyncIOMotorClient(settings.MONGODB_URL, serverSelectionTimeoutMS=2000)
        await _client.server_info()
    except Exception:
        logger.warning("MongoDB not available! Falling back to in-memory mongomock_motor.")
        from mongomock_motor import AsyncMongoMockClient
        _client = AsyncMongoMockClient()
        
    from app.models.user import User
    from app.models.project import Project
    from app.models.scene import Scene
    from app.models.asset import Asset
    from app.models.job import GenerationJob
    from app.models.publish import PublishRecord
    from app.models.settings import UserSettings

    await init_beanie(
        database=_client[settings.MONGODB_DB_NAME],
        document_models=[User, Project, Scene, Asset, GenerationJob, PublishRecord, UserSettings],
    )
    logger.info("Database connected and Beanie initialized")


async def close_db():
    global _client
    if _client:
        _client.close()
        logger.info("MongoDB connection closed")
