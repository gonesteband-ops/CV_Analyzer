from fastmcp import FastMCP

# 1. Creas la instancia del servidor
mcp = FastMCP("IA-Recruiter-Tools")

# 2. Creas las funciones (Tools) que se conectan al exterior
@mcp.tool()
def obtener_clima(ciudad: str) -> str:
    """Consulta el clima para ayudar en la logística de entrevistas."""
    # Aquí irá tu lógica de conexión a la API de clima
    return f"El clima en {ciudad} es soleado, ideal para una entrevista presencial."

# 3. No necesitas un main complejo, FastMCP se encarga del resto
