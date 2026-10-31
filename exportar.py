# =====================================================================
# exportar.py
# Reportes descargables en CSV, preparados para abrirse con doble clic en Excel:
#   a) Entregas de producción aprobadas (filtro opcional por fechas y área).
#   b) Inventario completo (todos los ítems, también los que están en cero).
#
# ¿Qué es un CSV? Un archivo de texto donde cada línea es una fila y las
# columnas se separan con un carácter. Para Excel en español (Colombia):
#   - el separador es punto y coma (;), porque la coma se usa para los decimales;
#   - se guarda en UTF-8 "con BOM" (una marca invisible al inicio) para que
#     Excel muestre bien las tildes y la ñ.
# Para otros programas (o Excel en inglés) hay un segundo formato: CSV estándar.
#
# Patrones de diseño en este archivo:
#   - GoF Estrategia (Strategy): FORMATOS guarda varias "estrategias" de formato
#     (separador y signo decimal). Se elige una según lo que pida el usuario y el
#     resto del código no cambia. Agregar un formato = agregar una entrada al diccionario.
#   - GoF Método plantilla (Template Method): crear_csv fija SIEMPRE los mismos
#     pasos (encabezados, filas, codificar, nombre con fecha). Cada reporte solo
#     aporta lo que cambia: su nombre, sus encabezados y sus filas.
#   - GRASP Fabricación pura: este módulo no es un concepto del negocio; existe
#     para no mezclar "cómo se arma un archivo" con las reglas de producción.
#   - GRASP Variaciones protegidas: si cambia el formato que pide Excel, solo se
#     toca FORMATOS.
# =====================================================================

import csv
import io
from datetime import date, timedelta

import base_datos

# Las estrategias de formato. Cada una es un diccionario con las mismas claves,
# así crear_csv puede usar cualquiera sin preguntar cuál es (GRASP Polimorfismo).
FORMATOS = {
    "excel": {"nombre": "Excel en español", "separador": ";", "decimal": ","},
    "estandar": {"nombre": "CSV estándar", "separador": ",", "decimal": "."},
}
FORMATO_POR_DEFECTO = "excel"

ENCABEZADOS_ENTREGAS = [
    "Fecha de aprobación", "OP", "Cliente", "Área", "Referencia", "Ítem",
    "Descripción", "Cantidad aprobada", "Reportado por", "Aprobado por",
]
ENCABEZADOS_INVENTARIO = ["Ítem", "Descripción", "Tipo", "Unidad de medida", "Existencia"]


# ---------------------------------------------------------------------
# Elegir la estrategia
# ---------------------------------------------------------------------

def elegir_formato(datos):
    """La estrategia que pidió la página (?formato=excel o ?formato=estandar)."""
    codigo = datos.get("formato", "")
    if codigo == "":
        codigo = FORMATO_POR_DEFECTO
    if codigo not in FORMATOS:
        raise ValueError("Formato no válido. Usa «excel» o «estandar».")
    return FORMATOS[codigo]


# ---------------------------------------------------------------------
# a) Entregas de producción aprobadas
# ---------------------------------------------------------------------

def leer_fecha(datos, campo, nombre):
    """'2026-10-26' (lo que envía un <input type="date">) -> fecha. Si viene vacío -> None."""
    texto = str(datos.get(campo) or "").strip()
    if texto == "":
        return None
    try:
        return date.fromisoformat(texto)
    except ValueError:
        raise ValueError(f"La fecha «{nombre}» no es válida. Usa el formato AAAA-MM-DD.")


