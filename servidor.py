# =====================================================================
# servidor.py
# El servidor web del proyecto. Para arrancarlo:  python servidor.py
# Luego se abre http://localhost:8000 en el navegador.
#
# ¿Qué hace un servidor web? Espera "peticiones" del navegador y las responde:
#   - Si piden una página (/ordenes)       -> envía el archivo HTML.
#   - Si piden un estilo o script          -> envía el archivo .css o .js.
#   - Si piden datos (/api/...)            -> ejecuta una función de Python y
#                                             responde con datos en formato JSON.
# Antes de responder revisa quién es el usuario (su sesión) y si su rol tiene permiso.
#
# Patrones de diseño en este archivo:
#   - GRASP Controlador: atender_api es el único punto que recibe las peticiones
#     de la API y se las pasa a la función que corresponde.
#   - GoF Comando (Command): RUTAS guarda cada "orden" (una función) con su clave;
#     el servidor busca la orden en la tabla y la ejecuta, sin un if gigante.
#   - GRASP Indirección: RUTAS está en medio entre HTTP y las reglas del negocio;
#     catalogo.py, ordenes.py, etc. no saben nada de cookies ni de peticiones.
#   - GRASP Polimorfismo: todas las funciones de RUTAS tienen la misma forma
#     (conexion, usuario, datos), así el servidor las llama a todas igual.
#   - GRASP Variaciones protegidas: PAGINAS y RUTAS concentran en un solo lugar
#     lo que más cambia (páginas, permisos y direcciones).
# =====================================================================

import json
import os
import secrets
import traceback
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, unquote, urlparse

import base_datos
import catalogo
import entregas
import exportar
import inventario
import ordenes

PUERTO = 8000
CARPETA_PROYECTO = os.path.dirname(os.path.abspath(__file__))
CARPETA_PAGINAS = os.path.join(CARPETA_PROYECTO, "paginas")

# Carpetas cuyos archivos se pueden descargar sin iniciar sesión (los necesita el login).
CARPETAS_PUBLICAS = ["estilos", "scripts", "imagenes"]

# El navegador necesita saber qué tipo de archivo recibe para mostrarlo bien.
TIPOS_DE_ARCHIVO = {
    ".html": "text/html; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".js": "text/javascript; charset=utf-8",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".svg": "image/svg+xml",
}

# ---------------------------------------------------------------------
# Roles y páginas
# ---------------------------------------------------------------------

AREA = "AREA"
ANALISTA = "ANALISTA"
SUPERVISOR = "SUPERVISOR"
TODOS = [AREA, ANALISTA, SUPERVISOR]

# Lista de páginas: dirección, título del menú, archivo HTML y roles que pueden verla.
# (GRASP Variaciones protegidas: agregar una página o cambiar un permiso se hace solo aquí.)
# De aquí salen el menú de cada usuario y la protección de las páginas.
# El orden importa: la primera página permitida para un rol es su página de inicio.
PAGINAS = [
    {"ruta": "/aprobaciones", "titulo": "Aprobaciones", "archivo": "aprobaciones.html", "roles": [ANALISTA]},
    {"ruta": "/reporte", "titulo": "Reportar entrega", "archivo": "reporte.html", "roles": [AREA]},
    {"ruta": "/panel", "titulo": "Panel de producción", "archivo": "panel.html", "roles": [SUPERVISOR, ANALISTA]},
    {"ruta": "/ordenes", "titulo": "Órdenes", "archivo": "ordenes.html", "roles": TODOS},
    {"ruta": "/catalogo", "titulo": "Ítems y referencias", "archivo": "catalogo.html", "roles": [ANALISTA]},
    {"ruta": "/estructura", "titulo": "Estructura", "archivo": "estructura.html", "roles": [ANALISTA, SUPERVISOR]},
    {"ruta": "/inventario", "titulo": "Inventario", "archivo": "inventario.html", "roles": [ANALISTA, SUPERVISOR]},
    {"ruta": "/reportes", "titulo": "Reportes", "archivo": "reportes.html", "roles": [ANALISTA, SUPERVISOR]},
]


