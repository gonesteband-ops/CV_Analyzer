"""
Rutas de API para gestión de Perfiles de Cargo.
"""
import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Request, Form, Query
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from api.deps import get_db, require_auth
from models.perfil_cargo import PerfilCargo
from models.usuario import Usuario
from models.analisis import Analisis
from models.schemas_perfil_cargo import (
    PerfilCargoCreate as PerfilCargoCreateSchema,
    PerfilCargoUpdate,
    PerfilCargoResponse
)
from services.profile_service import ProfileService, ProfileServiceError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/profiles", tags=["Perfiles"])


def render_perfil_html(perfil: PerfilCargo) -> str:
    """
    Renderiza un perfil como fragmento HTML para HTMX.
    
    Args:
        perfil: Objeto PerfilCargo a renderizar
        
    Returns:
        str: HTML del card del perfil
    """
    from jinja2 import Template

    template_str = '''
<div id="perfil-{{ perfil.id }}" class="{% if perfil.activo == False %}border-2 rounded-lg p-4 shadow-inner{% else %}border-2 border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow{% endif %}" {% if perfil.activo == False %}style="background-color: #E0D8D7; border-color: #5A5550;"{% endif %} data-perfil-id="{{ perfil.id }}">
  <div class="flex justify-between items-start">
    <div class="flex-1">
      <div class="flex items-center gap-2">
        <h4 class="font-semibold text-[#2F4DAA] text-lg">{{ perfil.titulo }} ({% if perfil.activo == False %}Inactivo{% else %}Activo{% endif %})</h4>
      </div>

      <p class="text-sm text-gray-600 mt-1">{{ perfil.descripcion[:150] }}{% if perfil.descripcion|length > 150 %}...{% endif %}</p>

      <div class="mt-3 grid grid-cols-2 gap-2 text-sm">
        {% if perfil.nivel_experiencia %}
        <div><span class="font-medium text-gray-600">Nivel:</span> <span class="text-gray-900">{{ perfil.nivel_experiencia }}</span></div>
        {% endif %}
        {% if perfil.departamento %}
        <div><span class="font-medium text-gray-600">Dept:</span> <span class="text-gray-900">{{ perfil.departamento }}</span></div>
        {% endif %}

        {% if perfil.salario_minimo is not none or perfil.salario_maximo is not none %}
        <div class="col-span-2">
          <span class="font-medium text-gray-600">Salario:</span>
          <span class="text-gray-900">
            {% if perfil.salario_minimo %} ${{ perfil.salario_minimo|intformatter }}{% else %} No especificado{% endif %}
            {% if perfil.salario_minimo and perfil.salario_maximo %} - {% endif %}
            {% if perfil.salario_maximo %} ${{ perfil.salario_maximo|intformatter }}{% else %} No especificado{% endif %}
          </span>
        </div>
        {% endif %}

        {% if perfil.habilidades_requeridas and perfil.habilidades_requeridas|length > 0 %}
        <div class="col-span-2">
          <span class="font-medium text-gray-600">Hab. Requeridas:</span>
          <span class="text-gray-900">{{ perfil.habilidades_requeridas|join(', ') }}</span>
        </div>
        {% endif %}

        {% if perfil.habilidades_deseables and perfil.habilidades_deseables|length > 0 %}
        <div class="col-span-2">
          <span class="font-medium text-gray-600">Hab. Deseables:</span>
          <span class="text-gray-900">{{ perfil.habilidades_deseables|join(', ') }}</span>
        </div>
        {% endif %}
      </div>

      <div class="mt-4 flex items-center gap-2 text-xs text-gray-500">
        <span>Creado: {{ perfil.created_at.strftime('%d/%m/%Y') }}</span>
      </div>
    </div>

    <div class="flex space-x-2 ml-4">
      <button
        onclick="editarPerfil({{ perfil.id }})"
        class="text-blue-600 hover:text-blue-800 text-sm font-medium px-3 py-1 rounded hover:bg-blue-50 transition-colors"
      >
        Editar
      </button>
      <button
        onclick="toggleActivo({{ perfil.id }})"
        class="{% if perfil.activo %}text-red-600 hover:text-red-800{% else %}text-green-600 hover:text-green-800{% endif %} text-sm font-medium px-3 py-1 rounded hover:bg-{% if perfil.activo %}red-50{% else %}green-50{% endif %} transition-colors"
      >
        {% if perfil.activo %}Desactivar{% else %}Activar{% endif %}
      </button>
    </div>
  </div>
</div>
'''
    
    template = Template(template_str)
    
    # Formatear habilidades
    hab_req = ', '.join(perfil.habilidades_requeridas) if perfil.habilidades_requeridas else ''
    hab_des = ', '.join(perfil.habilidades_deseables) if perfil.habilidades_deseables else ''
    
    return template.render(
        perfil=perfil,
        hab_req=hab_req,
        hab_des=hab_des
    )


