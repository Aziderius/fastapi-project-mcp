# Rutas relacionadas con las categorías: crear, listar y consultar una.
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.dependencies import get_db
from app.models.models import Category
from app.schemas.category import CategoryCreate, CategoryRead

router = APIRouter(prefix="/categories", tags=["categories"])


@router.get("", response_model=list[CategoryRead])
async def list_categories(db: AsyncSession = Depends(get_db)):
    """Devuelve todas las categorías ordenadas por id."""
    result = await db.scalars(select(Category).order_by(Category.id))
    return result.all()


@router.get("/{category_id}", response_model=CategoryRead)
async def get_category(category_id: int, db: AsyncSession = Depends(get_db)):
    """Devuelve una categoría buscándola por su id."""
    category = await db.get(Category, category_id)
    if category is None:
        raise HTTPException(
            status_code=404,
            detail=f"No existe ninguna categoría con el id {category_id}",
        )
    return category


@router.post("", response_model=CategoryRead, status_code=201)
async def create_category(category_in: CategoryCreate, db: AsyncSession = Depends(get_db)):
    """Crea una categoría nueva. El nombre llega ya en minúsculas y sin espacios."""
    category = Category(name=category_in.name, description=category_in.description)
    # add no lleva await: solo prepara el objeto en memoria, no habla con la base de datos
    db.add(category)
    try:
        await db.commit()
    except IntegrityError:
        # La columna name es UNIQUE: el nombre ya existe
        await db.rollback()
        raise HTTPException(
            status_code=409,
            detail=f"Ya existe una categoría con el nombre '{category_in.name}'",
        )
    # Recarga la fila para leer el id y el created_at que ha puesto PostgreSQL
    await db.refresh(category)
    return category