def filas_de_entregas(conexion, datos):
    """Las entregas aprobadas como lista de filas (cada fila es una lista de valores)."""
    desde = leer_fecha(datos, "desde", "Desde")
    hasta = leer_fecha(datos, "hasta", "Hasta")
    if desde is not None and hasta is not None and desde > hasta:
        raise ValueError("La fecha «Desde» no puede ser posterior a la fecha «Hasta».")

    sql = (
        "SELECT rp.fecha_revision, o.numero, c.nombre, a.nombre, r.codigo, i.codigo, i.descripcion, "
        "       rp.cantidad, u.nombre_completo, rv.nombre_completo "
        "FROM reportes rp "
        "JOIN ordenes o ON o.id = rp.orden_id "
        "JOIN clientes c ON c.id = o.cliente_id "
        "JOIN areas a ON a.id = rp.area_id "
        "JOIN referencias r ON r.id = rp.referencia_id "
        "JOIN items i ON i.id = r.item_id "
        "JOIN usuarios u ON u.id = rp.reportado_por_id "
        "JOIN usuarios rv ON rv.id = rp.revisado_por_id "
        "WHERE rp.estado = 'APROBADO'"
    )
    valores = []
    # Las fechas se guardan como texto "AAAA-MM-DD HH:MM", así que se pueden comparar como texto:
    # "2026-10-26 14:30" >= "2026-10-26" es verdadero.
    if desde is not None:
        sql += " AND rp.fecha_revision >= ?"
        valores.append(desde.isoformat())
    if hasta is not None:
        # "Hasta" incluye todo ese día: se toma lo anterior al día siguiente.
        sql += " AND rp.fecha_revision < ?"
        valores.append((hasta + timedelta(days=1)).isoformat())
    if datos.get("area", "") != "":
        sql += " AND a.codigo = ?"
        valores.append(datos["area"])
    sql += " ORDER BY rp.fecha_revision, rp.id"

    filas = []
    for fila in conexion.execute(sql, valores).fetchall():
        filas.append(list(fila))      # list() convierte la fila de SQLite en una lista normal
    return filas


def vista_previa_entregas(conexion, usuario, datos):
    """Las mismas filas del archivo, para mostrarlas en pantalla antes de descargar."""
    filas = filas_de_entregas(conexion, datos)
    total_unidades = 0
    for fila in filas:
        total_unidades += fila[7]      # La columna 7 es "Cantidad aprobada"
    return {"encabezados": ENCABEZADOS_ENTREGAS, "filas": filas, "total_unidades": total_unidades}


def exportar_entregas(conexion, usuario, datos):
    filas = filas_de_entregas(conexion, datos)
    formato = elegir_formato(datos)
    # El servidor ve la clave "descarga" y envía un archivo en lugar de JSON.
    return {"descarga": crear_csv("entregas_aprobadas", ENCABEZADOS_ENTREGAS, filas, formato)}


# ---------------------------------------------------------------------
# b) Inventario completo
# ---------------------------------------------------------------------

def exportar_inventario(conexion, usuario, datos):
    """TODOS los ítems (MP, PP y PT), también los que tienen existencia cero."""
    # ORDER BY tipo: alfabéticamente MP < PP < PT, justo el orden que queremos.
    resultado = conexion.execute(
        "SELECT codigo, descripcion, tipo, unidad_medida, existencia FROM items ORDER BY tipo, codigo"
    ).fetchall()
    filas = []
    for fila in resultado:
        filas.append(list(fila))
    formato = elegir_formato(datos)
    return {"descarga": crear_csv("inventario", ENCABEZADOS_INVENTARIO, filas, formato)}


# ---------------------------------------------------------------------
# Crear el archivo CSV (el método plantilla)
# ---------------------------------------------------------------------

def crear_csv(nombre_base, encabezados, filas, formato):
    """Arma el archivo en memoria y devuelve su contenido, su nombre y su tipo.

    Es la "plantilla": los pasos son siempre los mismos, para cualquier reporte
    y con cualquier formato. Lo único que varía llega por parámetro.
    """
    # Paso 1. StringIO es un "archivo de texto en memoria": se escribe en él como
    # en un archivo, pero no se guarda en el disco.
    texto = io.StringIO()
    escritor = csv.writer(texto, delimiter=formato["separador"])
    # Paso 2. Encabezados.
    escritor.writerow(encabezados)
    # Paso 3. Filas, cada valor escrito según la estrategia elegida.
    for fila in filas:
        valores = []
        for valor in fila:
            valores.append(valor_para_csv(valor, formato))
        escritor.writerow(valores)

    # Paso 4. "utf-8-sig" = UTF-8 con BOM: la marca que le dice a Excel que use UTF-8 (tildes y ñ bien).
    contenido = texto.getvalue().encode("utf-8-sig")
    # Paso 5. El nombre lleva la fecha de hoy, por ejemplo: inventario_2026-10-26.csv
    nombre = f"{nombre_base}_{date.today().isoformat()}.csv"
    return {"contenido": contenido, "nombre": nombre, "tipo": "text/csv; charset=utf-8"}


def valor_para_csv(valor, formato):
    """Cómo se escribe cada dato. Los decimales usan el signo de la estrategia:
    coma para Excel en español (2,5) y punto para el CSV estándar (2.5)."""
    if valor is None:
        return ""
    if isinstance(valor, float):
        if valor == int(valor):
            return str(int(valor))                                   # 1680.0 -> "1680"
        return str(round(valor, 6)).replace(".", formato["decimal"])  # 2.5 -> "2,5" o "2.5"
    return str(valor)