@router.get("")
async def list_perfiles(
    activos: bool = Query(False),
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_auth),
):
    """
    Lista todos los perfiles de cargo del usuario actual.
    """
    try:
        # Obtener perfiles con filtro por estado activo
        if activos:
            perfiles = db.query(PerfilCargo).filter(
                PerfilCargo.created_by == usuario.id,
                PerfilCargo.activo == True
            ).order_by(PerfilCargo.created_at.desc()).all()
        else:
            perfiles = db.query(PerfilCargo).filter(
                PerfilCargo.created_by == usuario.id
            ).order_by(PerfilCargo.created_at.desc()).all()

        return [PerfilCargoResponse.model_validate(p) for p in perfiles]
    except ProfileServiceError as e:
        logger.error(f"Error al listar perfiles: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Ruta separada para retornar fragmentos HTML renderizados con Jinja2
@router.get("/list", response_class=HTMLResponse)
async def list_perfiles_html(
    request: Request,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_auth),
):
    """
    Lista todos los perfiles de cargo como fragmento HTML renderizado (HTMX).
    
    Esta ruta es específica para ser llamada por HTMX desde la plantilla.
    """
    from main import format_currency
    
    try:
        service = ProfileService(db)
        perfiles = service.obtener_perfiles_por_usuario(usuario.id)
        
        # Renderizar cada perfil usando HTML directo
        perfiles_html_list = []
        for perfil in perfiles:
            # Formatear valores
            salario_min_str = format_currency(perfil.salario_minimo) if perfil.salario_minimo else "No especificado"
            salario_max_str = format_currency(perfil.salario_maximo) if perfil.salario_maximo else "No especificado"
            hab_req_str = ", ".join(perfil.habilidades_requeridas) if perfil.habilidades_requeridas else ""
            hab_des_str = ", ".join(perfil.habilidades_deseables) if perfil.habilidades_deseables else ""
            descripcion_truncada = perfil.descripcion[:150] + "..." if len(perfil.descripcion) > 150 else perfil.descripcion
            fecha_creacion = perfil.created_at.strftime('%d/%m/%Y')
            
            # Color badge según umbral
            if perfil.umbral_recomendado is not None:
                if perfil.umbral_recomendado >= 70:
                    badge_class = "bg-success-500 text-white"
                elif perfil.umbral_recomendado >= 40:
                    badge_class = "bg-yellow-400 text-gray-900"
                else:
                    badge_class = "bg-danger-500 text-white"

                umbral_html = f'''
                <span class="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium {badge_class}">
                  Umbral: {perfil.umbral_recomendado}
                </span>'''
            else:
                umbral_html = ""

            # Badge de estado activo/inactivo
            if perfil.activo == False:
                activo_html = f'''
                <span class="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-gray-400 text-white">
                  Inactivo
                </span>'''
            else:
                activo_html = ""
            
            # Construir grid de información condicional
            info_items = []
            if perfil.nivel_experiencia:
                info_items.append(f'<div><span class="font-medium text-gray-600">Nivel:</span> <span class="text-gray-900">{perfil.nivel_experiencia}</span></div>')
            if perfil.departamento:
                info_items.append(f'<div><span class="font-medium text-gray-600">Dept:</span> <span class="text-gray-900">{perfil.departamento}</span></div>')
            if perfil.salario_minimo is not None or perfil.salario_maximo is not None:
                info_items.append(f'<div class="col-span-2"><span class="font-medium text-gray-600">Salario:</span> <span class="text-gray-900">{salario_min_str} - {salario_max_str}</span></div>')
            if hab_req_str:
                info_items.append(f'<div class="col-span-2"><span class="font-medium text-gray-600">Hab. Requeridas:</span> <span class="text-gray-900">{hab_req_str}</span></div>')
            if hab_des_str:
                info_items.append(f'<div class="col-span-2"><span class="font-medium text-gray-600">Hab. Deseables:</span> <span class="text-gray-900">{hab_des_str}</span></div>')
            
            info_html = "".join(info_items)

            # Clases según estado activo/inactivo
            if perfil.activo:
                clases_card = "border-2 border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow"
                estilo_inline = ""
            else:
                clases_card = "border-2 rounded-lg p-4 shadow-inner"
                estilo_inline = 'style="background-color: #E0D8D7; border-color: #5A5550;"'

            html = f'''
<div id="perfil-{perfil.id}" class="{clases_card}" {estilo_inline} data-perfil-id="{perfil.id}">
  <div class="flex justify-between items-start">
    <div class="flex-1">
      <div class="flex items-center gap-2">
        <h4 class="font-semibold text-[#2F4DAA] text-lg">{perfil.titulo} ({'Activo' if perfil.activo else 'Inactivo'})</h4>
      </div>

      <p class="text-sm text-gray-600 mt-1">{descripcion_truncada}</p>

      <div class="mt-3 grid grid-cols-2 gap-2 text-sm">
        {info_html}
      </div>

      <div class="mt-4 flex items-center gap-2 text-xs text-gray-500">
        <span>Creado: {fecha_creacion}</span>
      </div>
    </div>

    <div class="flex space-x-2 ml-4">
      <button onclick="editarPerfil({perfil.id})" class="text-blue-600 hover:text-blue-800 text-sm font-medium px-3 py-1 rounded hover:bg-blue-50 transition-colors">Editar</button>
      <button onclick="toggleActivo({perfil.id})" class="{'text-red-600 hover:text-red-800 hover:bg-red-50' if perfil.activo else 'text-green-600 hover:text-green-800 hover:bg-green-50'} text-sm font-medium px-3 py-1 rounded transition-colors">{'Desactivar' if perfil.activo else 'Activar'}</button>
    </div>
  </div>
</div>
'''
            perfiles_html_list.append(html)
        
        if not perfiles_html_list:
            return '<div class="text-center py-8 text-gray-500"><p>No hay perfiles creados aún</p></div>'
        
        count = len(perfiles)
        return f'<div id="count-perfiles-inner" class="text-sm text-gray-500 mb-4">{count} perfil(es)</div><div class="space-y-4">' + ''.join(perfiles_html_list) + '</div>'
    
    except ProfileServiceError as e:
        logger.error(f"Error al listar perfiles (HTML): {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{perfil_id}", response_model=PerfilCargoResponse)
