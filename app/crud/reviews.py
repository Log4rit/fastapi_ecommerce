from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Sequence

from app.models import Review as ReviewModel


async def get_reviews(db_session: AsyncSession,
                      product_id: int = None,
                      user_id: int = None,
                      review_id: int = None,
                      is_active: bool = None) -> Sequence[ReviewModel]:
    review_stmt = select(ReviewModel)

    if product_id:
        review_stmt = review_stmt.where(ReviewModel.product_id == product_id)
    if user_id:
        review_stmt = review_stmt.where(ReviewModel.user_id == user_id)
    if review_id:
        review_stmt = review_stmt.where(ReviewModel.id == review_id)
    if is_active is not None:
        review_stmt = review_stmt.where(ReviewModel.is_active == True)

    reviews = (await db_session.scalars(review_stmt)).all()

    return reviews