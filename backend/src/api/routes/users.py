"""
Endpoints de gestión de usuarios (solo Admin).
"""
import logging
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query, Form
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.orm import Session

from api.deps import get_db, require_auth, require_admin
from models.usuario import Usuario
from services.user_service import UserService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/users", tags=["Users"])


# --- Pydantic Schemas ---

class UsuarioCreate(BaseModel):
    """Schema para crear un usuario."""
    email: str = Field(..., description="Email único del usuario")
    password: str = Field(..., min_length=8, description="Mínimo 8 caracteres")
    nombre: str = Field(..., min_length=3, description="Nombre completo")
    rol: str = Field(default="reclutador", description="admin o reclutador")


class UsuarioUpdate(BaseModel):
    """Schema para actualizar un usuario."""
    email: Optional[str] = Field(None, description="Email único del usuario")
    nombre: Optional[str] = Field(None, min_length=3)
    rol: Optional[str] = None


class UsuarioResponse(BaseModel):
    """Schema de respuesta de usuario."""
    id: int
    email: str
    nombre: str
    rol: str
    activo: bool
    created_at: Optional[str] = None
    last_login: Optional[str] = None

    class Config:
        from_attributes = True

    @field_validator("created_at", "last_login", mode="before")
    @classmethod
    def convert_datetime_to_str(cls, value):
        """Convierte datetime a string ISO para serialización JSON."""
        if value is None:
            return None
        if isinstance(value, datetime):
            return value.isoformat()
        return value


# --- Endpoints ---

@router.post("", response_class=HTMLResponse)
def crear_usuario(
    nombre: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    rol: str = Form(default="reclutador"),
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(require_admin),
):
    """
    Crea un nuevo usuario (solo Admin).

    - **email**: Email único del usuario
    - **password**: Contraseña (mínimo 8 caracteres)
    - **nombre**: Nombre completo
    - **rol**: Rol del usuario (admin o reclutador)
    """
    try:
        from core.security import hash_password

        service = UserService(db)

        # Hashear password
        password_hash = hash_password(password)

        # Crear usuario
        nuevo_usuario = service.crear_usuario(
            email=email,
            password_hash=password_hash,
            nombre=nombre,
            rol=rol
        )
        
        # Response HTML para HTMX
        success_html = f'''
<div hx-swap-oob="true" id="form-messages">
  <div class="bg-success-500 text-white px-4 py-3 rounded-lg transition-all duration-500">
    <p class="font-semibold">✓ Usuario creado</p>
    <p class="text-sm">El usuario {nuevo_usuario.email} ha sido creado exitosamente</p>
  </div>
</div>

<div hx-swap-oob="true" id="lista-usuarios-container"
     hx-get="/api/users/table-html"
     hx-trigger="load"
     hx-swap="innerHTML">
  <div class="text-center py-8 text-gray-500">
    <p>Actualizando lista...</p>
  </div>
</div>
'''
        return success_html
        
    except ValueError as e:
        error_html = f'''
<div hx-swap-oob="true" id="form-messages">
  <div class="bg-danger-500 text-white px-4 py-3 rounded-lg transition-all duration-500">
    <p class="font-semibold">✗ Error</p>
    <p class="text-sm">{str(e)}</p>
  </div>
</div>
'''
        raise HTTPException(status_code=400, detail=error_html)
    
    except Exception as e:
        logger.error(f"Error al crear usuario: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno al crear el usuario"
        )


