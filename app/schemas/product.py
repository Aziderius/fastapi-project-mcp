# Esquemas de Pydantic para los productos.
# Validan los datos que entran (ProductCreate al crear, ProductUpdate al
# modificar) y salen (ProductRead) de la API. También definen cómo se comparan
# los nombres de producto (product_name_key).
import unicodedata
from datetime import datetime
from decimal import Decimal
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StrictInt, StringConstraints, field_validator

from app.schemas.category import CategorySummary

# Valor máximo de una columna INTEGER de PostgreSQL. Lo usan el stock y la
# comprobación de que la categoría existe (un id mayor no puede existir).
MAX_INTEGER = 2_147_483_647

# Valor mínimo de una columna INTEGER de PostgreSQL. Junto con MAX_INTEGER
# sirve para saber si un id cabe en la columna antes de consultar (un id
# fuera de ese rango no puede existir).
MIN_INTEGER = -2_147_483_648

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


class ProductUpdate(ProductCreate):
    """Datos necesarios para modificar un producto (sustitución completa).

    No añade campos ni validadores: hereda todos los de ProductCreate, así que
    la modificación valida exactamente igual que la creación, con los mismos
    mensajes. Existe como clase propia para que /docs muestre "ProductUpdate"
    como cuerpo del PUT.
    """


# Tabla de equivalencias del alfabeto español para comparar nombres de producto.
# Cada carácter de la primera cadena se sustituye por el que ocupa la misma
# posición en la segunda (por eso las dos tienen la misma longitud):
#   - Las mayúsculas A-Z pasan a minúscula.
#   - Las vocales con tilde o diéresis (Á É Í Ó Ú Ü y á é í ó ú ü) pasan a la
#     vocal sin marca y en minúscula.
#   - La Ñ pasa a ñ (pero la ñ NO se iguala a la n: "Año" y "Ano" son distintos).
# Lo que NO se iguala, a propósito, y se compara tal cual:
#   - La ß (no equivale a "ss"): "Straße" y "STRASSE" son distintos.
#   - Otras letras con marca (à, è, ç, ö...) ni se igualan a la letra sin marca
#     ni entre mayúscula y minúscula: "À" y "à" son distintos.
#   - Letras de ancho completo (Ｔ) o de otros alfabetos.
# No se usa lower() ni casefold() porque igualarían también esos casos.
SPANISH_NAME_TABLE = str.maketrans(
    "ABCDEFGHIJKLMNOPQRSTUVWXYZ" + "ÁÉÍÓÚÜ" + "áéíóúü" + "Ñ",
    "abcdefghijklmnopqrstuvwxyz" + "aeiouu" + "aeiouu" + "ñ",
)


def product_name_key(name: str) -> str:
    """Devuelve la clave con la que se comparan dos nombres de producto.

    Dos nombres son equivalentes si tienen la misma clave. Pasos:
    1. strip(): quita los espacios en blanco de los extremos (los de dentro
       cuentan: "Teclado  mecánico" no es "Teclado mecánico").
    2. Normalización NFC: une las dos formas internas de una misma letra
       ("o" + tilde suelta se convierte en "ó"). También convierte el signo
       kelvin en la letra K, el signo de ohmio en Ω y el de ångström en Å.
    3. translate() con SPANISH_NAME_TABLE: quita mayúsculas, tildes y diéresis
       del alfabeto español.

    Ejemplos:
        product_name_key("  Camión ")  -> "camion"   (igual que "CAMION")
        product_name_key("ÑANDÚ")      -> "ñandu"    (igual que "ñandú")
        product_name_key("Kelvin") -> "kelvin"  (signo kelvin, igual que "Kelvin")
        product_name_key("Año")        -> "año"      (distinto de "Ano")
    """
    stripped = name.strip()
    normalized = unicodedata.normalize("NFC", stripped)
    return normalized.translate(SPANISH_NAME_TABLE)


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
