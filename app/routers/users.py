from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.security import OAuth2PasswordRequestForm

from app.models.users import User as UserModel
from app.schemas import UserCreate, User as UserSchema
from app.database.session import get_async_db
from app.auth import hash_password, verify_password, create_access_token, create_refresh_token
from app.auth import get_current_user
from app.config import JWT_SECRET_KEY, JWT_ALGORITHM
from app.crud import get_user_by_email

import jwt


router = APIRouter(prefix="/users", tags=["users"])


@router.post("/", response_model=UserSchema, status_code=status.HTTP_201_CREATED)
async def create_user(user: UserCreate, db: AsyncSession = Depends(get_async_db)):
    """
    Регистрирует нового пользователя с ролью 'buyer' или 'seller'.
    """

    db_user = await get_user_by_email(db_session=db, email=user.email)
    if db_user:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail="Email already registered")

    # Создание объекта пользователя с хешированным паролем
    db_new_user = UserModel(
        email=user.email,
        hashed_password=hash_password(user.password),
        role=user.role
    )

    # Добавление в сессию и сохранение в базе
    db.add(db_new_user)
    await db.commit()

    return db_new_user


@router.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends(),
                db: AsyncSession = Depends(get_async_db)):
    """
    Аутентифицирует пользователя и возвращает JWT с email, role и id.
    """
    db_user = await get_user_by_email(db_session=db, email=form_data.username, is_active=True)
    if not db_user or not verify_password(form_data.password, db_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": db_user.email, "role": db_user.role, "id": db_user.id})
    refresh_token = create_refresh_token(data={"sub": db_user.email, "role": db_user.role, "id": db_user.id})

    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}


@router.get("/me", response_model=UserSchema)
async def get_me(current_user: UserModel = Depends(get_current_user)):
    return current_user


@router.post("/refresh-token")
async def refresh_token(refresh_token: str, db: AsyncSession = Depends(get_async_db)): # refresh_token: str = Depends(oauth2_scheme)
    """
    Обновляет access_token с помощью refresh_token.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate refresh token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(refresh_token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        email: str = payload.get("sub")
        token_type = payload.get("type")
        if not email or token_type != "refresh":
            raise credentials_exception
    except jwt.PyJWTError:
        raise credentials_exception

    db_user = await get_user_by_email(db_session=db, email=email, is_active=True)
    if db_user is None:
        raise credentials_exception
    access_token = create_access_token(data={"sub": db_user.email, "role": db_user.role, "id": db_user.id})

    return {"access_token": access_token, "token_type": "bearer"}