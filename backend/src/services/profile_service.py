"""
Servicio para la gestión de perfiles de cargo (CRUD).
Implementa operaciones para crear, leer, actualizar y eliminar perfiles de cargo.
"""
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from models.perfil_cargo import PerfilCargo
from models.usuario import Usuario
from models.schemas_perfil_cargo import PerfilCargoCreate, PerfilCargoUpdate
import logging

logger = logging.getLogger(__name__)


class ProfileServiceError(Exception):
    """Excepción específica para errores del servicio de perfiles."""
    pass


class ProfileService:
    """
    Servicio para gestionar perfiles de cargo.
    
    Proporciona operaciones CRUD completas para perfiles de cargo.
    """
    
    def __init__(self, db: Session):
        """
        Inicializa el servicio con una sesión de base de datos.
        
        Args:
            db: Sesión de SQLAlchemy
        """
        self.db = db

    def crear_perfil(
        self, 
        perfil_data: PerfilCargoCreate, 
        usuario_id: int
    ) -> PerfilCargo:
        """
        Crea un nuevo perfil de cargo.
        
        Args:
            perfil_data: Datos del perfil a crear
            usuario_id: ID del usuario que crea el perfil
            
        Returns:
            PerfilCargo: El perfil creado
            
        Raises:
            ProfileServiceError: Si ocurre un error al crear el perfil
        """
        try:
            perfil = PerfilCargo(
                titulo=perfil_data.titulo,
                descripcion=perfil_data.descripcion,
                requisitos=perfil_data.requisitos,
                responsabilidades=perfil_data.responsabilidades,
                habilidades_requeridas=perfil_data.habilidades_requeridas,
                habilidades_deseables=perfil_data.habilidades_deseables,
                nivel_experiencia=perfil_data.nivel_experiencia,
                salario_minimo=perfil_data.salario_minimo,
                salario_maximo=perfil_data.salario_maximo,
                departamento=perfil_data.departamento,
                created_by=usuario_id
            )
            
            self.db.add(perfil)
            self.db.commit()
            self.db.refresh(perfil)
            
            logger.info(f"Perfil de cargo '{perfil.titulo}' creado exitosamente por usuario {usuario_id}")
            return perfil
            
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Error de base de datos al crear perfil: {e}")
            raise ProfileServiceError(f"Error al crear perfil: {str(e)}")
        except Exception as e:
            self.db.rollback()
            logger.exception("Error inesperado al crear perfil")
            raise ProfileServiceError(f"Error inesperado al crear perfil: {str(e)}")

    def obtener_perfil_por_id(self, perfil_id: int) -> Optional[PerfilCargo]:
        """
        Obtiene un perfil por su ID.
        
        Args:
            perfil_id: ID del perfil a buscar
            
        Returns:
            PerfilCargo: El perfil encontrado o None si no existe
        """
        try:
            perfil = self.db.query(PerfilCargo).filter(PerfilCargo.id == perfil_id).first()
            return perfil
        except SQLAlchemyError as e:
            logger.error(f"Error de base de datos al obtener perfil {perfil_id}: {e}")
            raise ProfileServiceError(f"Error al obtener perfil: {str(e)}")
        except Exception as e:
            logger.exception(f"Error inesperado al obtener perfil {perfil_id}")
            raise ProfileServiceError(f"Error inesperado al obtener perfil: {str(e)}")

    def obtener_perfiles_por_usuario(self, usuario_id: int) -> List[PerfilCargo]:
        """
        Obtiene todos los perfiles creados por un usuario específico.
        
        Args:
            usuario_id: ID del usuario
            
        Returns:
            List[PerfilCargo]: Lista de perfiles del usuario
        """
        try:
            perfiles = self.db.query(PerfilCargo).filter(
                PerfilCargo.created_by == usuario_id
            ).order_by(PerfilCargo.created_at.desc()).all()
            return perfiles
        except SQLAlchemyError as e:
            logger.error(f"Error de base de datos al obtener perfiles del usuario {usuario_id}: {e}")
            raise ProfileServiceError(f"Error al obtener perfiles: {str(e)}")
        except Exception as e:
            logger.exception(f"Error inesperado al obtener perfiles del usuario {usuario_id}")
            raise ProfileServiceError(f"Error inesperado al obtener perfiles: {str(e)}")

    def obtener_todos_los_perfiles(self, skip: int = 0, limit: int = 100) -> List[PerfilCargo]:
        """
        Obtiene todos los perfiles con paginación.
        
        Args:
            skip: Número de registros a saltar
            limit: Número máximo de registros a devolver
            
        Returns:
            List[PerfilCargo]: Lista de perfiles
        """
        try:
            perfiles = self.db.query(PerfilCargo).offset(skip).limit(limit).all()
            return perfiles
        except SQLAlchemyError as e:
            logger.error(f"Error de base de datos al obtener perfiles: {e}")
            raise ProfileServiceError(f"Error al obtener perfiles: {str(e)}")
        except Exception as e:
            logger.exception("Error inesperado al obtener perfiles")
            raise ProfileServiceError(f"Error inesperado al obtener perfiles: {str(e)}")

    def actualizar_perfil(
        self, 
        perfil_id: int, 
        perfil_data: PerfilCargoUpdate
    ) -> Optional[PerfilCargo]:
        """
        Actualiza un perfil existente.
        
        Args:
            perfil_id: ID del perfil a actualizar
            perfil_data: Datos para actualizar el perfil
            
        Returns:
            PerfilCargo: El perfil actualizado o None si no existe
        """
        try:
            perfil = self.db.query(PerfilCargo).filter(PerfilCargo.id == perfil_id).first()
            
            if not perfil:
                return None

            # Actualizar solo los campos proporcionados
            update_data = perfil_data.model_dump(exclude_unset=True)
            logger.info(f"UPDATE DATA: {update_data}")
            
            # FORZAR: incluir siempre campos que son 0 (Pydantic a veces los excluye con exclude_unset)
            for field_name in ['umbral_recomendado', 'umbral_reservas', 'peso_tecnico', 'peso_experiencia', 'peso_soft_skills', 'penalizacion_sobrecalificado', 'penalizacion_cambio_rubro']:
                field_value = getattr(perfil_data, field_name, None)
                if field_value is not None and field_name not in update_data:
                    update_data[field_name] = field_value
                    logger.info(f"  Forzando campo {field_name}={field_value} en update_data")

            for field, value in update_data.items():
                setattr(perfil, field, value)
            
            self.db.commit()
            self.db.refresh(perfil)
            
            logger.info(f"Perfil {perfil_id} actualizado exitosamente")
            return perfil
            
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Error de base de datos al actualizar perfil {perfil_id}: {e}")
            raise ProfileServiceError(f"Error al actualizar perfil: {str(e)}")
        except Exception as e:
            self.db.rollback()
            logger.exception(f"Error inesperado al actualizar perfil {perfil_id}")
            raise ProfileServiceError(f"Error inesperado al actualizar perfil: {str(e)}")

    def eliminar_perfil(self, perfil_id: int) -> bool:
        """
        Elimina un perfil por su ID.
        
        Args:
            perfil_id: ID del perfil a eliminar
            
        Returns:
            bool: True si se eliminó exitosamente, False si no existía
        """
        try:
            perfil = self.db.query(PerfilCargo).filter(PerfilCargo.id == perfil_id).first()
            
            if not perfil:
                return False
            
            self.db.delete(perfil)
            self.db.commit()
            
            logger.info(f"Perfil {perfil_id} eliminado exitosamente")
            return True
            
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Error de base de datos al eliminar perfil {perfil_id}: {e}")
            raise ProfileServiceError(f"Error al eliminar perfil: {str(e)}")
        except Exception as e:
            self.db.rollback()
            logger.exception(f"Error inesperado al eliminar perfil {perfil_id}")
            raise ProfileServiceError(f"Error inesperado al eliminar perfil: {str(e)}")