def buscar_pagina(ruta):
    for pagina in PAGINAS:
        if pagina["ruta"] == ruta:
            return pagina
    return None


def menu_del_rol(rol):
    """Las páginas que puede ver un rol, en el orden de la lista PAGINAS."""
    menu = []
    for pagina in PAGINAS:
        if rol in pagina["roles"]:
            menu.append({"ruta": pagina["ruta"], "titulo": pagina["titulo"]})
    return menu


def ruta_de_inicio(rol):
    return menu_del_rol(rol)[0]["ruta"]


# ---------------------------------------------------------------------
# Sesiones
# Al iniciar sesión se crea una "llave" aleatoria, se guarda en la tabla sesiones
# y se le entrega al navegador en una cookie. En cada petición el navegador
# devuelve la cookie y así sabemos quién es.
# ---------------------------------------------------------------------

NOMBRE_COOKIE = "sesion"


def leer_llave_de_sesion(texto_cookies):
    """Busca la cookie 'sesion' en el encabezado Cookie que envía el navegador."""
    if not texto_cookies:
        return None
    cookies = SimpleCookie()
    cookies.load(texto_cookies)
    if NOMBRE_COOKIE not in cookies:
        return None
    return cookies[NOMBRE_COOKIE].value


def buscar_usuario_de_sesion(conexion, texto_cookies):
    """Devuelve el usuario dueño de la sesión, o None si no ha iniciado sesión."""
    llave = leer_llave_de_sesion(texto_cookies)
    if llave is None:
        return None
    usuario = conexion.execute(
        "SELECT u.id, u.usuario, u.nombre_completo, u.rol, u.area_id, "
        "       a.codigo AS area_codigo, a.nombre AS area_nombre "
        "FROM sesiones s "
        "JOIN usuarios u ON u.id = s.usuario_id "
        "LEFT JOIN areas a ON a.id = u.area_id "   # LEFT JOIN: el analista y el supervisor no tienen área
        "WHERE s.llave = ?",
        (llave,),
    ).fetchone()
    if usuario is None:
        return None
    # Se convierte en diccionario normal para poder enviarlo como JSON.
    return dict(usuario)


def iniciar_sesion(manejador, conexion, datos):
    nombre_usuario = str(datos.get("usuario", "")).strip().lower()
    contrasena = str(datos.get("contrasena", ""))

    fila = conexion.execute("SELECT * FROM usuarios WHERE usuario = ?", (nombre_usuario,)).fetchone()
    # Se cifra lo que escribió el usuario con SU sal y se compara con lo guardado.
    # El mensaje no dice qué estuvo mal (usuario o contraseña) para no darle pistas a un intruso.
    if fila is None or base_datos.cifrar_contrasena(contrasena, fila["sal"]) != fila["contrasena_hash"]:
        enviar_json(manejador, 401, {"error": "Usuario o contraseña incorrectos."})
        return

    llave = secrets.token_urlsafe(32)
    conexion.execute(
        "INSERT INTO sesiones (llave, usuario_id, fecha) VALUES (?, ?, ?)",
        (llave, fila["id"], base_datos.fecha_actual()),
    )
    conexion.commit()
    # HttpOnly: el JavaScript de la página no puede leer la cookie (más seguro).
    # SameSite=Lax: otras páginas web no pueden usar la cookie para hacer peticiones aquí.
    cookie = f"{NOMBRE_COOKIE}={llave}; Path=/; HttpOnly; SameSite=Lax"
    enviar_json(manejador, 200, {"inicio": ruta_de_inicio(fila["rol"])}, cookie)


