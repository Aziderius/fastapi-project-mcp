# Rutas relacionadas con los productos: listar y consultar uno.
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.database.dependencies import get_db
from app.models.models import Product
from app.schemas.product import ProductRead

router = APIRouter(prefix="/products", tags=["products"])


@router.get("", response_model=list[ProductRead])
async def list_products(db: AsyncSession = Depends(get_db)):
    """Devuelve todos los productos ordenados por id, con su categoría."""
    # joinedload trae la categoría en la misma consulta (un solo JOIN)
    query = select(Product).options(joinedload(Product.category)).order_by(Product.id)
    result = await db.scalars(query)
    return result.all()


@router.get("/{product_id}", response_model=ProductRead)
async def get_product(product_id: int, db: AsyncSession = Depends(get_db)):
    """Devuelve un producto buscándolo por su id, con su categoría."""
    product = await db.get(Product, product_id, options=[joinedload(Product.category)])
    if product is None:
        raise HTTPException(
            status_code=404,
            detail=f"No existe ningún producto con el id {product_id}",
        )
    return product
