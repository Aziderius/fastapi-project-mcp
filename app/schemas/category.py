# Esquemas de Pydantic para las categorías.
# Validan los datos que entran (CategoryCreate) y salen (CategoryRead) de la API.
from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

# Nombre de categoría: se quitan los espacios de los extremos y se pasa a
# minúsculas, como los datos que ya hay en la base de datos.
CategoryName = Annotated[
    str,
    StringConstraints(strip_whitespace=True, to_lower=True, min_length=1, max_length=50),
]


class CategoryCreate(BaseModel):
    """Datos necesarios para crear una categoría."""

    name: CategoryName
    description: str | None = Field(default=None, max_length=255)


class CategoryRead(BaseModel):
    """Categoría tal como la devuelve la API."""

    # Permite crear el esquema directamente desde un objeto de SQLAlchemy
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str | None
    created_at: datetime | None


class CategorySummary(BaseModel):
    """Versión reducida de la categoría, para incluirla dentro de otros recursos."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
