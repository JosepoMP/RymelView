# =====================================================================
# base_datos.py
# Todo lo que tiene que ver con la base de datos SQLite:
#   1. Abrir la conexión con el archivo rymel.db.
#   2. Crear las tablas (si todavía no existen).
#   3. Cargar los datos de prueba (usuarios, ítems, referencias, OP...).
#   4. Dos ayudas que usan otros archivos: cifrar contraseñas y la fecha actual.
#
# Patrón GRASP Fabricación pura: este módulo no es un concepto del negocio
# (no es un ítem ni una OP); existe solo para ordenar el acceso a la base de datos.
#
# Se puede ejecutar solo para probarlo:
#   python base_datos.py            -> crea rymel.db si no existe y muestra un resumen
#   python base_datos.py reiniciar  -> BORRA rymel.db y lo vuelve a crear con los datos de prueba
# =====================================================================

import hashlib    # Para cifrar las contraseñas
import os         # Para armar rutas de archivos y saber si un archivo existe
import secrets    # Para generar valores aleatorios seguros (la "sal" de cada contraseña)
import sqlite3    # La base de datos que viene incluida con Python
import sys        # Para leer la palabra "reiniciar" escrita al ejecutar el archivo
from datetime import datetime

# La base de datos es un solo archivo, guardado junto a este archivo .py.
CARPETA_PROYECTO = os.path.dirname(os.path.abspath(__file__))
RUTA_BASE_DATOS = os.path.join(CARPETA_PROYECTO, "rymel.db")

# Todos los usuarios de prueba usan esta contraseña.
CONTRASENA_PRUEBA = "rymel123"


# ---------------------------------------------------------------------
# 1. Conexión
# ---------------------------------------------------------------------

def conectar():
    """Abre la base de datos y devuelve la conexión.

    row_factory = sqlite3.Row hace que cada fila se pueda leer por el nombre
    de la columna, por ejemplo fila["codigo"], en vez de fila[1].
    """
    conexion = sqlite3.connect(RUTA_BASE_DATOS)
    conexion.row_factory = sqlite3.Row
    # SQLite no revisa las llaves foráneas a menos que se lo pidamos.
    conexion.execute("PRAGMA foreign_keys = ON")
    return conexion


# ---------------------------------------------------------------------
# 2. Ayudas que también usan los demás archivos
# ---------------------------------------------------------------------

def fecha_actual():
    """Fecha y hora de ahora como texto, por ejemplo '2026-10-26 14:30'.

    Se guarda como texto en ese orden (año-mes-día) porque así, al ordenar
    alfabéticamente, también queda ordenado por fecha.
    """
    return datetime.now().strftime("%Y-%m-%d %H:%M")


def nueva_sal():
    """Texto aleatorio que se mezcla con la contraseña antes de cifrarla.

    Gracias a la sal, dos usuarios con la misma contraseña quedan con
    cifrados distintos, y nadie puede usar tablas de contraseñas ya calculadas.
    """
    return secrets.token_hex(16)


def filas_a_diccionarios(filas):
    """Convierte las filas que devuelve SQLite en diccionarios normales de Python.

    Se necesita para poder enviarlas al navegador en formato JSON.
    Patrón GoF Adaptador (Adapter): adapta el formato de SQLite al que entiende JSON.
    """
    lista = []
    for fila in filas:
        lista.append(dict(fila))
    return lista


def cifrar_contrasena(contrasena, sal):
    """Convierte la contraseña en un código que no se puede revertir.

    En la base de datos NUNCA se guarda la contraseña real, solo este código.
    Al iniciar sesión se cifra lo que escribió el usuario y se comparan los códigos.
    pbkdf2_hmac repite el cifrado 100.000 veces para que adivinar sea muy lento.
    """
    codigo = hashlib.pbkdf2_hmac("sha256", contrasena.encode("utf-8"), sal.encode("utf-8"), 100000)
    return codigo.hex()


