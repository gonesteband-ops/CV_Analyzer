"""
Servicio de gestión de usuarios.
"""
import logging
from datetime import datetime
from typing import List, Optional

from sqlalchemy.orm import Session

from models.usuario import Usuario

logger = logging.getLogger(__name__)


class UserService:
    """
    Servicio para operaciones CRUD de usuarios.
    """

    def __init__(self, db: Session):
        """
        Inicializa el servicio con la sesión de base de datos.
        
        Args:
            db: Sesión de base de datos
        """
        self.db = db

    def obtener_usuario_por_id(self, usuario_id: int) -> Optional[Usuario]:
        """
        Obtiene un usuario por su ID.
        
        Args:
            usuario_id: ID del usuario
            
        Returns:
            Usuario si existe, None en caso contrario
        """
        return self.db.query(Usuario).filter(Usuario.id == usuario_id).first()

    def obtener_usuario_por_email(self, email: str) -> Optional[Usuario]:
        """
        Obtiene un usuario por su email.
        
        Args:
            email: Email del usuario
            
        Returns:
            Usuario si existe, None en caso contrario
        """
        return self.db.query(Usuario).filter(Usuario.email == email).first()

    def listar_usuarios(
        self,
        activo: Optional[bool] = None,
        rol: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Usuario]:
        """
        Lista usuarios con filtros opcionales.

        Args:
            activo: Filtrar por estado activo (True/False)
            rol: Filtrar por rol
            skip: Cantidad de registros a saltar (paginación)
            limit: Cantidad máxima de registros a devolver

        Returns:
            Lista de usuarios que coinciden con los filtros
        """
        query = self.db.query(Usuario).filter(Usuario.email != "admin@test.com")

        if activo is not None:
            query = query.filter(Usuario.activo == activo)

        if rol:
            query = query.filter(Usuario.rol == rol)

        return query.offset(skip).limit(limit).all()

    def contar_usuarios(self, activo: Optional[bool] = None, rol: Optional[str] = None) -> int:
        """
        Cuenta usuarios con filtros opcionales.

        Args:
            activo: Filtrar por estado activo (True/False)
            rol: Filtrar por rol

        Returns:
            Cantidad de usuarios que coinciden con los filtros
        """
        query = self.db.query(Usuario).filter(Usuario.email != "admin@test.com")

        if activo is not None:
            query = query.filter(Usuario.activo == activo)

        if rol:
            query = query.filter(Usuario.rol == rol)

        return query.count()

    def crear_usuario(
        self,
        email: str,
        password_hash: str,
        nombre: str,
        rol: str = "reclutador"
    ) -> Usuario:
        """
        Crea un nuevo usuario.
        
        Args:
            email: Email del usuario (debe ser único)
            password_hash: Hash de la contraseña
            nombre: Nombre completo del usuario
            rol: Rol del usuario (admin o reclutador)
            
        Returns:
            Usuario creado
            
        Raises:
            ValueError: Si el email ya existe
        """
        # Verificar si el email ya existe
        existing = self.obtener_usuario_por_email(email)
        if existing:
            raise ValueError(f"El email '{email}' ya está registrado")
        
        usuario = Usuario(
            email=email,
            password_hash=password_hash,
            nombre=nombre,
            rol=rol,
            activo=True,
            created_at=datetime.utcnow()
        )
        
        self.db.add(usuario)
        self.db.commit()
        self.db.refresh(usuario)
        
        logger.info(f"Usuario creado exitosamente: {usuario.email}")
        return usuario

    def actualizar_usuario(
        self,
        usuario_id: int,
        nombre: Optional[str] = None,
        email: Optional[str] = None,
        rol: Optional[str] = None
    ) -> Optional[Usuario]:
        """
        Actualiza los datos de un usuario.
        
        Args:
            usuario_id: ID del usuario a actualizar
            nombre: Nuevo nombre (opcional)
            email: Nuevo email (opcional)
            rol: Nuevo rol (opcional)
            
        Returns:
            Usuario actualizado o None si no existe
            
        Raises:
            ValueError: Si el nuevo email ya existe en otro usuario
        """
        usuario = self.obtener_usuario_por_id(usuario_id)
        if not usuario:
            return None
        
        if nombre:
            usuario.nombre = nombre
        
        if email and email != usuario.email:
            # Verificar que el nuevo email no exista en otro usuario
            existing = self.obtener_usuario_por_email(email)
            if existing and existing.id != usuario_id:
                raise ValueError(f"El email '{email}' ya está registrado")
            usuario.email = email
        
        if rol:
            usuario.rol = rol
        
        self.db.commit()
        self.db.refresh(usuario)
        
        logger.info(f"Usuario actualizado exitosamente: {usuario.email}")
        return usuario

    def cambiar_rol(self, usuario_id: int, rol: str) -> Optional[Usuario]:
        """
        Cambia el rol de un usuario.
        
        Args:
            usuario_id: ID del usuario
            rol: Nuevo rol (admin o reclutador)
            
        Returns:
            Usuario actualizado o None si no existe
            
        Raises:
            ValueError: Si el rol no es válido
        """
        if rol not in ["admin", "reclutador"]:
            raise ValueError("El rol debe ser 'admin' o 'reclutador'")
        
        return self.actualizar_usuario(usuario_id, rol=rol)

    def desactivar_usuario(self, usuario_id: int) -> bool:
        """
        Desactiva un usuario (soft delete).
        
        Args:
            usuario_id: ID del usuario a desactivar
            
        Returns:
            True si se desactivó exitosamente, False si no existe
        """
        usuario = self.obtener_usuario_por_id(usuario_id)
        if not usuario:
            return False
        
        usuario.activo = False
        self.db.commit()
        
        logger.info(f"Usuario desactivado: {usuario.email}")
        return True

    def activar_usuario(self, usuario_id: int) -> bool:
        """
        Activa un usuario previamente desactivado.
        
        Args:
            usuario_id: ID del usuario a activar
            
        Returns:
            True si se activó exitosamente, False si no existe
        """
        usuario = self.obtener_usuario_por_id(usuario_id)
        if not usuario:
            return False
        
        usuario.activo = True
        self.db.commit()
        
        logger.info(f"Usuario activado: {usuario.email}")
        return True

    def eliminar_usuario(self, usuario_id: int) -> bool:
        """
        Elimina físicamente un usuario de la base de datos.
        
        Args:
            usuario_id: ID del usuario a eliminar
            
        Returns:
            True si se eliminó exitosamente, False si no existe
        """
        usuario = self.obtener_usuario_por_id(usuario_id)
        if not usuario:
            return False
        
        self.db.delete(usuario)
        self.db.commit()
        
        logger.info(f"Usuario eliminado: {usuario.email}")
        return True
