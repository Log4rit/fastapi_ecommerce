from datetime import datetime

from pydantic import BaseModel, Field, ConfigDict

class ReviewCreate(BaseModel):
    """
    Модель для создания и обновления отзыва.
    Используется в POST и PUT запросах.
    """
    product_id: int = Field(description="ID продукта к которому относится отзыв")
    comment: str | None = Field(None, description="Текст отзыва")
    grade: int = Field(ge=1, le=5, description="Оценка для товара, от 1 до 5")


class Review(BaseModel):
    """
    Модель для ответа с данными отзыва.
    Используется в GET-запросах.
    """
    id: int = Field(description="Идентификатор отзыва")
    user_id: int = Field(description="ID пользователя")
    product_id: int = Field(description="ID продукта")
    comment: str | None = Field(None, description="Комментарий к отзыву")
    comment_date: datetime = Field(description="Время публикации")
    grade: float = Field(description="Оценка товара")
    is_active: bool = Field(description="Активность отзыва")

    model_config = ConfigDict(from_attributes=True)