# ---------------------------------------------------------------------
# 3. Tablas
# ---------------------------------------------------------------------

# Cada CREATE TABLE describe una tabla: sus columnas y sus reglas.
#   PRIMARY KEY  -> número único de cada fila (SQLite lo asigna solo).
#   UNIQUE       -> el valor no se puede repetir (ej. dos ítems con el mismo código).
#   NOT NULL     -> el dato es obligatorio.
#   REFERENCES   -> llave foránea: el valor debe existir en otra tabla.
#   CHECK        -> una condición que el dato debe cumplir.
SQL_TABLAS = """
CREATE TABLE IF NOT EXISTS areas (
    id      INTEGER PRIMARY KEY,
    codigo  TEXT NOT NULL UNIQUE,     -- NUCLEO, BOBINADO... también es el prefijo de sus referencias
    nombre  TEXT NOT NULL,
    orden   INTEGER NOT NULL          -- posición en el flujo de la planta (1 = Núcleo)
);

CREATE TABLE IF NOT EXISTS usuarios (
    id               INTEGER PRIMARY KEY,
    usuario          TEXT NOT NULL UNIQUE,
    nombre_completo  TEXT NOT NULL,
    contrasena_hash  TEXT NOT NULL,   -- la contraseña cifrada, nunca la real
    sal              TEXT NOT NULL,
    rol              TEXT NOT NULL CHECK (rol IN ('AREA', 'ANALISTA', 'SUPERVISOR')),
    area_id          INTEGER REFERENCES areas(id)   -- solo para el rol AREA
);

CREATE TABLE IF NOT EXISTS sesiones (
    llave       TEXT PRIMARY KEY,     -- texto aleatorio que se guarda en la cookie del navegador
    usuario_id  INTEGER NOT NULL REFERENCES usuarios(id),
    fecha       TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS items (
    id             INTEGER PRIMARY KEY,
    codigo         TEXT NOT NULL UNIQUE,   -- MP-0001, PP-0001, PT-0001
    descripcion    TEXT NOT NULL,
    tipo           TEXT NOT NULL CHECK (tipo IN ('MP', 'PP', 'PT')),
    unidad_medida  TEXT NOT NULL,
    existencia     REAL NOT NULL DEFAULT 0  -- solo cambia junto con un registro en movimientos
);

CREATE TABLE IF NOT EXISTS referencias (
    id           INTEGER PRIMARY KEY,
    codigo       TEXT NOT NULL UNIQUE,    -- NUCLEO-001 (nemotecnia: ÁREA-número)
    descripcion  TEXT NOT NULL,
    area_id      INTEGER NOT NULL REFERENCES areas(id),
    item_id      INTEGER NOT NULL UNIQUE REFERENCES items(id)  -- el ítem que produce (uno por referencia)
);

-- Lista de materiales (BOM): qué consume cada referencia y cuánto por unidad.
CREATE TABLE IF NOT EXISTS lineas_material (
    id             INTEGER PRIMARY KEY,
    referencia_id  INTEGER NOT NULL REFERENCES referencias(id),
    item_id        INTEGER NOT NULL REFERENCES items(id),
    cantidad       REAL NOT NULL CHECK (cantidad > 0),
    UNIQUE (referencia_id, item_id)       -- un material no se repite en la misma lista
);

CREATE TABLE IF NOT EXISTS clientes (
    id      INTEGER PRIMARY KEY,
    nit     TEXT NOT NULL UNIQUE,
    nombre  TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS ordenes (
    id              INTEGER PRIMARY KEY,
    numero          TEXT NOT NULL UNIQUE,   -- número de OP, no se repite
    referencia_id   INTEGER NOT NULL REFERENCES referencias(id),  -- el ensamble (producto terminado)
    cliente_id      INTEGER NOT NULL REFERENCES clientes(id),
    cantidad        INTEGER NOT NULL CHECK (cantidad > 0),         -- cantidad a despachar
    fecha_creacion  TEXT NOT NULL,
    creada_por_id   INTEGER NOT NULL REFERENCES usuarios(id)
);

-- Lo que debe entregar cada área en cada OP. Se calcula UNA vez, al crear la OP
-- (cantidad de la OP x lista de materiales), para que no cambie si después se edita la BOM.
CREATE TABLE IF NOT EXISTS requerimientos (
    id                  INTEGER PRIMARY KEY,
    orden_id            INTEGER NOT NULL REFERENCES ordenes(id),
    area_id             INTEGER NOT NULL REFERENCES areas(id),
    referencia_id       INTEGER NOT NULL REFERENCES referencias(id),
    cantidad_requerida  INTEGER NOT NULL,
    UNIQUE (orden_id, area_id)
);

-- Entregas que reporta cada área. Solo mueven inventario cuando el analista las aprueba.
CREATE TABLE IF NOT EXISTS reportes (
    id                INTEGER PRIMARY KEY,
    orden_id          INTEGER NOT NULL REFERENCES ordenes(id),
    area_id           INTEGER NOT NULL REFERENCES areas(id),
    referencia_id     INTEGER NOT NULL REFERENCES referencias(id),
    cantidad          INTEGER NOT NULL CHECK (cantidad > 0),
    estado            TEXT NOT NULL DEFAULT 'PENDIENTE'
                      CHECK (estado IN ('PENDIENTE', 'APROBADO', 'RECHAZADO')),
    motivo_rechazo    TEXT,
    reportado_por_id  INTEGER NOT NULL REFERENCES usuarios(id),
    fecha_reporte     TEXT NOT NULL,
    revisado_por_id   INTEGER REFERENCES usuarios(id),
    fecha_revision    TEXT
);

-- Historial de inventario: cada entrada o salida queda registrada con su motivo.
CREATE TABLE IF NOT EXISTS movimientos (
    id                     INTEGER PRIMARY KEY,
    item_id                INTEGER NOT NULL REFERENCES items(id),
    tipo                   TEXT NOT NULL CHECK (tipo IN ('ENTRADA', 'SALIDA')),
    cantidad               REAL NOT NULL,
    existencia_resultante  REAL NOT NULL,   -- cómo quedó la existencia después del movimiento
    orden_id               INTEGER REFERENCES ordenes(id),
    reporte_id             INTEGER REFERENCES reportes(id),
    usuario_id             INTEGER NOT NULL REFERENCES usuarios(id),
    fecha                  TEXT NOT NULL,
    concepto               TEXT NOT NULL
);
"""


