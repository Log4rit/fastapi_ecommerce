from datetime import datetime
from sqlalchemy import ForeignKey, Text, DateTime, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class Review(Base):
    __tablename__ = "reviews"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'), nullable=False)
    product_id: Mapped[int] = mapped_column(ForeignKey('products.id'), nullable=False)
    comment: Mapped[str] = mapped_column(Text)
    comment_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    grade: Mapped[int] = mapped_column(nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True)
    __table_args__ = (
        CheckConstraint("grade >=1 AND grade <= 5"),
    )

    user: Mapped["User"] = relationship("User")
    product : Mapped["Product"] = relationship("Product")
