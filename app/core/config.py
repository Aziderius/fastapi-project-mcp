# Configuración de la aplicación.
# Lee las variables de entorno (o del archivo .env) usando pydantic-settings.
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import URL


class Settings(BaseSettings):
    # Datos de conexión a PostgreSQL (obligatorios, se definen en .env)
    db_user: str
    db_password: str
    db_host: str
    db_port: int
    db_name: str

    # Indica a pydantic-settings que lea las variables desde el archivo .env
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    @property
    def database_url(self) -> URL:
        """Construye la URL de conexión a partir de las variables por separado."""
        # URL.create se encarga de los caracteres especiales de la contraseña
        return URL.create(
            # asyncpg: driver async de PostgreSQL
            drivername="postgresql+asyncpg",
            username=self.db_user,
            password=self.db_password,
            host=self.db_host,
            port=self.db_port,
            database=self.db_name,
        )


# Instancia única de la configuración que usará el resto de la app
settings = Settings()
