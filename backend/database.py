from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from config import get_settings

settings = get_settings()

client: AsyncIOMotorClient = None
db: AsyncIOMotorDatabase = None


async def connect_db():
    """Connect to MongoDB on startup."""
    global client, db
    client = AsyncIOMotorClient(settings.mongodb_url)
    db = client[settings.mongodb_db_name]

    # Create indexes
    await db.campaigns.create_index("created_at")
    await db.leads.create_index("campaign_id")
    await db.leads.create_index("email")
    await db.leads.create_index([("campaign_id", 1), ("email", 1)], unique=True)
    await db.outreach_steps.create_index("lead_id")
    await db.replies.create_index("lead_id")
    await db.suppression_list.create_index("email", unique=True)


async def close_db():
    """Close MongoDB connection on shutdown."""
    global client
    if client:
        client.close()


def get_db() -> AsyncIOMotorDatabase:
    """Get the database instance."""
    return db
