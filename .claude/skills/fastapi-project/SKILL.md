---
name: fastapi-project
description: Buenas prácticas para escribir o revisar endpoints, schemas y modelos de esta API FastAPI async con SQLAlchemy 2.0 (AsyncSession), asyncpg y PostgreSQL. Úsala al crear o modificar archivos en app/routers, app/schemas, app/models o app/database.
---

# FastAPI async en este proyecto

Adaptada de la skill `fastapi-python` de mindrally/skills. Las reglas del proyecto están en CLAUDE.md y siempre prevalecen; esta skill explica **cómo escribir el código** para cumplirlas.

## Principios

- Código claro antes que corto: quien mantiene el proyecto está aprendiendo. Nada de condicionales en una línea ni trucos ingeniosos.
- Nombres descriptivos en inglés. Para booleanos, usa verbos auxiliares: `is_active`, `has_stock`.
- Archivos en minúsculas con guion bajo y nombrados por recurso: `routers/categories.py`, no `routers/category_routes.py`.
- Usa clases donde el stack las pide (modelos de SQLAlchemy y schemas de Pydantic) y funciones simples para todo lo demás.
- Antes de repetir código en un segundo sitio, pregunta si conviene extraerlo a una función; no crees utilidades "por si acaso".

## Endpoints async

- Los endpoints que usan la base de datos son `async def` y reciben la sesión con `db: AsyncSession = Depends(get_db)`.
- **Cada operación de base de datos lleva `await`**: `db.get`, `db.scalars`, `db.execute`, `db.commit`, `db.rollback` y `db.refresh`. Si falta un `await`, no hay error inmediato: obtienes una corrutina en lugar del dato y el fallo aparece más adelante.
- `db.add(objeto)` **no** lleva `await`: solo marca el objeto en la sesión, sin hablar con la base de datos.
- **Nunca hagas operaciones bloqueantes dentro de un `async def`**: nada de `time.sleep`, `requests` ni drivers síncronos como psycopg2. Bloquean el servidor entero. Si alguna vez hace falta una librería síncrona, pregunta antes.
- Una sesión por petición. No uses la misma `AsyncSession` en tareas simultáneas (por ejemplo, con `asyncio.gather`): una sesión no admite consultas en paralelo.
- Pon type hints en todos los parámetros y declara siempre `response_model` con un schema de Pydantic. Nunca devuelvas diccionarios sueltos (salvo el contrato fijo de `/healthz`).
- Busca por clave primaria con `await db.get(Modelo, id)`.

## Relaciones y carga de datos

- Las relaciones son `lazy="raise"`. En async, además, la carga perezosa es imposible: acceder a una relación no cargada falla siempre.
- Carga las relaciones en la propia consulta: `joinedload` para relaciones de muchos a uno (como `Product.category`) y `selectinload` para colecciones.
- `db.refresh(objeto)` recarga las columnas, pero **no** las relaciones. Si después de crear un objeto la respuesta debe incluir una relación, vuelve a consultarlo con las opciones de carga adecuadas.
- La sesión usa `expire_on_commit=False`, así que los atributos siguen accesibles después de `commit()`. Aun así, haz `refresh` tras crear un objeto para obtener los valores que genera PostgreSQL (`id`, `created_at`).

## Manejo de errores

- Comprueba los casos de error al principio de la función y sal con `raise HTTPException(...)`. El camino feliz va al final.
- Evita `else` innecesarios después de un `raise` o un `return`.
- Usa los códigos de CLAUDE.md: 404 si no existe, 409 si hay un duplicado. El `detail` siempre en español y comprensible para el usuario.
- Si un `commit()` falla, haz `await db.rollback()` antes de lanzar la excepción.
- No configures logging nuevo sin preguntar, y nunca registres la contraseña ni la URL de conexión.

## Ejemplo de referencia

Ilustra el patrón; si el código existente en `app/routers/` difiere en detalles (rutas, nombres), sigue el código existente.

```python
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.database.dependencies import get_db
from app.models.models import Category, Product
from app.schemas.category import CategoryCreate, CategoryRead
from app.schemas.product import ProductRead


@router.get("/{category_id}", response_model=CategoryRead)
async def get_category(category_id: int, db: AsyncSession = Depends(get_db)):
    """Devuelve una categoría por su id."""
    category = await db.get(Category, category_id)
    if category is None:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")

    return category


@router.post("/", response_model=CategoryRead, status_code=status.HTTP_201_CREATED)
async def create_category(data: CategoryCreate, db: AsyncSession = Depends(get_db)):
    """Crea una categoría. El schema ya normaliza el nombre."""
    category = Category(**data.model_dump())
    db.add(category)  # Sin await: todavía no se habla con la base de datos.
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=409, detail="Ya existe una categoría con ese nombre")

    await db.refresh(category)  # Trae id y created_at generados por PostgreSQL.
    return category


@router.get("/", response_model=list[ProductRead])
async def list_products(db: AsyncSession = Depends(get_db)):
    """Lista los productos con su categoría cargada en la misma consulta."""
    query = select(Product).options(joinedload(Product.category)).order_by(Product.id)
    result = await db.scalars(query)
    return result.all()
```

## Schemas

- Pydantic v2: `model_config = ConfigDict(from_attributes=True)` en los schemas que se construyen desde modelos ORM.
- Separa entrada y salida: `XCreate` para lo que recibe la API y `XRead` para lo que devuelve.
- La normalización de datos (como pasar a minúsculas) va en el schema de entrada con un validador, no en el endpoint.
- Los schemas no cambian por ser async: la validación de Pydantic es la misma.

## Lo que esta skill no incluye a propósito

La skill original recomienda caché con Redis, middleware y gestores de `lifespan`. Este proyecto no usa nada de eso; no lo propongas salvo que el usuario lo pida.
