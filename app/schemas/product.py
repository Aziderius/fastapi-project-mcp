# Esquemas de Pydantic para los productos.
# Validan los datos que salen de la API (ProductRead).
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict

from app.schemas.category import CategorySummary


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