def crear_tablas(conexion):
    # executescript ejecuta varias instrucciones SQL seguidas.
    conexion.executescript(SQL_TABLAS)


# ---------------------------------------------------------------------
# 4. Datos de prueba
# ---------------------------------------------------------------------

# (código, nombre, orden en la planta)
AREAS = [
    ("NUCLEO", "Núcleo", 1),
    ("BOBINADO", "Bobinado", 2),
    ("PACTIVA", "Parte activa", 3),
    ("METALMEC", "Metalmecánica", 4),
    ("PINTURA", "Pintura", 5),
    ("ENSAMBLE", "Ensamble final", 6),
]

# (usuario, nombre completo, rol, código del área o None)
USUARIOS = [
    ("nucleo", "Operario de Núcleo", "AREA", "NUCLEO"),
    ("bobinado", "Operario de Bobinado", "AREA", "BOBINADO"),
    ("pactiva", "Operario de Parte activa", "AREA", "PACTIVA"),
    ("metalmec", "Operario de Metalmecánica", "AREA", "METALMEC"),
    ("pintura", "Operario de Pintura", "AREA", "PINTURA"),
    ("ensamble", "Operario de Ensamble final", "AREA", "ENSAMBLE"),
    ("analista", "Analista de Producción", "ANALISTA", None),
    ("supervisor", "Supervisor de Planta", "SUPERVISOR", None),
]

