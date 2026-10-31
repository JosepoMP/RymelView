# =====================================================================
# inventario.py
# Módulo 6: todo lo que tiene que ver con las existencias.
#   - registrar_entrada / registrar_salida: la ÚNICA forma de cambiar una
#     existencia. Las usan la aprobación de entregas (entregas.py), la entrada
#     de materia prima y los datos de prueba (base_datos.py).
#   - Portal de inventarios: existencias, historial y entrada de MP.
#
# Patrones de diseño en este archivo:
#   - GRASP Experto en información: este módulo es el que "sabe" de existencias
#     y movimientos, así que es el único que los cambia.
#   - GRASP Alta cohesión: antes estas funciones estaban repartidas entre
#     base_datos.py y entregas.py; ahora todo lo de inventario vive aquí.
#   - GoF Fachada (Facade): registrar_entrada y registrar_salida esconden los
#     detalles (leer la existencia, UPDATE en items, INSERT en movimientos).
#     Quien las usa solo dice "entra esto" o "sale esto".
# =====================================================================

import base_datos
from catalogo import buscar_item, leer_numero, leer_texto


# ---------------------------------------------------------------------
# La fachada: entradas y salidas
# ---------------------------------------------------------------------

def registrar_entrada(conexion, item_id, cantidad, usuario_id, concepto, orden_id=None, reporte_id=None):
    """Suma la cantidad a la existencia del ítem y deja el movimiento en el historial."""
    return mover_existencia(conexion, item_id, "ENTRADA", cantidad, usuario_id, concepto, orden_id, reporte_id)


def registrar_salida(conexion, item_id, cantidad, usuario_id, concepto, orden_id=None, reporte_id=None):
    """Resta la cantidad a la existencia del ítem. Nunca deja la existencia en negativo."""
    return mover_existencia(conexion, item_id, "SALIDA", cantidad, usuario_id, concepto, orden_id, reporte_id)


def mover_existencia(conexion, item_id, tipo, cantidad, usuario_id, concepto, orden_id, reporte_id):
    """El detalle que la fachada esconde: leer, calcular, actualizar y registrar.

    orden_id y reporte_id son opcionales (=None): una compra no tiene OP ni reporte.
    """
    item = conexion.execute("SELECT codigo, existencia FROM items WHERE id = ?", (item_id,)).fetchone()
    if tipo == "ENTRADA":
        nueva_existencia = item["existencia"] + cantidad
    else:
        nueva_existencia = item["existencia"] - cantidad
    # round evita errores diminutos de los decimales (ej. 0.30000000000000004).
    nueva_existencia = round(nueva_existencia, 6)
    if nueva_existencia < 0:
        raise ValueError(f"No hay existencia suficiente de {item['codigo']}.")

    conexion.execute("UPDATE items SET existencia = ? WHERE id = ?", (nueva_existencia, item_id))
    conexion.execute(
        "INSERT INTO movimientos (item_id, tipo, cantidad, existencia_resultante, orden_id, reporte_id, "
        "usuario_id, fecha, concepto) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (item_id, tipo, cantidad, nueva_existencia, orden_id, reporte_id, usuario_id,
         base_datos.fecha_actual(), concepto),
    )
    return nueva_existencia


# ---------------------------------------------------------------------
# Portal de inventarios (funciones de la API)
# Los PP y PT no se ingresan a mano: entran al inventario cuando el
# analista aprueba una entrega.
# ---------------------------------------------------------------------

def consultar_inventario(conexion, usuario, datos):
    """Los ítems filtrados por tipo y texto, más un resumen de cuántos hay de cada tipo."""
    sql = "SELECT codigo, descripcion, tipo, unidad_medida, existencia FROM items WHERE 1 = 1"
    valores = []
    if datos.get("tipo", "") != "":
        sql += " AND tipo = ?"
        valores.append(datos["tipo"])
    texto = datos.get("texto", "").strip()
    if texto != "":
        sql += " AND (codigo LIKE ? OR descripcion LIKE ?)"
        valores.append(f"%{texto}%")
        valores.append(f"%{texto}%")
    sql += " ORDER BY codigo"
    items = base_datos.filas_a_diccionarios(conexion.execute(sql, valores).fetchall())

    # El resumen cuenta TODOS los ítems (no depende de los filtros de la tabla).
    resumen = {}
    for tipo in ["MP", "PP", "PT"]:
        total = conexion.execute("SELECT COUNT(*) FROM items WHERE tipo = ?", (tipo,)).fetchone()[0]
        en_cero = conexion.execute(
            "SELECT COUNT(*) FROM items WHERE tipo = ? AND existencia <= 0", (tipo,)
        ).fetchone()[0]
        resumen[tipo] = {"items": total, "sin_existencia": en_cero}

    return {"items": items, "resumen": resumen}


def consultar_movimientos(conexion, usuario, datos):
    """El historial de un ítem: cada entrada y salida, la más reciente primero."""
    item = buscar_item(conexion, leer_texto(datos, "codigo", "Código del ítem"))
    filas = conexion.execute(
        "SELECT m.fecha, m.tipo, m.cantidad, m.existencia_resultante, m.concepto, "
        "       o.numero AS orden, u.nombre_completo AS usuario "
        "FROM movimientos m "
        "LEFT JOIN ordenes o ON o.id = m.orden_id "     # LEFT: las compras no tienen OP
        "JOIN usuarios u ON u.id = m.usuario_id "
        "WHERE m.item_id = ? ORDER BY m.id DESC",
        (item["id"],),
    ).fetchall()
    movimientos = base_datos.filas_a_diccionarios(filas)

    total_entradas = 0
    total_salidas = 0
    for movimiento in movimientos:
        if movimiento["tipo"] == "ENTRADA":
            total_entradas += movimiento["cantidad"]
        else:
            total_salidas += movimiento["cantidad"]

    return {
        "item": item,
        "movimientos": movimientos,
        "total_entradas": round(total_entradas, 6),
        "total_salidas": round(total_salidas, 6),
    }


def registrar_entrada_mp(conexion, usuario, datos):
    """Entrada de materia prima (por ejemplo, una compra). Solo el analista."""
    item = buscar_item(conexion, leer_texto(datos, "item", "Ítem"))
    if item["tipo"] != "MP":
        raise ValueError("Solo se registran entradas de materia prima. "
                         "Los PP y PT entran al inventario cuando se aprueba una entrega.")
    cantidad = leer_numero(datos.get("cantidad"), "La cantidad")
    concepto = str(datos.get("concepto") or "").strip()
    if concepto == "":
        concepto = "Entrada de materia prima"

    nueva_existencia = registrar_entrada(conexion, item["id"], cantidad, usuario["id"], concepto[:150])
    return {"item": item["codigo"], "cantidad": cantidad, "existencia": nueva_existencia}
