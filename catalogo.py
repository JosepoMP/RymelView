# =====================================================================
# catalogo.py
# Módulo 4: ítems (MP, PP, PT), referencias con su nemotecnia y
# listas de materiales (BOM). También el Módulo 5 (árbol de estructura)
# y el asistente "Nuevo producto".
#
# Todas las funciones que usa la API tienen la misma forma:
#     def nombre(conexion, usuario, datos):
# - conexion: la base de datos (la abre y la cierra servidor.py).
# - usuario:  quién hizo la petición (diccionario con su rol y su área).
# - datos:    lo que envió la página (filtros de un GET o el JSON de un POST).
# Si algo no es válido, se hace  raise ValueError("mensaje")  y servidor.py
# deshace los cambios y le muestra el mensaje al usuario.
#
# Patrones de diseño en este archivo:
#   - GRASP Experto en información: las reglas de ítems y referencias (nemotecnia,
#     ciclos, tipo correcto) están aquí, junto a los datos que revisan.
#   - GRASP Alta cohesión: todo lo del catálogo y su estructura en un solo módulo.
#   - GRASP Bajo acoplamiento: el asistente "Nuevo producto" reutiliza crear_item y
#     crear_referencia en lugar de escribir sus propios INSERT.
# =====================================================================

import math

import base_datos

TIPOS_ITEM = {"MP": "Materia prima", "PP": "Producto en proceso", "PT": "Producto terminado"}
UNIDADES = ["und", "kg", "g", "m", "m2", "L", "gal"]
DIGITOS_ITEM = 4          # MP-0001
DIGITOS_REFERENCIA = 3    # NUCLEO-001
AREA_PRODUCTO_TERMINADO = "ENSAMBLE"   # La única área que produce PT


# ---------------------------------------------------------------------
# Ayudas para leer y validar datos
# (también las usan ordenes.py y entregas.py)
# ---------------------------------------------------------------------

def leer_texto(datos, campo, nombre):
    """Devuelve el texto sin espacios de sobra. Si viene vacío, avisa que es obligatorio."""
    valor = str(datos.get(campo) or "").strip()
    if valor == "":
        raise ValueError(f"El campo «{nombre}» es obligatorio.")
    return valor


def leer_numero(valor, nombre):
    """Convierte a número y revisa que sea mayor que cero."""
    try:
        numero = float(valor)
    except (TypeError, ValueError):
        raise ValueError(f"{nombre} debe ser un número.")
    # isfinite descarta valores raros como "infinito" o "nan" (no es un número).
    if not math.isfinite(numero) or numero <= 0:
        raise ValueError(f"{nombre} debe ser mayor que cero.")
    return numero


def leer_entero(valor, nombre):
    numero = leer_numero(valor, nombre)
    if numero != int(numero):
        raise ValueError(f"{nombre} debe ser un número entero.")
    return int(numero)


def tiene_formato(codigo, prefijo, digitos):
    """¿El código es PREFIJO-número con la cantidad de dígitos indicada? Ej: NUCLEO-001."""
    numero = codigo[len(prefijo) + 1:]          # Lo que va después de "PREFIJO-"
    return codigo.startswith(prefijo + "-") and len(numero) == digitos and numero.isdigit()


def siguiente_codigo(codigos, prefijo, digitos):
    """El siguiente consecutivo libre. Ej: ['MP-0001', 'MP-0007'] -> 'MP-0008'."""
    mayor = 0
    for codigo in codigos:
        if tiene_formato(codigo, prefijo, digitos):
            numero = int(codigo[len(prefijo) + 1:])
            if numero > mayor:
                mayor = numero
    # zfill rellena con ceros a la izquierda: "8" -> "0008"
    return prefijo + "-" + str(mayor + 1).zfill(digitos)


# ---------------------------------------------------------------------
# Búsquedas que usan varias funciones
# ---------------------------------------------------------------------

def buscar_area(conexion, codigo):
    fila = conexion.execute("SELECT * FROM areas WHERE codigo = ?", (codigo.upper(),)).fetchone()
    if fila is None:
        raise ValueError(f"No existe el área {codigo}.")
    return dict(fila)


def buscar_item(conexion, codigo):
    fila = conexion.execute("SELECT * FROM items WHERE codigo = ?", (codigo.upper(),)).fetchone()
    if fila is None:
        raise ValueError(f"No existe el ítem {codigo}.")
    return dict(fila)