def cerrar_sesion(manejador, conexion):
    llave = leer_llave_de_sesion(manejador.headers.get("Cookie"))
    conexion.execute("DELETE FROM sesiones WHERE llave = ?", (llave,))
    conexion.commit()
    # Max-Age=0 le dice al navegador que borre la cookie.
    cookie = f"{NOMBRE_COOKIE}=; Path=/; Max-Age=0; HttpOnly; SameSite=Lax"
    enviar_json(manejador, 200, {"ok": True}, cookie)


def consultar_sesion(conexion, usuario, datos):
    """Quién está conectado y qué páginas puede ver (para pintar el menú)."""
    return {"usuario": usuario, "menu": menu_del_rol(usuario["rol"])}


# ---------------------------------------------------------------------
# Rutas de la API  (patrón GoF Comando: una tabla de órdenes)
# Clave: "MÉTODO /dirección". Valor: (función que responde, roles que pueden usarla).
# Cada función recibe (conexion, usuario, datos) y devuelve un diccionario o una lista,
# que el servidor convierte en JSON. En cada entrega se agregan aquí las nuevas rutas.
#
# GET  = consultar (los datos llegan en la dirección: /api/algo?filtro=valor)
# POST = crear o cambiar (los datos llegan en JSON en el cuerpo de la petición)
# ---------------------------------------------------------------------

RUTAS = {
    "GET /api/sesion": (consultar_sesion, TODOS),

    # Entrega 4 · Catálogo: ítems, referencias y listas de materiales
    "GET /api/listas": (catalogo.consultar_listas, TODOS),
    "GET /api/items": (catalogo.listar_items, [ANALISTA, SUPERVISOR]),
    "GET /api/items/siguiente-codigo": (catalogo.sugerir_codigo_item, [ANALISTA]),
    "POST /api/items": (catalogo.crear_item, [ANALISTA]),
    "POST /api/items/editar": (catalogo.editar_item, [ANALISTA]),
    "GET /api/referencias": (catalogo.listar_referencias, [ANALISTA, SUPERVISOR]),
    "GET /api/referencia": (catalogo.consultar_referencia, [ANALISTA, SUPERVISOR]),
    "GET /api/referencias/siguiente-codigo": (catalogo.sugerir_codigo_referencia, [ANALISTA]),
    "POST /api/referencias": (catalogo.crear_referencia, [ANALISTA]),
    "POST /api/referencias/materiales": (catalogo.cambiar_materiales, [ANALISTA]),

    # Entrega 5 · Estructura del producto (árbol)
    "GET /api/estructura": (catalogo.consultar_estructura, [ANALISTA, SUPERVISOR]),

    # Entrega 6 · Clientes y órdenes de producción
    "GET /api/clientes": (ordenes.listar_clientes, [ANALISTA, SUPERVISOR]),
    "POST /api/clientes": (ordenes.crear_cliente, [ANALISTA, SUPERVISOR]),
    "GET /api/ordenes": (ordenes.listar_ordenes, TODOS),
    "GET /api/orden": (ordenes.consultar_orden, TODOS),
    "GET /api/ordenes/siguiente-numero": (ordenes.sugerir_numero_orden, [ANALISTA, SUPERVISOR]),
    "GET /api/ordenes/ensambles": (ordenes.listar_ensambles, [ANALISTA, SUPERVISOR]),
    "GET /api/ordenes/vista-previa": (ordenes.vista_previa_orden, [ANALISTA, SUPERVISOR]),
    "POST /api/ordenes": (ordenes.crear_orden, [ANALISTA, SUPERVISOR]),

    # Entrega 7 · Reporte de entregas por área
    "GET /api/mi-orden": (entregas.consultar_orden_para_area, [AREA]),
    "POST /api/reportes": (entregas.crear_reporte, [AREA]),
    "GET /api/reportes": (entregas.listar_reportes, TODOS),

    # Entrega 8 · Aprobación del analista y movimientos de inventario
    "GET /api/reporte": (entregas.consultar_reporte_para_revision, [ANALISTA]),
    "POST /api/reportes/aprobar": (entregas.aprobar_reporte, [ANALISTA]),
    "POST /api/reportes/rechazar": (entregas.rechazar_reporte, [ANALISTA]),

    # Entrega 9 · Panel del supervisor
    "GET /api/panel": (entregas.consultar_panel, [SUPERVISOR, ANALISTA]),

    # Entrega 10 · Portal de inventarios
    "GET /api/inventario": (inventario.consultar_inventario, [ANALISTA, SUPERVISOR]),
    "GET /api/inventario/movimientos": (inventario.consultar_movimientos, [ANALISTA, SUPERVISOR]),
    "POST /api/inventario/entradas": (inventario.registrar_entrada_mp, [ANALISTA]),

    # Entrega 11 · Exportaciones CSV
    "GET /api/exportar/entregas/vista-previa": (exportar.vista_previa_entregas, [ANALISTA, SUPERVISOR]),
    "GET /api/exportar/entregas": (exportar.exportar_entregas, [ANALISTA, SUPERVISOR]),
    "GET /api/exportar/inventario": (exportar.exportar_inventario, [ANALISTA, SUPERVISOR]),

    # Entrega 12 · Asistente "Nuevo producto"
    "GET /api/producto/plantilla": (catalogo.plantilla_producto, [ANALISTA]),
    "GET /api/producto/copiar": (catalogo.copiar_producto, [ANALISTA]),
    "POST /api/producto/vista-previa": (catalogo.vista_previa_producto, [ANALISTA]),
    "POST /api/producto": (catalogo.crear_producto, [ANALISTA]),
}


