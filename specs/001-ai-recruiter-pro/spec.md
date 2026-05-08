# Especificación de Funcionalidad: AI-Recruiter Pro (Edición Call Center)

**Rama de Funcionalidad**: `001-ai-recruiter-pro`
**Creado**: 2026-04-23
**Estado**: Borrador
**Entrada**: Descripción del usuario: "Especificación Técnica: AI-Recruiter Pro (Call Center Edition) - Automatizar la revisión masiva de CVs para una empresa de Call Center"

## Escenarios de Usuario y Pruebas

### Historia de Usuario 1 - Carga y Análisis Masivo de CVs (Prioridad: P1)

Como reclutador, quiero cargar múltiples archivos de CV simultáneamente y que sean analizados automáticamente contra un perfil de cargo seleccionado, para poder identificar rápidamente candidatos adecuados sin revisar manualmente cada CV.

**Por qué esta prioridad**: Esta es la propuesta de valor central del sistema. Sin el análisis automatizado de CVs, los reclutadores deben revisar manualmente cada CV, lo cual consume mucho tiempo y derrota el propósito de la automatización con IA.

**Prueba Independiente**: Cargar 10+ archivos de CV en formatos comunes (PDF, DOCX, TXT) mediante arrastrar-y-soltar, seleccionar un perfil de cargo, y verificar que cada CV reciba un puntaje, etiqueta de recomendación, y retroalimentación dentro de 2 minutos.

**Escenarios de Aceptación**:

1. **Dado** que estoy autenticado y en la página de Inicio, **Cuando** arrastro y suelto 5 archivos de CV en la zona de carga, **Entonces** cada archivo muestra una barra de progreso individual y se carga exitosamente
2. **Dado** que los CVs están cargados, **Cuando** selecciono un perfil de cargo e inicio el análisis, **Entonces** cada CV muestra un puntaje (0-100), una etiqueta de recomendación, y retroalimentación detallada
3. **Dado** que el análisis está completo, **Cuando** veo la tabla de resultados, **Entonces** puedo ver todos los CVs con sus puntajes ordenados de mayor a menor

---

### Historia de Usuario 2 - Creación de Perfiles de Cargo (Prioridad: P2)

Como gerente de contratación, quiero crear perfiles de cargo detallados con títulos, descripciones y fortalezas/consejos clave, para que la IA pueda emparejar candidatos con precisión a los requisitos específicos de cada rol.

**Por qué esta prioridad**: Los perfiles de cargo son el estándar de referencia contra el cual se evalúan todos los CVs. Sin perfiles bien definidos, la IA no puede proporcionar puntajes de emparejamiento significativos.

**Prueba Independiente**: Crear un nuevo perfil de cargo para "Ejecutivo de Ventas" con descripción y 3 fortalezas clave, guardarlo, y verificar que aparezca en el menú desplegable de selección de perfiles para análisis de CV.

**Escenarios de Aceptación**:

1. **Dado** que estoy en la página de Perfiles, **Cuando** completo Título, Descripción y Puntos Fuertes para un nuevo cargo, **Entonces** el perfil se guarda y está disponible para selección
2. **Dado** que existen múltiples perfiles, **Cuando** creo un nuevo perfil para "Cobranzas", **Entonces** aparece junto a los perfiles existentes (SAC, Ventas, Soporte)
3. **Dado** que un perfil está seleccionado para análisis, **Cuando** veo sus detalles, **Entonces** todos los campos (título, descripción, fortalezas) se muestran correctamente

---

### Historia de Usuario 3 - Revisión Histórica y Exportación (Prioridad: P3)

Como reclutador, quiero acceder a una tabla histórica de todos los CVs analizados con filtros avanzados y capacidades de exportación, para poder hacer seguimiento a candidatos en el tiempo y compartir resultados con mi equipo.

**Por qué esta prioridad**: Los reclutadores necesitan revisar candidatos pasados, comparar lotes en el tiempo, y exportar datos para reportes o colaboración con otras partes interesadas.

**Prueba Independiente**: Navegar a la página Histórico, aplicar filtros por tipo de perfil y rango de fechas, buscar un candidato específico por nombre, y exportar resultados filtrados a formato XLSX.

