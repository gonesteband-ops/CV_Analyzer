# Tarea 3: Corrección de errores (Rollback parcial de Tarea 1 + Fix batch)

## Problemas detectados

### Error 1: `response_format` incompatible
Qwen agregó `"response_format": {"type": "json_object"}` en groq.py, pero el modelo `llama-3.3-70b-versatile` NO lo soporta. Causa error 400.

### Error 2: Falta campo `puntaje` en el JSON del prompt
Qwen reemplazó el esquema JSON pero eliminó el campo `"puntaje"` que GROQ necesita devolver. Sin ese campo, el código toma valores default y el resultado es incorrecto.

### Error 3: Batch analysis puede timeoutear
El cambio de 202 a 200 es correcto, pero sin `response_format` el análisis funciona, y el batch debe responder. Este error se corrige automáticamente al arreglar el Error 1.

---

## Archivos a modificar

### Archivo 1: `backend/src/services/ia_analyzer/groq.py`

#### Cambio A: Eliminar `response_format`

**Buscar:**
```python
                        "max_tokens": 2500,
                        "response_format": {"type": "json_object"}
```

**Reemplazar por:**
```python
                        "max_tokens": 2500
```

#### Cambio B: Agregar campo `puntaje` al JSON del prompt

**Buscar en `_construir_prompt`:**
```json
{
  "puntaje_tecnico": 0-100,
```

**Reemplazar por:**
```json
{
  "puntaje": 0-100,
  "puntaje_tecnico": 0-100,
```

**Y al final del JSON en el prompt, después de `"justificacion": "Resumen ejecutivo..."` y antes de cerrar las llaves, agregar:**
```json
  "puntaje": 0-100
```

**El JSON completo del prompt debe quedar así:**
```json
{{
  "puntaje": 0-100,
  "puntaje_tecnico": 0-100,
  "puntaje_experiencia": 0-100,
  "puntaje_soft_skills": 0-100,
  "justificacion_tecnico": "Explica el puntaje técnico: habilidades técnicas, herramientas, conocimientos específicos del cargo",
  "justificacion_experiencia": "Explica el puntaje de experiencia: años, nivel seniority, coherencia con el cargo",
  "justificacion_soft_skills": "Explica el puntaje de soft skills: comunicación, liderazgo, trabajo en equipo",
  "sobrecalificado": true o false,
  "cambio_rubro": true o false,
  "razonamiento_inferencia": "ANALISIS OBLIGATORIO PASO A PASO. Escribe aquí tu mapeo semántico. Relaciona la experiencia del CV con las competencias requeridas. Explica qué habilidades implícitas detectaste a partir de las herramientas o cargos mencionados.",
  "etiqueta": "Recomendado" | "Recomendado con reservas" | "No Recomendado",
  "analisis_tecnico": {{
    "puntaje_experiencia": 0-100,
    "puntaje_educacion": 0-100,
    "puntaje_habilidades_tecnicas": 0-100,
    "puntaje_habilidades_blandas": 0-100,
    "anos_experiencia": numero,
    "nivel_educativo": "string",
    "habilidades_directas_detectadas": ["skill1", "skill2"],
    "habilidades_inferidas": ["skill implícita 1", "skill implícita 2"],
    "habilidades_faltantes_criticas": ["skill1"]
  }},
  "fortalezas": ["fortaleza específica 1", "fortaleza específica 2"],
  "debilidades": ["debilidad real, no inventada"],
  "justificacion": "Resumen ejecutivo del porqué de la decisión final.",
  "puntaje": 0-100
}}
```

**Importante: `puntaje` aparece DOS VECES dentro del JSON. Eso es correcto porque GROQ usará el último valor que vea, y el código actual toma `resultado_json.get("puntaje", 50)` de la primera aparición. Para evitar duplicados, dejar solo la PRIMERA aparición (al inicio del JSON).**

