from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from api.user import item_to_response
from domain.auth import authenticate_admin, create_access_token, require_admin
from domain.models import Item
from domain.schemas import AdminLoginRequest, ItemBuyUpdate, ItemCreate, ItemResponse, ItemUpdate, TokenResponse
from infra.database import get_db

router = APIRouter(tags=["admin"])


@router.post("/admin/login", response_model=TokenResponse)
def login(credentials: AdminLoginRequest) -> TokenResponse:
    if not authenticate_admin(credentials):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    token = create_access_token(credentials.username)
    return TokenResponse(access_token=token)


@router.post("/items", response_model=ItemResponse, dependencies=[Depends(require_admin)])
def add(item: ItemCreate, db: Session = Depends(get_db)) -> ItemResponse:
    payload = _to_columns(item)
    db_item = Item(**payload)
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return item_to_response(db_item)


@router.patch("/items/{item_id}/buy", response_model=ItemResponse, dependencies=[Depends(require_admin)])
def bought(item_id: int, body: ItemBuyUpdate, db: Session = Depends(get_db)) -> ItemResponse:
    item = db.get(Item, item_id)
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")

    item.is_bought = body.is_bought
    db.commit()
    db.refresh(item)
    return item_to_response(item)


@router.put("/items/{item_id}", response_model=ItemResponse, dependencies=[Depends(require_admin)])
def update(item_id: int, body: ItemUpdate, db: Session = Depends(get_db)) -> ItemResponse:
    item = db.get(Item, item_id)
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")

    payload = _to_columns(body)
    for field, value in payload.items():
        setattr(item, field, value)
    db.commit()
    db.refresh(item)
    return item_to_response(item)


@router.delete("/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_admin)])
def remove(item_id: int, db: Session = Depends(get_db)) -> None:
    item = db.get(Item, item_id)
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")

    db.delete(item)
    db.commit()


def _to_columns(item: ItemCreate | ItemUpdate) -> dict:
    links = item.links
    link2_url = links[1].url if len(links) >= 2 else None
    link2_label = links[1].label if len(links) >= 2 else None
    link3_url = links[2].url if len(links) >= 3 else None
    link3_label = links[2].label if len(links) >= 3 else None

    return {
        "name": item.name,
        "description": item.description,
        "category": item.category,
        "link1_url": str(links[0].url),
        "link1_label": links[0].label,
        "link2_url": str(link2_url) if link2_url else None,
        "link2_label": link2_label,
        "link3_url": str(link3_url) if link3_url else None,
        "link3_label": link3_label,
    }

