from fastapi import APIRouter, Depends, HTTPException, status, Query

from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.session import get_async_db

from app.crud import get_product_by_id, get_category_by_id, get_products, get_products_pagination

from app.models.products import Product as ProductModel
from app.models.users import User as UserModel

from app.schemas import Product as ProductSchema, ProductCreate, ProductList
from app.auth import get_current_seller

router = APIRouter(
    prefix="/products",
    tags=["products"],
)


@router.get("/", response_model=ProductList)
async def get_all_products(
        page: int = Query(1, ge=1),
        page_size: int = Query(20, ge=1, le=100),
        category_id: int | None = Query(
            None, description="ID категории для фильтрации"),
        min_price: float | None = Query(
            None, ge=0, description="Минимальная цена товара"),
        max_price: float | None = Query(
            None, ge=0, description="Максимальная цена товара"),
        in_stock: bool | None = Query(
            None, description="true — только товары в наличии, false — только без остатка"),
        seller_id: int | None = Query(
            None, description="ID продавца для фильтрации"),
        db: AsyncSession = Depends(get_async_db),
):
    """
    Возвращает список всех активных товаров.
    """
    if min_price is not None and max_price is not None and min_price > max_price:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="min_price не может быть больше max_price",
        )

    db_products = await get_products_pagination(db_session=db,
                                                page=page,
                                                page_size=page_size,
                                                category_id=category_id,
                                                min_price=min_price,
                                                max_price=max_price,
                                                in_stock=in_stock,
                                                seller_id=seller_id)
    return db_products


@router.get("/{product_id}", response_model=ProductSchema)
async def get_product(product_id: int, db: AsyncSession = Depends(get_async_db)):
    """
    Возвращает детальную информацию о товаре по его ID.
    """
    db_product = await get_product_by_id(db_session=db, product_id=product_id)
    if db_product is None:
        raise HTTPException(status_code=404, detail="Product not found")

    db_category = await get_category_by_id(db_session=db, category_id=db_product.category_id)
    if db_category is None:
        raise HTTPException(status_code=400, detail="Category not found")

    return db_product


@router.get("/category/{category_id}", response_model=list[ProductSchema])
async def get_products_by_category(category_id: int, db: AsyncSession = Depends(get_async_db)):
    """
    Возвращает список товаров в указанной категории по её ID.
    """
    db_category = await get_category_by_id(db_session=db, category_id=category_id)
    if db_category is None:
        raise HTTPException(status_code=404, detail="Category not found")

    db_products = await get_products(db_session=db, category_id=category_id)
    return db_products


@router.post("/", response_model=ProductSchema, status_code=status.HTTP_201_CREATED)
async def create_product(
        product: ProductCreate,
        db: AsyncSession = Depends(get_async_db),
        current_user: UserModel = Depends(get_current_seller)
):
    """
    Создаёт новый товар, привязанный к текущему продавцу (только для 'seller').
    """
    db_category = await get_category_by_id(db_session=db, category_id=product.category_id)
    if not db_category:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Category not found or inactive")

    db_product = ProductModel(**product.model_dump(), seller_id=current_user.id)
    db.add(db_product)
    await db.commit()
    await db.refresh(db_product)

    return db_product


@router.put("/{product_id}", response_model=ProductSchema)
async def update_product(
        product_id: int,
        product: ProductCreate,
        db: AsyncSession = Depends(get_async_db),
        current_user: UserModel = Depends(get_current_seller)
):
    """
    Обновляет товар, если он принадлежит текущему продавцу (только для 'seller').
    """
    db_product = await get_product_by_id(db_session=db, product_id=product_id)
    if not db_product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    if db_product.seller_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You can only update your own products")

    db_category = await get_category_by_id(db_session=db, category_id=product.category_id)
    if not db_category:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Category not found or inactive")

    await db.execute(
        update(ProductModel)
        .where(ProductModel.id == product_id)
        .values(**product.model_dump())
    )
    await db.commit()
    await db.refresh(db_product)

    return db_product


@router.delete("/{product_id}", response_model=ProductSchema)
async def delete_product(
        product_id: int,
        db: AsyncSession = Depends(get_async_db),
        current_user: UserModel = Depends(get_current_seller)
):
    """
    Выполняет мягкое удаление товара, если он принадлежит текущему продавцу (только для 'seller').
    """
    db_product = await get_product_by_id(db_session=db, product_id=product_id)
    if not db_product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found or inactive")
    if db_product.seller_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You can only delete your own products")

    db_product.is_active = False
    await db.commit()
    await db.refresh(db_product)

    return db_product