@router.get("/table-html", response_class=HTMLResponse)
def listar_usuarios_html(
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(require_admin),
    activo: Optional[bool] = Query(None),
    rol: Optional[str] = Query(None),
):
    """
    Retorna el HTML de la tabla de usuarios para HTMX (solo Admin).
    """
    try:
        service = UserService(db)
        
        # Listar usuarios
        usuarios = service.listar_usuarios(activo=activo, rol=rol)
        
        if not usuarios:
            return '''
<div class="text-center py-12 text-gray-500">
    <p class="text-lg">No se encontraron usuarios</p>
</div>
'''
        
        # Generar filas
        rows_html = ""
        for u in usuarios:
            rol_badge = (
                '<span class="px-2 py-1 bg-[#2F4DAA] text-black text-xs rounded font-semibold">Administrador</span>'
                if u.rol == "admin" else
                '<span class="px-2 py-1 bg-gray-300 text-gray-800 text-xs rounded font-medium">Reclutador</span>'
            )

            activo_badge = (
                '<span class="px-2 py-1 bg-green-600 text-black text-xs rounded font-semibold">Activo</span>'
                if u.activo else
                '<span class="px-2 py-1 bg-gray-500 text-black text-xs rounded font-semibold">Inactivo</span>'
            )
            
            fecha_str = "N/A"
            if u.created_at:
                try:
                    fecha_str = u.created_at.strftime("%d/%m/%Y")
                except Exception:
                    pass
            
            rows_html += f'''
<tr class="border-b border-gray-100 hover:bg-gray-50">
    <td class="py-3 px-4">{u.nombre}</td>
    <td class="py-3 px-4 text-gray-600">{u.email}</td>
    <td class="py-3 px-4">{rol_badge}</td>
    <td class="py-3 px-4">{activo_badge}</td>
    <td class="py-3 px-4 text-sm text-gray-600">{fecha_str}</td>
    <td class="py-3 px-4">
        <div class="flex gap-2">
            <a href="#" onclick="editarUsuario({u.id}); return false;" class="text-blue-600 hover:text-blue-800 text-sm font-medium underline">Editar</a>
            <span class="text-gray-400">|</span>
            <a href="#" onclick="toggleActivoUsuario({u.id}, {str(u.activo).lower()}); return false;" class="{'text-red-600 hover:text-red-800' if u.activo else 'text-green-600 hover:text-green-800'} text-sm font-medium underline">
                {'Desactivar' if u.activo else 'Activar'}
            </a>
        </div>
    </td>
</tr>
'''
        
        html = f'''
<div class="overflow-x-auto">
    <table class="min-w-full bg-white rounded-lg overflow-hidden">
        <thead class="bg-[#2F4DAA] text-gray-900">
            <tr>
                <th class="py-3 px-4 text-left text-sm font-semibold">Nombre</th>
                <th class="py-3 px-4 text-left text-sm font-semibold">Email</th>
                <th class="py-3 px-4 text-left text-sm font-semibold">Rol</th>
                <th class="py-3 px-4 text-left text-sm font-semibold">Estado</th>
                <th class="py-3 px-4 text-left text-sm font-semibold">Creado</th>
                <th class="py-3 px-4 text-left text-sm font-semibold">Acciones</th>
            </tr>
        </thead>
        <tbody>
            {rows_html}
        </tbody>
    </table>
</div>
<div class="text-sm text-gray-600 mt-4 text-center">
    Mostrando {len(usuarios)} usuarios
</div>
'''
        return html
        
    except Exception as e:
        logger.error(f"Error al generar tabla de usuarios: {e}", exc_info=True)
        return HTMLResponse(
            content='<div class="text-center py-12 text-danger-600"><p>Error al cargar la tabla</p></div>',
            status_code=500,
        )


@router.get("", response_model=List[UsuarioResponse])
def listar_usuarios_json(
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(require_admin),
    activo: Optional[bool] = Query(None),
    rol: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
):
    """
    Lista usuarios en formato JSON (solo Admin).
    """
    service = UserService(db)
    usuarios = service.listar_usuarios(activo=activo, rol=rol, skip=skip, limit=limit)
    return usuarios


@router.get("/{usuario_id}", response_model=UsuarioResponse)
def obtener_usuario(
    usuario_id: int,
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(require_admin),
):
    """
    Obtiene un usuario por ID (solo Admin).
    """
    service = UserService(db)
    usuario = service.obtener_usuario_por_id(usuario_id)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return usuario


