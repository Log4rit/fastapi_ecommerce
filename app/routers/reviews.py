from fastapi import APIRouter, Depends, HTTPException, status

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.session import get_async_db

from app.crud import get_reviews
from app.crud import get_product_by_id

from app.models.users import User as UserModel
from app.models import Review as ReviewModel

from app.schemas import ReviewCreate
from app.schemas import Review as ReviewSchema

from app.auth import get_current_buyer, get_current_admin
from app.services import update_product_rating

router = APIRouter(
    tags=["reviews"],
)


@router.get("/reviews", response_model=list[ReviewSchema])
async def get_all_reviews(db: AsyncSession = Depends(get_async_db)):
    """
    Возвращает список всех активных отзывов
    """
    reviews = await get_reviews(db_session=db)

    return reviews


@router.get("/products/{product_id}/reviews", response_model=list[ReviewSchema])
async def get_all_product_reviews(product_id: int, db: AsyncSession = Depends(get_async_db)):
    reviews = await get_reviews(db_session=db, product_id=product_id)

    return reviews


@router.post("/reviews", response_model=ReviewSchema, status_code=status.HTTP_201_CREATED)
async def create_review(
        new_review: ReviewCreate,
        db: AsyncSession = Depends(get_async_db),
        current_user: UserModel = Depends(get_current_buyer)):
    """
    Создаёт новый отзыв, привязанный к текущему пользователю (только для 'buyer').
    """
    db_product = await get_product_by_id(db_session=db, product_id=new_review.product_id)
    if not db_product:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Product not found or inactive")

    review_stmt = select(ReviewModel).where(ReviewModel.product_id == new_review.product_id,
                                            ReviewModel.user_id == current_user.id,
                                            ReviewModel.is_active == True)
    db_review = (await db.scalars(review_stmt)).first()
    if db_review:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="You already reviewed this product")

    db_new_review = ReviewModel(**new_review.model_dump(), user_id=current_user.id)
    db.add(db_new_review)
    await db.commit()
    await db.refresh(db_new_review)
    await update_product_rating(db_session=db, product_id=new_review.product_id)

    return db_new_review


@router.delete("/reviews/{review_id}", dependencies=[Depends(get_current_admin)])
async def deactivate_review(review_id: int, db: AsyncSession = Depends(get_async_db)):
    db_review = (await get_reviews(db_session=db, review_id=review_id, is_active=True))[0]
    if not db_review:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review not found or inactive")

    db_review.is_active = False
    await db.commit()
    await db.refresh(db_review)
    await update_product_rating(db_session=db, product_id=db_review.product_id)

    return {"message": "Review deleted"}