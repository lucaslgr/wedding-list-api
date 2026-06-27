from datetime import datetime

from pydantic import BaseModel, Field, HttpUrl, field_validator


class Link(BaseModel):
    label: str = Field(min_length=1)
    url: HttpUrl


class ItemBase(BaseModel):
    name: str = Field(min_length=1)
    description: str = Field(min_length=1)
    category: str = Field(min_length=1)
    links: list[Link]

    @field_validator("links")
    @classmethod
    def validate_links_count(cls, value: list[Link]) -> list[Link]:
        if not 1 <= len(value) <= 3:
            raise ValueError("links must contain between 1 and 3 items")
        return value


class ItemCreate(ItemBase):
    pass


class ItemUpdate(ItemBase):
    pass


class ItemBuyUpdate(BaseModel):
    is_bought: bool


class UserItemBuyUpdate(BaseModel):
    is_bought: bool
    pass_code: str


class ItemResponse(BaseModel):
    id: int
    name: str
    description: str
    category: str
    links: list[Link]
    is_bought: bool
    created_at: datetime


class AdminLoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
