from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.categories import Category as CategoryModel
from app.schemas import Category as CategorySchema, CategoryCreate
from app.database.session import get_async_db

from app.crud import get_category_by_id, get_categories

router = APIRouter(
    prefix="/categories",
    tags=["categories"],
)


@router.get("/", response_model=list[CategorySchema])
async def get_all_categories(db: AsyncSession = Depends(get_async_db)):
    """
    Возвращает список всех категорий товаров.
    """
    db_categories = await get_categories(db_session=db)

    return db_categories


@router.post("/", response_model=CategorySchema, status_code=status.HTTP_201_CREATED)
async def create_category(category: CategoryCreate, db: AsyncSession = Depends(get_async_db)):
    """
    Создаёт новую категорию.
    """
    if category.parent_id is not None:
        db_parent_category = await get_category_by_id(db_session=db, category_id=category.parent_id)
        if db_parent_category is None:
            raise HTTPException(status_code=400, detail="Parent category not found")

    db_category = CategoryModel(**category.model_dump())
    db.add(db_category)
    await db.commit()
    await db.refresh(db_category)

    return db_category


@router.put("/{category_id}", response_model=CategorySchema)
async def update_category(category_id: int, category: CategoryCreate, db: AsyncSession = Depends(get_async_db)):
    """
    Обновляет категорию по её ID.
    """
    db_category = await get_category_by_id(db_session=db, category_id=category_id)
    if not db_category:
        raise HTTPException(status_code=404, detail="Category not found")

    if category.parent_id is not None:
        db_parent_category = await get_category_by_id(db_session=db, category_id=category.parent_id)
        if not db_parent_category:
            raise HTTPException(status_code=400, detail="Parent category not found")
        if db_parent_category.id == category_id:
            raise HTTPException(status_code=400, detail="Category can't be it's own parent")

    await db.execute(
        update(CategoryModel)
        .where(CategoryModel.id == category_id)
        .values(**category.model_dump(exclude_unset=True))
    )
    await db.commit()
    await db.refresh(db_category)

    return db_category


@router.delete("/{category_id}", status_code=status.HTTP_200_OK)
async def delete_category(category_id: int, db: AsyncSession = Depends(get_async_db)):
    """
    Удаляет категорию по её ID.
    """
    db_category = await get_category_by_id(db_session=db, category_id=category_id)
    if not db_category:
        raise HTTPException(status_code=404, detail="Category not found")

    db_category.is_active = False
    await db.commit()
    await db.refresh(db_category)

    return db_category
