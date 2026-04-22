from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from infra.database import Base


class Item(Base):
    __tablename__ = "items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(String, nullable=False)

    link1_url: Mapped[str] = mapped_column(Text, nullable=False)
    link1_label: Mapped[str] = mapped_column(String, nullable=False)

    link2_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    link2_label: Mapped[str | None] = mapped_column(String, nullable=True)

    link3_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    link3_label: Mapped[str | None] = mapped_column(String, nullable=True)

    is_bought: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
