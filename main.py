from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.future import select
from models import Base, User, Product, CartItem
from pydantic import BaseModel
import asyncio

DATABASE_URL = "postgresql+asyncpg://user:password@localhost/shop_db"
engine = create_async_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

app = FastAPI()

class CartItemCreate(BaseModel):
    user_id: int
    product_id: int
    quantity: int

class CartItemUpdate(BaseModel):
    quantity: int

class CartItem(BaseModel):
    id: int
    user_id: int
    product_id: int
    quantity: int

async def startup_event(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def shutdown_event(app: FastAPI):
    SessionLocal.close_all()

async def get_db():
    async with SessionLocal() as session:
        yield session

@app.post("/cart/", response_model=CartItem)
async def add_to_cart(item: CartItemCreate, db: AsyncSession = Depends(get_db)):
    new_item = CartItem(**item.dict())
    db.add(new_item)
    await db.commit()
    await db.refresh(new_item)
    return new_item

@app.delete("/cart/{item_id}", response_model=CartItem)
async def remove_from_cart(item_id: int, db: AsyncSession = Depends(get_db)):
    item = await db.get(CartItem, item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    await db.delete(item)
    await db.commit()
    return item

@app.put("/cart/{item_id}", response_model=CartItem)
async def update_cart(item_id: int, item: CartItemUpdate, db: AsyncSession = Depends(get_db)):
    cart_item = await db.get(CartItem, item_id)
    if cart_item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    cart_item.quantity = item.quantity
    await db.commit()
    await db.refresh(cart_item)
    return cart_item

if __name__ == "main":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
