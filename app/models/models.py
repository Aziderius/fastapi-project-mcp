# Modelos de la base de datos (tablas).
# IMPORTANTE: las tablas se crearon a mano con SQL. Estos modelos solo describen
# el esquema que ya existe; la app nunca crea ni modifica tablas
# (no se usa Base.metadata.create_all en ningún sitio).
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Category(Base):
    """Tabla "categories"."""

    __tablename__ = "categories"

    # SERIAL PRIMARY KEY: el id lo genera PostgreSQL
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    # VARCHAR(50) NOT NULL UNIQUE
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    # VARCHAR(255), opcional
    description: Mapped[str | None] = mapped_column(String(255))
    # TIMESTAMP DEFAULT CURRENT_TIMESTAMP: la fecha la pone PostgreSQL (puede ser nula)
    created_at: Mapped[datetime | None] = mapped_column(
        DateTime, server_default=func.current_timestamp()
    )


class Product(Base):
    """Tabla "products"."""

    __tablename__ = "products"

    # SERIAL PRIMARY KEY: el id lo genera PostgreSQL
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    # VARCHAR(150) NOT NULL
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    # VARCHAR(255), opcional
    description: Mapped[str | None] = mapped_column(String(255))
    # NUMERIC(10, 2) NOT NULL: se lee como Decimal para no perder precisión
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    # INTEGER NOT NULL
    stock: Mapped[int] = mapped_column(Integer, nullable=False)
    # INTEGER NOT NULL, clave foránea a categories.id
    category_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("categories.id"), nullable=False
    )
    # TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP: la fecha la pone PostgreSQL
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.current_timestamp(), nullable=False
    )

    # Categoría del producto (relación de un solo sentido, no cambia la tabla).
    # lazy="raise": la categoría nunca se carga "a escondidas". Cada consulta debe
    # pedirla con joinedload(Product.category); si no, SQLAlchemy lanza un error.
    # Así se evita el problema de N+1 consultas al listar productos.
    category: Mapped[Category] = relationship(lazy="raise")