async def get_perfil(
    perfil_id: int,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_auth),
):
    try:
        service = ProfileService(db)
        perfil = service.obtener_perfil_por_id(perfil_id)
        
        if not perfil or perfil.created_by != usuario.id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No se encontró el perfil con id {perfil_id}",
            )
        
        return PerfilCargoResponse.model_validate(perfil)
    except ProfileServiceError as e:
        logger.error(f"Error al obtener perfil {perfil_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("", response_class=HTMLResponse, status_code=status.HTTP_201_CREATED)
async def create_perfil(
    titulo: str = Form(...),
    descripcion: str = Form(...),
    requisitos: Optional[str] = Form(None),
    responsabilidades: Optional[str] = Form(None),
    nivel_experiencia: Optional[str] = Form(None),
    departamento: Optional[str] = Form(None),
    salario_minimo: Optional[str] = Form(None),
    salario_maximo: Optional[str] = Form(None),
    habilidades_requeridas: Optional[str] = Form(None),
    habilidades_deseables: Optional[str] = Form(None),
    umbral_recomendado: Optional[int] = Form(70),
    umbral_reservas: Optional[int] = Form(40),
    peso_tecnico: Optional[int] = Form(50),
    peso_experiencia: Optional[int] = Form(30),
    peso_soft_skills: Optional[int] = Form(20),
    penalizacion_sobrecalificado: Optional[int] = Form(25),
    penalizacion_cambio_rubro: Optional[int] = Form(15),
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_auth),
):
    """
    Crea un nuevo perfil de cargo y devuelve HTML para HTMX.
    """
    try:
        # Procesar salarios
        sal_min = None
        sal_max = None
        try:
            if salario_minimo and salario_minimo.strip():
                sal_min = int(salario_minimo)
        except (ValueError, TypeError) as e:
            logger.warning(f"Error al parsear salario_minimo '{salario_minimo}': {e}")

        try:
            if salario_maximo and salario_maximo.strip():
                sal_max = int(salario_maximo)
        except (ValueError, TypeError) as e:
            logger.warning(f"Error al parsear salario_maximo '{salario_maximo}': {e}")

        # El schema se encarga de convertir habilidades de string a lista
        perfil_data = PerfilCargoCreateSchema(
            titulo=titulo,
            descripcion=descripcion,
            requisitos=requisitos,
            responsabilidades=responsabilidades,
            nivel_experiencia=nivel_experiencia,
            departamento=departamento,
            salario_minimo=sal_min,
            salario_maximo=sal_max,
            habilidades_requeridas=habilidades_requeridas,
            habilidades_deseables=habilidades_deseables,
            umbral_recomendado=umbral_recomendado,
            umbral_reservas=umbral_reservas,
            peso_tecnico=peso_tecnico,
            peso_experiencia=peso_experiencia,
            peso_soft_skills=peso_soft_skills,
            penalizacion_sobrecalificado=penalizacion_sobrecalificado,
            penalizacion_cambio_rubro=penalizacion_cambio_rubro,
        )

        logger.info(f"Esquema validado: {perfil_data}")

        service = ProfileService(db)
        perfil = service.crear_perfil(perfil_data, usuario.id)

        logger.info(f"Perfil creado exitosamente: {perfil.id}")

        # Generar HTML para la fila de la tabla
        from main import format_currency

        salario_min_str = format_currency(perfil.salario_minimo) if perfil.salario_minimo else "No especificado"
        salario_max_str = format_currency(perfil.salario_maximo) if perfil.salario_maximo else "No especificado"
        hab_req_str = ", ".join(perfil.habilidades_requeridas) if perfil.habilidades_requeridas else ""
        hab_des_str = ", ".join(perfil.habilidades_deseables) if perfil.habilidades_deseables else ""
        descripcion_truncada = perfil.descripcion[:150] + "..." if len(perfil.descripcion) > 150 else perfil.descripcion
        fecha_creacion = perfil.created_at.strftime('%d/%m/%Y')

        if perfil.umbral_recomendado is not None:
            if perfil.umbral_recomendado >= 70:
                badge_class = "bg-success-500 text-white"
            elif perfil.umbral_recomendado >= 40:
                badge_class = "bg-yellow-400 text-gray-900"
            else:
                badge_class = "bg-danger-500 text-white"
            umbral_html = f'<span class="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium {badge_class}">Umbral: {perfil.umbral_recomendado}</span>'
        else:
            umbral_html = ""

        # Inicializar activo_html (badge "Inactivo" para perfiles desactivados)
        activo_html = ""
        if not perfil.activo:
            activo_html = '<span class="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-gray-400 text-white">Inactivo</span>'

        info_items = []
        if perfil.nivel_experiencia:
            info_items.append(f'<div><span class="font-medium text-gray-600">Nivel:</span> <span class="text-gray-900">{perfil.nivel_experiencia}</span></div>')
        if perfil.departamento:
            info_items.append(f'<div><span class="font-medium text-gray-600">Dept:</span> <span class="text-gray-900">{perfil.departamento}</span></div>')
        if perfil.salario_minimo is not None or perfil.salario_maximo is not None:
            info_items.append(f'<div class="col-span-2"><span class="font-medium text-gray-600">Salario:</span> <span class="text-gray-900">{salario_min_str} - {salario_max_str}</span></div>')
        if hab_req_str:
            info_items.append(f'<div class="col-span-2"><span class="font-medium text-gray-600">Hab. Requeridas:</span> <span class="text-gray-900">{hab_req_str}</span></div>')
        if hab_des_str:
            info_items.append(f'<div class="col-span-2"><span class="font-medium text-gray-600">Hab. Deseables:</span> <span class="text-gray-900">{hab_des_str}</span></div>')

        info_html = "".join(info_items)

        # Clases según estado activo/inactivo
        if perfil.activo:
            clases_card = "border-2 border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow"
            estilo_inline = ""
        else:
            clases_card = "border-2 rounded-lg p-4 shadow-inner"
            estilo_inline = 'style="background-color: #E0D8D7; border-color: #5A5550;"'

        fila_html = f'''
<div id="perfil-{perfil.id}" class="{clases_card}" {estilo_inline}
     data-perfil-id="{perfil.id}"
     hx-swap-oob="afterbegin:#lista-perfiles-container">
  <div class="flex justify-between items-start">
    <div class="flex-1">
      <div class="flex items-center gap-2">
        <h4 class="font-semibold text-[#2F4DAA] text-lg">{perfil.titulo} ({'Activo' if perfil.activo else 'Inactivo'})</h4>
      </div>
      <p class="text-sm text-gray-600 mt-1">{descripcion_truncada}</p>
      <div class="mt-3 grid grid-cols-2 gap-2 text-sm">
        {info_html}
      </div>
      <div class="mt-4 flex items-center gap-2 text-xs text-gray-500">
        <span>Creado: {fecha_creacion}</span>
      </div>
    </div>
    <div class="flex space-x-2 ml-4">
      <button onclick="editarPerfil({perfil.id})" class="text-blue-600 hover:text-blue-800 text-sm font-medium px-3 py-1 rounded hover:bg-blue-50 transition-colors">Editar</button>
      <button onclick="toggleActivo({perfil.id})" class="{'text-red-600 hover:text-red-800 hover:bg-red-50' if perfil.activo else 'text-green-600 hover:text-green-800 hover:bg-green-50'} text-sm font-medium px-3 py-1 rounded transition-colors">{'Desactivar' if perfil.activo else 'Activar'}</button>
    </div>
  </div>
</div>
'''

        # Mensaje de éxito con hx-swap-oob="true" para ir a #form-messages
        mensaje_exito = f'''
<div hx-swap-oob="true" id="form-messages">
  <div class="bg-success-500 text-white px-4 py-3 rounded-lg transition-all duration-500">
    <p class="font-semibold">✓ Perfil creado exitosamente</p>
    <p class="text-sm">{perfil.titulo} ha sido agregado a tu lista de perfiles</p>
  </div>
</div>
'''

        # Retornar ambos: mensaje y fila (hx-swap-oob maneja la inserción automática)
        return mensaje_exito + fila_html

    except ProfileServiceError as e:
        logger.error(f"Error en ProfileService: {e}")
        error_html = f'''<div hx-swap-oob="true" id="form-messages">
  <div class="bg-danger-500 text-white px-4 py-3 rounded-lg transition-all duration-500">
    <p class="font-semibold">✗ Error al crear perfil</p>
    <p class="text-sm">{str(e)}</p>
  </div>
</div>'''
        raise HTTPException(status_code=500, detail=error_html)
    except Exception as e:
        logger.exception(f"Error inesperado al crear perfil: {e}")
        error_html = f'''<div hx-swap-oob="true" id="form-messages">
  <div class="bg-danger-500 text-white px-4 py-3 rounded-lg transition-all duration-500">
    <p class="font-semibold">✗ Error al crear perfil</p>
    <p class="text-sm">Error interno del servidor</p>
  </div>
</div>'''
        raise HTTPException(status_code=500, detail=error_html)