# Consulta de una referencia con los datos de su área y de su ítem (se usa en varias funciones).
SQL_REFERENCIAS = """
    SELECT r.id, r.codigo, r.descripcion,
           a.codigo AS area_codigo, a.nombre AS area_nombre,
           i.id AS item_id, i.codigo AS item_codigo, i.tipo AS item_tipo,
           i.descripcion AS item_descripcion, i.unidad_medida AS item_unidad
    FROM referencias r
    JOIN areas a ON a.id = r.area_id
    JOIN items i ON i.id = r.item_id
"""


def buscar_referencia(conexion, codigo):
    fila = conexion.execute(SQL_REFERENCIAS + " WHERE r.codigo = ?", (codigo.upper(),)).fetchone()
    if fila is None:
        raise ValueError(f"No existe la referencia {codigo}.")
    return dict(fila)


def leer_materiales(conexion, referencia_id):
    """La lista de materiales de una referencia, en el orden en que se agregaron."""
    filas = conexion.execute(
        "SELECT i.codigo, i.descripcion, i.tipo, i.unidad_medida, i.existencia, lm.cantidad "
        "FROM lineas_material lm JOIN items i ON i.id = lm.item_id "
        "WHERE lm.referencia_id = ? ORDER BY lm.id",
        (referencia_id,),
    ).fetchall()
    return base_datos.filas_a_diccionarios(filas)


# ---------------------------------------------------------------------
# Listas para los <select> de las páginas
# ---------------------------------------------------------------------

def consultar_listas(conexion, usuario, datos):
    """Áreas, tipos de ítem y unidades de medida."""
    areas = conexion.execute("SELECT codigo, nombre FROM areas ORDER BY orden").fetchall()
    tipos = []
    for codigo in TIPOS_ITEM:
        tipos.append({"codigo": codigo, "nombre": TIPOS_ITEM[codigo]})
    return {"areas": base_datos.filas_a_diccionarios(areas), "tipos": tipos, "unidades": UNIDADES}


# ---------------------------------------------------------------------
# Ítems
# ---------------------------------------------------------------------

def listar_items(conexion, usuario, datos):
    """Ítems filtrados por tipo y por texto (código o descripción).

    El SQL se arma por partes según los filtros que lleguen. "WHERE 1 = 1" siempre
    es verdadero; está ahí para que cada filtro se pueda agregar con "AND ...".
    """
    sql = "SELECT id, codigo, descripcion, tipo, unidad_medida, existencia FROM items WHERE 1 = 1"
    valores = []

    tipo = datos.get("tipo", "")
    if tipo != "":
        sql += " AND tipo = ?"
        valores.append(tipo)

    texto = datos.get("texto", "").strip()
    if texto != "":
        # LIKE con % busca el texto en cualquier parte: "%chapa%" encuentra "Chapa de acero".
        sql += " AND (codigo LIKE ? OR descripcion LIKE ?)"
        valores.append(f"%{texto}%")
        valores.append(f"%{texto}%")

    # Solo los ítems que todavía no produce ninguna referencia (para crear una nueva).
    if datos.get("sin_referencia") == "si":
        sql += " AND id NOT IN (SELECT item_id FROM referencias)"

    sql += " ORDER BY codigo"
    return base_datos.filas_a_diccionarios(conexion.execute(sql, valores).fetchall())


def validar_tipo(tipo):
    tipo = str(tipo or "").strip().upper()
    if tipo not in TIPOS_ITEM:
        raise ValueError("El tipo debe ser MP, PP o PT.")
    return tipo


def sugerir_codigo_item(conexion, usuario, datos):
    tipo = validar_tipo(datos.get("tipo"))
    codigos = []
    for fila in conexion.execute("SELECT codigo FROM items WHERE tipo = ?", (tipo,)):
        codigos.append(fila["codigo"])
    return {"codigo": siguiente_codigo(codigos, tipo, DIGITOS_ITEM)}


def validar_unidad(unidad):
    if unidad not in UNIDADES:
        raise ValueError("La unidad debe ser una de: " + ", ".join(UNIDADES) + ".")
    return unidad


