from sqlalchemy import select, func
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


async def get_products_pagination(
        db_session: AsyncSession,
        page: int,
        page_size: int,
        category_id: int | None = None,
        min_price: float | None = None,
        max_price: float | None = None,
        in_stock: bool | None = None,
        seller_id: int | None = None) -> Sequence[ProductModel]:
    filters = [ProductModel.is_active == True]

    if category_id is not None:
        filters.append(ProductModel.category_id == category_id)
    if min_price is not None:
        filters.append(ProductModel.price >= min_price)
    if max_price is not None:
        filters.append(ProductModel.price <= max_price)
    if in_stock is not None:
        filters.append(ProductModel.stock > 0 if in_stock else ProductModel.stock == 0)
    if seller_id is not None:
        filters.append(ProductModel.seller_id == seller_id)

    total_products_stmt = (select(func.count())
                           .select_from(ProductModel)
                           .where(*filters))
    total_products = await db_session.scalar(total_products_stmt) or 0

    products_stmt = (
        select(ProductModel)
        .where(*filters)
        .order_by(ProductModel.id)
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    products = (await db_session.scalars(products_stmt)).all()

    return {
        "items": products,
        "total": total_products,
        "page": page,
        "page_size": page_size
    }