@router.put("/{perfil_id}", response_class=HTMLResponse)
async def update_perfil(
    perfil_id: int,
    titulo: str = Form(...),
    descripcion: str = Form(...),
    requisitos: Optional[str] = Form(None),
    responsabilidades: Optional[str] = Form(None),
    nivel_experiencia: Optional[str] = Form(None),
    departamento: Optional[str] = Form(None),
    salario_minimo: Optional[str] = Form(None),
    salario_maximo: Optional[str] = Form(None),
    habilidades_requeridas: Optional[str] = Form(None),
    habilidades_deseables: Optional[str] = Form(None),
    umbral_recomendado: Optional[int] = Form(None),
    umbral_reservas: Optional[int] = Form(None),
    peso_tecnico: Optional[int] = Form(None),
    peso_experiencia: Optional[int] = Form(None),
    peso_soft_skills: Optional[int] = Form(None),
    penalizacion_sobrecalificado: Optional[int] = Form(None),
    penalizacion_cambio_rubro: Optional[int] = Form(None),
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_auth),
):
    """
    Actualiza un perfil de cargo existente. Acepta datos como formulario (HTMX).
    """
    try:
        # Verificar que el perfil pertenece al usuario
        service = ProfileService(db)
        perfil_existente = service.obtener_perfil_por_id(perfil_id)

        if not perfil_existente or perfil_existente.created_by != usuario.id:
            error_html = f'''<div hx-swap-oob="true" id="form-messages">
  <div class="bg-danger-500 text-white px-4 py-3 rounded-lg transition-all duration-500">
    <p class="font-semibold">✗ Error al actualizar</p>
    <p class="text-sm">No se encontró el perfil o no tienes permiso</p>
  </div>
</div>'''
            raise HTTPException(status_code=404, detail=error_html)

        # Procesar salarios
        sal_min = None
        sal_max = None
        try:
            if salario_minimo and salario_minimo.strip():
                sal_min = int(salario_minimo)
        except (ValueError, TypeError) as e:
            logger.warning(f"Error al parsear salario_minimo '{salario_minimo}': {e}")

        try:
            if salario_maximo and salario_maximo.strip():
                sal_max = int(salario_maximo)
        except (ValueError, TypeError) as e:
            logger.warning(f"Error al parsear salario_maximo '{salario_maximo}': {e}")

        # El schema se encarga de convertir habilidades de string a lista
        logger.info(f"UPDATE: penalizacion_sobrecalificado={penalizacion_sobrecalificado}, penalizacion_cambio_rubro={penalizacion_cambio_rubro}")
        logger.info(f"UPDATE: umbral_recomendado={umbral_recomendado}, umbral_reservas={umbral_reservas}")
        logger.info(f"UPDATE: peso_tecnico={peso_tecnico}, peso_experiencia={peso_experiencia}, peso_soft_skills={peso_soft_skills}")
        
        # Usar valores por defecto solo si es None (0 es un valor válido)
        perfil_data = PerfilCargoUpdate(
            titulo=titulo,
            descripcion=descripcion,
            requisitos=requisitos,
            responsabilidades=responsabilidades,
            nivel_experiencia=nivel_experiencia,
            departamento=departamento,
            salario_minimo=sal_min,
            salario_maximo=sal_max,
            habilidades_requeridas=habilidades_requeridas,
            habilidades_deseables=habilidades_deseables,
            umbral_recomendado=umbral_recomendado if umbral_recomendado is not None else 70,
            umbral_reservas=umbral_reservas if umbral_reservas is not None else 40,
            peso_tecnico=peso_tecnico if peso_tecnico is not None else 50,
            peso_experiencia=peso_experiencia if peso_experiencia is not None else 30,
            peso_soft_skills=peso_soft_skills if peso_soft_skills is not None else 20,
            penalizacion_sobrecalificado=penalizacion_sobrecalificado if penalizacion_sobrecalificado is not None else 25,
            penalizacion_cambio_rubro=penalizacion_cambio_rubro if penalizacion_cambio_rubro is not None else 15,
        )

        perfil_actualizado = service.actualizar_perfil(perfil_id, perfil_data)

        if not perfil_actualizado:
            error_html = f'''<div hx-swap-oob="true" id="form-messages">
  <div class="bg-danger-500 text-white px-4 py-3 rounded-lg transition-all duration-500">
    <p class="font-semibold">✗ Error al actualizar</p>
    <p class="text-sm">No se pudo actualizar el perfil</p>
  </div>
</div>'''
            raise HTTPException(status_code=404, detail=error_html)

        # Mensaje de éxito + recarga automática de lista
        success_html = f'''<div hx-swap-oob="true" id="form-messages">
  <div class="bg-success-500 text-white px-4 py-3 rounded-lg transition-all duration-500">
    <p class="font-semibold">✓ Perfil actualizado exitosamente</p>
    <p class="text-sm">{perfil_actualizado.titulo} ha sido actualizado</p>
  </div>
</div>

<div hx-swap-oob="true" id="lista-perfiles-container"
     hx-get="/api/profiles/list"
     hx-trigger="load"
     hx-swap="innerHTML">
  <div class="text-center py-8 text-gray-500">
    <p>Actualizando lista de perfiles...</p>
  </div>
</div>'''

        return success_html
    except ProfileServiceError as e:
        logger.error(f"Error al actualizar perfil {perfil_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.exception(f"Error inesperado al actualizar perfil {perfil_id}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")


@router.patch("/{perfil_id}/toggle-activo", response_class=HTMLResponse)
async def toggle_activo_perfil(
    perfil_id: int,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_auth),
):
    """
    Cambia el estado de activo/inactivo de un perfil de cargo.
    """
    try:
        # Verificar que el perfil pertenece al usuario
        service = ProfileService(db)
        perfil_existente = service.obtener_perfil_por_id(perfil_id)

        if not perfil_existente or perfil_existente.created_by != usuario.id:
            error_html = f'''<div hx-swap-oob="true" id="form-messages">
  <div class="bg-danger-500 text-white px-4 py-3 rounded-lg transition-all duration-500">
    <p class="font-semibold">✗ Error al cambiar estado</p>
    <p class="text-sm">No se encontró el perfil o no tienes permiso</p>
  </div>
</div>'''
            raise HTTPException(status_code=404, detail=error_html)

        # Cambiar el estado activo al valor opuesto
        perfil_existente.activo = not perfil_existente.activo
        db.commit()

        # Recargar toda la lista para mostrar el cambio de estado
        success_html = f'''<div hx-swap-oob="true" id="form-messages">
  <div class="bg-success-500 text-white px-4 py-3 rounded-lg transition-all duration-500">
    <p class="font-semibold">✓ Perfil {'desactivado' if perfil_existente.activo == False else 'activado'}</p>
    <p class="text-sm">El perfil ha sido {'desactivado' if perfil_existente.activo == False else 'reactivado'} exitosamente</p>
  </div>
</div>

<div hx-swap-oob="true" id="lista-perfiles-container"
     hx-get="/api/profiles/list"
     hx-trigger="load"
     hx-swap="innerHTML">
  <div class="text-center py-8 text-gray-500">
    <p>Actualizando lista de perfiles...</p>
  </div>
</div>'''

        return success_html

    except ProfileServiceError as e:
        logger.error(f"Error al cambiar estado del perfil {perfil_id}: {e}")
        error_html = f'''<div hx-swap-oob="true" id="form-messages">
  <div class="bg-danger-500 text-white px-4 py-3 rounded-lg transition-all duration-500">
    <p class="font-semibold">✗ Error del servidor</p>
    <p class="text-sm">{str(e)}</p>
  </div>
</div>'''
        raise HTTPException(status_code=500, detail=error_html)
    except Exception as e:
        logger.exception(f"Error inesperado al cambiar estado del perfil {perfil_id}")
        error_html = f'''<div hx-swap-oob="true" id="form-messages">
  <div class="bg-danger-500 text-white px-4 py-3 rounded-lg transition-all duration-500">
    <p class="font-semibold">✗ Error al cambiar estado del perfil</p>
    <p class="text-sm">Error interno del servidor</p>
  </div>
</div>'''
        raise HTTPException(status_code=500, detail=error_html)


