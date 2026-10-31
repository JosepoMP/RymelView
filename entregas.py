# =====================================================================
# entregas.py
# Lo que pasa después de crear una OP:
#   - Módulo 1: cada área reporta lo que entregó (queda PENDIENTE de revisión).
#   - Módulo 2: el analista aprueba (y se mueve el inventario) o rechaza.
#   - Módulo 3: panel del supervisor (estado de cada área en cada OP).
# El inventario (Módulo 6) está en inventario.py.
# Las funciones de la API tienen la forma (conexion, usuario, datos).
#
# Patrones de diseño en este archivo:
#   - GRASP Experto en información: avance_del_area y calcular_consumos están
#     aquí porque este módulo es el que conoce los reportes de entrega.
#   - GRASP Bajo acoplamiento: para mover el inventario no escribe SQL sobre
#     items ni movimientos; usa la fachada de inventario.py.
# =====================================================================

import base_datos
import inventario
from catalogo import leer_entero, leer_materiales, leer_texto
from ordenes import avance_por_area, buscar_orden, sumar_reportes


# ---------------------------------------------------------------------
# Lo que le toca a un área en una OP
# ---------------------------------------------------------------------

def requerimiento_del_area(conexion, orden, area_id):
    """Qué referencia fabrica el área en esta OP y cuántas unidades debe entregar."""
    fila = conexion.execute(
        "SELECT rq.cantidad_requerida, r.id AS referencia_id, r.codigo AS referencia, r.descripcion, "
        "       i.codigo AS item_codigo, i.tipo AS item_tipo, i.unidad_medida "
        "FROM requerimientos rq "
        "JOIN referencias r ON r.id = rq.referencia_id "
        "JOIN items i ON i.id = r.item_id "
        "WHERE rq.orden_id = ? AND rq.area_id = ?",
        (orden["id"], area_id),
    ).fetchone()
    if fila is None:
        raise ValueError(f"La OP {orden['numero']} no tiene nada que entregar para tu área.")
    return dict(fila)


def avance_del_area(conexion, orden, area_id):
    """Lo requerido, lo aprobado, lo que está en revisión y cuánto se puede reportar todavía."""
    avance = requerimiento_del_area(conexion, orden, area_id)
    avance["aprobadas"] = sumar_reportes(conexion, orden["id"], area_id, "APROBADO")
    avance["en_revision"] = sumar_reportes(conexion, orden["id"], area_id, "PENDIENTE")
    # Lo que está en revisión también cuenta: así nadie reporta dos veces lo mismo
    # mientras el analista revisa. Lo rechazado NO cuenta: se puede volver a reportar.
    disponible = avance["cantidad_requerida"] - avance["aprobadas"] - avance["en_revision"]
    avance["disponible"] = max(disponible, 0)
    return avance


# ---------------------------------------------------------------------
# Módulo 1: reporte de entregas (rol Área)
# ---------------------------------------------------------------------

def consultar_orden_para_area(conexion, usuario, datos):
    """Lo que ve el operario al buscar una OP: su referencia, sus materiales y su avance."""
    orden = buscar_orden(conexion, leer_texto(datos, "numero", "Número de OP"))
    avance = avance_del_area(conexion, orden, usuario["area_id"])
    avance["materiales"] = leer_materiales(conexion, avance["referencia_id"])
    return {"orden": orden, "avance": avance}


def crear_reporte(conexion, usuario, datos):
    orden = buscar_orden(conexion, leer_texto(datos, "orden", "Número de OP"))
    cantidad = leer_entero(datos.get("cantidad"), "La cantidad entregada")
    avance = avance_del_area(conexion, orden, usuario["area_id"])

    # Validación contra la OP: no se puede reportar más de lo que falta.
    if cantidad > avance["disponible"]:
        raise ValueError(
            f"Solo puedes reportar hasta {avance['disponible']} und. "
            f"(requerido en la OP {avance['cantidad_requerida']}, aprobado {avance['aprobadas']}, "
            f"en revisión {avance['en_revision']})."
        )

    cursor = conexion.execute(
        "INSERT INTO reportes (orden_id, area_id, referencia_id, cantidad, estado, reportado_por_id, fecha_reporte) "
        "VALUES (?, ?, ?, ?, 'PENDIENTE', ?, ?)",
        (orden["id"], usuario["area_id"], avance["referencia_id"], cantidad, usuario["id"], base_datos.fecha_actual()),
    )
    return {"id": cursor.lastrowid, "orden": orden["numero"], "cantidad": cantidad}