# (código, descripción, unidad, existencia inicial)
MATERIAS_PRIMAS = [
    ("MP-0001", "Chapa de acero al silicio", "kg", 2000),
    ("MP-0002", "Alambre de cobre esmaltado", "kg", 600),
    ("MP-0003", "Fibra aislante", "m2", 50),
    ("MP-0004", "Papel aislante", "m2", 100),
    ("MP-0005", "Lámina de acero para tanque", "kg", 800),
    ("MP-0006", "Pintura epóxica", "L", 60),
    ("MP-0007", "Aceite dieléctrico", "L", 1200),
]

# (referencia, área, ítem que produce, tipo, descripción, [(material, cantidad por unidad)])
REFERENCIAS = [
    ("NUCLEO-001", "NUCLEO", "PP-0001", "PP", "Núcleo transformador 45 kVA",
     [("MP-0001", 80)]),
    ("BOBINADO-001", "BOBINADO", "PP-0002", "PP", "Bobinado transformador 45 kVA",
     [("MP-0002", 25), ("MP-0003", 2), ("MP-0004", 5)]),
    ("PACTIVA-001", "PACTIVA", "PP-0003", "PP", "Parte activa 45 kVA",
     [("PP-0001", 1), ("PP-0002", 1)]),
    ("METALMEC-001", "METALMEC", "PP-0004", "PP", "Tanque 45 kVA",
     [("MP-0005", 40)]),
    ("PINTURA-001", "PINTURA", "PP-0005", "PP", "Tanque pintado 45 kVA",
     [("PP-0004", 1), ("MP-0006", 3)]),
    ("ENSAMBLE-001", "ENSAMBLE", "PT-0001", "PT", "Transformador monofásico 45 kVA",
     [("PP-0003", 1), ("PP-0005", 1), ("MP-0007", 90)]),

    ("NUCLEO-002", "NUCLEO", "PP-0006", "PP", "Núcleo transformador 75 kVA",
     [("MP-0001", 120)]),
    ("BOBINADO-002", "BOBINADO", "PP-0007", "PP", "Bobinado transformador 75 kVA",
     [("MP-0002", 38), ("MP-0003", 3), ("MP-0004", 7)]),
    ("PACTIVA-002", "PACTIVA", "PP-0008", "PP", "Parte activa 75 kVA",
     [("PP-0006", 1), ("PP-0007", 1)]),
    ("METALMEC-002", "METALMEC", "PP-0009", "PP", "Tanque 75 kVA",
     [("MP-0005", 55)]),
    ("PINTURA-002", "PINTURA", "PP-0010", "PP", "Tanque pintado 75 kVA",
     [("PP-0009", 1), ("MP-0006", 4)]),
    ("ENSAMBLE-002", "ENSAMBLE", "PT-0002", "PT", "Transformador monofásico 75 kVA",
     [("PP-0008", 1), ("PP-0010", 1), ("MP-0007", 140)]),

    # Incompleto a propósito: no tiene tanque (le faltan Metalmecánica y Pintura).
    # Sirve para probar que el sistema NO deja crear una OP con él.
    ("ENSAMBLE-003", "ENSAMBLE", "PT-0003", "PT", "Transformador tipo seco 45 kVA",
     [("PP-0003", 1), ("MP-0004", 4)]),
]

# (NIT, nombre). Empresas ficticias.
CLIENTES = [
    ("900123456-7", "Energía del Valle S.A.S."),
    ("830987654-1", "Constructora Andina Ltda."),
    ("901555222-3", "Distribuidora Eléctrica del Norte S.A."),
]

# (número de OP, ensamble, cantidad a despachar, NIT del cliente)
ORDENES = [
    ("1001", "ENSAMBLE-001", 10, "900123456-7"),
    ("1002", "ENSAMBLE-002", 5, "830987654-1"),
    ("1003", "ENSAMBLE-001", 3, "901555222-3"),
]

