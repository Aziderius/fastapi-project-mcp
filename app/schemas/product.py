# Esquemas de Pydantic para los productos.
# Validan los datos que entran (ProductCreate) y salen (ProductRead) de la API.
from datetime import datetime
from decimal import Decimal
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StrictInt, StringConstraints, field_validator

from app.schemas.category import CategorySummary

# Valor máximo de una columna INTEGER de PostgreSQL. Lo usan el stock y la
# comprobación de que la categoría existe (un id mayor no puede existir).
MAX_INTEGER = 2_147_483_647

# Nombre del producto: se quitan los espacios en blanco de los extremos
# (también tabuladores y saltos de línea) y se respetan las mayúsculas.
ProductName = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=150),
]

# Descripción: se recorta igual que el nombre; la longitud se mide ya recortada.
ProductDescription = Annotated[
    str,
    StringConstraints(strip_whitespace=True, max_length=255),
]


class ProductCreate(BaseModel):
    """Datos necesarios para crear un producto."""

    name: ProductName
    description: ProductDescription | None = None
    # Mayor que 0, menor que 100 000 000 y con 2 decimales como máximo
    # (es lo que cabe en la columna NUMERIC(10, 2)). Nunca se redondea.
    price: Decimal = Field(gt=0, lt=100_000_000, decimal_places=2)
    # StrictInt: solo enteros de verdad. Rechaza "5" (texto), 5.0 y true.
    stock: StrictInt = Field(ge=0, le=MAX_INTEGER)
    # Aquí solo se comprueba que sea un entero; que la categoría exista
    # lo comprueba el endpoint consultando la base de datos.
    category_id: StrictInt

    @field_validator("price", mode="before")
    @classmethod
    def price_must_be_a_number(cls, price: object) -> object:
        """Rechaza el precio enviado como texto ("19.90") o como booleano (true)."""
        # bool va primero a propósito: en Python, True y False también son números
        if isinstance(price, bool) or isinstance(price, str):
            raise ValueError("El precio debe ser un número")
        return price

    @field_validator("description")
    @classmethod
    def empty_description_to_none(cls, description: str | None) -> str | None:
        """Una descripción vacía (o solo con espacios) se guarda como ausente."""
        if description == "":
            return None
        return description


class ProductRead(BaseModel):
    """Producto tal como lo devuelve la API."""

    # Permite crear el esquema directamente desde un objeto de SQLAlchemy
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str | None
    # Decimal se devuelve en el JSON como texto ("19.99") para no perder precisión
    price: Decimal
    stock: int
    category_id: int
    # Id y nombre de la categoría (necesita joinedload(Product.category) en la consulta)
    category: CategorySummary
    created_at: datetime