@router.put("/{usuario_id}", response_class=HTMLResponse)
def actualizar_usuario(
    usuario_id: int,
    nombre: str = Form(...),
    email: str = Form(...),
    rol: str = Form(...),
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(require_admin),
):
    """
    Actualiza un usuario existente (solo Admin).
    """
    try:
        service = UserService(db)

        # Verificar que el usuario existe
        usuario_existente = service.obtener_usuario_por_id(usuario_id)
        if not usuario_existente:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")

        # Validar que el email no exista en otro usuario
        if email.lower().strip() != usuario_existente.email.lower().strip():
            email_duplicado = service.obtener_usuario_por_email(email)
            if email_duplicado:
                raise ValueError(f"El email '{email}' ya está registrado por otro usuario")

        # No permitir cambiar el rol del último admin a reclutador
        if usuario_existente.rol == "admin" and rol != "admin":
            admins = service.listar_usuarios(rol="admin", activo=True)
            if len(admins) == 1 and admins[0].id == usuario_id:
                raise ValueError("No se puede cambiar el rol del último administrador")

        # Actualizar usuario
        usuario_actualizado = service.actualizar_usuario(
            usuario_id=usuario_id,
            nombre=nombre,
            email=email,
            rol=rol
        )

        # Response HTML para HTMX con OOB swap
        success_html = f'''
<div hx-swap-oob="true" id="form-messages">
  <div class="bg-success-500 text-white px-4 py-3 rounded-lg transition-all duration-500">
    <p class="font-semibold">✓ Usuario actualizado</p>
    <p class="text-sm">Los datos del usuario han sido actualizados exitosamente</p>
  </div>
</div>

<div hx-swap-oob="true" id="lista-usuarios-container"
     hx-get="/api/users/table-html"
     hx-trigger="load"
     hx-swap="innerHTML">
  <div class="text-center py-8 text-gray-500">
    <p>Actualizando lista...</p>
  </div>
</div>
'''
        return success_html

    except ValueError as e:
        error_html = f'''
<div hx-swap-oob="true" id="form-messages">
  <div class="bg-danger-500 text-white px-4 py-3 rounded-lg transition-all duration-500">
    <p class="font-semibold">✗ Error</p>
    <p class="text-sm">{str(e)}</p>
  </div>
</div>
'''
        raise HTTPException(status_code=400, detail=error_html)

    except Exception as e:
        logger.error(f"Error al actualizar usuario: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno al actualizar el usuario"
        )


@router.put("/{usuario_id}/role", response_class=HTMLResponse)
def cambiar_rol_usuario(
    usuario_id: int,
    rol: str = Query(..., description="Nuevo rol (admin o reclutador)"),
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(require_admin),
):
    """
    Cambia el rol de un usuario (solo Admin).
    """
    try:
        service = UserService(db)
        
        # No permitir cambiar el rol del último admin
        if rol != "admin":
            admins = service.listar_usuarios(rol="admin", activo=True)
            if len(admins) == 1 and admins[0].id == usuario_id:
                raise ValueError("No se puede eliminar el último administrador")
        
        usuario = service.cambiar_rol(usuario_id, rol)
        
        if not usuario:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        
        success_html = f'''
<div hx-swap-oob="true" id="form-messages">
  <div class="bg-success-500 text-white px-4 py-3 rounded-lg transition-all duration-500">
    <p class="font-semibold">✓ Rol actualizado</p>
    <p class="text-sm">El rol del usuario ha sido actualizado a {rol}</p>
  </div>
</div>

<div hx-swap-oob="true" id="lista-usuarios-container"
     hx-get="/api/users/table-html"
     hx-trigger="load"
     hx-swap="innerHTML">
  <div class="text-center py-8 text-gray-500">
    <p>Actualizando lista...</p>
  </div>
</div>
'''
        return success_html
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    except Exception as e:
        logger.error(f"Error al cambiar rol: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno al cambiar el rol"
        )