def crear_item(conexion, usuario, datos):
    tipo = validar_tipo(datos.get("tipo"))
    codigo = leer_texto(datos, "codigo", "Código").upper()
    if not tiene_formato(codigo, tipo, DIGITOS_ITEM):
        raise ValueError(f"El código debe tener el formato {tipo}-0000 (por ejemplo, {tipo}-0001).")
    existe = conexion.execute("SELECT id FROM items WHERE codigo = ?", (codigo,)).fetchone()
    if existe is not None:
        raise ValueError(f"Ya existe un ítem con el código {codigo}.")

    descripcion = leer_texto(datos, "descripcion", "Descripción")
    unidad = validar_unidad(datos.get("unidad_medida"))
    conexion.execute(
        "INSERT INTO items (codigo, descripcion, tipo, unidad_medida) VALUES (?, ?, ?, ?)",
        (codigo, descripcion, tipo, unidad),
    )
    return buscar_item(conexion, codigo)


def editar_item(conexion, usuario, datos):
    """Solo se cambian la descripción y la unidad: el código y el tipo identifican al ítem."""
    item = buscar_item(conexion, leer_texto(datos, "codigo", "Código"))
    descripcion = leer_texto(datos, "descripcion", "Descripción")
    unidad = validar_unidad(datos.get("unidad_medida"))
    conexion.execute(
        "UPDATE items SET descripcion = ?, unidad_medida = ? WHERE id = ?",
        (descripcion, unidad, item["id"]),
    )
    return buscar_item(conexion, item["codigo"])


# ---------------------------------------------------------------------
# Referencias
# ---------------------------------------------------------------------

def listar_referencias(conexion, usuario, datos):
    sql = SQL_REFERENCIAS + " WHERE 1 = 1"
    valores = []

    area = datos.get("area", "")
    if area != "":
        sql += " AND a.codigo = ?"
        valores.append(area)

    texto = datos.get("texto", "").strip()
    if texto != "":
        sql += " AND (r.codigo LIKE ? OR r.descripcion LIKE ?)"
        valores.append(f"%{texto}%")
        valores.append(f"%{texto}%")

    sql += " ORDER BY a.orden, r.codigo"
    return base_datos.filas_a_diccionarios(conexion.execute(sql, valores).fetchall())


def consultar_referencia(conexion, usuario, datos):
    """Una referencia con su lista de materiales."""
    referencia = buscar_referencia(conexion, leer_texto(datos, "codigo", "Código"))
    referencia["materiales"] = leer_materiales(conexion, referencia["id"])
    return referencia


def sugerir_codigo_referencia(conexion, usuario, datos):
    area = buscar_area(conexion, leer_texto(datos, "area", "Área"))
    codigos = []
    for fila in conexion.execute("SELECT codigo FROM referencias WHERE area_id = ?", (area["id"],)):
        codigos.append(fila["codigo"])
    return {"codigo": siguiente_codigo(codigos, area["codigo"], DIGITOS_REFERENCIA)}


def tipo_del_area(codigo_area):
    """Ensamble final produce producto terminado (PT); las demás áreas, producto en proceso (PP)."""
    if codigo_area == AREA_PRODUCTO_TERMINADO:
        return "PT"
    return "PP"


def crear_referencia(conexion, usuario, datos):
    area = buscar_area(conexion, leer_texto(datos, "area", "Área"))

    # Nemotecnia: el código empieza por el código del área. Ej: NUCLEO-001 solo en Núcleo.
    codigo = leer_texto(datos, "codigo", "Código").upper()
    if not tiene_formato(codigo, area["codigo"], DIGITOS_REFERENCIA):
        raise ValueError(f"El código debe tener el formato {area['codigo']}-000 "
                         f"(por ejemplo, {area['codigo']}-001).")
    existe = conexion.execute("SELECT id FROM referencias WHERE codigo = ?", (codigo,)).fetchone()
    if existe is not None:
        raise ValueError(f"Ya existe la referencia {codigo}.")

    item = buscar_item(conexion, leer_texto(datos, "item", "Ítem que produce"))
    validar_item_propio(conexion, item, area)
    descripcion = leer_texto(datos, "descripcion", "Descripción")
    lineas = validar_materiales(conexion, item, datos.get("materiales"))

    cursor = conexion.execute(
        "INSERT INTO referencias (codigo, descripcion, area_id, item_id) VALUES (?, ?, ?, ?)",
        (codigo, descripcion, area["id"], item["id"]),
    )
    guardar_materiales(conexion, cursor.lastrowid, lineas)
    return consultar_referencia(conexion, usuario, {"codigo": codigo})