# Qué referencia fabrica cada área para cada ensamble.
# En la aplicación esto lo calcula ordenes.py recorriendo la estructura; aquí se
# escribe a mano para que este archivo funcione solo, sin depender de los demás.
# En estos productos cada parte lleva 1 unidad de la anterior, así que cada área
# debe entregar exactamente la cantidad de la OP.
PARTES_POR_ENSAMBLE = {
    "ENSAMBLE-001": ["NUCLEO-001", "BOBINADO-001", "PACTIVA-001", "METALMEC-001", "PINTURA-001", "ENSAMBLE-001"],
    "ENSAMBLE-002": ["NUCLEO-002", "BOBINADO-002", "PACTIVA-002", "METALMEC-002", "PINTURA-002", "ENSAMBLE-002"],
}

# (usuario que reporta, OP, referencia, cantidad, estado, motivo de rechazo)
REPORTES = [
    ("nucleo", "1001", "NUCLEO-001", 4, "APROBADO", None),
    ("nucleo", "1001", "NUCLEO-001", 3, "PENDIENTE", None),
    ("bobinado", "1001", "BOBINADO-001", 5, "PENDIENTE", None),
    ("metalmec", "1002", "METALMEC-002", 2, "RECHAZADO", "Soldadura con poros en la tapa; se debe reprocesar."),
]


def cargar_datos_prueba(conexion):
    """Llena la base con los datos de ejemplo, en orden: primero lo que otros necesitan."""
    ids_areas = insertar_areas(conexion)
    ids_usuarios = insertar_usuarios(conexion, ids_areas)
    id_analista = ids_usuarios["analista"]
    ids_items = insertar_materias_primas(conexion, id_analista)
    ids_referencias = insertar_referencias(conexion, ids_areas, ids_items)
    ids_clientes = insertar_clientes(conexion)
    ids_ordenes = insertar_ordenes(conexion, ids_referencias, ids_clientes, ids_areas, id_analista)
    insertar_reportes(conexion, ids_ordenes, ids_referencias, ids_areas, ids_usuarios, ids_items)


# Cada función "insertar_..." devuelve un diccionario {código: id} para que las
# siguientes funciones puedan buscar el id de lo que ya se insertó.

def insertar_areas(conexion):
    ids = {}
    for codigo, nombre, orden in AREAS:
        cursor = conexion.execute(
            "INSERT INTO areas (codigo, nombre, orden) VALUES (?, ?, ?)",
            (codigo, nombre, orden),
        )
        # lastrowid es el id que SQLite le asignó a la fila recién insertada.
        ids[codigo] = cursor.lastrowid
    return ids


def insertar_usuarios(conexion, ids_areas):
    ids = {}
    for usuario, nombre_completo, rol, codigo_area in USUARIOS:
        sal = nueva_sal()
        contrasena_hash = cifrar_contrasena(CONTRASENA_PRUEBA, sal)
        area_id = None
        if codigo_area is not None:
            area_id = ids_areas[codigo_area]
        cursor = conexion.execute(
            "INSERT INTO usuarios (usuario, nombre_completo, contrasena_hash, sal, rol, area_id) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (usuario, nombre_completo, contrasena_hash, sal, rol, area_id),
        )
        ids[usuario] = cursor.lastrowid
    return ids


def insertar_materias_primas(conexion, id_analista):
    """Crea la materia prima con su existencia y deja la entrada en el historial."""
    # Las existencias se cambian con la fachada de inventario.py, igual que en la aplicación.
    # El import va aquí adentro (y no arriba del archivo) porque inventario.py también
    # importa base_datos: si los dos se importaran arriba, uno quedaría a medio cargar
    # (esto se llama importación circular).
    import inventario
    ids = {}
    for codigo, descripcion, unidad, existencia in MATERIAS_PRIMAS:
        cursor = conexion.execute(
            "INSERT INTO items (codigo, descripcion, tipo, unidad_medida) VALUES (?, ?, 'MP', ?)",
            (codigo, descripcion, unidad),
        )
        ids[codigo] = cursor.lastrowid
        inventario.registrar_entrada(conexion, ids[codigo], existencia, id_analista, "Inventario inicial")
    return ids


