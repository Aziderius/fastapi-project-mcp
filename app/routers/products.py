# Rutas relacionadas con los productos: listar, consultar uno, crear y modificar.
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.database.dependencies import get_db
from app.models.models import Category, Product
from app.schemas.product import (
    MAX_INTEGER,
    MIN_INTEGER,
    ProductCreate,
    ProductRead,
    ProductUpdate,
    product_name_key,
)

router = APIRouter(prefix="/products", tags=["products"])

# Código de error de PostgreSQL para una clave foránea que no existe
FOREIGN_KEY_VIOLATION = "23503"


def fits_in_integer(value: int) -> bool:
    """Indica si un id cabe en una columna INTEGER de PostgreSQL.

    Un id fuera de ese rango no puede existir en la tabla. Además, asyncpg no
    acepta ese número como parámetro y la consulta acabaría en un error 500,
    así que hay que comprobarlo antes de consultar.
    """
    return MIN_INTEGER <= value <= MAX_INTEGER


def product_not_found(product_id: int) -> HTTPException:
    """Error 404 para un producto de la ruta que no existe."""
    return HTTPException(
        status_code=404,
        detail=f"No existe ningún producto con el id {product_id}",
    )


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
    # Un id que no cabe en INTEGER no existe: 404 sin consultar
    if not fits_in_integer(product_id):
        raise product_not_found(product_id)

    product = await db.get(Product, product_id, options=[joinedload(Product.category)])
    if product is None:
        raise product_not_found(product_id)
    return product


@router.post("", response_model=ProductRead, status_code=201)
async def create_product(product_in: ProductCreate, db: AsyncSession = Depends(get_db)):
    """Crea un producto en una categoría existente y lo devuelve con su categoría."""
    # Una categoría con un id que no cabe en INTEGER no existe: 422 sin consultar
    if not fits_in_integer(product_in.category_id):
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


@router.put("/{product_id}", response_model=ProductRead)
async def update_product(
    product_id: int, product_in: ProductUpdate, db: AsyncSession = Depends(get_db)
):
    """Modifica un producto sustituyendo todos sus datos editables.

    Los errores se comprueban en este orden: producto (404), categoría (422)
    y nombre repetido (409). Ninguno modifica nada: todos saltan antes del commit.
    """
    # Un id que no cabe en INTEGER no existe: 404 sin consultar
    if not fits_in_integer(product_id):
        raise product_not_found(product_id)

    # Se lee el producto bloqueando su fila (SELECT ... FOR UPDATE) hasta el
    # commit: si llegan dos modificaciones a la vez, la segunda espera a que
    # termine la primera y nunca queda una mezcla de las dos.
    # Sin joinedload a propósito: PostgreSQL no admite FOR UPDATE sobre el lado
    # opcional de un LEFT OUTER JOIN. La categoría se carga en la consulta final.
    product = await db.get(Product, product_id, with_for_update=True)
    if product is None:
        raise product_not_found(product_id)

    # La categoría debe existir (422: es un dato del cuerpo, no de la ruta)
    if not fits_in_integer(product_in.category_id):
        raise category_not_found(product_in.category_id)

    category = await db.get(Category, product_in.category_id)
    if category is None:
        raise category_not_found(product_in.category_id)

    # Nombre repetido (409). Solo se comprueba si el nombre cambia: cambiar
    # únicamente mayúsculas o tildes del propio nombre no cuenta como cambio.
    # product_name_key decide cuándo dos nombres son equivalentes.
    new_name_key = product_name_key(product_in.name)
    if new_name_key != product_name_key(product.name):
        # Se leen solo los nombres de los demás productos y se comparan en Python
        query = select(Product.name).where(Product.id != product_id)
        other_names = await db.scalars(query)
        for other_name in other_names.all():
            if product_name_key(other_name) == new_name_key:
                raise HTTPException(
                    status_code=409,
                    detail=f"Ya existe otro producto con el nombre {product_in.name}",
                )

    # Sustitución completa: se asignan los cinco datos editables.
    # Si no se envió descripción, el schema la deja en None y se borra.
    # El id y created_at no se tocan nunca.
    product.name = product_in.name
    product.description = product_in.description
    product.price = product_in.price
    product.stock = product_in.stock
    product.category_id = product_in.category_id

    try:
        await db.commit()
    except IntegrityError as error:
        await db.rollback()
        # La categoría existía al comprobarla, pero alguien la borró antes del commit
        if getattr(error.orig, "sqlstate", None) == FOREIGN_KEY_VIOLATION:
            raise category_not_found(product_in.category_id)
        # Cualquier otro error de integridad es inesperado: que acabe en un 500
        raise

    # Se vuelve a consultar para devolverlo con su categoría (la nueva, si ha
    # cambiado) y con el precio tal como lo guarda PostgreSQL. populate_existing=True
    # obliga a releerlo: sin él, db.get devolvería el objeto que ya está en la
    # sesión sin cargar la categoría.
    product = await db.get(
        Product,
        product_id,
        options=[joinedload(Product.category)],
        populate_existing=True,
    )
    return product