def cambiar_materiales(conexion, usuario, datos):
    """Reemplaza toda la lista de materiales de una referencia por la nueva."""
    referencia = buscar_referencia(conexion, leer_texto(datos, "codigo", "Código"))
    item = buscar_item(conexion, referencia["item_codigo"])
    lineas = validar_materiales(conexion, item, datos.get("materiales"))

    conexion.execute("DELETE FROM lineas_material WHERE referencia_id = ?", (referencia["id"],))
    guardar_materiales(conexion, referencia["id"], lineas)
    return consultar_referencia(conexion, usuario, {"codigo": referencia["codigo"]})


def guardar_materiales(conexion, referencia_id, lineas):
    for linea in lineas:
        conexion.execute(
            "INSERT INTO lineas_material (referencia_id, item_id, cantidad) VALUES (?, ?, ?)",
            (referencia_id, linea["item_id"], linea["cantidad"]),
        )


# ---------------------------------------------------------------------
# Reglas de las referencias
# ---------------------------------------------------------------------

def validar_item_propio(conexion, item, area):
    """El ítem que produce la referencia debe ser del tipo del área y no tener otra referencia."""
    tipo_esperado = tipo_del_area(area["codigo"])
    if item["tipo"] != tipo_esperado:
        raise ValueError(f"Las referencias de {area['nombre']} deben producir un ítem de tipo {tipo_esperado}.")
    otra = conexion.execute("SELECT codigo FROM referencias WHERE item_id = ?", (item["id"],)).fetchone()
    if otra is not None:
        raise ValueError(f"El ítem {item['codigo']} ya pertenece a la referencia {otra['codigo']}.")


def validar_materiales(conexion, item_propio, materiales):
    """Revisa la lista [{"item": "MP-0001", "cantidad": 80}, ...] y la devuelve lista para guardar."""
    if not isinstance(materiales, list) or len(materiales) == 0:
        raise ValueError("La lista de materiales debe tener al menos un material.")

    lineas = []
    codigos_usados = []
    for material in materiales:
        if not isinstance(material, dict):
            raise ValueError("Hay un material con datos no válidos.")
        item = buscar_item(conexion, leer_texto(material, "item", "Material"))
        cantidad = leer_numero(material.get("cantidad"), f"La cantidad de {item['codigo']}")

        if item["codigo"] in codigos_usados:
            raise ValueError(f"El ítem {item['codigo']} está repetido en la lista de materiales.")
        if item["tipo"] == "PT":
            raise ValueError(f"{item['codigo']} es producto terminado: no puede ser material de otra referencia.")
        if item["id"] == item_propio["id"]:
            raise ValueError(f"La referencia no puede consumir su propio ítem ({item['codigo']}).")
        if contiene_item(conexion, item["id"], item_propio["id"]):
            raise ValueError(f"{item['codigo']} ya contiene a {item_propio['codigo']}: "
                             "la estructura quedaría en un ciclo.")

        codigos_usados.append(item["codigo"])
        lineas.append({"item_id": item["id"], "cantidad": cantidad})
    return lineas


def contiene_item(conexion, item_id, buscado_id):
    """¿Aparece 'buscado' en algún nivel de la estructura de 'item'?

    Patrón GRASP Experto en información: el catálogo conoce las listas de
    materiales, así que es quien revisa los ciclos.

    Evita ciclos: si A consume B, B no puede consumir A (sería infinito).
    La función se llama a sí misma para bajar nivel por nivel (esto se llama recursión).
    Se detiene en la materia prima, que no tiene referencia ni materiales.
    """
    filas = conexion.execute(
        "SELECT lm.item_id FROM lineas_material lm "
        "JOIN referencias r ON r.id = lm.referencia_id "
        "WHERE r.item_id = ?",
        (item_id,),
    ).fetchall()
    for fila in filas:
        if fila["item_id"] == buscado_id:
            return True
        if contiene_item(conexion, fila["item_id"], buscado_id):
            return True
    return False


# ---------------------------------------------------------------------
# Módulo 5: estructura del producto (árbol PT -> PP -> MP)
# ---------------------------------------------------------------------

