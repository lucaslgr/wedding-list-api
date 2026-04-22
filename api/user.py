from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from domain.models import Item
from domain.schemas import ItemResponse, Link
from infra.database import get_db

router = APIRouter(tags=["items"])


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