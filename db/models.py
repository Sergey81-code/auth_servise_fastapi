import uuid

from sqlalchemy import ARRAY, String
from sqlalchemy import String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from utils.roles import PortalRole

Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(nullable=False)
    surname: Mapped[str] = mapped_column(nullable=False)
    email: Mapped[str] = mapped_column(nullable=False, unique=True)
    is_active: Mapped[bool] = mapped_column(default=True)
    hashed_password: Mapped[str] = mapped_column(nullable=False)
    roles: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=False)


    # user_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    # name = Column(String, nullable=False)
    # surname = Column(String, nullable=False)
    # email = Column(String, nullable=False, unique=True)
    # is_active = Column(Boolean(), default=True)
    # hashed_password = Column(String, nullable=False)
    # roles = Column(ARRAY(String), nullable=False)

    @property
    def is_superadmin(self) -> bool:
        return PortalRole.ROLE_PORTAL_SUPERADMIN in self.roles

    @property
    def is_admin(self) -> bool:
        return PortalRole.ROLE_PORTAL_ADMIN in self.roles

    def extend_roles_with_admin(self) -> list:
        if not self.is_admin:
            return list({*self.roles, PortalRole.ROLE_PORTAL_ADMIN})
        return self.roles

    def exclude_admin_role(self) -> list:
        if self.is_admin:
            return [role for role in self.roles if role != PortalRole.ROLE_PORTAL_ADMIN]
        return self.roles