@router.patch("/{usuario_id}/toggle-activo", response_class=HTMLResponse)
def toggle_activo_usuario(
    usuario_id: int,
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(require_admin),
):
    """
    Activa o desactiva un usuario (solo Admin).
    """
    try:
        service = UserService(db)
        usuario = service.obtener_usuario_por_id(usuario_id)
        
        if not usuario:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        
        # No permitir desactivar el último admin
        if usuario.activo and usuario.rol == "admin":
            admins = service.listar_usuarios(rol="admin", activo=True)
            if len(admins) == 1 and admins[0].id == usuario_id:
                raise ValueError("No se puede desactivar el último administrador")
        
        # Toggle
        if usuario.activo:
            service.desactivar_usuario(usuario_id)
            mensaje = "Usuario desactivado exitosamente"
        else:
            service.activar_usuario(usuario_id)
            mensaje = "Usuario activado exitosamente"
        
        success_html = f'''
<div hx-swap-oob="true" id="form-messages">
  <div class="bg-success-500 text-white px-4 py-3 rounded-lg transition-all duration-500">
    <p class="font-semibold">✓ {mensaje}</p>
  </div>
</div>

<div hx-swap-oob="true" id="lista-usuarios-container"
     hx-get="/api/users/table-html"
     hx-trigger="load"
     hx-swap="innerHTML">
  <div class="text-center py-8 text-gray-500">
    <p>Actualizando lista...</p>
  </div>
</div>
'''
        return success_html
        
    except ValueError as e:
        error_html = f'''
<div hx-swap-oob="true" id="form-messages">
  <div class="bg-danger-500 text-white px-4 py-3 rounded-lg transition-all duration-500">
    <p class="font-semibold">✗ Error</p>
    <p class="text-sm">{str(e)}</p>
  </div>
</div>
'''
        raise HTTPException(status_code=400, detail=error_html)
    
    except Exception as e:
        logger.error(f"Error al toggle activo: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno"
        )


@router.delete("/{usuario_id}", response_class=HTMLResponse)
def eliminar_usuario(
    usuario_id: int,
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(require_admin),
):
    """
    Elimina físicamente un usuario (solo Admin, soft delete no implementado).
    """
    try:
        service = UserService(db)
        usuario = service.obtener_usuario_por_id(usuario_id)
        
        if not usuario:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        
        # No permitir eliminar el último admin
        if usuario.rol == "admin":
            admins = service.listar_usuarios(rol="admin", activo=True)
            if len(admins) == 1 and admins[0].id == usuario_id:
                raise ValueError("No se puede eliminar el último administrador")
        
        # Eliminar
        service.eliminar_usuario(usuario_id)
        
        success_html = f'''
<div hx-swap-oob="true" id="form-messages">
  <div class="bg-success-500 text-white px-4 py-3 rounded-lg transition-all duration-500">
    <p class="font-semibold">✓ Usuario eliminado</p>
  </div>
</div>

<div hx-swap-oob="true" id="lista-usuarios-container"
     hx-get="/api/users/table-html"
     hx-trigger="load"
     hx-swap="innerHTML">
  <div class="text-center py-8 text-gray-500">
    <p>Actualizando lista...</p>
  </div>
</div>
'''
        return success_html
        
    except ValueError as e:
        error_html = f'''
<div hx-swap-oob="true" id="form-messages">
  <div class="bg-danger-500 text-white px-4 py-3 rounded-lg transition-all duration-500">
    <p class="font-semibold">✗ Error</p>
    <p class="text-sm">{str(e)}</p>
  </div>
</div>
'''
        raise HTTPException(status_code=400, detail=error_html)
    
    except Exception as e:
        logger.error(f"Error al eliminar usuario: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno"
        )