# ---------------------------------------------------------------------
# Consulta de reportes (todos los roles)
# ---------------------------------------------------------------------

SQL_REPORTES = """
    SELECT rp.id, rp.cantidad, rp.estado, rp.motivo_rechazo, rp.fecha_reporte, rp.fecha_revision,
           rp.orden_id, o.numero AS orden, a.codigo AS area_codigo, a.nombre AS area,
           r.id AS referencia_id, r.codigo AS referencia, r.descripcion,
           i.id AS item_id, i.codigo AS item_codigo, i.descripcion AS item_descripcion,
           i.unidad_medida, i.existencia AS item_existencia,
           u.nombre_completo AS reportado_por, rv.nombre_completo AS revisado_por
    FROM reportes rp
    JOIN ordenes o ON o.id = rp.orden_id
    JOIN areas a ON a.id = rp.area_id
    JOIN referencias r ON r.id = rp.referencia_id
    JOIN items i ON i.id = r.item_id
    JOIN usuarios u ON u.id = rp.reportado_por_id
    LEFT JOIN usuarios rv ON rv.id = rp.revisado_por_id
"""
# LEFT JOIN en "rv" (quien revisó): un reporte pendiente todavía no tiene revisor,
# y con un JOIN normal ese reporte no aparecería.


def listar_reportes(conexion, usuario, datos):
    """Reportes filtrados por estado, área y OP. Cada área ve SOLO los suyos."""
    sql = SQL_REPORTES + " WHERE 1 = 1"
    valores = []

    if usuario["rol"] == "AREA":
        # Este filtro lo pone el servidor, no la página: un operario no puede ver otras áreas.
        sql += " AND rp.area_id = ?"
        valores.append(usuario["area_id"])
    elif datos.get("area", "") != "":
        sql += " AND a.codigo = ?"
        valores.append(datos["area"])

    if datos.get("estado", "") != "":
        sql += " AND rp.estado = ?"
        valores.append(datos["estado"])

    numero = datos.get("op", "").strip()
    if numero != "":
        sql += " AND o.numero = ?"
        valores.append(numero)

    sql += " ORDER BY rp.id DESC"     # Los más recientes primero
    return base_datos.filas_a_diccionarios(conexion.execute(sql, valores).fetchall())


# ---------------------------------------------------------------------
# Módulo 2: revisión del analista
# Al APROBAR se descuenta cada material de la lista (cantidad de la lista x cantidad
# entregada) y se suma el producto entregado. Si falta existencia de algún material,
# no se puede aprobar. Al RECHAZAR no se mueve inventario y el motivo es obligatorio.
# ---------------------------------------------------------------------

def buscar_reporte(conexion, reporte_id):
    if not str(reporte_id or "").isdigit():
        raise ValueError("Falta el número del reporte.")
    fila = conexion.execute(SQL_REPORTES + " WHERE rp.id = ?", (int(reporte_id),)).fetchone()
    if fila is None:
        raise ValueError("El reporte no existe.")
    return dict(fila)


def buscar_reporte_pendiente(conexion, reporte_id):
    """Un reporte ya aprobado o rechazado no se puede volver a revisar."""
    reporte = buscar_reporte(conexion, reporte_id)
    if reporte["estado"] != "PENDIENTE":
        raise ValueError(f"El reporte #{reporte['id']} ya fue revisado (estado: {reporte['estado'].lower()}).")
    return reporte


