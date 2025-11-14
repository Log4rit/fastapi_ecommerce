from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Sequence

from app.models.categories import Category as CategoryModel


async def get_category_by_id(db_session: AsyncSession, category_id: int) -> CategoryModel:
    category_stmt = select(CategoryModel).where(CategoryModel.id == category_id,
                                       CategoryModel.is_active == True)
    category = (await db_session.scalars(category_stmt)).first()

    return category

async def get_categories(db_session: AsyncSession) -> Sequence[CategoryModel]:
    categories_stmt = select(CategoryModel).where(CategoryModel.is_active == True)
    categories = (await db_session.scalars(categories_stmt)).all()

    return categories