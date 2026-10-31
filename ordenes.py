# =====================================================================
# ordenes.py
# Órdenes de producción (OP) y clientes.
#   - Crear OP (analista y supervisor): número, ítem de ensamble, cantidad
#     a despachar y cliente. Al crearla se calcula y se guarda cuánto debe
#     producir cada área (tabla requerimientos).
#   - Consultar OP (todos): por área, unidades requeridas, en revisión,
#     aprobadas, rechazadas y pendientes.
# Las funciones de la API tienen la forma (conexion, usuario, datos), igual que en catalogo.py.
# =====================================================================

import base_datos
from catalogo import (buscar_nodo_de_area, buscar_referencia, construir_estructura, leer_entero,
                      leer_materiales, leer_texto)

NUMERO_INICIAL_OP = 1001

# Estado de una OP en la consulta
COMPLETA = "COMPLETA"        # Ningún área tiene unidades pendientes
PENDIENTES = "PENDIENTES"    # Al menos un área tiene unidades pendientes


# ---------------------------------------------------------------------
# Clientes
# ---------------------------------------------------------------------

def listar_clientes(conexion, usuario, datos):
    filas = conexion.execute("SELECT id, nit, nombre FROM clientes ORDER BY nombre").fetchall()
    return base_datos.filas_a_diccionarios(filas)


def nit_valido(nit):
    """NIT colombiano: de 5 a 15 dígitos y, si tiene, un dígito de verificación. Ej: 900123456-7."""
    partes = nit.split("-")          # "900123456-7" -> ["900123456", "7"]
    if len(partes) > 2:
        return False
    if not partes[0].isdigit() or len(partes[0]) < 5 or len(partes[0]) > 15:
        return False
    if len(partes) == 2 and (not partes[1].isdigit() or len(partes[1]) != 1):
        return False
    return True


def crear_cliente(conexion, usuario, datos):
    # Se quitan puntos y espacios: "900.123.456-7" -> "900123456-7"
    nit = leer_texto(datos, "nit", "NIT").replace(".", "").replace(" ", "")
    if not nit_valido(nit):
        raise ValueError("El NIT solo puede tener dígitos y, si aplica, el dígito de verificación (ej. 900123456-7).")
    existe = conexion.execute("SELECT id FROM clientes WHERE nit = ?", (nit,)).fetchone()
    if existe is not None:
        raise ValueError(f"Ya existe un cliente con el NIT {nit}.")

    nombre = leer_texto(datos, "nombre", "Nombre o razón social")
    cursor = conexion.execute("INSERT INTO clientes (nit, nombre) VALUES (?, ?)", (nit, nombre))
    return {"id": cursor.lastrowid, "nit": nit, "nombre": nombre}


# ---------------------------------------------------------------------
# Cálculo de lo que debe producir cada área
# ---------------------------------------------------------------------

def calcular_requerimientos(conexion, codigo_ensamble, cantidad):
    """Para cada área: qué referencia fabrica y cuántas unidades debe entregar.

    Patrón GRASP Experto en información: este cálculo vive en ordenes.py porque
    es el módulo que conoce la OP, su cantidad y las áreas que deben participar.

    Unidades requeridas = cantidad de la OP x cantidad de la lista de materiales
    (ese cálculo ya lo hace construir_estructura en cada nodo del árbol).
    Devuelve: el árbol, la lista de requerimientos y los nombres de las áreas que faltan.
    """
    arbol = construir_estructura(conexion, codigo_ensamble, cantidad)
    areas = conexion.execute("SELECT * FROM areas ORDER BY orden").fetchall()

    requerimientos = []
    areas_faltantes = []
    for area in areas:
        nodo = buscar_nodo_de_area(arbol, area["codigo"])
        if nodo is None:
            areas_faltantes.append(area["nombre"])
        else:
            requerimientos.append({
                "area_id": area["id"],
                "area_codigo": area["codigo"],
                "area_nombre": area["nombre"],
                "referencia": nodo["referencia"],
                "item_codigo": nodo["item"]["codigo"],
                "descripcion": nodo["item"]["descripcion"],
                "cantidad_por_unidad": nodo["cantidad_total"] / cantidad,
                "cantidad_requerida": nodo["cantidad_total"],
            })
    return arbol, requerimientos, areas_faltantes


def revisar_requerimientos(requerimientos, areas_faltantes):
    """Los motivos por los que NO se puede crear la OP. Lista vacía = sí se puede."""
    problemas = []
    if len(areas_faltantes) > 0:
        problemas.append("La lista de materiales está incompleta: falta amarrar la referencia de "
                         + ", ".join(areas_faltantes) + ".")
    # Las áreas reportan unidades enteras: si alguna cantidad da con decimales, no se podría completar.
    con_decimales = []
    for requerimiento in requerimientos:
        if requerimiento["cantidad_requerida"] != int(requerimiento["cantidad_requerida"]):
            con_decimales.append(requerimiento["area_nombre"])
    if len(con_decimales) > 0:
        problemas.append("Las unidades de " + ", ".join(con_decimales)
                         + " no dan un número entero; revisa la lista de materiales.")
    return problemas