**Escenarios de Aceptación**:

1. **Dado** que estoy en la página Histórico, **Cuando** aplico filtros para perfiles "Ventas" de los últimos 30 días, **Entonces** solo los CVs coincidentes se muestran en la tabla
2. **Dado** que los resultados filtrados se muestran, **Cuando** busco un nombre de candidato "María González", **Entonces** los registros coincidentes aparecen instantáneamente
3. **Dado** que los resultados están filtrados, **Cuando** hago clic en Exportar a XLSX, **Entonces** un archivo Excel descargable contiene todos los datos visibles con formato adecuado

---

### Historia de Usuario 4 - Gestión de Integración con Portales de Empleo (Prioridad: P4)

Como reclutador administrador, quiero configurar credenciales para portales de empleo externos (Laborum, Trabajando), para que el sistema eventualmente pueda obtener datos de candidatos directamente desde estas fuentes.

**Por qué esta prioridad**: Aunque la integración está preparada para implementación futura, tener la estructura de gestión de credenciales en su lugar permite una activación fluida cuando se obtenga acceso a las APIs.

**Prueba Independiente**: Navegar a la sección Portales de Empleo, ingresar credenciales de prueba para los portales Laborum y Trabajando, guardar la configuración, y verificar que las credenciales se almacenan de forma segura.

**Escenarios de Aceptación**:

1. **Dado** que estoy en la página Portales de Empleo, **Cuando** ingreso credenciales Cliente/Usuario para Laborum, **Entonces** se guardan y pueden actualizarse después
2. **Dado** que las credenciales están configuradas, **Cuando** veo el estado del portal, **Entonces** puedo ver qué portales están listos para integración vs. pendientes de configuración

---

### Historia de Usuario 5 - Colaboración en Equipo y Recuperación de Acceso (Prioridad: P5)

Como reclutador de equipo, quiero tener sesiones de inicio de sesión individuales mientras accedo a datos compartidos del equipo, y poder recuperar mi contraseña si la olvido, para que múltiples reclutadores puedan colaborar y mantenerse la cobertura.

**Por qué esta prioridad**: La contratación en call center es frecuentemente un esfuerzo de equipo con turnos de cobertura. Los reclutadores necesitan acceder a datos históricos dejados por colegas y recuperar acceso sin intervención administrativa.

**Prueba Independiente**: Crear dos cuentas de usuario, iniciar sesión como Usuario A, cargar y analizar CVs, cerrar sesión, iniciar sesión como Usuario B, verificar que Usuario B puede ver todos los CVs del equipo, luego probar el flujo de recuperación de contraseña para Usuario A.

**Escenarios de Aceptación**:

1. **Dado** que tengo una cuenta registrada, **Cuando** inicio sesión con email/contraseña, **Entonces** veo un mensaje de bienvenida personalizado con mi nombre
2. **Dado** que olvidé mi contraseña, **Cuando** solicito recuperación de contraseña vía email, **Entonces** recibo instrucciones para restablecer mi contraseña
3. **Dado** que múltiples reclutadores han cargado CVs, **Cuando** inicio sesión, **Entonces** puedo ver y filtrar todos los CVs del equipo en la tabla Histórico

---

### Casos de Borde

- ¿Qué sucede cuando un archivo de CV está corrupto o en un formato no soportado? El sistema muestra un mensaje de error para ese archivo específico mientras continúa procesando los otros archivos del lote
- ¿Cómo maneja el sistema CVs en idiomas distintos al español? El sistema analiza CVs en español principalmente; los CVs en inglés pueden tener precisión reducida en el emparejamiento
- ¿Qué sucede cuando la IA no puede generar un puntaje significativo (ej. CV extremadamente corto con información mínima)? El sistema muestra la etiqueta "Información Insuficiente" en lugar de un puntaje numérico
- ¿Cómo se comporta el sistema cuando se pierde la conectividad a internet durante la carga de lotes? La carga se pausa y puede reanudarse; los archivos parcialmente cargados muestran el estado de progreso
- ¿Qué sucede cuando dos reclutadores cargan CVs simultáneamente? Cada carga se procesa independientemente; la tabla histórica muestra todas las cargas con marca de tiempo e identificación del reclutador
- ¿Qué retroalimentación visual indica los niveles de puntaje? La visualización de puntaje usa un gradiente de color desde rojo (bajo) pasando por amarillo (medio) hasta verde (alto)