# ---------------------------------------------------------------------
# Enviar respuestas al navegador
# Toda respuesta tiene: un código (200 = bien, 302 = ve a otra dirección,
# 400 = datos inválidos, 401 = sin sesión, 403 = sin permiso, 404 = no existe,
# 500 = error del servidor), unos encabezados y el contenido.
# ---------------------------------------------------------------------

def enviar_json(manejador, codigo, datos, cookie=None):
    contenido = json.dumps(datos, ensure_ascii=False).encode("utf-8")
    manejador.send_response(codigo)
    manejador.send_header("Content-Type", "application/json; charset=utf-8")
    manejador.send_header("Content-Length", str(len(contenido)))
    if cookie is not None:
        manejador.send_header("Set-Cookie", cookie)
    manejador.end_headers()
    manejador.wfile.write(contenido)


def enviar_texto(manejador, codigo, texto, tipo="text/html; charset=utf-8"):
    contenido = texto.encode("utf-8")
    manejador.send_response(codigo)
    manejador.send_header("Content-Type", tipo)
    manejador.send_header("Content-Length", str(len(contenido)))
    manejador.end_headers()
    manejador.wfile.write(contenido)


def enviar_archivo(manejador, ruta_archivo):
    """Envía un archivo del disco (HTML, CSS, JS o imagen)."""
    if not os.path.isfile(ruta_archivo):
        enviar_texto(manejador, 404, "Archivo no encontrado.", "text/plain; charset=utf-8")
        return
    extension = os.path.splitext(ruta_archivo)[1].lower()
    tipo = TIPOS_DE_ARCHIVO.get(extension, "application/octet-stream")
    # "rb" = leer en binario: sirve igual para texto e imágenes.
    with open(ruta_archivo, "rb") as archivo:
        contenido = archivo.read()
    manejador.send_response(200)
    manejador.send_header("Content-Type", tipo)
    manejador.send_header("Content-Length", str(len(contenido)))
    # no-cache: el navegador siempre pide la versión nueva (útil mientras se programa).
    manejador.send_header("Cache-Control", "no-cache")
    manejador.end_headers()
    manejador.wfile.write(contenido)


