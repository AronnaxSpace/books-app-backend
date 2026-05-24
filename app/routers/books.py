import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.auth.dependencies import get_current_user
from app.database import get_db
from app.models import Book
from app.schemas import BookCreate, BookResponse, BookUpdate

router = APIRouter(
    prefix="/books",
    tags=["books"],
    dependencies=[Depends(get_current_user)],
)


@router.get("/", response_model=list[BookResponse])
async def list_books(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Book).options(selectinload(Book.author)).order_by(Book.created_at.desc())
    )
    return result.scalars().all()


@router.get("/{book_id}", response_model=BookResponse)
async def get_book(book_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Book).options(selectinload(Book.author)).where(Book.id == book_id)
    )
    book = result.scalar_one_or_none()
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    return book


@router.post("/", response_model=BookResponse, status_code=201)
async def create_book(data: BookCreate, db: AsyncSession = Depends(get_db)):
    book = Book(**data.model_dump())
    db.add(book)
    await db.commit()
    result = await db.execute(
        select(Book).options(selectinload(Book.author)).where(Book.id == book.id)
    )
    return result.scalar_one()


@router.patch("/{book_id}", response_model=BookResponse)
async def update_book(
    book_id: uuid.UUID, data: BookUpdate, db: AsyncSession = Depends(get_db)
):
    book = await db.get(Book, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(book, key, value)
    await db.commit()
    result = await db.execute(
        select(Book).options(selectinload(Book.author)).where(Book.id == book.id)
    )
    return result.scalar_one()


@router.delete("/{book_id}", status_code=204)
async def delete_book(book_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    book = await db.get(Book, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    await db.delete(book)
    await db.commit()