def insertar_referencias(conexion, ids_areas, ids_items):
    """Crea el ítem que produce cada referencia, la referencia y su lista de materiales.

    Las referencias están ordenadas de modo que cada material ya existe cuando se usa
    (por ejemplo, PP-0001 se crea con NUCLEO-001 antes de que PACTIVA-001 lo consuma).
    """
    ids = {}
    for codigo, codigo_area, codigo_item, tipo, descripcion, materiales in REFERENCIAS:
        cursor = conexion.execute(
            "INSERT INTO items (codigo, descripcion, tipo, unidad_medida) VALUES (?, ?, ?, 'und')",
            (codigo_item, descripcion, tipo),
        )
        ids_items[codigo_item] = cursor.lastrowid

        cursor = conexion.execute(
            "INSERT INTO referencias (codigo, descripcion, area_id, item_id) VALUES (?, ?, ?, ?)",
            (codigo, descripcion, ids_areas[codigo_area], ids_items[codigo_item]),
        )
        ids[codigo] = cursor.lastrowid

        for codigo_material, cantidad in materiales:
            conexion.execute(
                "INSERT INTO lineas_material (referencia_id, item_id, cantidad) VALUES (?, ?, ?)",
                (ids[codigo], ids_items[codigo_material], cantidad),
            )
    return ids


def insertar_clientes(conexion):
    ids = {}
    for nit, nombre in CLIENTES:
        cursor = conexion.execute("INSERT INTO clientes (nit, nombre) VALUES (?, ?)", (nit, nombre))
        ids[nit] = cursor.lastrowid
    return ids


def insertar_ordenes(conexion, ids_referencias, ids_clientes, ids_areas, id_analista):
    """Crea cada OP y lo que debe entregar cada una de las 6 áreas."""
    ids = {}
    for numero, codigo_ensamble, cantidad, nit in ORDENES:
        cursor = conexion.execute(
            "INSERT INTO ordenes (numero, referencia_id, cliente_id, cantidad, fecha_creacion, creada_por_id) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (numero, ids_referencias[codigo_ensamble], ids_clientes[nit], cantidad, fecha_actual(), id_analista),
        )
        ids[numero] = cursor.lastrowid

        # PARTES_POR_ENSAMBLE trae las referencias en el orden de las áreas (Núcleo primero).
        partes = PARTES_POR_ENSAMBLE[codigo_ensamble]
        for posicion in range(len(AREAS)):
            codigo_area = AREAS[posicion][0]
            codigo_referencia = partes[posicion]
            conexion.execute(
                "INSERT INTO requerimientos (orden_id, area_id, referencia_id, cantidad_requerida) "
                "VALUES (?, ?, ?, ?)",
                (ids[numero], ids_areas[codigo_area], ids_referencias[codigo_referencia], cantidad),
            )
    return ids


def insertar_reportes(conexion, ids_ordenes, ids_referencias, ids_areas, ids_usuarios, ids_items):
    """Crea los reportes de ejemplo. El aprobado también mueve el inventario."""
    for usuario, numero_orden, codigo_referencia, cantidad, estado, motivo in REPORTES:
        id_usuario = ids_usuarios[usuario]
        # El área del reporte es el área del usuario que reporta.
        area_id = conexion.execute("SELECT area_id FROM usuarios WHERE id = ?", (id_usuario,)).fetchone()["area_id"]

        revisado_por = None
        fecha_revision = None
        if estado != "PENDIENTE":
            revisado_por = ids_usuarios["analista"]
            fecha_revision = fecha_actual()

        cursor = conexion.execute(
            "INSERT INTO reportes (orden_id, area_id, referencia_id, cantidad, estado, motivo_rechazo, "
            "reportado_por_id, fecha_reporte, revisado_por_id, fecha_revision) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (ids_ordenes[numero_orden], area_id, ids_referencias[codigo_referencia], cantidad, estado,
             motivo, id_usuario, fecha_actual(), revisado_por, fecha_revision),
        )

        if estado == "APROBADO":
            mover_inventario_de_prueba(conexion, cursor.lastrowid, ids_ordenes[numero_orden], numero_orden,
                                       codigo_referencia, cantidad, ids_usuarios["analista"])