def calcular_consumos(conexion, reporte):
    """Qué sale del inventario al aprobar: cada material de la lista x la cantidad entregada."""
    filas = conexion.execute(
        "SELECT i.id, i.codigo, i.descripcion, i.unidad_medida, i.existencia, lm.cantidad "
        "FROM lineas_material lm JOIN items i ON i.id = lm.item_id "
        "WHERE lm.referencia_id = ? ORDER BY lm.id",
        (reporte["referencia_id"],),
    ).fetchall()
    consumos = []
    for fila in filas:
        consumo = round(fila["cantidad"] * reporte["cantidad"], 6)
        consumos.append({
            "item_id": fila["id"],
            "codigo": fila["codigo"],
            "descripcion": fila["descripcion"],
            "unidad_medida": fila["unidad_medida"],
            "existencia": fila["existencia"],
            "consumo": consumo,
            "quedara": round(fila["existencia"] - consumo, 6),
            "suficiente": fila["existencia"] >= consumo,
        })
    return consumos


def consultar_reporte_para_revision(conexion, usuario, datos):
    """Lo que el analista ve antes de decidir: qué entra, qué sale y si alcanza."""
    reporte = buscar_reporte(conexion, datos.get("id"))
    consumos = calcular_consumos(conexion, reporte)
    alcanza = True
    for consumo in consumos:
        if not consumo["suficiente"]:
            alcanza = False
    return {
        "reporte": reporte,
        "consumos": consumos,
        "puede_aprobar": reporte["estado"] == "PENDIENTE" and alcanza,
    }


def aprobar_reporte(conexion, usuario, datos):
    reporte = buscar_reporte_pendiente(conexion, datos.get("id"))
    consumos = calcular_consumos(conexion, reporte)

    # 1. Primero se revisa que TODO alcance. Si falta algo, no se toca nada.
    faltantes = []
    for consumo in consumos:
        if not consumo["suficiente"]:
            falta = round(consumo["consumo"] - consumo["existencia"], 6)
            faltantes.append(f"{consumo['codigo']} (faltan {falta:g} {consumo['unidad_medida']})")
    if len(faltantes) > 0:
        raise ValueError("No hay existencias suficientes para aprobar: " + ", ".join(faltantes) + ".")

    # 2. Salidas: se descuenta cada material (con la fachada de inventario.py).
    for consumo in consumos:
        inventario.registrar_salida(
            conexion, consumo["item_id"], consumo["consumo"], usuario["id"],
            f"Consumo de {reporte['referencia']} · OP {reporte['orden']}", reporte["orden_id"], reporte["id"],
        )
    # 3. Entrada: se suma el producto que entregó el área.
    inventario.registrar_entrada(
        conexion, reporte["item_id"], reporte["cantidad"], usuario["id"],
        f"Entrega de {reporte['area']} · OP {reporte['orden']}", reporte["orden_id"], reporte["id"],
    )
    # 4. El reporte queda aprobado, con quién y cuándo lo revisó.
    marcar_revisado(conexion, reporte["id"], "APROBADO", None, usuario)
    # Todo lo anterior se guarda junto (commit en servidor.py): o se hace completo, o nada.
    return {"id": reporte["id"], "estado": "APROBADO"}


def rechazar_reporte(conexion, usuario, datos):
    reporte = buscar_reporte_pendiente(conexion, datos.get("id"))
    motivo = leer_texto(datos, "motivo", "Motivo del rechazo")
    marcar_revisado(conexion, reporte["id"], "RECHAZADO", motivo, usuario)
    return {"id": reporte["id"], "estado": "RECHAZADO"}


def marcar_revisado(conexion, reporte_id, estado, motivo, usuario):
    conexion.execute(
        "UPDATE reportes SET estado = ?, motivo_rechazo = ?, revisado_por_id = ?, fecha_revision = ? WHERE id = ?",
        (estado, motivo, usuario["id"], base_datos.fecha_actual(), reporte_id),
    )