@router.delete("/{perfil_id}", response_class=HTMLResponse, status_code=200)
async def delete_perfil(
    perfil_id: int,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_auth),
):
    """
    Elimina un perfil de cargo y retorna HTML para recargar la lista automáticamente.
    """
    try:
        # Verificar que el perfil pertenece al usuario
        service = ProfileService(db)
        perfil_existente = service.obtener_perfil_por_id(perfil_id)

        if not perfil_existente or perfil_existente.created_by != usuario.id:
            error_html = f'''<div hx-swap-oob="true" id="form-messages">
  <div class="bg-danger-500 text-white px-4 py-3 rounded-lg transition-all duration-500">
    <p class="font-semibold">✗ Error al eliminar</p>
    <p class="text-sm">No se encontró el perfil o no tienes permiso</p>
  </div>
</div>'''
            raise HTTPException(status_code=404, detail=error_html)

        # Verificar si existen análisis asociados al perfil
        num_analisis = db.query(Analisis).filter(Analisis.perfil_id == perfil_id).count()
        if num_analisis > 0:
            error_html = f'''<div hx-swap-oob="true" id="form-messages">
  <div class="bg-danger-500 text-white px-4 py-3 rounded-lg transition-all duration-500">
    <p class="font-semibold">✗ Error al eliminar</p>
    <p class="text-sm">No se puede eliminar el perfil porque tiene {num_analisis} análisis asociados. Elimine los análisis primero.</p>
  </div>
</div>'''
            raise HTTPException(status_code=400, detail=error_html)

        eliminado = service.eliminar_perfil(perfil_id)

        if not eliminado:
            error_html = f'''<div hx-swap-oob="true" id="form-messages">
  <div class="bg-danger-500 text-white px-4 py-3 rounded-lg transition-all duration-500">
    <p class="font-semibold">✗ Error al eliminar</p>
    <p class="text-sm">No se pudo eliminar el perfil</p>
  </div>
</div>'''
            raise HTTPException(status_code=404, detail=error_html)

        # Mensaje de éxito + recarga automática de lista
        success_html = f'''<div hx-swap-oob="true" id="form-messages">
  <div class="bg-success-500 text-white px-4 py-3 rounded-lg transition-all duration-500">
    <p class="font-semibold">✓ Perfil eliminado exitosamente</p>
  </div>
</div>

<div hx-swap-oob="true" id="lista-perfiles-container"
     hx-get="/api/profiles/list"
     hx-trigger="load"
     hx-swap="innerHTML">
  <div class="text-center py-8 text-gray-500">
    <p>Actualizando lista de perfiles...</p>
  </div>
</div>'''

        return success_html

    except ProfileServiceError as e:
        logger.error(f"Error al eliminar perfil {perfil_id}: {e}")
        error_html = f'''<div hx-swap-oob="true" id="form-messages">
  <div class="bg-danger-500 text-white px-4 py-3 rounded-lg transition-all duration-500">
    <p class="font-semibold">✗ Error del servidor</p>
    <p class="text-sm">{str(e)}</p>
  </div>
</div>'''
        raise HTTPException(status_code=500, detail=error_html)
    except Exception as e:
        logger.exception(f"Error inesperado al eliminar perfil {perfil_id}")
        error_html = f'''<div hx-swap-oob="true" id="form-messages">
  <div class="bg-danger-500 text-white px-4 py-3 rounded-lg transition-all duration-500">
    <p class="font-semibold">✗ Error al eliminar perfil</p>
    <p class="text-sm">Error interno del servidor</p>
  </div>
</div>'''
        raise HTTPException(status_code=500, detail=error_html)
