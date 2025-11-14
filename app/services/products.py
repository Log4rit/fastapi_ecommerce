from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import func

from app.models import Review as ReviewModel, Product as ProductModel

async def update_product_rating(db_session: AsyncSession, product_id: int) -> None:
    result = await db_session.execute(
        select(func.avg(ReviewModel.grade)).where(
            ReviewModel.product_id == product_id,
            ReviewModel.is_active == True
        )
    )
    avg_rating = result.scalar() or 0.0
    product = await db_session.get(ProductModel, product_id)
    product.rating = avg_rating

    await db_session.commit()