def consultar_estructura(conexion, usuario, datos):
    """El árbol completo de una referencia para fabricar 'cantidad' unidades,
    y el total de materia prima que se necesita."""
    referencia = buscar_referencia(conexion, leer_texto(datos, "referencia", "Referencia"))
    cantidad = 1
    if str(datos.get("cantidad") or "").strip() != "":
        cantidad = leer_numero(datos.get("cantidad"), "La cantidad")

    arbol = construir_estructura(conexion, referencia["codigo"], cantidad)
    return {
        "referencia": referencia["codigo"],
        "cantidad": cantidad,
        "arbol": arbol,
        "materia_prima": resumir_materia_prima(arbol),
    }


def construir_estructura(conexion, codigo_referencia, cantidad):
    """Arma el árbol empezando por el ítem que produce la referencia (la raíz)."""
    referencia = buscar_referencia(conexion, codigo_referencia)
    item = buscar_item(conexion, referencia["item_codigo"])
    # La raíz no tiene "cantidad por unidad": es lo que se quiere fabricar.
    return armar_nodo(conexion, item, None, cantidad)


def armar_nodo(conexion, item, cantidad_por_unidad, cantidad_total):
    """Un nodo del árbol: el ítem, la referencia que lo fabrica (si tiene) y sus hijos.

    Los hijos son los materiales de su lista. Para armar cada hijo, la función
    se llama a sí misma (recursión). La materia prima no tiene referencia,
    así que no tiene hijos y ahí se detiene.
    """
    nodo = {
        "item": {
            "codigo": item["codigo"],
            "descripcion": item["descripcion"],
            "tipo": item["tipo"],
            "unidad_medida": item["unidad_medida"],
            "existencia": item["existencia"],
        },
        "referencia": None,
        "area": None,
        "area_codigo": None,
        "cantidad_por_unidad": cantidad_por_unidad,
        "cantidad_total": round(cantidad_total, 6),   # round evita cosas como 0.30000000000000004
        "hijos": [],
    }

    referencia = conexion.execute(SQL_REFERENCIAS + " WHERE r.item_id = ?", (item["id"],)).fetchone()
    if referencia is None:
        return nodo

    nodo["referencia"] = referencia["codigo"]
    nodo["area"] = referencia["area_nombre"]
    nodo["area_codigo"] = referencia["area_codigo"]
    for material in leer_materiales(conexion, referencia["id"]):
        item_material = buscar_item(conexion, material["codigo"])
        # Cuánto se necesita en total = cantidad por unidad x lo que se fabrica del nivel de arriba.
        total_material = material["cantidad"] * cantidad_total
        nodo["hijos"].append(armar_nodo(conexion, item_material, material["cantidad"], total_material))
    return nodo


def resumir_materia_prima(arbol):
    """Suma la materia prima de todo el árbol (un mismo MP puede aparecer en varias ramas)."""
    totales = {}
    sumar_materia_prima(arbol, totales)
    resumen = []
    for codigo in sorted(totales):        # sorted ordena los códigos: MP-0001, MP-0002...
        resumen.append(totales[codigo])
    return resumen


def sumar_materia_prima(nodo, totales):
    """Recorre el árbol (otra vez con recursión) y va sumando en el diccionario 'totales'."""
    item = nodo["item"]
    if item["tipo"] == "MP":
        if item["codigo"] not in totales:
            totales[item["codigo"]] = {"item": item, "cantidad_requerida": 0}
        totales[item["codigo"]]["cantidad_requerida"] += nodo["cantidad_total"]
    for hijo in nodo["hijos"]:
        sumar_materia_prima(hijo, totales)


def buscar_nodo_de_area(arbol, codigo_area):
    """El primer nodo del árbol que fabrica el área indicada (o None si no hay).

    Recorre el árbol por niveles: empieza con la raíz en una lista de "pendientes";
    saca uno, revisa si es del área y, si no, agrega sus hijos al final de la lista.
    (La usan ordenes.py y el asistente "Nuevo producto".)
    """
    pendientes = [arbol]
    while len(pendientes) > 0:
        nodo = pendientes.pop(0)          # pop(0) saca el primero de la lista
        if nodo["area_codigo"] == codigo_area:
            return nodo
        for hijo in nodo["hijos"]:
            pendientes.append(hijo)
    return None