def enviar_descarga(manejador, descarga):
    """Envía un archivo para descargar (los CSV de exportar.py).

    descarga = {"contenido": bytes, "nombre": "inventario_2026-10-26.csv", "tipo": "text/csv..."}
    """
    manejador.send_response(200)
    manejador.send_header("Content-Type", descarga["tipo"])
    manejador.send_header("Content-Length", str(len(descarga["contenido"])))
    # attachment: el navegador lo descarga con ese nombre en vez de mostrarlo.
    manejador.send_header("Content-Disposition", f'attachment; filename="{descarga["nombre"]}"')
    manejador.end_headers()
    manejador.wfile.write(descarga["contenido"])


def redirigir(manejador, ruta):
    """Le dice al navegador que vaya a otra dirección."""
    manejador.send_response(302)
    manejador.send_header("Location", ruta)
    manejador.end_headers()


# ---------------------------------------------------------------------
# Leer lo que envía el navegador
# ---------------------------------------------------------------------

def leer_parametros(texto_consulta):
    """'op=1001&area=NUCLEO' -> {"op": "1001", "area": "NUCLEO"}"""
    parametros = {}
    valores = parse_qs(texto_consulta)   # parse_qs devuelve listas: {"op": ["1001"]}
    for nombre in valores:
        parametros[nombre] = valores[nombre][0]
    return parametros


def leer_cuerpo_json(manejador):
    """Lee el JSON que envía el navegador en un POST. Si no hay o está mal, devuelve {}."""
    largo = int(manejador.headers.get("Content-Length") or 0)
    if largo == 0:
        return {}
    texto = manejador.rfile.read(largo).decode("utf-8")
    try:
        datos = json.loads(texto)
    except json.JSONDecodeError:
        return {}
    if not isinstance(datos, dict):
        return {}
    return datos


# ---------------------------------------------------------------------
# Atender cada petición
# ---------------------------------------------------------------------

def atender_peticion(manejador, metodo):
    direccion = urlparse(manejador.path)       # separa "/api/ordenes" de "?op=1001"
    ruta = unquote(direccion.path)             # convierte "%C3%B3" en "ó", etc.
    conexion = base_datos.conectar()           # una conexión por petición
    try:
        usuario = buscar_usuario_de_sesion(conexion, manejador.headers.get("Cookie"))
        if ruta.startswith("/api/"):
            atender_api(manejador, conexion, metodo, ruta, direccion.query, usuario)
        elif metodo == "GET":
            atender_archivo_o_pagina(manejador, ruta, usuario)
        else:
            enviar_texto(manejador, 404, "No encontrado.", "text/plain; charset=utf-8")
    finally:
        # finally se ejecuta siempre, haya error o no: la conexión nunca queda abierta.
        conexion.close()


def atender_api(manejador, conexion, metodo, ruta, texto_consulta, usuario):
    # Patrón GRASP Controlador: todas las peticiones de la API pasan por aquí.
    # Iniciar y cerrar sesión son especiales porque crean o borran la cookie.
    if metodo == "POST" and ruta == "/api/login":
        iniciar_sesion(manejador, conexion, leer_cuerpo_json(manejador))
        return
    if metodo == "POST" and ruta == "/api/logout":
        cerrar_sesion(manejador, conexion)
        return

    clave = metodo + " " + ruta
    if clave not in RUTAS:
        enviar_json(manejador, 404, {"error": "Esa dirección de la API no existe."})
        return
    funcion, roles_permitidos = RUTAS[clave]

    if usuario is None:
        enviar_json(manejador, 401, {"error": "Debes iniciar sesión."})
        return
    if usuario["rol"] not in roles_permitidos:
        enviar_json(manejador, 403, {"error": "No tienes permiso para esta acción."})
        return

    if metodo == "GET":
        datos = leer_parametros(texto_consulta)
    else:
        datos = leer_cuerpo_json(manejador)

    try:
        respuesta = funcion(conexion, usuario, datos)
        # Si la función terminó sin errores, se guardan TODOS sus cambios juntos.
        conexion.commit()
    except ValueError as error:
        # Las funciones avisan de datos inválidos con: raise ValueError("mensaje para el usuario").
        # rollback deshace todo lo que alcanzó a hacer la función: nada queda a medias.
        conexion.rollback()
        enviar_json(manejador, 400, {"error": str(error)})
        return
    except Exception:
        # Cualquier otro error es un fallo del programa: se muestra en la terminal para corregirlo.
        conexion.rollback()
        traceback.print_exc()
        enviar_json(manejador, 500, {"error": "Ocurrió un error inesperado en el servidor."})
        return

    if isinstance(respuesta, dict) and "descarga" in respuesta:
        enviar_descarga(manejador, respuesta["descarga"])
    else:
        enviar_json(manejador, 200, respuesta)


