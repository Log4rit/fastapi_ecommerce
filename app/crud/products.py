from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Sequence

from app.models.products import Product as ProductModel


async def get_product_by_id(db_session: AsyncSession, product_id: int) -> ProductModel:
    product_stmt = select(ProductModel).where(ProductModel.id == product_id,
                                              ProductModel.is_active == True)
    product = (await db_session.scalars(product_stmt)).first()
    return product


async def get_products(db_session: AsyncSession, category_id: int = None) -> Sequence[ProductModel]:
    product_stmt = select(ProductModel).where(ProductModel.is_active == True)

    if category_id:
        product_stmt = product_stmt.where(ProductModel.category_id == category_id)

    products = (await db_session.scalars(product_stmt)).all()

    return products