## Requisitos

### Requisitos Funcionales

- **FR-001**: El sistema DEBE permitir a los usuarios cargar múltiples archivos de CV simultáneamente mediante interfaz de arrastrar-y-soltar
- **FR-002**: El sistema DEBE mostrar barras de progreso individuales para cada archivo durante la carga
- **FR-003**: El sistema DEBE permitir a los usuarios crear perfiles de cargo con campos Título, Descripción y Puntos Fuertes/Consejos
- **FR-004**: El sistema DEBE analizar cada CV cargado contra un perfil de cargo seleccionado y generar un puntaje de emparejamiento (0-100)
- **FR-005**: El sistema DEBE clasificar cada CV con una etiqueta según umbrales configurables en el perfil de cargo: "Recomendado" (puntaje ≥ umbral_recomendado), "Recomendado con reservas" (puntaje ≥ umbral_reservas), o "No Recomendado" (puntaje < umbral_reservas)
- **FR-006**: El sistema DEBE generar texto de retroalimentación detallado describiendo fortalezas y debilidades del candidato relativas al perfil de cargo
- **FR-007**: El sistema DEBE reintentar automáticamente análisis fallidos con backoff exponencial (3 intentos) y notificar al usuario si falla permanentemente
- **FR-008**: El sistema DEBE mostrar resultados de análisis de CV en un formato de tabla profesional con visualización de puntaje codificada por colores (gradiente rojo → amarillo → verde)
- **FR-009**: El sistema DEBE persistir todos los resultados de análisis de CV en una tabla histórica accesible desde la página Histórico
- **FR-010**: El sistema DEBE proporcionar filtros avanzados en la tabla histórica por tipo de perfil, rango de fechas, rango de puntajes, y etiqueta de recomendación
- **FR-011**: El sistema DEBE proporcionar una función de búsqueda en la tabla histórica para encontrar candidatos por nombre u otros atributos
- **FR-012**: El sistema DEBE permitir exportar datos filtrados de la tabla histórica a formato XLSX con formato corporativo: headers en azul #2F4DAA con texto blanco y bold, filas alternas gris claro, puntajes con conditional formatting (verde/amarillo/rojo), columnas auto-ajustadas
- **FR-013**: El sistema DEBE proporcionar una sección Portales de Empleo para configurar credenciales de API (Cliente/Usuario) para Laborum y Trabajando
- **FR-014**: El sistema DEBE requerir autenticación de usuario vía email/contraseña antes de acceder a cualquier funcionalidad
- **FR-015**: El sistema DEBE mostrar mensaje de bienvenida personalizado con el nombre del usuario en la página de Inicio
- **FR-016**: El sistema DEBE proporcionar flujo de recuperación de contraseña vía email para usuarios que olvidaron sus credenciales
- **FR-017**: El sistema DEBE mantener sesiones de usuario individuales mientras permite a todos los miembros del equipo acceder a datos compartidos de CVs
- **FR-018**: El sistema DEBE mostrar una navegación de barra lateral izquierda fija con secciones: Inicio, Perfiles, Portales de Empleo, Histórico
- **FR-019**: El sistema DEBE usar colores corporativos de marca consistentemente en toda la interfaz
- **FR-020**: El sistema DEBE ser responsivo y adaptar diseños de tabla para diferentes tamaños de pantalla
- **FR-021**: El sistema DEBE operar en la zona horaria local y mostrar fechas/tiempos y moneda en formato local

### Entidades Clave

