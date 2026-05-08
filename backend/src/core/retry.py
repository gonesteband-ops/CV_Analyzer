"""
Cola de reintentos con backoff exponencial.
Maneja fallos transitorios en proveedores de IA externos.
"""
import asyncio
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Coroutine, Optional

logger = logging.getLogger(__name__)


class EstadoReintento(Enum):
    """Estado de un reintento en la cola."""
    PENDIENTE = "pending"
    EN_PROGRESO = "in_progress"
    COMPLETADO = "completed"
    FALLIDO = "failed"
    CANCELADO = "cancelled"


@dataclass
class ReintentoTask:
    """
    Representa una tarea de reintento en la cola.
    
    Attributes:
        id: Identificador único de la tarea.
        funcion: Función asíncrona a reintentar.
        args: Argumentos posicionales para la función.
        kwargs: Argumentos nombrados para la función.
        max_reintentos: Máximo número de reintentos (default: 3).
        intento_actual: Número de intento actual (0-based).
        estado: Estado actual de la tarea.
        ultimo_error: Último error capturado.
        creado_en: Timestamp de creación.
        proximo_intento: Timestamp del próximo intento permitido.
        resultado: Resultado de la ejecución (si completó).
    """
    id: str
    funcion: Callable[..., Coroutine[Any, Any, Any]]
    args: tuple = field(default_factory=tuple)
    kwargs: dict = field(default_factory=dict)
    max_reintentos: int = 3
    intento_actual: int = 0
    estado: EstadoReintento = EstadoReintento.PENDIENTE
    ultimo_error: Optional[Exception] = None
    creado_en: datetime = field(default_factory=datetime.utcnow)
    proximo_intento: datetime = field(default_factory=datetime.utcnow)
    resultado: Any = None
    metadata: dict = field(default_factory=dict)  # Metadata adicional (cv_id, perfil_id, etc.)
    
    def calcular_backoff(self) -> float:
        """
        Calcula el tiempo de espera con backoff exponencial.
        
        Fórmula: base_delay * (2 ^ intento) + jitter
        
        Returns:
            float: Segundos de espera antes del próximo intento.
        """
        import random
        
        base_delay = 1.0  # 1 segundo base
        max_delay = 300.0  # Máximo 5 minutos
        
        # Backoff exponencial: 1s, 2s, 4s, 8s, 16s...
        delay = base_delay * (2 ** self.intento_actual)
        
        # Agregar jitter aleatorio (±20%) para evitar thundering herd
        jitter = delay * 0.2 * random.random()
        delay = delay + jitter
        
        # Limitar a máximo
        delay = min(delay, max_delay)
        
        logger.debug(f"Backoff calculado: {delay:.2f}s (intento {self.intento_actual})")
        
        return delay
    
    def puede_reintentar(self) -> bool:
        """
        Verifica si la tarea puede ser reintentada.
        
        Returns:
            bool: True si puede reintentar, False si alcanzó el máximo.
        """
        return (
            self.estado in [EstadoReintento.PENDIENTE, EstadoReintento.EN_PROGRESO] and
            self.intento_actual < self.max_reintentos
        )
    
    def marcar_completado(self, resultado: Any) -> None:
        """Marca la tarea como completada con éxito."""
        self.estado = EstadoReintento.COMPLETADO
        self.resultado = resultado
        logger.info(f"Tarea {self.id} completada exitosamente en intento {self.intento_actual + 1}")
    
    def marcar_fallido(self, error: Exception) -> None:
        """Marca la tarea como fallida y calcula próximo intento."""
        self.ultimo_error = error
        self.intento_actual += 1
        
        if self.intento_actual >= self.max_reintentos:
            self.estado = EstadoReintento.FALLIDO
            logger.error(f"Tarea {self.id} falló después de {self.max_reintentos} intentos")
        else:
            self.estado = EstadoReintento.PENDIENTE
            self.proximo_intento = datetime.utcnow() + timedelta(seconds=self.calcular_backoff())
            logger.warning(
                f"Tarea {self.id} falló (intento {self.intento_actual}/{self.max_reintentos}). "
                f"Próximo intento en {self.calcular_backoff():.2f}s"
            )


