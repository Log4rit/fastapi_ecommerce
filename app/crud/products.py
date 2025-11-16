from sqlalchemy import select, func, desc
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
        search: str | None = None,
        min_price: float | None = None,
        max_price: float | None = None,
        in_stock: bool | None = None,
        seller_id: int | None = None) -> dict:
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

    rank_col = None
    if search:
        search_value = search.strip()
        if search_value:
            ts_query = func.websearch_to_tsquery('english', search_value)
            filters.append(ProductModel.tsv.op('@@')(ts_query))
            rank_col = func.ts_rank_cd(ProductModel.tsv, ts_query).label("rank")
            total_products_stmt = select(func.count()).select_from(ProductModel).where(*filters)

    total_products = await db_session.scalar(total_products_stmt) or 0

    if rank_col is not None:
        products_stmt = (
            select(ProductModel, rank_col)
            .where(*filters)
            .order_by(desc(rank_col), ProductModel.id)
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        rows = (await db_session.execute(products_stmt)).all()
        products = [row[0] for row in rows]
    else:
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
