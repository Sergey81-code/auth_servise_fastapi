import asyncio
import os
import sys

from sqlalchemy import delete
from sqlalchemy import select

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from db.models import User
from api.core.dependencies import get_session


async def prompt_for_superadmin_credentials():
    email = input("Enter email of superadmin: ")

    async for session in get_session():
        await delete_superadmin(email, session)


async def delete_superadmin(email, session):
    """Delete a superadmin in the database"""
    async with session.begin():
        exists = await session.execute(select(User).where(User.email == email))
        user = exists.scalar_one_or_none()

        if not user:
            print("Error: A user with this email does not exist.")
            return

        query = delete(User).where(User.email == email)

        try:
            await session.execute(query)
            await session.commit()
            print(f"Superadmin {email} was deleted successfully!")
        except Exception as e:
            print(f"Unexpected error: {e}")


if __name__ == "__main__":
    asyncio.run(prompt_for_superadmin_credentials())
