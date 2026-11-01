"""
Configuración central de la aplicación.
"""
import os
from pathlib import Path
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    """Configuración de la aplicación obtenida de variables de entorno."""
    
    model_config = SettingsConfigDict(
        env_file=Path(__file__).parent.parent.parent.parent / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )
    
    # Aplicación
    app_name: str = Field(default="CV Analyzer", description="Nombre de la aplicación")
    version: str = Field(default="0.1.0", description="Versión de la aplicación")
    debug: bool = Field(default=False, description="Modo debug")
    secret_key: str = Field(..., description="Clave secreta para sesiones y tokens")
    timezone: str = Field(default="America/Santiago", description="Zona horaria")
    
    # Administrador inicial (opcional, solo se crea si ambos valores existen)
    admin_email: str = Field(default="", description="Email del administrador inicial")
    admin_password: str = Field(default="", description="Password del administrador inicial")
    admin_name: str = Field(default="Admin", description="Nombre del administrador inicial")
    
    # Base de datos
    database_url: str = Field(
        default="sqlite:///./dev.db",
        description="URL de conexión a la base de datos"
    )
    
    # Encriptación
    credential_encryption_key: str = Field(
        ...,
        description="Clave de encriptación Fernet para credenciales de portales"
    )
    
    # Sesiones
    session_cookie_name: str = Field(default="session_id", description="Nombre de la cookie de sesión")
    session_cookie_secure: bool = Field(default=False, description="Cookie segura (solo HTTPS)")
    session_cookie_httponly: bool = Field(default=True, description="Cookie HttpOnly")
    session_cookie_samesite: str = Field(default="lax", description="Política SameSite")
    
    # Rate limiting
    rate_limit_per_minute: int = Field(default=60, description="Peticiones por minuto")
    
    # Upload de archivos
    max_file_size_mb: int = Field(default=10, description="Tamaño máximo de archivo en MB")
    max_files_per_batch: int = Field(default=50, description="Máximo de archivos por lote")
    allowed_file_types: str = Field(default=".pdf,.docx,.txt", description="Tipos de archivo permitidos")
    
    # Logging
    log_level: str = Field(default="INFO", description="Nivel de logging")
    log_format: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        description="Formato de logging"
    )
    
    # IA Providers
    groq_api_key: str = Field(default="", description="API Key de GROQ para análisis con IA")
    
    @property
    def max_file_size_bytes(self) -> int:
        """Obtiene el tamaño máximo de archivo en bytes."""
        return self.max_file_size_mb * 1024 * 1024
    
    @property
    def allowed_extensions(self) -> list[str]:
        """Obtiene la lista de extensiones permitidas."""
        return [ext.strip() for ext in self.allowed_file_types.split(",")]


@lru_cache
def get_settings() -> Settings:
    """
    Obtiene la configuración de la aplicación (cached).
    
    Returns:
        Settings: Configuración cargada desde variables de entorno.
    """
    return Settings()


# Instancia global de configuración
settings = get_settings()