# ---------------------------------------------------------------------
# Asistente "Nuevo producto"
# Crea en un solo paso los 6 ítems (5 PP + 1 PT), las 6 referencias y sus
# listas de materiales. Las conexiones entre áreas son fijas, según el flujo
# de la planta; el usuario solo describe cada parte y elige su materia prima.
#
#   Núcleo ──┐
#            ├──► Parte activa ──┐
#   Bobinado ┘                   ├──► Ensamble final (PT)
#   Metalmecánica ──► Pintura ───┘
# ---------------------------------------------------------------------

# En el orden de la planta: así cada parte ya existe cuando otra la consume.
PARTES_DEL_PRODUCTO = [
    {"area": "NUCLEO", "nombre_parte": "Núcleo", "componentes": [], "mp_obligatoria": True},
    {"area": "BOBINADO", "nombre_parte": "Bobinado", "componentes": [], "mp_obligatoria": True},
    {"area": "PACTIVA", "nombre_parte": "Parte activa", "componentes": ["NUCLEO", "BOBINADO"], "mp_obligatoria": False},
    {"area": "METALMEC", "nombre_parte": "Tanque", "componentes": [], "mp_obligatoria": True},
    {"area": "PINTURA", "nombre_parte": "Tanque pintado", "componentes": ["METALMEC"], "mp_obligatoria": False},
    {"area": "ENSAMBLE", "nombre_parte": "Producto terminado", "componentes": ["PACTIVA", "PINTURA"], "mp_obligatoria": False},
]


def buscar_parte(codigo_area):
    for parte in PARTES_DEL_PRODUCTO:
        if parte["area"] == codigo_area:
            return parte
    return None


def plantilla_producto(conexion, usuario, datos):
    """Lo que necesita la página para dibujar el asistente: los bloques por área,
    las materias primas que se pueden elegir y los productos que se pueden copiar."""
    partes = []
    for parte in PARTES_DEL_PRODUCTO:
        area = buscar_area(conexion, parte["area"])
        componentes = []
        for codigo in parte["componentes"]:
            componentes.append({
                "area": codigo,
                "area_nombre": buscar_area(conexion, codigo)["nombre"],
                "nombre_parte": buscar_parte(codigo)["nombre_parte"],
            })
        partes.append({
            "area": parte["area"],
            "area_nombre": area["nombre"],
            "nombre_parte": parte["nombre_parte"],
            "tipo": tipo_del_area(parte["area"]),
            "componentes": componentes,
            "mp_obligatoria": parte["mp_obligatoria"],
        })

    materias_primas = conexion.execute(
        "SELECT codigo, descripcion, unidad_medida FROM items WHERE tipo = 'MP' ORDER BY codigo"
    ).fetchall()
    productos = conexion.execute(
        "SELECT r.codigo, r.descripcion, i.codigo AS item_codigo FROM referencias r "
        "JOIN items i ON i.id = r.item_id WHERE i.tipo = 'PT' ORDER BY i.codigo"
    ).fetchall()
    return {
        "partes": partes,
        "materias_primas": base_datos.filas_a_diccionarios(materias_primas),
        "productos": base_datos.filas_a_diccionarios(productos),
    }


def copiar_producto(conexion, usuario, datos):
    """Materia prima y cantidades de un producto existente, para llenar el asistente."""
    referencia = buscar_referencia(conexion, leer_texto(datos, "referencia", "Producto a copiar"))
    if referencia["item_tipo"] != "PT":
        raise ValueError("Solo se pueden copiar productos terminados.")
    arbol = construir_estructura(conexion, referencia["codigo"], 1)

    partes = {}
    for parte in PARTES_DEL_PRODUCTO:
        nodo = buscar_nodo_de_area(arbol, parte["area"])
        if nodo is None:
            continue                      # Si el producto no tiene esa área, el bloque queda vacío
        materiales = []
        componentes = {}
        for hijo in nodo["hijos"]:
            if hijo["item"]["tipo"] == "MP":
                materiales.append({"item": hijo["item"]["codigo"], "cantidad": hijo["cantidad_por_unidad"]})
            elif hijo["area_codigo"] in parte["componentes"]:
                componentes[hijo["area_codigo"]] = hijo["cantidad_por_unidad"]
        partes[parte["area"]] = {"materiales": materiales, "componentes": componentes}
    return {"partes": partes}


