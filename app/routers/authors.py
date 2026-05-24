import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.database import get_db
from app.models import Author
from app.schemas import AuthorCreate, AuthorResponse, AuthorUpdate

router = APIRouter(
    prefix="/authors",
    tags=["authors"],
    dependencies=[Depends(get_current_user)],
)


@router.get("/", response_model=list[AuthorResponse])
async def list_authors(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Author).order_by(Author.name))
    return result.scalars().all()


@router.get("/{author_id}", response_model=AuthorResponse)
async def get_author(author_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    author = await db.get(Author, author_id)
    if not author:
        raise HTTPException(status_code=404, detail="Author not found")
    return author


@router.post("/", response_model=AuthorResponse, status_code=201)
async def create_author(data: AuthorCreate, db: AsyncSession = Depends(get_db)):
    author = Author(**data.model_dump())
    db.add(author)
    await db.commit()
    await db.refresh(author)
    return author


@router.patch("/{author_id}", response_model=AuthorResponse)
async def update_author(
    author_id: uuid.UUID, data: AuthorUpdate, db: AsyncSession = Depends(get_db)
):
    author = await db.get(Author, author_id)
    if not author:
        raise HTTPException(status_code=404, detail="Author not found")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(author, key, value)
    await db.commit()
    await db.refresh(author)
    return author


@router.delete("/{author_id}", status_code=204)
async def delete_author(author_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    author = await db.get(Author, author_id)
    if not author:
        raise HTTPException(status_code=404, detail="Author not found")
    await db.delete(author)
    await db.commit()