def atender_archivo_o_pagina(manejador, ruta, usuario):
    # 1. Archivos públicos: /estilos/estilos.css, /scripts/comun.js, /imagenes/logo.png
    partes = ruta.strip("/").split("/")
    if len(partes) == 2 and partes[0] in CARPETAS_PUBLICAS:
        # basename se queda solo con el nombre del archivo. Así nadie puede pedir
        # "/scripts/../servidor.py" para leer archivos que no debe ver.
        nombre_archivo = os.path.basename(partes[1])
        enviar_archivo(manejador, os.path.join(CARPETA_PROYECTO, partes[0], nombre_archivo))
        return

    # 2. La raíz: lleva al login o a la página de inicio del rol.
    if ruta == "/":
        if usuario is None:
            redirigir(manejador, "/login")
        else:
            redirigir(manejador, ruta_de_inicio(usuario["rol"]))
        return

    # 3. El login: si ya inició sesión, no tiene sentido mostrarlo otra vez.
    if ruta == "/login":
        if usuario is not None:
            redirigir(manejador, ruta_de_inicio(usuario["rol"]))
        else:
            enviar_pagina(manejador, "login.html")
        return

    # 4. Las páginas de la lista PAGINAS, solo para quien tenga el rol.
    pagina = buscar_pagina(ruta)
    if pagina is None:
        enviar_texto(manejador, 404, "Página no encontrada.", "text/plain; charset=utf-8")
    elif usuario is None:
        redirigir(manejador, "/login")
    elif usuario["rol"] not in pagina["roles"]:
        redirigir(manejador, ruta_de_inicio(usuario["rol"]))
    else:
        enviar_pagina(manejador, pagina["archivo"])


def enviar_pagina(manejador, nombre_archivo):
    ruta_archivo = os.path.join(CARPETA_PAGINAS, nombre_archivo)
    if os.path.isfile(ruta_archivo):
        enviar_archivo(manejador, ruta_archivo)
    else:
        # Mientras se construye el proyecto, algunas páginas todavía no existen.
        enviar_texto(manejador, 200,
                     f"<h1>Página en construcción</h1><p>El archivo paginas/{nombre_archivo} "
                     f"llega en una próxima entrega.</p><p><a href='/'>Volver</a></p>")


# ---------------------------------------------------------------------
# La única clase del proyecto
# http.server exige una clase con los métodos do_GET y do_POST: los llama
# cada vez que llega una petición GET o POST. Aquí solo le pasan el trabajo
# a la función atender_peticion de arriba.
# ---------------------------------------------------------------------

class ManejadorPeticiones(BaseHTTPRequestHandler):
    def do_GET(self):
        atender_peticion(self, "GET")

    def do_POST(self):
        atender_peticion(self, "POST")


def iniciar_servidor():
    base_datos.preparar_base_datos()
    # ThreadingHTTPServer atiende varias peticiones a la vez. Así el navegador nunca
    # se queda esperando mientras carga los estilos, los scripts y los datos de una página.
    servidor = ThreadingHTTPServer(("localhost", PUERTO), ManejadorPeticiones)
    print(f"Servidor listo en http://localhost:{PUERTO}  (Ctrl+C para detenerlo)")
    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        print("\nServidor detenido.")
    servidor.server_close()


if __name__ == "__main__":
    iniciar_servidor()