def armar_producto(conexion, usuario, datos):
    """Crea (sin commit) el ítem y la referencia de cada área, usando las mismas
    funciones crear_item y crear_referencia de la pestaña Ítems y Referencias.
    Así se aplican exactamente las mismas reglas.
    """
    partes_recibidas = datos.get("partes")
    if not isinstance(partes_recibidas, dict):
        partes_recibidas = {}

    items_creados = {}       # {"NUCLEO": "PP-0011", ...}: el ítem que se creó para cada área
    resumen = []
    for parte in PARTES_DEL_PRODUCTO:
        area = buscar_area(conexion, parte["area"])
        datos_parte = partes_recibidas.get(parte["area"])
        if not isinstance(datos_parte, dict):
            datos_parte = {}
        try:
            resumen.append(armar_parte(conexion, usuario, parte, datos_parte, items_creados))
        except ValueError as error:
            # Se le agrega el nombre del área al mensaje, para saber en qué bloque está el problema.
            raise ValueError(f"{area['nombre']}: {error}")
    return resumen


def armar_parte(conexion, usuario, parte, datos_parte, items_creados):
    # GRASP Bajo acoplamiento: se reutilizan crear_item y crear_referencia (las mismas
    # de las pestañas Ítems y Referencias), así se cumplen las mismas reglas.
    descripcion = leer_texto(datos_parte, "descripcion", "Descripción")
    tipo = tipo_del_area(parte["area"])

    # 1. El ítem que produce esta parte, con el siguiente código libre (ej. PP-0011).
    codigo_item = sugerir_codigo_item(conexion, usuario, {"tipo": tipo})["codigo"]
    crear_item(conexion, usuario, {"tipo": tipo, "codigo": codigo_item,
                                   "descripcion": descripcion, "unidad_medida": "und"})

    # 2. Su lista de materiales: primero las conexiones fijas con otras áreas...
    materiales = []
    cantidades = datos_parte.get("componentes")
    if not isinstance(cantidades, dict):
        cantidades = {}
    for codigo_area in parte["componentes"]:
        cantidad = cantidades.get(codigo_area, 1)      # Si no la cambian, 1 por unidad
        materiales.append({"item": items_creados[codigo_area], "cantidad": cantidad})

    # ...y después la materia prima que eligió el usuario.
    materias_primas = datos_parte.get("materiales")
    if not isinstance(materias_primas, list):
        materias_primas = []
    if parte["mp_obligatoria"] and len(materias_primas) == 0:
        raise ValueError("debe tener al menos una materia prima.")
    for material in materias_primas:
        if not isinstance(material, dict):
            raise ValueError("hay una materia prima con datos no válidos.")
        item = buscar_item(conexion, leer_texto(material, "item", "Materia prima"))
        if item["tipo"] != "MP":
            raise ValueError(f"{item['codigo']} no es materia prima. En el asistente solo se agregan ítems MP.")
        materiales.append(material)

    # 3. La referencia, con el siguiente código libre del área (ej. NUCLEO-003).
    codigo_referencia = sugerir_codigo_referencia(conexion, usuario, {"area": parte["area"]})["codigo"]
    crear_referencia(conexion, usuario, {"area": parte["area"], "codigo": codigo_referencia,
                                         "item": codigo_item, "descripcion": descripcion,
                                         "materiales": materiales})

    items_creados[parte["area"]] = codigo_item
    return {"area": parte["area"], "referencia": codigo_referencia, "item": codigo_item,
            "tipo": tipo, "descripcion": descripcion}


def vista_previa_producto(conexion, usuario, datos):
    """Crea todo, arma el árbol para mostrarlo... y lo deshace con rollback (no guarda nada)."""
    resumen = armar_producto(conexion, usuario, datos)
    ensamble = resumen[len(resumen) - 1]["referencia"]     # La última parte es el ensamble
    arbol = construir_estructura(conexion, ensamble, 1)
    materia_prima = resumir_materia_prima(arbol)
    # rollback deshace todo lo de esta petición: así la vista previa usa las mismas
    # reglas que el guardado, pero no deja nada creado.
    conexion.rollback()
    return {"partes": resumen, "arbol": arbol, "materia_prima": materia_prima}


def crear_producto(conexion, usuario, datos):
    """Crea todo. Si una parte falla, servidor.py deshace TODAS (todo o nada)."""
    resumen = armar_producto(conexion, usuario, datos)
    return {"partes": resumen, "ensamble": resumen[len(resumen) - 1]["referencia"]}