- **Usuario**: Reclutador o gerente de contratación con email, contraseña, nombre, y rol dentro del equipo
- **Perfil de Cargo**: Definición de perfil de cargo con título, descripción, puntos_fuertes (fortalezas/consejos clave), y umbrales configurables de clasificación (puntaje_min_recomendado, puntaje_min_reservas)
- **CV**: Curriculum vitae del candidato con metadatos del archivo, contenido de texto extraído, y marca de tiempo de carga
- **Análisis**: Resultado de emparejamiento entre un CV y un Perfil de Cargo, conteniendo puntaje (0-100), etiqueta, y narrativa de retroalimentación
- **CredencialPortal**: Credenciales de API almacenadas (cliente, usuario, contraseña/token) para portales de empleo externos como Laborum y Trabajando

## Criterios de Éxito

### Resultados Medibles

- **SC-001**: Los reclutadores pueden cargar y recibir resultados de análisis para 50 CVs en menos de 5 minutos de principio a fin
- **SC-002**: El sistema clasifica candidatos que coinciden con perfiles de cargo con 85% de tasa de acuerdo comparado con revisión manual de reclutador senior
- **SC-003**: 90% de los reclutadores reportan tiempo reducido en cribado inicial de CVs (de horas a minutos por lote)
- **SC-004**: El sistema soporta 10+ usuarios concurrentes cargando y analizando CVs sin degradación del rendimiento
- **SC-005**: 95% de las cargas de CV se completan exitosamente en el primer intento sin errores o reintentos
- **SC-006**: Las búsquedas en la tabla histórica devuelven resultados en menos de 2 segundos para conjuntos de datos de hasta 10,000 CVs
- **SC-007**: Los emails de recuperación de contraseña se entregan dentro de 2 minutos de la solicitud
- **SC-008**: Los archivos XLSX exportados contienen 100% de los datos filtrados con formato adecuado y sin pérdida de datos

## Supuestos

- Los usuarios tienen conectividad estable a internet y navegadores web modernos (Chrome, Firefox, Edge, Safari)
- Los archivos de CV están principalmente en español; los CVs en otros idiomas pueden tener precisión de emparejamiento reducida
- Los formatos de CV soportados incluyen PDF, DOCX, y TXT; otros formatos pueden no procesarse correctamente
- El motor de análisis de IA debe seguir el patrón Adapter con interfaz única `IAnalizadorIA`, permitiendo cambiar entre proveedores (Deepseek, OpenAI, local) mediante configuración sin modificar el código de negocio
- El algoritmo de matching usa enfoque híbrido: 70% similitud semántica (embeddings) + 30% coverage de keywords explícitas del perfil de cargo
- Los umbrales de clasificación son configurables por cada Perfil de Cargo, permitiendo ajustar estándares de selección por rol
- Los portales de empleo (Laborum, Trabajando) proporcionarán documentación de API y credenciales cuando la integración se active
- El sistema debe manejar fallos del proveedor IA con cola de reintentos (3 intentos, backoff exponencial) y notificación al usuario si falla permanentemente
- El modelo de colaboración de equipo asume que todos los reclutadores dentro de una empresa deben tener acceso a todos los datos de CV; no se requiere aislamiento de datos por usuario
- El despliegue inicial usa SQLite por simplicidad; la base de datos puede migrarse a PostgreSQL o MySQL para escala de producción
- Los usuarios crearán perfiles de cargo significativos con suficiente detalle para el emparejamiento de IA; aplica basura-entra-basura-sale
- El soporte móvil está limitado a diseño responsivo; aplicaciones móviles nativas están fuera del alcance para v1
- El sistema no publica automáticamente ofertas en portales; solo analiza CVs entrantes

## Clarificaciones

### Session 2026-04-23

- Q: ¿Qué nivel de abstracción requiere el motor de IA para considerar que es "fácil de cambiar"? → A: Adapter pattern con interfaz única `IAnalizadorIA`
- Q: ¿Qué significa "comparación simple" para el algoritmo de matching de CVs? → A: Embeddings + keywords ponderados (70/30)
- Q: ¿Los umbrales de clasificación (70/40) son fijos o configurables? → A: Configurables por perfil de cargo
- Q: ¿Cómo manejar fallos del proveedor IA externo durante el análisis? → A: Cola de reintentos con notificación (3 intentos, backoff exponencial)
- Q: ¿Qué nivel de formato debe tener el Excel exportado? → A: Formato corporativo completo (headers azul #2F4DAA, puntajes con conditional formatting)
