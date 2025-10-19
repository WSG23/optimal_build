import asyncio

from backend.app.core.database import AsyncSessionLocal
from backend.app.models.property import Property, PropertyType


def dump(value, label):
    print(label, value, type(value))


async def main():
    async with AsyncSessionLocal() as session:
        record = await session.get(Property, "d47174ee-bb6f-4f3f-8baa-141d7c5d9051")
        dump(record.property_type, "record.property_type")
        print("value attr:", getattr(record.property_type, "value", None))
        print("is enum:", isinstance(record.property_type, PropertyType))


asyncio.run(main())
