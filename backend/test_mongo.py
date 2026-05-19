import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

async def test():
    try:
        uri = "mongodb+srv://unvraviteja_db_user:Raviteja%402003@raviteja.qofofnp.mongodb.net/?appName=Raviteja"
        client = AsyncIOMotorClient(uri)
        db = client['prospectiq']
        await db.command('ping')
        print('MongoDB Atlas connected OK')
        client.close()
    except Exception as e:
        print(f'MongoDB connection failed: {e}')

if __name__ == "__main__":
    asyncio.run(test())
