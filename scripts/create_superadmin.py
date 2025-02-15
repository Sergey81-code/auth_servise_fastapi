import asyncio
import os
import re
import sys
from getpass import getpass

from sqlalchemy import select

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from uuid import uuid4
from db.models import User
from db.session import get_session
from utils.hashing import Hasher
from utils.roles import PortalRole


def get_password(message):
    return getpass(message).strip()


def is_valid_email(email: str) -> bool:
    """Checks if the email matches the format."""
    pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    return re.match(pattern, email) is not None


def is_valid_password(password: str) -> bool:
    """Checks if the password meets security requirements."""
    if len(password) < 8:
        return False
    if not re.search(r"[A-Z]", password):
        return False
    if not re.search(r"[a-z]", password):
        return False
    if not re.search(r"\d", password):
        return False
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        return False
    return True


async def prompt_for_superadmin_credentials():
    while True:
        email = input("Enter email: ").strip()
        if email.lower() == "exit" or email == "exit()":
            print("Exiting...")
            sys.exit(0)
        if is_valid_email(email):
            break
        print(
            "Invalid email format. Please enter a valid email. Type 'exit' or 'exit()' to exit the program."
        )

    while True:
        password = get_password("Enter password: ")
        if password.lower() == "exit" or password == "exit()":
            print("Exiting...")
            sys.exit(0)
        if is_valid_password(password):
            break
        print(
            "Password must be at least 8 characters long and contain uppercase and lowercase letters, numbers, and special characters. Type 'exit' or 'exit()' to exit the program."
        )

    while True:
        password2 = get_password("Repeat password: ")
        if password.lower() == "exit" or password == "exit()":
            print("Exiting...")
            sys.exit(0)
        if password2 == password:
            break
        print("Passwords do not match")

    name = input("Enter name (default: 'Super'): ").strip() or "Super"
    surname = input("Enter surname (default: 'Admin'): ").strip() or "Admin"

    async for session in get_session():
        await create_superadmin(email, password, name, surname, session)


async def create_superadmin(email, password, name, surname, session):
    """Create a superadmin in the database"""

    async with session.begin():
        exists = await session.execute(select(User).where(User.email == email))
        user = exists.scalar_one_or_none()

        if user:
            print("Error: A user with this email already exists.")
            return

        new_superuser = User(
            user_id=uuid4(),
            name=name,
            surname=surname,
            email=email,
            hashed_password=Hasher.get_password_hash(password),
            is_active=True,
            roles=[PortalRole.ROLE_PORTAL_SUPERADMIN],
        )

        try:
            session.add(new_superuser)
            await session.commit()
            print(f"Superadmin {email} was created successfully!")
        except TypeError:
            print("Error: possibly an incorrect argument name in the User model.")
        except Exception as e:
            print(f"Unexpected error: {e}")


if __name__ == "__main__":
    asyncio.run(prompt_for_superadmin_credentials())
