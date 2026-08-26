from dataclasses import dataclass
from typing import Optional


@dataclass
class ChatSearch:
    chat_id: Optional[str] = None
    kws: Optional[str] = None
    cat_ids: Optional[str] = None
    min_price: Optional[str] = None
    max_price: Optional[str] = None
    dist: Optional[str] = "400"
    publish_date: Optional[int] = 24
    orde: Optional[str] = "newest"
    username: Optional[str] = None
    name: Optional[str] = None
    active: Optional[int] = 1


@dataclass
class Item:
    item_id: int
    chat_id: str
    title: str
    price: str
    url: str
    publish_date: Optional[int] = None
    observaciones: Optional[str] = None
    user: Optional[str] = None