**Versión corregida (sin duplicado):**
```json
{{
  "puntaje": 0-100,
  "puntaje_tecnico": 0-100,
  "puntaje_experiencia": 0-100,
  "puntaje_soft_skills": 0-100,
  "justificacion_tecnico": "Explica el puntaje técnico: habilidades técnicas, herramientas, conocimientos específicos del cargo",
  "justificacion_experiencia": "Explica el puntaje de experiencia: años, nivel seniority, coherencia con el cargo",
  "justificacion_soft_skills": "Explica el puntaje de soft skills: comunicación, liderazgo, trabajo en equipo",
  "sobrecalificado": true o false,
  "cambio_rubro": true o false,
  "razonamiento_inferencia": "ANALISIS OBLIGATORIO PASO A PASO. Escribe aquí tu mapeo semántico. Relaciona la experiencia del CV con las competencias requeridas. Explica qué habilidades implícitas detectaste a partir de las herramientas o cargos mencionados.",
  "etiqueta": "Recomendado" | "Recomendado con reservas" | "No Recomendado",
  "analisis_tecnico": {{
    "puntaje_experiencia": 0-100,
    "puntaje_educacion": 0-100,
    "puntaje_habilidades_tecnicas": 0-100,
    "puntaje_habilidades_blandas": 0-100,
    "anos_experiencia": numero,
    "nivel_educativo": "string",
    "habilidades_directas_detectadas": ["skill1", "skill2"],
    "habilidades_inferidas": ["skill implícita 1", "skill implícita 2"],
    "habilidades_faltantes_criticas": ["skill1"]
  }},
  "fortalezas": ["fortaleza específica 1", "fortaleza específica 2"],
  "debilidades": ["debilidad real, no inventada"],
  "justificacion": "Resumen ejecutivo del porqué de la decisión final."
}}
```

#### Cambio C: Asegurar que el cálculo use `puntaje` como fallback

**Buscar en `analizar_cv`:**
```python
            puntaje_tecnico = resultado_json.get("puntaje_tecnico", 50)
            puntaje_experiencia = resultado_json.get("puntaje_experiencia", 50)
            puntaje_soft_skills = resultado_json.get("puntaje_soft_skills", 50)
```

**Reemplazar por:**
```python
            # Usar puntaje general como base, o los dimensionales si existen
            puntaje_general = resultado_json.get("puntaje", 50)
            puntaje_tecnico = resultado_json.get("puntaje_tecnico", puntaje_general)
            puntaje_experiencia = resultado_json.get("puntaje_experiencia", puntaje_general)
            puntaje_soft_skills = resultado_json.get("puntaje_soft_skills", puntaje_general)
```

---

### Archivo 2: `backend/src/api/routes/cvs.py` (sin cambios)

El cambio de `202` a `200` ya está hecho correctamente. No necesita modificación.

---

## Verificación

```bash
# 1. Compilar groq.py
cd backend/src
python -m py_compile services/ia_analyzer/groq.py

# 2. Probar GROQ directo (debe responder sin 400)
python -c "import httpx, asyncio; r = asyncio.run(httpx.AsyncClient().post('https://api.groq.com/openai/v1/chat/completions', headers={'Authorization': 'Bearer ' + open('../.env').read().split('GROQ_API_KEY=')[1].split()[0], 'Content-Type': 'application/json'}, json={'model': 'llama-3.3-70b-versatile', 'messages': [{'role': 'user', 'content': 'di OK'}], 'temperature': 0})); print('STATUS:', r.status_code); print('TEXTO:', r.text[:100])"

# 3. Probar análisis con un CV de prueba
python -c "import sys; sys.path.insert(0,'src'); import asyncio; from services.ia_analyzer.groq import GroqAdapter; from core.config import settings; g=GroqAdapter(api_key=settings.groq_api_key); r=asyncio.run(g.analizar_cv('Soy candidato con Power BI y SQL. Trabaje como analista de datos por 5 años.', 'Senior Data Analyst', 'Analista senior con Power BI', ['DAX','Modelamiento de Datos','Power BI'])); print('PUNTAJE:', r.puntaje); print('PONDERADO:', r.ponderado_final); print('TECNICO:', r.puntaje_tecnico); print('EXPERIENCIA:', r.puntaje_experiencia); print('SOFT:', r.puntaje_soft_skills)"
```

---

## Resumen de cambios

| Archivo | Cambio | Línea aprox |
|---------|--------|-------------|
| `groq.py` | Eliminar `response_format` | ~68 |
| `groq.py` | Agregar `"puntaje": 0-100` al JSON del prompt | ~76 |
| `groq.py` | Cambiar default de puntajes a usar `puntaje` como fallback | ~80-83 |