# ---------------------------------------------------------------------
# Módulo 3: panel del supervisor
# Estado de cada área dentro de cada OP:
#   PENDIENTE  -> el área no tiene nada aprobado ni en revisión.
#   EN_PROCESO -> ya hay entregas, pero lo aprobado es menor que lo requerido.
#   APROBADO   -> lo aprobado completa lo requerido.
# Los reportes en revisión y los rechazados se cuentan aparte, en sus indicadores.
# ---------------------------------------------------------------------

ESTADOS_DEL_AREA = ["PENDIENTE", "EN_PROCESO", "APROBADO"]


def calcular_estado(requeridas, aprobadas, en_revision):
    if aprobadas >= requeridas:
        return "APROBADO"
    if aprobadas > 0 or en_revision > 0:
        return "EN_PROCESO"
    return "PENDIENTE"


def contar_reportes(conexion, orden_id, area_id, estado):
    """Cuántos reportes (no unidades) tiene un área en una OP con cierto estado."""
    fila = conexion.execute(
        "SELECT COUNT(*) AS total FROM reportes WHERE orden_id = ? AND area_id = ? AND estado = ?",
        (orden_id, area_id, estado),
    ).fetchone()
    return fila["total"]


def consultar_panel(conexion, usuario, datos):
    """Una fila por cada OP y área, con su estado; más los indicadores de arriba."""
    codigo_area = datos.get("area", "")
    estado_buscado = datos.get("estado", "")

    # Las áreas que se muestran como columnas de la matriz.
    sql_areas = "SELECT codigo, nombre FROM areas"
    valores_areas = []
    if codigo_area != "":
        sql_areas += " WHERE codigo = ?"
        valores_areas.append(codigo_area)
    areas = base_datos.filas_a_diccionarios(conexion.execute(sql_areas + " ORDER BY orden", valores_areas).fetchall())

    # Las OP (todas, o solo la elegida en el filtro).
    sql_ordenes = "SELECT o.id, o.numero, r.codigo AS producto FROM ordenes o JOIN referencias r ON r.id = o.referencia_id"
    valores_ordenes = []
    if datos.get("op", "") != "":
        sql_ordenes += " WHERE o.numero = ?"
        valores_ordenes.append(datos["op"])
    ordenes = conexion.execute(sql_ordenes + " ORDER BY o.id DESC", valores_ordenes).fetchall()

    filas = []
    for orden in ordenes:
        # avance_por_area (de ordenes.py) ya trae requeridas, aprobadas y en revisión por área.
        for area in avance_por_area(conexion, orden["id"], codigo_area):
            requeridas = area["cantidad_requerida"]
            fila = {
                "orden": orden["numero"],
                "producto": orden["producto"],
                "area": area["area_nombre"],
                "area_codigo": area["area_codigo"],
                "referencia": area["referencia"],
                "requeridas": requeridas,
                "aprobadas": area["aprobadas"],
                "en_revision": area["en_revision"],
                "reportes_en_revision": contar_reportes(conexion, orden["id"], area["area_id"], "PENDIENTE"),
                "reportes_rechazados": contar_reportes(conexion, orden["id"], area["area_id"], "RECHAZADO"),
                "avance": 0,
                "estado": calcular_estado(requeridas, area["aprobadas"], area["en_revision"]),
            }
            if requeridas > 0:
                # Porcentaje aprobado, redondeado a un número entero (ej. 40).
                fila["avance"] = round(area["aprobadas"] / requeridas * 100)
            if estado_buscado == "" or fila["estado"] == estado_buscado:
                filas.append(fila)

    return {"areas": areas, "filas": filas, "indicadores": calcular_indicadores(filas)}


def calcular_indicadores(filas):
    """Los números grandes de arriba del panel."""
    indicadores = {"PENDIENTE": 0, "EN_PROCESO": 0, "APROBADO": 0,
                   "REPORTES_EN_REVISION": 0, "REPORTES_RECHAZADOS": 0}
    for fila in filas:
        indicadores[fila["estado"]] += 1
        indicadores["REPORTES_EN_REVISION"] += fila["reportes_en_revision"]
        indicadores["REPORTES_RECHAZADOS"] += fila["reportes_rechazados"]
    return indicadores
