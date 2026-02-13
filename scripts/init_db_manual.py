import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from backend.models.models import Base
import os

DATABASE_URL = "sqlite+aiosqlite:///./backend/costguard.db"

async def init_db():
    print(f"Initializing DB at: {DATABASE_URL}")
    engine = create_async_engine(DATABASE_URL, echo=True)
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        print("Schema created successfully.")
        
        # Verify
        async with engine.connect() as conn:
            from sqlalchemy import inspect
            def get_tables(sync_conn):
                return inspect(sync_conn).get_table_names()
            tables = await conn.run_sync(get_tables)
            print(f"Existing tables: {tables}")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(init_db())
