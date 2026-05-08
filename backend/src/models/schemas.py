"""
Schemas Pydantic para Usuario.
"""
from datetime import datetime
from pydantic import BaseModel, Field, field_validator
import re


class UsuarioBase(BaseModel):
    """Schema base para Usuario."""

    email: str = Field(..., min_length=5, max_length=255, description="Email del usuario")
    nombre: str = Field(..., min_length=3, max_length=255)
    rol: str = Field(default="reclutador", pattern="^(reclutador|admin)$")

    @field_validator("email")
    @classmethod
    def validar_email(cls, v: str) -> str:
        """Valida y normaliza el email."""
        v = v.strip().lower()
        if not re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", v):
            raise ValueError("El email no es válido")
        return v


class UsuarioCreate(UsuarioBase):
    """Schema para crear un nuevo usuario."""
    
    password: str = Field(..., min_length=8, description="Contraseña del usuario")
    
    @field_validator("password")
    @classmethod
    def validar_password_fortaleza(cls, v: str) -> str:
        """Valida que la contraseña tenga mayúsculas, minúsculas y números."""
        if not re.search(r"[A-Z]", v):
            raise ValueError("La contraseña debe contener al menos una mayúscula")
        if not re.search(r"[a-z]", v):
            raise ValueError("La contraseña debe contener al menos una minúscula")
        if not re.search(r"\d", v):
            raise ValueError("La contraseña debe contener al menos un número")
        return v


class UsuarioUpdate(BaseModel):
    """Schema para actualizar usuario."""

    email: str | None = Field(None, min_length=5, max_length=255)
    nombre: str | None = Field(None, min_length=3, max_length=255)
    rol: str | None = Field(None, pattern="^(reclutador|admin)$")
    last_login: datetime | None = None

    @field_validator("email")
    @classmethod
    def validar_email_optional(cls, v: str | None) -> str | None:
        """Valida y normaliza el email si está presente."""
        if v is None:
            return None
        v = v.strip().lower()
        if not re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", v):
            raise ValueError("El email no es válido")
        return v


class UsuarioResponse(UsuarioBase):
    """Schema para respuesta de usuario."""
    
    id: int
    created_at: datetime
    last_login: datetime | None
    
    class Config:
        from_attributes = True


class LoginRequest(BaseModel):
    """Schema para petición de login."""
    
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    """Schema para respuesta de login."""
    
    success: bool
    user: UsuarioResponse | None = None
    redirect: str | None = None
    error: str | None = None


class PasswordRecoverRequest(BaseModel):
    """Schema para recuperación de contraseña."""
    
    email: EmailStr


class PasswordResetRequest(BaseModel):
    """Schema para reseteo de contraseña."""
    
    token: str
    new_password: str