def mover_inventario_de_prueba(conexion, id_reporte, id_orden, numero_orden, codigo_referencia, cantidad, id_analista):
    """Hace lo mismo que la aprobación del analista (entregas.py), pero para los datos de prueba:
    descuenta cada material de la lista (cantidad de la BOM x cantidad entregada)
    y suma el producto entregado.
    """
    import inventario      # Aquí adentro por la misma razón que en insertar_materias_primas
    referencia = conexion.execute(
        "SELECT r.id, r.item_id, a.nombre AS area FROM referencias r JOIN areas a ON a.id = r.area_id "
        "WHERE r.codigo = ?",
        (codigo_referencia,),
    ).fetchone()

    lineas = conexion.execute(
        "SELECT item_id, cantidad FROM lineas_material WHERE referencia_id = ?", (referencia["id"],)
    ).fetchall()
    for linea in lineas:
        consumo = linea["cantidad"] * cantidad
        inventario.registrar_salida(conexion, linea["item_id"], consumo, id_analista,
                                    f"Consumo de {codigo_referencia} · OP {numero_orden}", id_orden, id_reporte)

    inventario.registrar_entrada(conexion, referencia["item_id"], cantidad, id_analista,
                                 f"Entrega de {referencia['area']} · OP {numero_orden}", id_orden, id_reporte)


# ---------------------------------------------------------------------
# 5. Preparar la base al arrancar
# ---------------------------------------------------------------------

def preparar_base_datos():
    """Crea las tablas y, si la base está vacía (sin usuarios), carga los datos de prueba.

    servidor.py llama a esta función cada vez que arranca.
    """
    conexion = conectar()
    crear_tablas(conexion)
    cantidad_usuarios = conexion.execute("SELECT COUNT(*) FROM usuarios").fetchone()[0]
    if cantidad_usuarios == 0:
        cargar_datos_prueba(conexion)
        print("Base de datos nueva: se cargaron los datos de prueba.")
    # commit guarda los cambios en el archivo. Sin commit, se pierden al cerrar.
    conexion.commit()
    conexion.close()


def reiniciar_base_datos():
    """Borra el archivo rymel.db y lo vuelve a crear con los datos de prueba."""
    if os.path.exists(RUTA_BASE_DATOS):
        os.remove(RUTA_BASE_DATOS)
    preparar_base_datos()


def mostrar_resumen():
    """Cuenta las filas de cada tabla, para comprobar que todo se cargó."""
    conexion = conectar()
    tablas = ["areas", "usuarios", "items", "referencias", "lineas_material", "clientes",
              "ordenes", "requerimientos", "reportes", "movimientos"]
    print("Filas por tabla en rymel.db:")
    for tabla in tablas:
        # El nombre de la tabla viene de la lista de arriba (no lo escribe un usuario),
        # por eso aquí sí se puede poner dentro del texto del SQL.
        cantidad = conexion.execute(f"SELECT COUNT(*) FROM {tabla}").fetchone()[0]
        print(f"  {tabla:<16} {cantidad}")
    conexion.close()


# Este bloque solo se ejecuta si se corre "python base_datos.py" directamente,
# no cuando otro archivo hace "import base_datos".
if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "reiniciar":
        reiniciar_base_datos()
        print("Base de datos reiniciada.")
    else:
        preparar_base_datos()
    mostrar_resumen()