def buscar_ensamble(conexion, codigo):
    """La referencia de un ítem de ensamble (producto terminado)."""
    referencia = buscar_referencia(conexion, codigo)
    if referencia["item_tipo"] != "PT":
        raise ValueError("La OP debe ser de un ítem de ensamble (producto terminado).")
    return referencia


# ---------------------------------------------------------------------
# Crear una OP (analista y supervisor)
# ---------------------------------------------------------------------

def sugerir_numero_orden(conexion, usuario, datos):
    mayor = NUMERO_INICIAL_OP - 1
    for fila in conexion.execute("SELECT numero FROM ordenes"):
        if fila["numero"].isdigit() and int(fila["numero"]) > mayor:
            mayor = int(fila["numero"])
    return {"numero": str(mayor + 1)}


def listar_ensambles(conexion, usuario, datos):
    """Los productos terminados, indicando si su lista de materiales está completa."""
    filas = conexion.execute(
        "SELECT r.codigo, r.descripcion, i.codigo AS item_codigo FROM referencias r "
        "JOIN items i ON i.id = r.item_id WHERE i.tipo = 'PT' ORDER BY i.codigo"
    ).fetchall()
    ensambles = []
    for fila in filas:
        arbol, requerimientos, areas_faltantes = calcular_requerimientos(conexion, fila["codigo"], 1)
        ensambles.append({
            "codigo": fila["codigo"],
            "descripcion": fila["descripcion"],
            "item_codigo": fila["item_codigo"],
            "completa": len(areas_faltantes) == 0,
        })
    return ensambles


def vista_previa_orden(conexion, usuario, datos):
    """Lo que se guardaría al crear la OP, para confirmarlo antes de guardar."""
    ensamble = buscar_ensamble(conexion, leer_texto(datos, "referencia", "Ítem de ensamble"))
    cantidad = leer_entero(datos.get("cantidad"), "La cantidad a despachar")
    arbol, requerimientos, areas_faltantes = calcular_requerimientos(conexion, ensamble["codigo"], cantidad)
    problemas = revisar_requerimientos(requerimientos, areas_faltantes)
    return {
        "arbol": arbol,
        "requerimientos": requerimientos,
        "areas_faltantes": areas_faltantes,
        "problemas": problemas,
        "puede_crear": len(problemas) == 0,
    }


def crear_orden(conexion, usuario, datos):
    # Patrón GRASP Creador: crear_orden crea también los requerimientos de la OP,
    # porque es quien tiene los datos para hacerlo (la cantidad y la estructura)
    # y porque los requerimientos "pertenecen" a la OP.
    # 1. Número de OP: solo dígitos y que no exista.
    numero = leer_texto(datos, "numero", "Número de OP")
    if not numero.isdigit() or len(numero) > 10:
        raise ValueError("El número de OP solo puede tener dígitos (por ejemplo, 1004).")
    existe = conexion.execute("SELECT id FROM ordenes WHERE numero = ?", (numero,)).fetchone()
    if existe is not None:
        raise ValueError(f"Ya existe la OP {numero}. El número no se puede repetir.")

    # 2. Ítem de ensamble, cliente y cantidad.
    ensamble = buscar_ensamble(conexion, leer_texto(datos, "referencia", "Ítem de ensamble"))
    cliente_id = str(datos.get("cliente") or "")
    cliente = None
    if cliente_id.isdigit():
        cliente = conexion.execute("SELECT id FROM clientes WHERE id = ?", (int(cliente_id),)).fetchone()
    if cliente is None:
        raise ValueError("Selecciona un cliente de la lista.")
    cantidad = leer_entero(datos.get("cantidad"), "La cantidad a despachar")

    # 3. La lista de materiales debe tener todas las áreas amarradas.
    arbol, requerimientos, areas_faltantes = calcular_requerimientos(conexion, ensamble["codigo"], cantidad)
    problemas = revisar_requerimientos(requerimientos, areas_faltantes)
    if len(problemas) > 0:
        raise ValueError(" ".join(problemas))

    # 4. Se guarda la OP y lo que debe producir cada área.
    #    Si algo fallara aquí, servidor.py deshace todo (rollback): nunca queda una OP sin requerimientos.
    cursor = conexion.execute(
        "INSERT INTO ordenes (numero, referencia_id, cliente_id, cantidad, fecha_creacion, creada_por_id) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (numero, ensamble["id"], cliente["id"], cantidad, base_datos.fecha_actual(), usuario["id"]),
    )
    orden_id = cursor.lastrowid
    for requerimiento in requerimientos:
        referencia = buscar_referencia(conexion, requerimiento["referencia"])
        conexion.execute(
            "INSERT INTO requerimientos (orden_id, area_id, referencia_id, cantidad_requerida) VALUES (?, ?, ?, ?)",
            (orden_id, requerimiento["area_id"], referencia["id"], int(requerimiento["cantidad_requerida"])),
        )
    return buscar_orden(conexion, numero)


