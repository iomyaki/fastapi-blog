from datetime import datetime
from typing import List

from passlib.context import CryptContext
from sqlalchemy import TIMESTAMP, String, Boolean, func, ForeignKey
from sqlalchemy.orm import (
    declared_attr,
    DeclarativeBase,
    Mapped,
    mapped_column,
    relationship,
)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class Base(DeclarativeBase):
    __abstract__ = True

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP,
        server_default=func.now(),
        onupdate=func.now(),
    )

    @declared_attr
    def __tablename__(self) -> str:
        return self.__name__.lower() + "s"

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(id={self.id}, created_at={self.created_at}, updated_at={self.updated_at})>"


class User(Base):
    username: Mapped[str] = mapped_column(String(20), nullable=False)
    password: Mapped[str] = mapped_column(String(60), nullable=False)  # pw hash
    role: Mapped[str] = mapped_column(String(10), nullable=False, default="user")
    recent_post_at: Mapped[datetime | None] = mapped_column(TIMESTAMP, default=None)
    is_blocked: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    posts: Mapped[List["Post"]] = relationship(back_populates="author")

    def verify_password(self, pw: str) -> bool:
        return pwd_context.verify(pw, self.password)

    def set_password(self, pw: str) -> None:
        self.password = pwd_context.hash(pw)

    def __repr__(self) -> str:
        return (
            f"<{self.__class__.__name__}(id={self.id}, created_at={self.created_at}, updated_at={self.updated_at}),"
            f"username={self.username}, role={self.role}, recent_post_at={self.recent_post_at},"
            f"is_blocked={self.is_blocked}, posts={self.posts}>"
        )


class Post(Base):
    author_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    body: Mapped[str] = mapped_column(String)

    author: Mapped[User] = relationship(back_populates="posts")

    def __repr__(self) -> str:
        return (
            f"<{self.__class__.__name__}(id={self.id}, created_at={self.created_at}, updated_at={self.updated_at}),"
            f"author_id={self.author_id}, title={self.title}, body={self.body[:10]}, author={self.author}>"
        )
