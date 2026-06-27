import os

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from domain.models import Item
from domain.schemas import ItemResponse, Link, UserItemBuyUpdate
from infra.database import get_db

router = APIRouter(tags=["items"])


def _load_user_buy_pass_code() -> str:
    pass_code = os.getenv("USER_BUY_PASS_CODE")
    if not pass_code:
        raise RuntimeError("USER_BUY_PASS_CODE must be set")
    return pass_code


USER_BUY_PASS_CODE = _load_user_buy_pass_code()


def item_to_response(item: Item) -> ItemResponse:
    links = [Link(label=item.link1_label, url=item.link1_url)]
    if item.link2_label and item.link2_url:
        links.append(Link(label=item.link2_label, url=item.link2_url))
    if item.link3_label and item.link3_url:
        links.append(Link(label=item.link3_label, url=item.link3_url))

    return ItemResponse(
        id=item.id,
        name=item.name,
        description=item.description,
        category=item.category,
        links=links,
        is_bought=item.is_bought,
        created_at=item.created_at,
    )


@router.get("/items", response_model=list[ItemResponse])
def get_all(db: Session = Depends(get_db)) -> list[ItemResponse]:
    items = db.query(Item).order_by(Item.created_at.desc()).all()
    return [item_to_response(item) for item in items]


@router.patch("/items/{item_id}/buy/user", response_model=ItemResponse)
def bought(item_id: int, body: UserItemBuyUpdate, db: Session = Depends(get_db)) -> ItemResponse:
    item = db.get(Item, item_id)
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")

    if body.pass_code != USER_BUY_PASS_CODE:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    item.is_bought = body.is_bought
    db.commit()
    db.refresh(item)
    return item_to_response(item)