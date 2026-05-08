"""
Utilidades de seguridad para autenticación y encriptación.
"""
import re

import bcrypt
from cryptography.fernet import Fernet

from core.config import settings


# Instancia Fernet para encriptación de credenciales
fernet = Fernet(settings.credential_encryption_key.encode())


def verificar_password_fortaleza(password: str) -> tuple[bool, str | None]:
    """
    Verifica que la contraseña cumpla con los requisitos de fortaleza.

    Args:
        password: Contraseña a verificar.

    Returns:
        tuple[bool, str | None]: (es_valida, mensaje_de_error)
    """
    if len(password) < 8:
        return False, "La contraseña debe tener al menos 8 caracteres"

    if not re.search(r"[A-Z]", password):
        return False, "La contraseña debe contener al menos una mayúscula"

    if not re.search(r"[a-z]", password):
        return False, "La contraseña debe contener al menos una minúscula"

    if not re.search(r"\d", password):
        return False, "La contraseña debe contener al menos un número"

    return True, None


def hash_password(password: str) -> str:
    """
    Hashea una contraseña usando bcrypt.

    Args:
        password: Contraseña en texto plano.

    Returns:
        str: Contraseña hasheada.
    """
    password_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode('utf-8')


def verificar_password(password: str, hashed_password: str) -> bool:
    """
    Verifica si una contraseña coincide con su hash.

    Args:
        password: Contraseña en texto plano.
        hashed_password: Contraseña hasheada.

    Returns:
        bool: True si coinciden, False si no.
    """
    password_bytes = password.encode('utf-8')
    hashed_bytes = hashed_password.encode('utf-8')
    try:
        return bcrypt.checkpw(password_bytes, hashed_bytes)
    except (ValueError, TypeError):
        return False


def encriptar_credencial(secret: str) -> str:
    """
    Encripta una credencial usando Fernet.
    
    Args:
        secret: Credencial en texto plano.
    
    Returns:
        str: Credencial encriptada.
    """
    return fernet.encrypt(secret.encode()).decode()


def desencriptar_credencial(encrypted_secret: str) -> str:
    """
    Desencripta una credencial usando Fernet.
    
    Args:
        encrypted_secret: Credencial encriptada.
    
    Returns:
        str: Credencial en texto plano.
    """
    return fernet.decrypt(encrypted_secret.encode()).decode()