class RetryQueue:
    """
    Cola de reintentos con backoff exponencial.
    
    Características:
    - Máximo 3 reintentos por defecto
    - Backoff exponencial con jitter
    - Procesamiento asíncrono en background
    - Callbacks para éxito/fallo
    - Métricas de reintentos
    """
    
    def __init__(self, max_concurrent: int = 10):
        """
        Inicializa la cola de reintentos.
        
        Args:
            max_concurrent: Máximo de tareas concurrentes.
        """
        self.max_concurrent = max_concurrent
        self._cola: list[ReintentoTask] = []
        self._en_proceso: set[str] = set()
        self._completadas: dict[str, ReintentoTask] = {}
        self._running = False
        self._task: Optional[asyncio.Task] = None
        
        # Métricas
        self._metricas = {
            "total_enqueued": 0,
            "total_completed": 0,
            "total_failed": 0,
            "total_retries": 0,
        }
    
    async def start(self) -> None:
        """Inicia el procesador de la cola en background."""
        if self._running:
            return
        
        self._running = True
        self._task = asyncio.create_task(self._procesar_cola())
        logger.info("Cola de reintentos iniciada")
    
    async def stop(self) -> None:
        """Detiene el procesador de la cola."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Cola de reintentos detenida")
    
    async def enqueue(
        self,
        task_id: str,
        funcion: Callable[..., Coroutine[Any, Any, Any]],
        *args: Any,
        max_reintentos: int = 3,
        metadata: Optional[dict] = None,
        **kwargs: Any,
    ) -> ReintentoTask:
        """
        Agrega una tarea a la cola de reintentos.
        
        Args:
            task_id: Identificador único de la tarea.
            funcion: Función asíncrona a ejecutar.
            *args: Argumentos para la función.
            max_reintentos: Máximo de reintentos (default: 3).
            metadata: Metadata adicional (cv_id, perfil_id, etc.).
            **kwargs: Argumentos nombrados para la función.
            
        Returns:
            ReintentoTask: Tarea creada.
        """
        task = ReintentoTask(
            id=task_id,
            funcion=funcion,
            args=args,
            kwargs=kwargs,
            max_reintentos=max_reintentos,
            metadata=metadata or {},
        )
        
        self._cola.append(task)
        self._en_proceso.add(task_id)
        self._metricas["total_enqueued"] += 1
        
        logger.info(f"Tarea {task_id} encolada para reintento (max: {max_reintentos})")
        
        return task
    
    async def _procesar_cola(self) -> None:
        """Procesa la cola de reintentos en background."""
        while self._running:
            try:
                # Obtener tareas listas para ejecutar
                tareas_listas = [
                    task for task in self._cola
                    if (
                        task.estado == EstadoReintento.PENDIENTE and
                        datetime.utcnow() >= task.proximo_intento and
                        task.id not in self._en_proceso
                    )
                ]
                
                # Limitar concurrentes
                tareas_a_ejecutar = tareas_listas[:self.max_concurrent]
                
                if not tareas_a_ejecutar:
                    await asyncio.sleep(0.5)  # Sleep corto para no busy-wait
                    continue
                
                # Ejecutar tareas en paralelo
                await asyncio.gather(
                    *[self._ejecutar_tarea(task) for task in tareas_a_ejecutar],
                    return_exceptions=True,
                )
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error en procesador de cola: {e}")
                await asyncio.sleep(1)
    
    async def _ejecutar_tarea(self, task: ReintentoTask) -> None:
        """
        Ejecuta una tarea de la cola.
        
        Args:
            task: Tarea a ejecutar.
        """
        self._en_proceso.add(task.id)
        task.estado = EstadoReintento.EN_PROGRESO
        
        try:
            logger.info(f"Ejecutando tarea {task.id} (intento {task.intento_actual + 1}/{task.max_reintentos})")
            
            # Ejecutar función
            resultado = await task.funcion(*task.args, **task.kwargs)
            
            # Marcar como completada
            task.marcar_completado(resultado)
            self._metricas["total_completed"] += 1
            
        except Exception as e:
            # Marcar como fallida y calcular próximo reintento
            task.marcar_fallido(e)
            self._metricas["total_retries"] += 1
            
            if task.estado == EstadoReintento.FALLIDO:
                self._metricas["total_failed"] += 1
                # Llamar callback de fallo si existe
                if "on_failure" in task.kwargs and callable(task.kwargs["on_failure"]):
                    try:
                        await task.kwargs["on_failure"](task.id, e, task.intento_actual)
                    except Exception as callback_error:
                        logger.error(f"Error en callback de fallo: {callback_error}")
        
        finally:
            self._en_proceso.discard(task.id)
            self._completadas[task.id] = task
            
            # Limpiar cola de tareas completadas (mantener últimas 100)
            if len(self._completadas) > 100:
                oldest_keys = list(self._completadas.keys())[:10]
                for key in oldest_keys:
                    del self._completadas[key]
    
    def obtener_estado(self, task_id: str) -> Optional[EstadoReintento]:
        """
        Obtiene el estado de una tarea.
        
        Args:
            task_id: ID de la tarea.
            
        Returns:
            EstadoReintento o None si no existe.
        """
        # Buscar en cola activa
        for task in self._cola:
            if task.id == task_id:
                return task.estado
        
        # Buscar en completadas
        if task_id in self._completadas:
            return self._completadas[task_id].estado
        
        return None
    
    def obtener_metricas(self) -> dict:
        """
        Obtiene métricas de la cola.
        
        Returns:
            dict: Métricas de reintentos.
        """
        return {
            **self._metricas,
            "pending": len([t for t in self._cola if t.estado == EstadoReintento.PENDIENTE]),
            "in_progress": len(self._en_proceso),
            "completed": self._metricas["total_completed"],
            "failed": self._metricas["total_failed"],
        }
    
    async def ejecutar_con_reintentos(
        self,
        task_id: str,
        funcion: Callable[..., Coroutine[Any, Any, Any]],
        *args: Any,
        max_reintentos: int = 3,
        metadata: Optional[dict] = None,
        **kwargs: Any,
    ) -> Any:
        """
        Ejecuta una función con reintentos inmediatos (blocking).
        
        Útil para casos donde se necesita el resultado inmediatamente
        en lugar de usar la cola asíncrona.
        
        Args:
            task_id: Identificador único.
            funcion: Función a ejecutar.
            *args: Argumentos para la función.
            max_reintentos: Máximo de reintentos.
            metadata: Metadata adicional.
            **kwargs: Argumentos nombrados.
            
        Returns:
            Resultado de la función.
            
        Raises:
            Exception: Si falla después de todos los reintentos.
        """
        task = ReintentoTask(
            id=task_id,
            funcion=funcion,
            args=args,
            kwargs=kwargs,
            max_reintentos=max_reintentos,
            metadata=metadata or {},
        )
        
        ultimo_error = None
        
        while task.puede_reintentar():
            try:
                logger.info(f"Ejecutando {task_id} (intento {task.intento_actual + 1}/{max_reintentos})")
                resultado = await funcion(*args, **kwargs)
                task.marcar_completado(resultado)
                return resultado
                
            except Exception as e:
                ultimo_error = e
                task.marcar_fallido(e)
                
                if task.puede_reintentar():
                    backoff = task.calcular_backoff()
                    logger.warning(f"Reintentando en {backoff:.2f}s...")
                    await asyncio.sleep(backoff)
        
        # Si llegamos aquí, falló todos los intentos
        logger.error(f"{task_id} falló después de {max_reintentos} intentos")
        raise ultimo_error


# Instancia global de la cola de reintentos
retry_queue = RetryQueue(max_concurrent=10)


async def iniciar_retry_queue() -> None:
    """Inicializa y arranca la cola de reintentos global."""
    await retry_queue.start()
    logger.info("Cola de reintentos global iniciada")


async def detener_retry_queue() -> None:
    """Detiene la cola de reintentos global."""
    await retry_queue.stop()
    logger.info("Cola de reintentos global detenida")
