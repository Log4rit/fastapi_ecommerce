from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.users import User as UserModel


async def get_user_by_email(db_session: AsyncSession, email: str, is_active: bool = None) -> UserModel:
    user_stmt = select(UserModel).where(UserModel.email == email)

    if is_active is not None:
        user_stmt = user_stmt.where(UserModel.is_active == is_active)

    user = (await db_session.scalars(user_stmt)).first()

    return user