# ---------------------------------------------------------------------
# Consultar OP (todos los usuarios)
# ---------------------------------------------------------------------

SQL_ORDENES = """
    SELECT o.id, o.numero, o.cantidad, o.fecha_creacion,
           u.nombre_completo AS creada_por,
           c.nombre AS cliente_nombre, c.nit AS cliente_nit,
           r.id AS referencia_id, r.codigo AS referencia, r.descripcion,
           i.codigo AS item_codigo
    FROM ordenes o
    JOIN clientes c ON c.id = o.cliente_id
    JOIN referencias r ON r.id = o.referencia_id
    JOIN items i ON i.id = r.item_id
    JOIN usuarios u ON u.id = o.creada_por_id
"""


def buscar_orden(conexion, numero):
    fila = conexion.execute(SQL_ORDENES + " WHERE o.numero = ?", (str(numero).strip(),)).fetchone()
    if fila is None:
        raise ValueError(f"No existe la orden de producción {numero}.")
    return dict(fila)


def sumar_reportes(conexion, orden_id, area_id, estado):
    """Suma las unidades de los reportes de un área en una OP con cierto estado.

    COALESCE(..., 0) devuelve 0 cuando no hay reportes (si no, SUM devolvería vacío).
    """
    fila = conexion.execute(
        "SELECT COALESCE(SUM(cantidad), 0) AS total FROM reportes "
        "WHERE orden_id = ? AND area_id = ? AND estado = ?",
        (orden_id, area_id, estado),
    ).fetchone()
    return fila["total"]


def avance_por_area(conexion, orden_id, codigo_area):
    """Una fila por área de la OP con sus unidades. Si codigo_area no está vacío, solo esa área."""
    sql = (
        "SELECT rq.area_id, rq.cantidad_requerida, a.codigo AS area_codigo, a.nombre AS area_nombre, "
        "       r.codigo AS referencia, r.descripcion, i.codigo AS item_codigo "
        "FROM requerimientos rq "
        "JOIN areas a ON a.id = rq.area_id "
        "JOIN referencias r ON r.id = rq.referencia_id "
        "JOIN items i ON i.id = r.item_id "
        "WHERE rq.orden_id = ?"
    )
    valores = [orden_id]
    if codigo_area != "":
        sql += " AND a.codigo = ?"
        valores.append(codigo_area)
    sql += " ORDER BY a.orden"

    filas = []
    for fila in conexion.execute(sql, valores).fetchall():
        area = dict(fila)
        area["en_revision"] = sumar_reportes(conexion, orden_id, area["area_id"], "PENDIENTE")
        area["aprobadas"] = sumar_reportes(conexion, orden_id, area["area_id"], "APROBADO")
        area["rechazadas"] = sumar_reportes(conexion, orden_id, area["area_id"], "RECHAZADO")
        # Pendientes por entregar = requeridas - aprobadas (nunca menos de cero).
        area["pendientes"] = max(area["cantidad_requerida"] - area["aprobadas"], 0)
        filas.append(area)
    return filas


def estado_de_orden(areas):
    if len(areas) == 0:
        return PENDIENTES
    for area in areas:
        if area["pendientes"] > 0:
            return PENDIENTES
    return COMPLETA


def listar_ordenes(conexion, usuario, datos):
    """Todas las OP con su estado. Filtros: número, cliente (nombre o NIT), área y estado.
    Si se filtra por área, el estado y el avance son los de esa área."""
    sql = SQL_ORDENES + " WHERE 1 = 1"
    valores = []

    numero = datos.get("op", "").strip()
    if numero != "":
        sql += " AND o.numero LIKE ?"
        valores.append(f"%{numero}%")

    cliente = datos.get("cliente", "").strip()
    if cliente != "":
        sql += " AND (c.nombre LIKE ? OR c.nit LIKE ?)"
        valores.append(f"%{cliente}%")
        valores.append(f"%{cliente}%")

    sql += " ORDER BY o.id DESC"     # Las más nuevas primero

    codigo_area = datos.get("area", "")
    estado = datos.get("estado", "")
    resultado = []
    for fila in conexion.execute(sql, valores).fetchall():
        orden = dict(fila)
        areas = avance_por_area(conexion, orden["id"], codigo_area)
        orden["total_areas"] = len(areas)
        orden["areas_completas"] = 0
        for area in areas:
            if area["pendientes"] == 0:
                orden["areas_completas"] += 1
        orden["estado"] = estado_de_orden(areas)
        # El filtro de estado se aplica aquí porque el estado se calcula, no está guardado.
        if estado == "" or orden["estado"] == estado:
            resultado.append(orden)
    return resultado


def consultar_orden(conexion, usuario, datos):
    """Detalle de una OP: datos, lista de materiales del ensamble y avance de cada área."""
    orden = buscar_orden(conexion, leer_texto(datos, "numero", "Número de OP"))
    areas = avance_por_area(conexion, orden["id"], "")
    return {
        "orden": orden,
        "materiales": leer_materiales(conexion, orden["referencia_id"]),
        "areas": areas,
        "estado": estado_de_orden(areas),
    }
