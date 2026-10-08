# Rutas relacionadas con los productos: listar, consultar uno y crear.
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.database.dependencies import get_db
from app.models.models import Category, Product
from app.schemas.product import MAX_INTEGER, ProductCreate, ProductRead

router = APIRouter(prefix="/products", tags=["products"])

# Código de error de PostgreSQL para una clave foránea que no existe
FOREIGN_KEY_VIOLATION = "23503"


def category_not_found(category_id: int) -> HTTPException:
    """Error 422 para una categoría del cuerpo de la petición que no existe."""
    # 422 y no 404: la ruta existe; lo que está mal es un dato del cuerpo
    return HTTPException(
        status_code=422,
        detail=f"No existe ninguna categoría con el id {category_id}",
    )


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


@router.post("", response_model=ProductRead, status_code=201)
async def create_product(product_in: ProductCreate, db: AsyncSession = Depends(get_db)):
    """Crea un producto en una categoría existente y lo devuelve con su categoría."""
    # Un id fuera del rango de INTEGER no puede existir. Además, asyncpg no
    # acepta ese número como parámetro y la consulta acabaría en un error 500.
    is_out_of_range = product_in.category_id > MAX_INTEGER or product_in.category_id < -MAX_INTEGER
    if is_out_of_range:
        raise category_not_found(product_in.category_id)

    category = await db.get(Category, product_in.category_id)
    if category is None:
        raise category_not_found(product_in.category_id)

    product = Product(
        name=product_in.name,
        description=product_in.description,
        price=product_in.price,
        stock=product_in.stock,
        category_id=product_in.category_id,
    )
    # add no lleva await: solo prepara el objeto en memoria, no habla con la base de datos
    db.add(product)
    try:
        await db.commit()
    except IntegrityError as error:
        await db.rollback()
        # La categoría existía al comprobarla, pero alguien la borró antes del commit
        if getattr(error.orig, "sqlstate", None) == FOREIGN_KEY_VIOLATION:
            raise category_not_found(product_in.category_id)
        # Cualquier otro error de integridad es inesperado: que acabe en un 500
        raise

    # Se vuelve a consultar para devolverlo con su categoría (refresh no carga
    # relaciones). populate_existing=True obliga a releerlo: sin él, db.get
    # devolvería el objeto que ya está en la sesión sin cargar la categoría.
    product = await db.get(
        Product,
        product.id,
        options=[joinedload(Product.category)],
        populate_existing=True,
    )
    return product
