# RymelView · Explicación del proyecto

**RymelView** es el sistema de inventario y reporte de producción de Rymel S.A.S.

Guía de estudio del sistema de inventario y reporte de producción de Rymel SAS.
Está pensada para leerla junto al código, entrega por entrega.

**Tecnologías:** solo Python (con lo que trae incluido), HTML, CSS y JavaScript.
No se instala nada. Se ejecuta con `python servidor.py` y se abre en <http://localhost:8000>.

## Contenido

1. [Guía rápida: ejecutar el proyecto desde cero](#guía-rápida-ejecutar-el-proyecto-desde-cero)
2. [Usuarios de prueba y qué ve cada rol](#usuarios-de-prueba-y-qué-ve-cada-rol)
3. [Recorrido de prueba completo](#recorrido-de-prueba-completo)
4. [Problemas frecuentes](#problemas-frecuentes)
5. [Árbol de carpetas](#árbol-de-carpetas) y [conceptos del negocio](#conceptos-del-negocio)
6. Explicación por entregas:
   1. `base_datos.py`
   2. `servidor.py`
   3. Estilos, `comun.js` y login
   4. Catálogo (ítems y referencias)
   5. Estructura (árbol)
   6. Órdenes de producción
   7. Reporte de entregas
   8. Aprobaciones e inventario
   9. Panel del supervisor
   10. Portal de inventarios
   11. Exportaciones CSV
   12. Asistente "Nuevo producto"
7. [Patrones de diseño (GRASP y GoF)](#patrones-de-diseño-grasp-y-gof)
8. [Mapa completo de la API](#mapa-completo-de-la-api)
9. [Preguntas de repaso](#preguntas-de-repaso)

> Las secciones "Cómo probarlo" de cada entrega cuentan cómo se probó esa parte en el momento
> en que se construyó. Por ejemplo, la entrega 2 habla de "Página en construcción" porque las
> páginas aún no existían. Para probar el sistema terminado, usa el
> [recorrido de prueba completo](#recorrido-de-prueba-completo).

---

## Guía rápida: ejecutar el proyecto desde cero

**Requisito:** Python 3.8 o más reciente. Para revisarlo, en la terminal: `python --version`.
No hace falta instalar nada más: ni `pip install` ni entornos virtuales.

1. Abre la carpeta `rymel-sencillo` en VS Code (o en una terminal).
2. En la terminal, dentro de esa carpeta, ejecuta:
   ```
   python servidor.py
   ```
3. Debe aparecer:
   ```
   Base de datos nueva: se cargaron los datos de prueba.
   Servidor listo en http://localhost:8000  (Ctrl+C para detenerlo)
   ```
   (La primera línea solo sale la primera vez, cuando se crea `rymel.db`.)
4. Abre <http://localhost:8000> en el navegador e inicia sesión con uno de los usuarios de abajo.
5. Para **detener** el servidor: **Ctrl+C** en la terminal.

**Volver a los datos de prueba originales** (borra todo lo que hayas creado):

```
python base_datos.py reiniciar
```

Hazlo con el servidor detenido. Después vuelve a ejecutar `python servidor.py`.

**El logo:** coloca la imagen oficial en `imagenes/logo.png`. Mientras no exista, se muestra el
texto **RYMEL**.

---

## Usuarios de prueba y qué ve cada rol

Todos usan la contraseña **`rymel123`**.

| Usuario | Rol | Página de inicio | Menú |
|---|---|---|---|
| `nucleo` | Área · Núcleo | Reportar entrega | Reportar entrega, Órdenes |
| `bobinado` | Área · Bobinado | Reportar entrega | Reportar entrega, Órdenes |
| `pactiva` | Área · Parte activa | Reportar entrega | Reportar entrega, Órdenes |
| `metalmec` | Área · Metalmecánica | Reportar entrega | Reportar entrega, Órdenes |
| `pintura` | Área · Pintura | Reportar entrega | Reportar entrega, Órdenes |
| `ensamble` | Área · Ensamble final | Reportar entrega | Reportar entrega, Órdenes |
| `analista` | Analista | Aprobaciones | Aprobaciones, Panel de producción, Órdenes, Ítems y referencias, Estructura, Inventario, Reportes |
| `supervisor` | Supervisor | Panel de producción | Panel de producción, Órdenes, Estructura, Inventario, Reportes |

**Qué puede hacer cada rol:**

| Función | Áreas | Analista | Supervisor |
|---|:---:|:---:|:---:|
| Reportar entregas de su área | ✔ | | |
| Consultar órdenes de producción | ✔ | ✔ | ✔ |
| Crear órdenes de producción y clientes | | ✔ | ✔ |
| Aprobar o rechazar entregas | | ✔ | |
| Crear ítems, referencias y "Nuevo producto" | | ✔ | |
| Ver la estructura (árbol) | | ✔ | ✔ |
| Panel de producción | | ✔ | ✔ |
| Ver inventario e historial | | ✔ | ✔ |
| Registrar entradas de materia prima | | ✔ | |
| Exportar CSV (entregas e inventario) | | ✔ | ✔ |

---

## Recorrido de prueba completo

Empieza con datos limpios (`python base_datos.py reiniciar`) y sigue este orden. Así recorres el
proceso de punta a punta, como en la planta.

**1. Supervisor: crear una OP**
- Entra con `supervisor` → **Panel**: Pendiente 16 · En proceso 2 · Por revisar 2 · Rechazados 1.
- **Órdenes → Nueva OP**:
  - elige **PT-0003** → no deja crearla (le falta el tanque);
  - elige **PT-0001**, cantidad **2**, crea un cliente nuevo y guarda la **OP 1004**.

**2. Áreas: reportar**
- Entra con `nucleo` → **Reportar entrega** → OP **1004** → reporta **2**.
- Haz lo mismo con `bobinado` (2) y `metalmec` (2).

**3. Analista: aprobar**
- Entra con `analista` → **Aprobaciones**: aprueba los tres reportes de la OP 1004.
  - En cada uno mira qué sale del inventario: chapa, alambre, lámina.
- **Inventario** → historial de **MP-0001**: aparece el consumo de la OP 1004.

**4. Siguen las áreas**
- `pactiva` reporta 2 en la OP 1004 → el analista aprueba (consume los núcleos y bobinados aprobados).
- `pintura` reporta 2 → el analista aprueba (consume los tanques).
- `ensamble` reporta 2 → el analista aprueba → **PT-0001** queda con 2 en el inventario.

**5. Revisar el resultado**
- **Órdenes → OP 1004 → Ver detalle**: todas las áreas con 0 pendientes y estado **Completa**.
- **Panel**: la fila de la OP 1004 aparece toda en **Aprobado**.

**6. Rechazo y faltantes**
- `nucleo` reporta en la OP 1001.
- El analista lo **rechaza** con un motivo.
- `nucleo` ve el motivo en su historial.

**7. Exportar**
- **Reportes → Exportar a CSV** y **Inventario → Exportar inventario a CSV**.
- Abre los archivos con doble clic en Excel.

**8. Nuevo producto**
- `analista` → **Ítems y referencias → Nuevo producto**: copia el PT-0002, cambia la descripción,
  revisa y crea.
- Míralo en **Estructura** y créale una OP en **Órdenes**.

---

## Problemas frecuentes

| Problema | Solución |
|---|---|
| `python` no se reconoce como comando | Python no está instalado o no está en el PATH. Instálalo desde python.org y marca "Add Python to PATH". En Windows también puedes probar con `py servidor.py` |
| `OSError: [Errno 98]` / `[WinError 10048]` (puerto en uso) | Ya hay un servidor corriendo en el puerto 8000. Detén el otro con Ctrl+C, o cambia `PUERTO = 8000` en `servidor.py` |
| La página no cambia después de editar un archivo | Recarga con **Ctrl+F5**. Si cambiaste un `.py`, detén el servidor (Ctrl+C) y vuelve a ejecutarlo |
| Aparece "Ocurrió un error inesperado en el servidor" | Mira la terminal donde corre `servidor.py`: ahí está el error de Python con la línea exacta |
| En la consola del navegador (F12) salen errores 404 de `logo.png` o `favicon.ico` | Es normal: el logo aún no se ha colocado y el navegador busca un ícono por su cuenta |
| Excel muestra todo el CSV en una sola columna | Ese computador tiene Windows configurado en inglés. Exporta con **Formato del archivo: CSV estándar**, o en Excel: **Datos → Desde texto/CSV → Delimitador: Punto y coma** |
| Quiero empezar de cero | Detén el servidor y ejecuta `python base_datos.py reiniciar` |
| Quiero abrirlo desde una tablet en la misma red | En `servidor.py`, cambia `"localhost"` por `"0.0.0.0"` en `iniciar_servidor`. Luego, en la tablet, abre `http://IP-DEL-COMPUTADOR:8000`. Solo en redes de confianza |

---

## Árbol de carpetas

```
rymel-sencillo/
├── servidor.py          Arranca el servidor web, revisa sesión y rol, y responde
├── base_datos.py        Tablas, datos de prueba y conexión con SQLite
├── catalogo.py          Ítems, referencias, listas de materiales, estructura y "Nuevo producto"
├── ordenes.py           Clientes, creación y consulta de órdenes de producción
├── entregas.py          Reportes de entrega, aprobación y panel
├── inventario.py        Existencias: entradas, salidas, consulta e historial
├── exportar.py          Reportes CSV (con dos formatos)
├── README.md            Este documento
├── paginas/             Un HTML por pantalla
│   ├── login.html
│   ├── reporte.html         (áreas)
│   ├── aprobaciones.html    (analista)
│   ├── panel.html           (supervisor y analista)
│   ├── ordenes.html         (todos)
│   ├── catalogo.html        (analista: ítems, referencias y nuevo producto)
│   ├── estructura.html      (analista y supervisor)
│   ├── inventario.html      (analista y supervisor)
│   └── reportes.html        (analista y supervisor)
├── estilos/
│   └── estilos.css      Todo el diseño; los colores, arriba
├── scripts/
│   ├── comun.js         Funciones de todas las páginas (servidor, menú, avisos, árbol)
│   ├── login.js
│   ├── reporte.js
│   ├── aprobaciones.js
│   ├── panel.js
│   ├── ordenes.js
│   ├── catalogo.js      Pestañas Ítems y Referencias
│   ├── asistente.js     Pestaña Nuevo producto
│   ├── estructura.js
│   ├── inventario.js
│   └── reportes.js
├── imagenes/
│   └── logo.png         (opcional; si no está, se muestra "RYMEL")
└── rymel.db             La base de datos (se crea sola)
```

**Cómo se conectan los archivos de Python** (cada flecha = "importa a"):

```
servidor.py ──► base_datos.py
            ──► catalogo.py ──► base_datos.py
            ──► ordenes.py  ──► catalogo.py
            ──► entregas.py ──► catalogo.py, ordenes.py, inventario.py
            ──► inventario.py ──► base_datos.py, catalogo.py
            ──► exportar.py ──► base_datos.py

base_datos.py ··► inventario.py   (solo dentro de las funciones de datos de prueba)
```

## Conceptos del negocio

| Término | Significa |
|---|---|
| **MP** | Materia prima: lo que se compra (chapa, alambre, aceite...). |
| **PP** | Producto en proceso: lo que fabrica un área y consume otra (núcleo, tanque...). |
| **PT** | Producto terminado: el transformador que se despacha. |
| **Referencia** | Lo que fabrica un área, con código `ÁREA-número` (ej. `NUCLEO-001`). Produce un ítem. |
| **Lista de materiales (BOM)** | Qué consume una referencia y cuánto por cada unidad. |
| **OP** | Orden de producción: cuántos transformadores fabricar y para qué cliente. |

Flujo de la planta:

```
Núcleo ──┐
         ├──► Parte activa ──┐
Bobinado ┘                   ├──► Ensamble final (PT)
Metalmecánica ──► Pintura ───┘
```

---

## Entrega 1 · `base_datos.py`

### ¿Qué es una base de datos SQLite?

Es un **solo archivo** (`rymel.db`) que guarda la información en **tablas**, como hojas
de Excel: cada fila es un registro y cada columna, un dato. Python trae el módulo
`sqlite3` para usarla, así que no hay que instalar nada.

Para hablar con la base se usa el lenguaje **SQL**:

| Instrucción | Para qué |
|---|---|
| `CREATE TABLE` | Crear una tabla |
| `INSERT INTO ... VALUES` | Agregar una fila |
| `SELECT ... FROM ... WHERE` | Consultar filas |
| `UPDATE ... SET` | Cambiar datos |
| `JOIN` | Unir dos tablas por una columna en común |

### Las 11 tablas

| Tabla | Guarda | Se relaciona con |
|---|---|---|
| `areas` | Las 6 áreas de la planta, en orden | — |
| `usuarios` | Usuario, contraseña cifrada, rol y área | `areas` |
| `sesiones` | Quién tiene la sesión abierta (una llave por inicio de sesión) | `usuarios` |
| `items` | Todos los MP, PP y PT, con su existencia | — |
| `referencias` | Qué fabrica cada área y qué ítem produce | `areas`, `items` |
| `lineas_material` | La lista de materiales de cada referencia | `referencias`, `items` |
| `clientes` | NIT y nombre | — |
| `ordenes` | Número de OP, ensamble, cliente y cantidad | `referencias`, `clientes`, `usuarios` |
| `requerimientos` | Cuánto debe entregar cada área en cada OP | `ordenes`, `areas`, `referencias` |
| `reportes` | Las entregas que reportan las áreas y su estado | `ordenes`, `areas`, `usuarios` |
| `movimientos` | Historial de entradas y salidas de inventario | `items`, `ordenes`, `reportes` |

Reglas que se escriben en la propia tabla:

- `PRIMARY KEY`: el `id`, un número único por fila que SQLite asigna solo.
- `UNIQUE`: no se puede repetir (dos ítems con el mismo código, dos OP con el mismo número).
- `NOT NULL`: dato obligatorio.
- `REFERENCES`: **llave foránea**. El valor debe existir en otra tabla. Por ejemplo,
  no se puede crear una referencia con un `area_id` que no exista.
- `CHECK`: una condición. Por ejemplo, `tipo IN ('MP', 'PP', 'PT')` o `cantidad > 0`.

### ¿Por qué existe la tabla `requerimientos`?

Lo que debe producir cada área se calcula **una vez, al crear la OP**:
cantidad de la OP × cantidad de la lista de materiales. Se guarda para que, si después
alguien cambia la lista de materiales, las OP que ya existían no cambien.

### Contraseñas: nunca se guardan tal cual

```python
def cifrar_contrasena(contrasena, sal):
    codigo = hashlib.pbkdf2_hmac("sha256", contrasena.encode("utf-8"), sal.encode("utf-8"), 100000)
    return codigo.hex()
```

1. **Cifrar (hash):** convierte `rymel123` en un código largo que **no se puede devolver**
   a la contraseña original.
2. **Sal:** un texto aleatorio distinto para cada usuario, que se mezcla con la contraseña.
   Así, dos personas con la misma contraseña quedan con códigos distintos.
3. **100.000 repeticiones:** hacen que probar contraseñas al azar sea muy lento para un atacante.
4. **Al iniciar sesión** (en `servidor.py`) se cifra lo que escribió el usuario con su sal
   y se compara con el código guardado. Si coinciden, la contraseña es correcta.

### Siempre `?` en el SQL

```python
conexion.execute("INSERT INTO clientes (nit, nombre) VALUES (?, ?)", (nit, nombre))
```

Los valores **nunca** se pegan dentro del texto del SQL. Se ponen `?` y los valores van
aparte. Así, si alguien escribe algo malicioso en un formulario, SQLite lo trata como
texto y no como una orden. Esto evita la **inyección SQL**.

La única excepción del archivo está en `mostrar_resumen`: el nombre de la tabla va dentro
del texto porque sale de una lista escrita en el código, no de un usuario.

### Recorrido del archivo, de arriba hacia abajo

1. **`conectar()`**: abre `rymel.db`. Con `row_factory = sqlite3.Row` cada fila se lee por
   nombre (`fila["codigo"]`). Con `PRAGMA foreign_keys = ON` SQLite revisa las llaves foráneas.
2. **`fecha_actual()`**: la fecha como texto `2026-10-26 14:30`. En ese orden
   (año-mes-día), ordenar como texto también ordena por fecha.
3. **`nueva_sal()` y `cifrar_contrasena()`**: lo explicado arriba.
4. **`SQL_TABLAS` y `crear_tablas()`**: el texto con todos los `CREATE TABLE`.
   `IF NOT EXISTS` evita errores si la tabla ya existe.
5. **Listas de datos de prueba** (`AREAS`, `USUARIOS`, `MATERIAS_PRIMAS`, `REFERENCIAS`,
   `CLIENTES`, `ORDENES`, `REPORTES`): los datos escritos como listas de tuplas, fáciles de leer y cambiar.
6. **`cargar_datos_prueba()`**: llama a las funciones `insertar_...` **en orden**, porque
   cada cosa necesita lo anterior: un usuario necesita su área, una referencia necesita su ítem.
7. **Funciones `insertar_...`**: recorren su lista con un `for` y hacen un `INSERT` por fila.
   Devuelven un diccionario `{código: id}` (con `cursor.lastrowid`) para que la siguiente
   función encuentre los ids. Ejemplo: `ids_areas["NUCLEO"]` → `1`.
8. **`mover_inventario_de_prueba()`**: el reporte aprobado de
   Núcleo (4 núcleos) descuenta 4 × 80 = 320 kg de chapa (queda en 1.680) y suma 4 núcleos.
   Cada cambio queda en `movimientos`. *(Al aplicar los patrones de diseño, la función que
   cambia la existencia pasó a `inventario.py`; ver "Patrones de diseño".)*
9. **`preparar_base_datos()`**: crea las tablas y, **solo si no hay usuarios**, carga los
   datos de prueba. Termina con `commit()`, que **guarda** los cambios en el archivo.
   Sin `commit`, todo se pierde al cerrar.
10. **`if __name__ == "__main__":`**: este bloque solo corre si ejecutas el archivo
    directamente, no cuando otro archivo hace `import base_datos`.

### Cómo se conecta con los demás archivos

- `servidor.py` llamará a `preparar_base_datos()` al arrancar y usará `cifrar_contrasena()`
  para el inicio de sesión.
- `catalogo.py`, `ordenes.py`, `entregas.py` y `exportar.py` usarán `conectar()` para
  consultar y `fecha_actual()` para las fechas.

### Cómo probarlo

En la terminal, dentro de la carpeta `rymel-sencillo`:

```
python base_datos.py
```

Debe mostrar:

```
Base de datos nueva: se cargaron los datos de prueba.
Filas por tabla en rymel.db:
  areas            6
  usuarios         8
  items            20
  referencias      13
  lineas_material  26
  clientes         3
  ordenes          3
  requerimientos   18
  reportes         4
  movimientos      9
```

- Si lo ejecutas otra vez, ya no dice "Base de datos nueva", porque ya hay usuarios.
- Para empezar de cero: `python base_datos.py reiniciar` (**borra todo**).

¿Por qué esos números?
- 20 ítems = 7 MP + 10 PP + 3 PT.
- 18 requerimientos = 3 OP × 6 áreas.
- 9 movimientos = 7 entradas de inventario inicial + 1 salida de chapa + 1 entrada de núcleos.

### Datos de prueba

| Dato | Contenido |
|---|---|
| Usuarios | `nucleo`, `bobinado`, `pactiva`, `metalmec`, `pintura`, `ensamble`, `analista`, `supervisor`. Contraseña: `rymel123` |
| Materias primas | MP-0001 a MP-0007, con existencia inicial |
| Productos | Transformador 45 kVA (`ENSAMBLE-001`) y 75 kVA (`ENSAMBLE-002`), completos |
| Ensamble incompleto | `ENSAMBLE-003`, sin tanque, para probar que no deja crear la OP |
| Clientes | Energía del Valle S.A.S., Constructora Andina Ltda., Distribuidora Eléctrica del Norte S.A. |
| OP | 1001 (10 × 45 kVA), 1002 (5 × 75 kVA), 1003 (3 × 45 kVA) |
| Reportes | Núcleo 1001: 4 aprobadas y 3 pendientes · Bobinado 1001: 5 pendientes · Metalmecánica 1002: 2 rechazadas |

---

## Entrega 2 · `servidor.py`

### ¿Qué es un servidor web?

Un programa que **espera peticiones** del navegador y las **responde**. Cada vez que
escribes una dirección o una página pide datos, el navegador envía una petición:

```
Navegador  ── GET /ordenes ──────────────►  servidor.py  → envía paginas/ordenes.html
Navegador  ── GET /scripts/ordenes.js ───►  servidor.py  → envía el archivo .js
Navegador  ── GET /api/ordenes?op=1001 ──►  servidor.py  → ejecuta una función de Python
                                                           y responde datos en JSON
```

- **GET** = consultar. Los datos van en la dirección: `/api/ordenes?op=1001`.
- **POST** = crear o cambiar. Los datos van "escondidos" en el cuerpo, en formato JSON.
- **JSON** = texto con la misma forma de un diccionario de Python: `{"numero": "1001", "cantidad": 10}`.
  JavaScript y Python lo entienden los dos.

### Códigos de respuesta

| Código | Significa | Cuándo lo usamos |
|---|---|---|
| 200 | Todo bien | Respuesta normal |
| 302 | Ve a otra dirección | Sin sesión → `/login`; página de otro rol → tu inicio |
| 400 | Datos inválidos | Una validación falló (`ValueError`) |
| 401 | Sin sesión | No has iniciado sesión |
| 403 | Sin permiso | Tu rol no puede usar esa función |
| 404 | No existe | Dirección desconocida |
| 500 | Error del servidor | Un fallo del programa (se ve en la terminal) |

### Recorrido del archivo

1. **Configuración:** `PUERTO = 8000`, las carpetas públicas (`estilos`, `scripts`,
   `imagenes`) y `TIPOS_DE_ARCHIVO`, que le dice al navegador si recibe HTML, CSS,
   JavaScript o una imagen.
2. **`PAGINAS`:** la lista de páginas con su título y los roles que pueden verla. De esta
   única lista salen el **menú** de cada usuario (`menu_del_rol`) y la **protección** de
   las páginas. La primera página permitida es la de inicio: el analista empieza en
   Aprobaciones, las áreas en Reportar entrega y el supervisor en el Panel.
3. **Sesiones:**
   - `iniciar_sesion`: busca el usuario, cifra lo que escribió con **su sal** y lo compara
     con lo guardado. Si coincide, crea una **llave aleatoria** (`secrets.token_urlsafe`),
     la guarda en la tabla `sesiones` y se la envía al navegador en una **cookie**.
   - En cada petición siguiente, el navegador devuelve la cookie solo.
     `buscar_usuario_de_sesion` lee la llave y encuentra al usuario con un `JOIN`.
   - `cerrar_sesion`: borra la llave de la tabla y le pide al navegador borrar la cookie.
   - La cookie es `HttpOnly` (el JavaScript de la página no la puede leer) y
     `SameSite=Lax` (otras páginas web no la pueden usar).
4. **`RUTAS`:** el diccionario de la API. Ejemplo:
   ```python
   "GET /api/sesion": (consultar_sesion, TODOS),
   ```
   Se lee así: "cuando llegue un GET a `/api/sesion`, ejecuta `consultar_sesion`, y
   pueden usarla todos los roles". **En cada entrega se agregan aquí las rutas nuevas.**
5. **Enviar respuestas:** `enviar_json`, `enviar_texto`, `enviar_archivo`, `enviar_descarga`
   (para los CSV de la entrega 11) y `redirigir`.
6. **Leer lo que llega:** `leer_parametros` convierte `op=1001&area=NUCLEO` en un
   diccionario; `leer_cuerpo_json` lee el JSON de un POST.
7. **`atender_peticion`:** el punto de entrada de cada petición:
   - abre una conexión a la base;
   - busca quién es el usuario;
   - decide si es de la API (`/api/...`) o un archivo o página;
   - **siempre** cierra la conexión (`finally`).
8. **`atender_api`:**
   1. Login y logout tienen trato especial porque manejan la cookie.
   2. Busca la ruta en `RUTAS` → 404 si no existe.
   3. Sin sesión → 401. Rol no permitido → 403.
   4. Ejecuta la función con `(conexion, usuario, datos)`.
   5. Si todo salió bien → `commit()` (guarda **todos** los cambios juntos).
   6. Si la función hizo `raise ValueError("mensaje")` → `rollback()` (deshace **todo**)
      y responde 400 con el mensaje.

   Así ninguna operación queda a medias. Por ejemplo, una aprobación que descuenta
   tres materiales nunca descuenta solo dos.
9. **`atender_archivo_o_pagina`:**
   - Archivos públicos: `os.path.basename` deja solo el nombre del archivo, así nadie
     puede pedir `/scripts/../servidor.py` para leer el código.
   - `/` → login o página de inicio.
   - `/login` → la página de login (o tu inicio, si ya iniciaste sesión).
   - Páginas de `PAGINAS` → solo con sesión y con el rol correcto.
   - Si el HTML todavía no existe, muestra "Página en construcción".
10. **`ManejadorPeticiones`:** la **única clase** del proyecto. `http.server` exige una clase
    con `do_GET` y `do_POST`; las nuestras solo llaman a `atender_peticion`.
11. **`iniciar_servidor`:** prepara la base de datos, crea el servidor y lo deja escuchando
    (`serve_forever`) hasta que presiones Ctrl+C.

**¿Por qué `ThreadingHTTPServer`?** Atiende **varias peticiones a la vez**, en lugar de una sola. Con una sola, Chrome a veces deja una
conexión abierta "por si acaso" y el servidor se queda esperándola sin atender las demás.
Igual viene incluido con Python, y cada petición usa su propia conexión a la base.

### Cómo se conecta con los demás archivos

- Usa `base_datos.preparar_base_datos()`, `conectar()`, `cifrar_contrasena()` y `fecha_actual()`.
- `catalogo.py`, `ordenes.py`, `entregas.py` y `exportar.py` tienen funciones con la forma
  `funcion(conexion, usuario, datos)`, registradas en `RUTAS`.
- Las páginas HTML y los scripts se servirán desde `paginas/`, `estilos/` y `scripts/`.

### Cómo probarlo

1. En la terminal, dentro de `rymel-sencillo`:
   ```
   python servidor.py
   ```
   Debe decir `Servidor listo en http://localhost:8000`. Si `rymel.db` no existía, también
   dice que cargó los datos de prueba.
2. Abre <http://localhost:8000>. Te lleva a `/login`. (Cuando se construyó esta entrega
   mostraba "Página en construcción", porque `login.html` llegó en la entrega 3.)
3. Abre <http://localhost:8000/api/sesion>. Debe responder
   `{"error": "Debes iniciar sesión."}` (código 401).
4. **Probar el login sin página.** Estando en <http://localhost:8000/login>, presiona **F12**,
   ve a la pestaña **Consola** y pega:
   ```js
   await fetch("/api/login", {method: "POST", headers: {"Content-Type": "application/json"},
     body: JSON.stringify({usuario: "nucleo", contrasena: "rymel123"})}).then(r => r.json())
   ```
   Debe responder `{inicio: "/reporte"}`. Luego abre otra vez <http://localhost:8000/api/sesion>:
   ahora muestra tu usuario, tu área y tu menú (`Reportar entrega`, `Órdenes`).
5. Con esa sesión, abre <http://localhost:8000/aprobaciones>. Te devuelve a `/reporte`,
   porque esa página es solo del analista.
6. Para detener el servidor: **Ctrl+C** en la terminal.

---

## Entrega 3 · `estilos.css`, `comun.js` y la página de login

### Cómo trabajan juntos HTML, CSS y JavaScript

| Lenguaje | Para qué | Ejemplo en el proyecto |
|---|---|---|
| **HTML** | La estructura: qué hay en la página | `paginas/login.html`: un formulario con usuario, contraseña y un botón |
| **CSS** | La apariencia: colores, tamaños, posiciones | `estilos/estilos.css`: el panel azul, los botones en píldora |
| **JavaScript** | El comportamiento: qué pasa al hacer clic | `scripts/login.js`: envía los datos al servidor y cambia de página |

El HTML enlaza los otros dos:

```html
<link rel="stylesheet" href="/estilos/estilos.css">   <!-- en el <head> -->
...
<script src="/scripts/comun.js"></script>              <!-- al final del <body> -->
<script src="/scripts/login.js"></script>
```

Los scripts van **al final del `<body>`** para que, cuando se ejecuten, todo el HTML ya exista.
**El orden importa:** primero `comun.js`, porque `login.js` usa sus funciones.

### `estilos.css`

Un solo archivo dividido en 18 secciones numeradas (el índice está arriba del archivo).

- **Colores en un solo lugar (sección 1).** En `:root` se definen variables como
  `--primario: #1C1660;` y se usan con `var(--primario)`. Para cambiar el azul de todo
  el sistema basta cambiar esa línea.
- **Clases:** un elemento toma un estilo cuando tiene su clase.
  - `class="boton"` → botón azul en píldora.
  - `class="boton boton-secundario"` → el mismo botón, pero con fondo transparente.
  - Las etiquetas de color combinan dos clases: `class="etiqueta aprobado"`. En el CSS se escribe
    `.etiqueta.aprobado` (sin espacio), que significa "un elemento con las dos clases".
- **Los campos de formulario** (`input`, `select`, `textarea`) tienen estilo sin necesidad
  de clase, para escribir menos. Cada campo se arma así:
  `<label class="campo"><span>Usuario</span><input name="usuario"></label>`.
- **`display: grid` y `display: flex`** acomodan elementos en filas y columnas:
  - `grid-template-columns: 2fr 1fr` → dos columnas; la primera mide el doble.
  - `flex-wrap: wrap` → si no caben en una fila, bajan a la siguiente.
- **`[hidden] { display: none !important; }`** → todo lo que tenga el atributo `hidden` se
  oculta. El JavaScript muestra y oculta cosas con `elemento.hidden = true / false`.
- **`@media (max-width: 900px)`** → reglas que se aplican solo en pantallas pequeñas (tablet):
  las columnas pasan a ser una sola. Así el sistema funciona en PC y en tablet.
- **El árbol (sección 15)** dibuja sus líneas con `::before` y `::after`: "elementos de
  mentira" que crea el CSS solo para dibujar la línea vertical y la horizontal de cada rama.
- La fuente es **Segoe UI**, que ya viene con Windows. No se descarga nada de internet.

### `comun.js`: las funciones que usan todas las páginas

| Función | Qué hace |
|---|---|
| `pedirDatos(ruta)` | Consulta al servidor (GET) y devuelve los datos |
| `enviarDatos(ruta, datos)` | Envía datos al servidor (POST) |
| `armarConsulta(filtros)` | `{op: "1001"}` → `"?op=1001"` |
| `iniciarPagina()` | Pide la sesión, dibuja el encabezado con el menú y el pie, y devuelve el usuario |
| `escaparHtml(texto)` | Convierte `<` en `&lt;`, etc. **Todo texto de la base pasa por aquí** antes de ir al HTML |
| `formatearNumero(n)` | `1680.5` → `"1.680,5"` (formato de Colombia) |
| `mostrarAviso` / `ocultarAviso` | Muestran u ocultan un mensaje rojo (error) o verde (éxito) |
| `llenarSelect(select, opciones)` | Llena una lista desplegable |
| `filaVacia(columnas, texto)` | Fila de tabla con "No hay resultados" |
| `etiquetaTipo` / `etiquetaEstado` | Las etiquetas de color (MP, PP, PT / Pendiente, Aprobado...) |
| `prepararPestanas(contenedor)` | Hace funcionar las pestañas de una página |

Conceptos de JavaScript que aparecen:

- **`fetch(ruta, opciones)`** envía una petición al servidor. **`await`** espera la respuesta
  sin congelar la página. Una función que usa `await` se declara `async function`.
- **`JSON.stringify(objeto)`** convierte un objeto en texto JSON para enviarlo.
  **`respuesta.json()`** hace lo contrario.
- **`throw new Error(mensaje)`** avisa que algo salió mal. La página lo atrapa con
  `try { ... } catch (error) { ... }` y muestra `error.message`.
- **Plantillas de texto** con comillas invertidas: `` `<strong>${nombre}</strong>` `` mete
  el valor de la variable dentro del texto. Así se arma el HTML.
- **`document.getElementById("pie")`** busca un elemento por su `id`;
  **`elemento.innerHTML = "..."`** le cambia el contenido.
- **`elemento.addEventListener("click", funcion)`** ejecuta la función cuando ocurre el evento.

**¿Por qué `escaparHtml` es tan importante?** Si alguien escribe
`<img src=x onerror=alert(1)>` como descripción de un ítem y lo mostramos tal cual con
`innerHTML`, el navegador lo ejecutaría como código. A esto se le llama **XSS**. Al escaparlo,
se ve como texto inofensivo.

**El 401 en `llamarServidor`:** si la sesión se cerró, cualquier página vuelve sola al login.
La excepción es el propio login, porque ahí un 401 significa "contraseña incorrecta".

**El logo:** `prepararLogo` revisa si `imagenes/logo.png` existe. Si no, pone el texto
**RYMEL**. Revisa dos casos: que la imagen **ya** haya fallado (`complete` y `naturalWidth === 0`)
o que falle **después** (evento `error`).

### `login.html` y `login.js`

1. La página tiene dos mitades: el panel azul institucional y la tarjeta con el formulario.
2. Al presionar **Ingresar** (o Enter) ocurre el evento `submit`.
3. `evento.preventDefault()` evita que el navegador recargue la página, que es lo que hace
   un formulario por defecto.
4. Se desactiva el botón para no enviar dos veces.
5. `enviarDatos("/api/login", {usuario, contrasena})` → el servidor revisa y responde:
   - **Bien:** `{inicio: "/aprobaciones"}`, y además guarda la cookie de sesión.
     El script va a esa página con `window.location.href = respuesta.inicio`.
   - **Mal:** error 401. Se muestra *"Usuario o contraseña incorrectos."* y se reactiva el botón.

### Cómo probarlo

1. `python servidor.py` y abre <http://localhost:8000>.
2. Debe aparecer el login: panel azul a la izquierda, formulario a la derecha y "RYMEL"
   arriba del formulario (porque aún no hay `logo.png`).
3. Escribe `analista` con una contraseña equivocada → aviso rojo
   *"Usuario o contraseña incorrectos."*
4. Escribe `analista` / `rymel123` → pasa a `/aprobaciones`. Con `nucleo` pasa a `/reporte`;
   con `supervisor`, a `/panel`. Arriba aparece el encabezado con el menú de tu rol.
5. Vuelve a abrir <http://localhost:8000/login>: como ya tienes sesión, te devuelve a tu inicio.
6. **Cerrar sesión:** botón **Cerrar sesión**, arriba a la derecha.
7. **Prueba de tablet:** con F12 → ícono de celular/tablet (Ctrl+Shift+M) elige un ancho de
   768 px. Las dos mitades del login quedan una encima de la otra.


---

## Entrega 4 · `catalogo.py` y la página "Ítems y referencias"

### El viaje completo de un clic

Este es el recorrido que se repite en **todas** las páginas desde ahora. Ejemplo: crear el ítem PP-0011.

```
1. catalogo.js     El usuario llena el formulario y presiona "Guardar ítem".
2. catalogo.js     enviarDatos("/api/items", {tipo: "PP", codigo: "PP-0011", ...})
3. servidor.py     Busca "POST /api/items" en RUTAS → (catalogo.crear_item, [ANALISTA]).
                   Revisa que haya sesión y que el rol sea ANALISTA.
4. catalogo.py     crear_item valida el código, que no esté repetido y la unidad,
                   y hace el INSERT.
5. servidor.py     Si no hubo error → commit() y responde el ítem en JSON.
                   Si hubo ValueError → rollback() y responde {"error": "mensaje"}.
6. catalogo.js     Muestra "Ítem PP-0011 creado." o el mensaje de error.
```

### `catalogo.py`

**Ayudas para validar** (al inicio del archivo; también las usarán `ordenes.py` y `entregas.py`):

| Función | Qué revisa |
|---|---|
| `leer_texto(datos, campo, nombre)` | Que el campo no venga vacío |
| `leer_numero(valor, nombre)` | Que sea un número mayor que cero |
| `leer_entero(valor, nombre)` | Lo mismo, y además sin decimales |
| `tiene_formato(codigo, prefijo, digitos)` | La nemotecnia: `NUCLEO-001` = prefijo + guion + 3 dígitos |
| `siguiente_codigo(codigos, prefijo, digitos)` | El consecutivo libre: si existen MP-0001 a MP-0007 → `MP-0008` |

**Funciones de la API** (todas con la forma `(conexion, usuario, datos)`):

| Ruta | Función | Rol | Qué hace |
|---|---|---|---|
| `GET /api/listas` | `consultar_listas` | Todos | Áreas, tipos y unidades para los `<select>` |
| `GET /api/items` | `listar_items` | Analista, Supervisor | Ítems filtrados por tipo y texto |
| `GET /api/items/siguiente-codigo` | `sugerir_codigo_item` | Analista | El próximo código libre de un tipo |
| `POST /api/items` | `crear_item` | Analista | Crea un ítem |
| `POST /api/items/editar` | `editar_item` | Analista | Cambia descripción y unidad |
| `GET /api/referencias` | `listar_referencias` | Analista, Supervisor | Referencias filtradas por área y texto |
| `GET /api/referencia` | `consultar_referencia` | Analista, Supervisor | Una referencia con su lista de materiales |
| `GET /api/referencias/siguiente-codigo` | `sugerir_codigo_referencia` | Analista | El próximo código libre de un área |
| `POST /api/referencias` | `crear_referencia` | Analista | Crea una referencia con su lista |
| `POST /api/referencias/materiales` | `cambiar_materiales` | Analista | Reemplaza la lista de materiales |

**Filtros que se arman por partes** (`listar_items`):

```python
sql = "SELECT ... FROM items WHERE 1 = 1"
if tipo != "":
    sql += " AND tipo = ?"
```

`WHERE 1 = 1` siempre es verdadero. Está ahí para que cada filtro se pueda pegar con
`AND ...` sin preguntarse si es el primero. `LIKE` con `%chapa%` busca el texto en
cualquier parte de la descripción.

**Reglas de una referencia:**

1. **Nemotecnia:** el código empieza por el código del área (`BOBINADO-009` no se puede crear en Núcleo).
2. **No repetida:** el código no existe ya.
3. **Ítem propio correcto** (`validar_item_propio`): Ensamble produce un **PT** y las demás
   áreas un **PP**. Además, el ítem no puede pertenecer ya a otra referencia.
4. **Lista de materiales** (`validar_materiales`):
   - al menos un material;
   - sin repetidos;
   - cantidades mayores que cero;
   - un PT no puede ser material;
   - la referencia no puede consumirse a sí misma;
   - **sin ciclos**.

**¿Qué es un ciclo y cómo se detecta?** Si la Parte activa consume el Núcleo, el Núcleo no
puede consumir la Parte activa: para fabricar uno necesitarías el otro, sin fin.
`contiene_item(conexion, item, buscado)` mira los materiales de `item`. Si alguno es
`buscado`, hay ciclo. Si no, **se llama a sí misma** con cada material para bajar un nivel
más. Esto se llama **recursión**. Se detiene sola en la materia prima, que no tiene materiales.

**Cambiar la lista de materiales** = `DELETE` de todas las líneas + `INSERT` de las nuevas.
Si alguna línea nueva no es válida, el servidor hace `rollback()` y la lista vieja queda intacta.

**Cambio pequeño en `base_datos.py`:** se agregó `filas_a_diccionarios(filas)`, que convierte las
filas de SQLite en diccionarios para poder enviarlas como JSON.

### Rutas nuevas en `servidor.py`

Se agregó `import catalogo` y estas líneas en `RUTAS`:

```python
"GET /api/listas": (catalogo.consultar_listas, TODOS),
"GET /api/items": (catalogo.listar_items, [ANALISTA, SUPERVISOR]),
...
"POST /api/referencias/materiales": (catalogo.cambiar_materiales, [ANALISTA]),
```

### `catalogo.html`

- **Encabezado** (`<header id="encabezado">`) y **pie** (`<footer id="pie">`) vacíos:
  los llena `comun.js`.
- **Dos pestañas:** los botones tienen `data-panel="panel-items"` y `data-panel="panel-referencias"`.
  `prepararPestanas` muestra el panel elegido y oculta el otro.
- **Pestaña Ítems:** a la izquierda el formulario (sirve para crear y para editar) y a la derecha
  los filtros y la tabla.
- **Pestaña Referencias:** a la izquierda la lista; a la derecha **una de tres vistas**:
  - vacía ("Elige una referencia...");
  - el detalle con su lista de materiales;
  - el formulario.

### `catalogo.js`

**Al cargar** (`arrancar`): dibuja el encabezado, pide las listas (áreas, tipos, unidades)
y prepara las dos pestañas.

**Variables que la página recuerda:**

| Variable | Guarda |
|---|---|
| `itemEnEdicion` | `null` si se está creando un ítem, o el código del que se edita |
| `referenciaActual` | La referencia abierta en el detalle |
| `materialesDisponibles` | Los ítems MP y PP (los únicos que pueden ser material) |
| `editandoMateriales` | `true` si el formulario cambia la lista de una referencia existente |

**Ítems:**
- `sugerirCodigoItem` pide el próximo código al cambiar el tipo.
- `cargarItems` se ejecuta al cambiar el filtro o al escribir en el buscador (evento `input`).
- `empezarEdicion` llena el formulario y **bloquea** el tipo y el código (`disabled = true`).
- `guardarItem` envía a `/api/items` (crear) o a `/api/items/editar` (editar), según `itemEnEdicion`.

**Un solo escuchador para toda la tabla:** en lugar de poner un evento en cada botón Editar,
se pone uno en la tabla. `evento.target.closest("[data-editar]")` averigua si el clic cayó
en un botón Editar. El código del ítem viaja en `data-editar="PP-0011"` y se lee con
`boton.dataset.editar`.

**Referencias:**
- Clic en una fila → `abrirReferencia` pide la referencia con sus materiales y muestra el detalle.
- **+ Nueva referencia** → al elegir el área (`alCambiarArea`):
  - se sugiere el código (`NUCLEO-003`);
  - se cargan solo los ítems **del tipo correcto que todavía no tienen referencia**
    (`sin_referencia=si`).
- **Editar lista de materiales** → el mismo formulario, con área, código, ítem y descripción bloqueados.
- **Filas de materiales:** `agregarFilaMaterial` crea una fila con `document.createElement("tr")`
  y la agrega al final con `appendChild`. Así no se borran las demás. El botón ✕ la quita.
- `leerMateriales` recorre las filas y arma `[{item: "MP-0001", cantidad: "80"}, ...]`.
- `mostrarVista` usa `scrollIntoView` para bajar hasta el detalle en tablet, donde queda
  debajo de la lista.

### Cómo probarlo (como `analista`)

1. `python servidor.py` → inicia sesión con `analista` → menú **Ítems y referencias**.
   Ya se ven el encabezado con **RYMEL**, el menú y tu nombre.
2. **Ítems:**
   - Elige tipo **PP**: el código sugerido es `PP-0011`. Escribe una descripción y guarda.
   - Intenta guardar con el código `MP-1` → error de formato.
   - Intenta repetir `PP-0011` → "Ya existe un ítem…".
   - Busca "chapa" en el filtro y pulsa **Editar** en un ítem: el código queda bloqueado.
3. **Referencias:**
   - Clic en `PACTIVA-001` → detalle con su lista: PP-0001 y PP-0002.
   - **+ Nueva referencia**, área **Núcleo** → código `NUCLEO-003` e ítem `PP-0011`
     (el que creaste). Prueba:
     - cambiar el código a `BOBINADO-009` → error de nemotecnia;
     - guardar sin materiales → error;
     - poner MP-0001 dos veces → error de repetido;
     - con MP-0001 × 100 → se crea.
   - **Ciclo:** abre `NUCLEO-001` → **Editar lista de materiales** → agrega `PP-0003`
     (Parte activa) → *"PP-0003 ya contiene a PP-0001: la estructura quedaría en un ciclo."*
4. **Permisos:** con `supervisor` el menú no muestra "Ítems y referencias". Si escribe
   `/catalogo` en la dirección, vuelve al Panel.

Para volver a los datos originales: detén el servidor y ejecuta `python base_datos.py reiniciar`.

---

## Entrega 5 · La página "Estructura" (el árbol)

### ¿De dónde sale el árbol?

Nadie lo dibuja a mano: **se arma solo** con lo que ya está en la base de datos.

1. La referencia `ENSAMBLE-001` produce el ítem `PT-0001` → es la **raíz**.
2. Su lista de materiales dice que consume `PP-0003`, `PP-0005` y `MP-0007` → son sus **hijos**.
3. `PP-0003` tiene su propia referencia (`PACTIVA-001`), con su propia lista → se baja otro nivel.
4. La **materia prima** no tiene referencia → ahí se detiene la rama (es una **hoja**).

Si creas ítems y referencias en el catálogo (entrega 4), el árbol del producto nuevo
aparece aquí automáticamente.

### Lo nuevo en `catalogo.py` (al final del archivo)

| Función | Qué hace |
|---|---|
| `consultar_estructura` | La función de la API (`GET /api/estructura?referencia=...&cantidad=...`). Devuelve el árbol y la materia prima total |
| `construir_estructura` | Busca el ítem que produce la referencia y arma el árbol desde ahí |
| `armar_nodo` | Arma un nodo y, **llamándose a sí misma**, todos los nodos de debajo |
| `resumir_materia_prima` y `sumar_materia_prima` | Recorren el árbol y suman la materia prima de todas las ramas |

**Cómo se calcula cada cantidad:**

```
cantidad total del hijo = cantidad por unidad (de la lista) × cantidad total del padre
```

Ejemplo con 10 transformadores de 45 kVA:
- PT-0001 → 10 und.
- PP-0003 (1 por transformador) → 1 × 10 = 10 und.
- PP-0001 (1 por parte activa) → 1 × 10 = 10 und.
- MP-0001 (80 kg por núcleo) → 80 × 10 = **800 kg**.

**Cada nodo es un diccionario:**

```python
{
    "item": {"codigo": "PP-0003", "descripcion": "Parte activa 45 kVA", "tipo": "PP", ...},
    "referencia": "PACTIVA-001",
    "area": "Parte activa",
    "cantidad_por_unidad": 1,
    "cantidad_total": 10,
    "hijos": [ ...más nodos con la misma forma... ]
}
```

**¿Por qué `round(cantidad_total, 6)`?** Los computadores guardan los decimales en binario
y a veces aparecen errores diminutos (`0.1 + 0.2` da `0.30000000000000004`). Redondear a
6 decimales los elimina.

**Sumar la materia prima:** un mismo MP puede aparecer en varias ramas. Por ejemplo, la
chapa en el núcleo y la lámina en el tanque. `sumar_materia_prima` recorre todo el árbol y
va acumulando en un diccionario `{código: total}`. Al final se ordena por código con `sorted`.

### Ruta nueva en `servidor.py`

```python
"GET /api/estructura": (catalogo.consultar_estructura, [ANALISTA, SUPERVISOR]),
```

### Lo nuevo en `comun.js` (sección 4: árbol)

El dibujo del árbol está en `comun.js` y no en `estructura.js` porque también lo usarán la
página de Órdenes (para confirmar antes de crear una OP) y el asistente "Nuevo producto".

- `crearNodoArbol(nodo)` devuelve el HTML de un nodo. Si tiene hijos, los mete en un `<ul>`
  llamándose a sí misma (la misma recursión que en Python).
- Cada rama con hijos va dentro de **`<details open>`** con un **`<summary>`**. Es HTML puro:
  al hacer clic en el `<summary>`, el navegador abre o cierra la rama sin JavaScript.
- `crearTarjetaNodo` dibuja la tarjeta: etiqueta de tipo, código, descripción, de dónde
  sale ("Referencia PACTIVA-001 · Parte activa" o "Materia prima comprada") y las cantidades.
- `abrirRamas(arbol, true/false)` abre o cierra todas las ramas (`rama.open = true`).

### Cambios en `estilos.css`

- La flecha ▸ ahora aparece **solo** en las ramas que tienen hijos (`.arbol summary .nodo-flecha`).
- En celular, la cantidad de cada tarjeta pasa debajo de la descripción.
- **Corrección:** `.cabecera p` cambió a `.cabecera > p`. El signo `>` significa
  "solo los hijos directos". Antes, la regla también pintaba de gris el antetítulo
  ("MÓDULO 4 · CATÁLOGO"), que está más adentro.

### `estructura.html` y `estructura.js`

- **El formulario:** referencia, cantidad y el botón "Ver estructura".
  - En la lista, las referencias van en dos grupos con `<optgroup>`: productos terminados
    primero y productos en proceso después.
- **Abrir la página ya filtrada:** desde el catálogo, el botón "Ver estructura ↗" lleva a
  `/estructura?referencia=PACTIVA-001`. `leerParametrosDeLaDireccion` usa
  `new URLSearchParams(window.location.search)` para leer esos valores y ponerlos en el formulario.
- **El resultado:**
  - el título (`ENSAMBLE-001 × 10`);
  - los botones Expandir y Contraer;
  - la leyenda de colores;
  - el árbol;
  - la tabla de materia prima.
- **La disponibilidad** compara lo requerido con la existencia: **Suficiente** (verde) o
  **Faltan 600** (rojo).

### Cómo probarlo

1. `python servidor.py` → entra con `supervisor` o `analista` → menú **Estructura**.
2. Aparece el primer producto terminado (`ENSAMBLE-001 × 1`) con su árbol completo.
3. Pon **10** y pulsa "Ver estructura": la chapa da **800 kg**, el aceite **900 L**, y todo está en verde.
4. Pon **20**: el aceite necesita 1.800 L y solo hay 1.200 → **Faltan 600**.
5. Haz clic en la tarjeta de `PP-0003`: esa rama se cierra. Prueba Contraer todo / Expandir todo.
6. Elige `ENSAMBLE-003` (el incompleto): su árbol no tiene tanque. Esto es lo que, en la
   entrega 6, impedirá crear una OP con él.
7. Desde **Ítems y referencias** (analista), abre una referencia y pulsa **"Ver estructura ↗"**:
   llega ya filtrada.
8. Con `nucleo`, "Estructura" no está en el menú.

---

## Entrega 6 · `ordenes.py` y la página "Órdenes de producción"

### Qué se puede hacer

| Quién | Qué |
|---|---|
| **Todos** | Ver la lista de OP con filtros (número, cliente, área, estado) y el detalle de cada una |
| **Analista y Supervisor** | Crear OP y clientes |

### `ordenes.py`, por partes

**1. Clientes**
- `listar_clientes`: todos, ordenados por nombre.
- `crear_cliente`: quita puntos y espacios del NIT (`900.123.456-7` → `900123456-7`)
  y lo valida con `nit_valido`:
  - `split("-")` separa el número del dígito de verificación;
  - `isdigit()` revisa que sean solo dígitos;
  - `len()` revisa la cantidad de dígitos.

  Tampoco deja repetir un NIT.

**2. Lo que debe producir cada área**

```
calcular_requerimientos(conexion, "ENSAMBLE-002", 4)
```

1. Arma el árbol del ensamble para 4 unidades, con la misma función de la página Estructura.
2. Para cada una de las 6 áreas busca en el árbol el nodo que fabrica esa área
   (`buscar_nodo_de_area`).
3. Si lo encuentra, la cantidad del nodo es lo que debe producir esa área.
   Si **no** lo encuentra, el área se anota en `areas_faltantes`.

`buscar_nodo_de_area` (hoy está en `catalogo.py`; se movió en la entrega 12) recorre el árbol
**por niveles** usando una lista de "pendientes":
1. empieza con la raíz;
2. saca el primero (`pop(0)`) y revisa si es el área buscada;
3. si no lo es, agrega sus hijos al final de la lista;
4. repite hasta encontrarlo o hasta que la lista quede vacía.

`revisar_requerimientos` devuelve los motivos para **no** crear la OP:
- áreas que faltan en la lista de materiales;
- cantidades con decimales, porque las áreas reportan unidades enteras.

**3. Crear la OP** (`crear_orden`), en este orden:
1. El número tiene solo dígitos y no existe.
2. El ítem de ensamble es un producto terminado (PT).
3. El cliente existe.
4. La cantidad es un entero mayor que cero.
5. La lista de materiales está completa (todas las áreas amarradas).
6. `INSERT` en `ordenes` y un `INSERT` en `requerimientos` por cada área.

Si algo falla en el paso 6, `servidor.py` hace `rollback()`, así que **nunca queda una OP
sin sus requerimientos**. La fecha y el usuario se ponen solos, con `fecha_actual()` y
`usuario["id"]`.

`vista_previa_orden` hace los mismos cálculos **sin guardar**, para mostrar en pantalla qué
se va a crear. Como usa las mismas funciones que `crear_orden`, lo que ves es exactamente
lo que se guarda.

**4. Consultar** (para todos)

`avance_por_area` da, por cada área de la OP:

| Columna | De dónde sale |
|---|---|
| Requeridas | La tabla `requerimientos` (calculada al crear la OP) |
| En revisión | Suma de los reportes `PENDIENTE` del área en esa OP |
| Aprobadas | Suma de los reportes `APROBADO` |
| Rechazadas | Suma de los reportes `RECHAZADO` |
| Pendientes | Requeridas − Aprobadas (nunca menos de 0) |

Las sumas se hacen con SQL:

```sql
SELECT COALESCE(SUM(cantidad), 0) FROM reportes WHERE orden_id = ? AND area_id = ? AND estado = ?
```

`SUM` suma la columna. Si no hay reportes, `SUM` da vacío (`NULL`); `COALESCE(..., 0)` lo
convierte en 0. Estos números **no se guardan**: se calculan cada vez, así que siempre
están al día.

**Estado de una OP:** `COMPLETA` si ninguna área tiene pendientes y `PENDIENTES` si alguna
tiene. Si se filtra por área, el estado es el de esa área. Por eso el filtro de estado se
aplica en Python, después de calcular, y no en el SQL.

### Rutas nuevas en `servidor.py`

| Ruta | Rol |
|---|---|
| `GET /api/clientes`, `POST /api/clientes` | Analista, Supervisor |
| `GET /api/ordenes` (lista con filtros) | Todos |
| `GET /api/orden?numero=1001` (detalle) | Todos |
| `GET /api/ordenes/siguiente-numero` | Analista, Supervisor |
| `GET /api/ordenes/ensambles` (PT con lista completa o incompleta) | Analista, Supervisor |
| `GET /api/ordenes/vista-previa` | Analista, Supervisor |
| `POST /api/ordenes` (crear) | Analista, Supervisor |

### `ordenes.html` y `ordenes.js`

- **Pestañas solo para quien puede crear.** El HTML las trae con `hidden`. `ordenes.js` las
  muestra si el rol es Analista o Supervisor. **Ocultar un botón no es seguridad:** el
  servidor también rechaza (403) a un operario que intente crear una OP.
- **Filtros:** OP y cliente se buscan mientras se escribe (`input`); área y estado al
  cambiar (`change`). A un operario se le preselecciona su área.
- **Respuestas desordenadas:** al escribir "andina" se envían 6 búsquedas seguidas
  (a, an, and...), y sus respuestas pueden llegar en desorden. Cada búsqueda recibe un
  número (`consultaActual`). Si al llegar la respuesta ya hay una búsqueda más nueva, se
  descarta para no mostrar resultados viejos. Lo mismo se agregó en `catalogo.js`.
- **Ventanas con `<dialog>`:** `dialogo.showModal()` abre la ventana con el fondo oscuro y
  `dialogo.close()` la cierra. Hay dos ventanas: el detalle de la OP y el nuevo cliente.
- **Detalle de la OP:** datos generales, la lista de materiales del ensamble (por unidad y
  total) y la tabla de avance por área. La fila del área del operario se resalta.
- **Nueva OP:**
  1. Al elegir el ensamble o cambiar la cantidad → `cargarVistaPrevia` pide
     `/api/ordenes/vista-previa` y muestra la tabla "lo que debe producir cada área" y el
     árbol (con `crearNodoArbol` de `comun.js`).
  2. El botón **Crear OP** solo se activa si `puede_crear` es verdadero.
  3. Los ensambles incompletos aparecen con "— incompleta". Se pueden elegir para ver qué
     les falta (en rojo), pero no se pueden guardar.
  4. **+ Nuevo cliente** abre la ventana. Al guardar, el cliente queda elegido en el formulario.

**Ajuste en `estilos.css`:** `.boton` ahora tiene `white-space: nowrap`, para que "Ver detalle"
no se parta en dos líneas en tablet.

### Cómo probarlo

**Como `supervisor` (o `analista`), en Órdenes:**
1. **Consultar OP:**
   - Se ven 1001, 1002 y 1003.
   - Abre **Ver detalle** de la 1001. Núcleo: 10 requeridas, 3 en revisión, 4 aprobadas,
     0 rechazadas, **6 pendientes**. Bobinado: 5 en revisión.
   - Abre la 1002. Metalmecánica tiene **2 rechazadas**, que no descuentan de los pendientes.
   - Filtra cliente "andina" → solo la 1002.
2. **Nueva OP:**
   - Elige **PT-0003 — incompleta** → aviso rojo "falta amarrar la referencia de
     Metalmecánica, Pintura" y el botón queda desactivado.
   - Elige **PT-0002** con cantidad **4** → cada área debe producir 4, con el árbol debajo.
   - **+ Nuevo cliente:**
     - NIT `abc` → error;
     - NIT `900123456-7` → repetido;
     - NIT `800.111.222-5` con un nombre → se crea y queda elegido.
   - Cambia el número a **1001** → "Ya existe la OP 1001". Vuelve a **1004** y crea:
     aparece en la lista y el número sugerido pasa a 1005.

**Como `nucleo`:**
- No hay pestaña "Nueva OP".
- El filtro Área viene en **Núcleo** y "Áreas completas" muestra 0 / 1, porque cuenta solo su área.
- En el detalle, la fila de Núcleo está resaltada.

---

## Entrega 7 · `entregas.py` y la página "Reportar entrega" (áreas)

### El flujo de un reporte

```
Operario de Núcleo                     Analista (entrega 8)
──────────────────                     ────────────────────
Busca la OP 1001
Ve su referencia (NUCLEO-001),
lo que consume y cuánto falta
Escribe "2" y envía  ──►  reporte PENDIENTE  ──►  lo aprueba o lo rechaza
                                                  (solo al aprobar se mueve el inventario)
```

### `entregas.py` (primera parte)

Este archivo también tiene la aprobación (entrega 8), el panel (9) y el inventario (10).

**1. Lo que le toca a un área en una OP**
- `requerimiento_del_area`: busca en la tabla `requerimientos` (la que se llenó al crear la OP)
  qué referencia fabrica el área y cuántas unidades debe entregar.
- `avance_del_area`: le suma lo aprobado y lo que está en revisión (con `sumar_reportes`,
  de `ordenes.py`) y calcula cuánto se puede reportar todavía:

```
disponible = requeridas − aprobadas − en revisión
```

**¿Por qué se resta lo que está en revisión?** Si Núcleo debe entregar 10, ya tiene 4
aprobadas y 3 esperando revisión, solo puede reportar 3 más. Si no se restaran las 3 en
revisión, podría reportar 6 y terminar entregando 13.

**¿Y lo rechazado?** No se resta. Si al área le rechazaron 2 unidades, las puede corregir
y volver a reportar.

**2. Funciones de la API**

| Ruta | Función | Rol | Qué hace |
|---|---|---|---|
| `GET /api/mi-orden?numero=1001` | `consultar_orden_para_area` | Área | La OP, la referencia del área, sus materiales y su avance |
| `POST /api/reportes` | `crear_reporte` | Área | Registra la entrega como `PENDIENTE` |
| `GET /api/reportes` | `listar_reportes` | Todos | Reportes filtrados por estado, área y OP |

**`crear_reporte`** valida que la cantidad sea un entero y que **no supere lo disponible**.
Si la supera, responde con un mensaje que explica la cuenta:
*"Solo puedes reportar hasta 3 und. (requerido en la OP 10, aprobado 4, en revisión 3)."*
El área y el usuario **no los envía la página**: salen de la sesión (`usuario["area_id"]`,
`usuario["id"]`), así que nadie puede reportar a nombre de otra área.

**`listar_reportes`:** si quien pregunta es de un área, el servidor agrega
`AND rp.area_id = <su área>` **siempre**. Aunque la página pidiera los reportes de otra área,
el operario solo recibe los suyos.

**`LEFT JOIN` en `SQL_REPORTES`:** quien revisó el reporte (`rv`) se une con `LEFT JOIN`
porque un reporte pendiente todavía no tiene revisor. Con un `JOIN` normal, los pendientes
no aparecerían en la lista.

### `reporte.html` y `reporte.js`

1. **Buscar la OP:** el campo usa `<datalist>`. Al escribir, el navegador sugiere las OP
   que existen, sin JavaScript adicional.
2. **Resultado**, en dos columnas:
   - **Izquierda:** la referencia del área y una tabla de materiales con "Por unidad" y
     "En esta entrega".
   - **Derecha:** cuatro indicadores (Requeridas, Aprobadas, En revisión, **Por reportar**)
     y el campo de cantidad.
3. **Consumo en vivo:** al escribir la cantidad (evento `input`), `pintarMateriales`
   multiplica cada material por esa cantidad. Por ejemplo, 2 núcleos → 160 kg de chapa.
   `Number(valor) || 0` convierte el texto en número y usa 0 si el campo está vacío.
4. **Límite:** `cantidad.max = disponible` hace que el navegador no acepte más de lo
   disponible. El servidor lo vuelve a revisar, porque el navegador se puede saltar.
   Si no queda nada por reportar, el formulario se bloquea.
5. **Enviar:** después de enviar se vuelve a consultar la OP para ver el avance actualizado,
   y se recarga el historial.
6. **Historial:** los reportes del área con su estado y, si fue rechazado, el motivo.
   Se puede filtrar por estado.

### Cómo probarlo

1. Entra con **`nucleo`** → **Reportar entrega**.
   - El historial muestra el reporte #1 (4, **Aprobado**) y el #2 (3, **Pendiente**).
2. Busca **9999** → *"No existe la orden de producción 9999."*
3. Busca **1001** → NUCLEO-001; Requeridas 10, Aprobadas 4, En revisión 3, **Por reportar 3**.
4. Escribe **2** en la cantidad → la chapa muestra **160 kg** en "En esta entrega".
5. Intenta enviar **4** → el navegador no lo deja, porque el máximo es 3.
6. Envía **2** → *"Reporte #5 enviado…"*. Ahora: En revisión 5, Por reportar 1, y el
   historial tiene una fila más.
7. Envía **1** → Por reportar queda en 0 y el formulario se bloquea.
8. Entra con **`metalmec`** → en el historial ve su reporte **Rechazado** con el motivo
   *"Soldadura con poros en la tapa…"*. En la OP 1002 puede reportar las **5** unidades,
   porque las rechazadas no cuentan.
9. Con `analista` no aparece "Reportar entrega": solo las áreas reportan.

---

## Entrega 8 · La página "Aprobaciones" y los movimientos de inventario

### Qué pasa al aprobar y al rechazar

| Decisión | Inventario | Reporte |
|---|---|---|
| **Aprobar** | **Sale** cada material de la lista (cantidad de la lista × cantidad entregada) y **entra** el producto entregado | Queda `APROBADO`, con quién y cuándo |
| **Rechazar** | No se mueve nada | Queda `RECHAZADO`, con el **motivo** (obligatorio) |

Ejemplo: Bobinado entrega **5** bobinados para la OP 1001. La lista de BOBINADO-001 dice
25 kg de alambre, 2 m² de fibra y 5 m² de papel por unidad. Al aprobar:

```
SALIDA  MP-0002  5 × 25 = 125 kg   (600 → 475)
SALIDA  MP-0003  5 × 2  =  10 m2   ( 50 →  40)
SALIDA  MP-0004  5 × 5  =  25 m2   (100 →  75)
ENTRADA PP-0002  5 und              (  0 →   5)
```

Cada línea queda en la tabla `movimientos` con su concepto
("Consumo de BOBINADO-001 · OP 1001", "Entrega de Bobinado · OP 1001").

### Lo nuevo en `entregas.py` (al final del archivo)

| Función | Qué hace |
|---|---|
| `buscar_reporte` | Busca un reporte por su número (#) |
| `buscar_reporte_pendiente` | Igual, pero falla si ya fue revisado: **un reporte no se revisa dos veces** |
| `calcular_consumos` | Para cada material: consumo, existencia actual, cuánto quedará y si alcanza |
| `consultar_reporte_para_revision` | Lo que muestra la ventana: el reporte, los consumos y si se puede aprobar |
| `aprobar_reporte` | Revisa faltantes → salidas → entrada → marca aprobado |
| `rechazar_reporte` | Exige el motivo y marca rechazado |
| `marcar_revisado` | El `UPDATE` que guarda estado, motivo, revisor y fecha |

**El orden en `aprobar_reporte` importa:**

1. **Primero se revisa que TODO alcance.** Si falta cualquier material, se lanza
   `ValueError` antes de tocar nada:
   *"No hay existencias suficientes para aprobar: PP-0003 (faltan 1 und)…"*
2. Después se descuenta cada material (`SALIDA`).
3. Luego se suma el producto entregado (`ENTRADA`).
4. Por último, el reporte se marca como aprobado.

Además, como todo ocurre dentro de una misma petición, `servidor.py` hace **un solo `commit()`**
al final. Si algo fallara a mitad de camino, el `rollback()` deshace todo y el inventario
queda exactamente como estaba.

**El inventario se mueve con una sola función reutilizada:** lee la existencia, suma o resta, la
guarda con `UPDATE` y registra el movimiento con `INSERT`, con `round(..., 6)` para evitar errores
diminutos de decimales. *(Cuando se construyó esta entrega se llamaba `base_datos.cambiar_existencia`.
Al aplicar los patrones de diseño pasó a `inventario.py` como `registrar_entrada` y `registrar_salida`:
ver "Patrones de diseño".)*

**`SQL_REPORTES` ahora trae más columnas** (`orden_id`, `referencia_id`, `item_id`, la
descripción, la unidad y la existencia del ítem), que la revisión necesita.

**Formato `:g` en Python:** `f"{falta:g}"` muestra `1` en lugar de `1.0`, y `2.5` igual.

### Rutas nuevas en `servidor.py` (solo Analista)

| Ruta | Qué hace |
|---|---|
| `GET /api/reporte?id=3` | Detalle para la ventana de revisión |
| `POST /api/reportes/aprobar` | Aprueba y mueve el inventario |
| `POST /api/reportes/rechazar` | Rechaza con motivo |

### `aprobaciones.html` y `aprobaciones.js`

- **Bandeja:** filtros por estado (empieza en **Pendiente**), área y OP. Los pendientes tienen
  el botón **Revisar** y los ya revisados, **Ver**.
- **Ventana de revisión** (`<dialog>`), en tres partes:
  1. **Entra al inventario:** el producto, su existencia actual y cuánto quedará.
  2. **Sale del inventario:** cada material con consumo, existencia, cuánto quedará y una
     etiqueta **Suficiente** (verde) o **Faltan N** (rojo).
  3. **Decisión** (`pintarDecision`):
     - **Ya revisado:** se ocultan los botones y se muestra quién lo revisó, cuándo y el motivo.
     - **Pendiente sin faltantes:** se pueden usar los dos botones.
     - **Pendiente con faltantes:** **Aprobar** queda desactivado, con un aviso que explica
       qué hacer. **Rechazar** sigue disponible.
- **Rechazar sin motivo:** la página avisa antes de ir al servidor, y el servidor también lo
  exige (`leer_texto`). Las dos capas son importantes: la de la página es por comodidad;
  la del servidor, por seguridad.
- **`decidir`:** la misma función envía la aprobación o el rechazo. Desactiva los botones
  mientras espera (para no hacer doble clic) y, si todo sale bien, cierra la ventana y
  recarga la bandeja.

### Cómo probarlo (como `analista`)

1. Menú **Aprobaciones**: en Pendiente están el #3 (Bobinado, 5) y el #2 (Núcleo, 3).
2. **Revisar #3** → entran 5 PP-0002; salen 125 kg de alambre, 10 m² de fibra y 25 m² de
   papel, todo **Suficiente** → **Aprobar entrega**.
   - En **Estructura** (o en la entrega 10, Inventario) el alambre queda en 475.
3. **Revisar #2** → pulsa **Rechazar** sin escribir nada → *"Escribe el motivo del rechazo."*
   Escribe un motivo y rechaza. La chapa **no** cambia (sigue en 1.680).
4. Filtro **Todos** → **Ver** el #2 → no hay botones; aparece quién lo rechazó y el motivo.
5. **Faltantes:**
   - Entra con `ensamble`, reporta **1** en la OP 1003.
   - Vuelve con `analista` y revísalo: faltan PP-0003 y PP-0005 (nadie ha entregado partes
     activas ni tanques pintados).
   - **Aprobar** está desactivado y el aceite no se toca.
6. En **Órdenes → Ver detalle de la 1001**, Bobinado ya muestra **5 aprobadas** y Núcleo
   **3 rechazadas**.
7. Con `nucleo`, `/aprobaciones` lo devuelve a su página. Si intenta aprobar por la API,
   recibe 403.

---

## Entrega 9 · El panel del supervisor

### Qué muestra

Una "foto" de toda la producción: el estado de **cada área en cada OP**.

| Estado del área | Significa | Regla en el código |
|---|---|---|
| **Pendiente** | Todavía no hay nada aprobado ni en revisión | `aprobadas == 0` y `en_revision == 0` |
| **En proceso** | Ya entregó algo, pero no completa lo requerido | `aprobadas > 0` o `en_revision > 0` |
| **Aprobado** | Lo aprobado completa lo requerido | `aprobadas >= requeridas` |

Los reportes **por revisar** y **rechazados** se cuentan aparte, en sus propios indicadores.

### Lo nuevo en `entregas.py` (al final del archivo)

| Función | Qué hace |
|---|---|
| `calcular_estado(requeridas, aprobadas, en_revision)` | Aplica la tabla de arriba, con dos `if` |
| `contar_reportes` | `SELECT COUNT(*)` cuenta **reportes** (no unidades) de un área en una OP con cierto estado |
| `consultar_panel` | Arma una fila por cada OP × área y la filtra por estado |
| `calcular_indicadores` | Recorre las filas y suma los cinco números de arriba |

**`consultar_panel`, paso a paso:**
1. Consulta las áreas (todas, o solo la del filtro). Serán las **columnas** de la matriz.
2. Consulta las OP (todas, o solo la del filtro). Serán las **filas**.
3. Para cada OP reutiliza `avance_por_area` de `ordenes.py` (la misma de la consulta de
   órdenes), que ya trae requeridas, aprobadas y en revisión. Así no se repite código.
4. Calcula el estado y el **porcentaje de avance**: `round(aprobadas / requeridas * 100)`.
   Por ejemplo, 4 de 10 → 40 %.
5. Si hay filtro de estado, solo deja las filas de ese estado.

**`SUM` frente a `COUNT`:** `sumar_reportes` (entrega 6) suma **unidades** (4 + 3 = 7 unidades).
`contar_reportes` cuenta **reportes** (2 reportes). El panel usa los dos: las unidades para el
avance y los reportes para los indicadores "Por revisar" y "Rechazados".

**Ruta nueva:** `GET /api/panel?op=&area=&estado=` → Supervisor y Analista.

### `panel.html` y `panel.js`

- **Filtros:** OP (lista con todas las OP), área, estado y el botón **Actualizar**, para ver
  reportes nuevos sin recargar la página.
- **Indicadores:** cada número tiene `id="indicador-CLAVE"`, con la misma clave que envía el
  servidor (`PENDIENTE`, `EN_PROCESO`...). Por eso un solo ciclo los llena todos:

  ```js
  for (const clave in indicadores) {
    document.getElementById("indicador-" + clave).textContent = indicadores[clave];
  }
  ```

  `for (const clave in objeto)` recorre los **nombres** de las claves de un objeto.
- **Matriz (`pintarMatriz`):** el servidor envía una lista plana de filas (OP + área). Para
  dibujar la matriz se reorganizan en un objeto por OP:

  ```js
  { "1001": { producto: "ENSAMBLE-001", celdas: { NUCLEO: fila, BOBINADO: fila, ... } } }
  ```

  Después, por cada OP y por cada área, se dibuja una celda con su estado,
  "aprobadas / requeridas" y la **barra de avance**. La barra es un `<div>` gris con otro `<div>`
  verde dentro, cuyo ancho se pone con `style="width: 40%"`. Si el filtro de estado dejó por
  fuera una celda, se muestra una raya (—).
- **Detalle:** la misma información en una tabla normal, una fila por OP y área.
- En tablet, la matriz se desplaza de lado dentro de su recuadro, gracias a `.tabla-contenedor`
  con `overflow-x: auto`.

### Cómo probarlo

1. Entra con **`supervisor`**: el panel es su página de inicio.
2. Con los datos de prueba (18 filas = 3 OP × 6 áreas):
   - **Pendiente 16 · En proceso 2 · Aprobado 0 · Por revisar 2 · Rechazados 1**.
   - En la OP 1001, Núcleo está **En proceso 4 / 10** (con la barra al 40 %) y Bobinado **En proceso 0 / 10**,
     porque tiene 5 en revisión.
3. **Filtro Estado = En proceso** → solo aparece la OP 1001, con raya en las áreas pendientes.
4. **Filtro Área = Núcleo** → la matriz queda con una sola columna de área.
5. **Para ver un "Aprobado":**
   - Entra con `nucleo` y reporta **3** en la OP 1003.
   - Con `analista`, apruébalo en Aprobaciones.
   - Vuelve al panel y pulsa **Actualizar**: Núcleo en la 1003 aparece **Aprobado 3 / 3** y el indicador
     Aprobado sube a 1.
6. El **analista** también ve el panel en su menú. Las áreas no: `/panel` las devuelve a su página
   y la API responde 403.

---

## Entrega 10 · El portal de inventarios

### Qué se puede hacer

| Quién | Qué |
|---|---|
| Analista y Supervisor | Ver existencias con filtros, el resumen por tipo y el historial de cada ítem |
| Solo Analista | Registrar entradas de **materia prima** (por ejemplo, una compra) |

**¿Y los PP y PT?** No se ingresan a mano: entran al inventario **solo** cuando el analista
aprueba una entrega (entrega 8). Así cada unidad en existencia tiene detrás un reporte aprobado.

### Lo nuevo en `entregas.py` (al final del archivo)

| Función | Ruta | Rol |
|---|---|---|
| `consultar_inventario` | `GET /api/inventario?tipo=&texto=` | Analista, Supervisor |
| `consultar_movimientos` | `GET /api/inventario/movimientos?codigo=MP-0001` | Analista, Supervisor |
| `registrar_entrada_mp` | `POST /api/inventario/entradas` | Analista |

- **`consultar_inventario`** devuelve dos cosas:
  - los ítems filtrados, con el mismo patrón `WHERE 1 = 1` + `AND ...`;
  - un **resumen** con dos `COUNT(*)` por tipo: cuántos ítems hay y cuántos están en cero.

  El resumen cuenta **todos** los ítems, sin importar los filtros de la tabla.
- **`consultar_movimientos`** trae el historial, el más reciente primero (`ORDER BY m.id DESC`).
  La OP se une con **`LEFT JOIN`**, porque una compra o el inventario inicial no tienen OP; con
  un `JOIN` normal esos movimientos no aparecerían. Después, un ciclo suma el total de entradas
  y el de salidas.
- **`registrar_entrada_mp`:**
  - solo acepta ítems MP;
  - la cantidad debe ser mayor que cero;
  - si el concepto viene vacío, usa "Entrada de materia prima";
  - `concepto[:150]` lo recorta a 150 caracteres como máximo.

  Para sumar la existencia reutiliza la misma función de la aprobación y de los datos de prueba,
  así que el movimiento queda registrado en el historial.

> **Nota:** estas tres funciones se construyeron en `entregas.py`. Al aplicar los patrones de diseño
> se movieron a **`inventario.py`** (ver "Patrones de diseño").

**Las tres formas en que cambia el inventario** usan la misma función (hoy,
`inventario.registrar_entrada` / `registrar_salida`):

| Origen | Tipo | Concepto de ejemplo |
|---|---|---|
| Datos de prueba | ENTRADA | Inventario inicial |
| Aprobar una entrega | SALIDA de materiales + ENTRADA del producto | Consumo de NUCLEO-001 · OP 1001 / Entrega de Núcleo · OP 1001 |
| Entrada de MP | ENTRADA | Compra OC-1234 |

### `inventario.html` y `inventario.js`

- **Resumen:** tres indicadores (MP, PP, PT) con el total de ítems y cuántos están "sin existencia".
  Como en el panel, los `id` usan la clave del servidor (`resumen-MP`, `resumen-MP-cero`...), así
  que un solo `for` los llena.
- **Entrada de MP:** la sección viene con `hidden` y solo se muestra si el usuario es analista.
  La lista desplegable trae solo los ítems MP. Al registrar, aparece la nueva existencia y la
  tabla se recarga.
- **Tabla de existencias:** filtros por tipo y por texto. Los ítems en cero llevan la etiqueta
  roja **Sin existencia**.
- **Historial** (ventana `<dialog>`):
  - arriba, total de entradas, total de salidas y existencia actual;
  - abajo, cada movimiento con fecha, tipo (verde **+** o rojo **−**), cantidad, existencia
    resultante, OP (o "—"), concepto y usuario.

  `movimiento.orden || "—"` significa "la OP, o una raya si no hay".

### Cómo probarlo

1. Entra con **`analista`** → **Inventario**.
   - Resumen: **MP 7** (0 sin existencia), **PP 10** (9 sin existencia: solo PP-0001 tiene 4),
     **PT 3** (3 sin existencia).
2. **Historial de MP-0001:** entradas 2.000 kg, salidas 320 kg, existencia 1.680 kg. Dos
   movimientos: "Inventario inicial" y "Consumo de NUCLEO-001 · OP 1001".
3. **Entrada:** elige MP-0007 (aceite), 500, concepto "Compra OC-1234" → *"Nueva existencia: 1.700."*
   Abre su historial: el primer movimiento es esa compra.
4. Filtro **Tipo = PT** → los tres transformadores con **Sin existencia**.
5. **Conexión con la entrega 8:** después de esta compra de aceite, todavía faltan las partes
   activas y los tanques para aprobar un Ensamble. El inventario de PP solo sube cuando se
   aprueban las entregas de Núcleo, Bobinado, Parte activa, Metalmecánica y Pintura.
6. Entra con **`supervisor`**: ve todo, pero **no** aparece la sección de entrada. Si intentara
   registrar una entrada por la API, recibiría 403.

---

## Entrega 11 · `exportar.py` y la página "Reportes" (CSV)

### ¿Qué es un CSV?

Un archivo de **texto** en el que cada línea es una fila y las columnas se separan con un
carácter. Así se ve el inventario por dentro:

```
Ítem;Descripción;Tipo;Unidad de medida;Existencia
MP-0001;Chapa de acero al silicio;MP;kg;1680
MP-0006;Pintura epóxica;MP;L;62,5
PT-0003;Transformador tipo seco 45 kVA;PT;und;0
```

Tres decisiones para que **Excel en español (Colombia)** lo abra bien con doble clic:

| Decisión | Por qué |
|---|---|
| Separador **punto y coma (`;`)** | En Colombia la coma es el separador decimal. Por eso Excel espera `;` entre columnas |
| Decimales con **coma** (`62,5`) | Así Excel los reconoce como números |
| **UTF-8 con BOM** (`"utf-8-sig"`) | El BOM es una marca invisible al inicio del archivo que le dice a Excel "esto es UTF-8". Sin ella, "Núcleo" se vería como "NÃºcleo" |

Si en algún computador Windows está configurado en inglés (separador de lista = coma), Excel
mostraría todo en una sola columna. En ese caso: Excel → **Datos → Desde texto/CSV** → elegir
"Punto y coma".

### `exportar.py`

| Función | Qué hace |
|---|---|
| `leer_fecha` | Convierte `"2026-10-26"` (lo que envía `<input type="date">`) en fecha con `date.fromisoformat`. Si no es válida → error claro |
| `filas_de_entregas` | La consulta de entregas **aprobadas** con filtros de fecha y área. Devuelve una lista de filas |
| `vista_previa_entregas` | Las mismas filas en JSON, para la tabla de la página |
| `exportar_entregas` | Las mismas filas convertidas en archivo CSV |
| `exportar_inventario` | Todos los ítems, también los que están en cero, ordenados por tipo y código |
| `crear_csv` | Escribe el CSV con el módulo `csv` y le pone el nombre con la fecha |
| `valor_para_csv` | `1680.0` → `"1680"`, `2.5` → `"2,5"`, `None` → `""` |

**La vista previa y el archivo usan la misma función** (`filas_de_entregas`). Así, lo que ves en
la tabla es exactamente lo que se descarga.

**Filtrar fechas guardadas como texto.** En la entrega 1 decidimos guardar las fechas como
`"2026-10-26 14:30"` (año-mes-día). Gracias a eso se pueden comparar como texto:
- `"2026-10-26 14:30" >= "2026-10-26"` → verdadero;
- para "Hasta" se usa `< "2026-10-27"` (el día siguiente), así se incluye **todo** el día 26.

**`crear_csv`, línea por línea:**
1. `io.StringIO()` crea un "archivo de texto en memoria": se escribe como en un archivo, pero
   no se guarda en el disco.
2. `csv.writer(texto, delimiter=";")` crea el escritor con punto y coma.
3. `writerow(encabezados)` escribe la primera línea; luego, una `writerow` por cada fila.
   El módulo `csv` se encarga de los casos difíciles: si una descripción tiene un `;` o comillas,
   la encierra entre comillas para que no se descuadren las columnas.
4. `.encode("utf-8-sig")` convierte el texto a bytes con el BOM.
5. El nombre se arma con `date.today().isoformat()` → `inventario_2026-10-26.csv`.

**¿Cómo llega el archivo al navegador?** La función devuelve `{"descarga": {...}}`.
`servidor.py` (desde la entrega 2) ve la clave `"descarga"` y, en lugar de JSON, envía el
archivo con el encabezado `Content-Disposition: attachment; filename="..."`. Eso le dice al
navegador "descárgalo con este nombre".

### Rutas nuevas (Analista y Supervisor)

| Ruta | Qué hace |
|---|---|
| `GET /api/exportar/entregas/vista-previa?desde=&hasta=&area=` | Filas en JSON para la tabla |
| `GET /api/exportar/entregas?desde=&hasta=&area=` | Descarga `entregas_aprobadas_FECHA.csv` |
| `GET /api/exportar/inventario` | Descarga `inventario_FECHA.csv` |

### Las páginas

- **Reportes** (`reportes.html` y `reportes.js`):
  - filtros "Aprobadas desde", "Hasta" y "Área";
  - el botón **Exportar a CSV** y una tabla con la vista previa y el total de unidades;
  - el botón es un **enlace** `<a download>`, cuya dirección actualiza `actualizarEnlace` con los
    mismos filtros de la tabla. Al hacer clic, el navegador descarga el archivo;
  - si no hay resultados o las fechas están mal, el enlace recibe la clase `deshabilitado`
    (se ve gris y no responde al clic).
- **Inventario:** se agregó el enlace **Exportar inventario a CSV**, que siempre exporta todo,
  sin importar los filtros de la tabla.
- **El formulario escucha `change`:** se dispara cuando cambia **cualquiera** de sus campos,
  así que con un solo escuchador basta para los tres filtros.
- **`for (let posicion = 0; posicion < fila.length; posicion++)`:** el ciclo `for` clásico, con
  un contador. Se usa aquí porque se necesita la **posición** de cada valor para saber a qué
  columna pertenece.

### Cómo probarlo

1. Entra con **`analista`** o **`supervisor`** → **Reportes**.
   - Aparece 1 entrega aprobada (Núcleo, OP 1001, 4 unidades).
2. **Exportar a CSV** → se descarga `entregas_aprobadas_<fecha de hoy>.csv`. Ábrelo con doble
   clic en Excel: cada dato en su columna y "Núcleo" y "Energía" con tilde.
3. Filtros:
   - Área **Bobinado** → 0 entregas y el botón gris;
   - Desde 2026-12-01 y Hasta 2026-01-01 → aviso rojo;
   - Desde y Hasta = hoy → vuelve a aparecer la entrega.
4. Aprueba más entregas (página Aprobaciones) y vuelve: aparecen en la vista previa y en el archivo.
5. **Inventario → Exportar inventario a CSV** → `inventario_<fecha>.csv` con **20 ítems**,
   incluidos los que están en 0 (PP y PT).
6. Para ver un decimal: registra en Inventario una entrada de 2,5 L de pintura (MP-0006) y vuelve
   a exportar → la existencia sale **62,5**.
7. Con un usuario de área, "Reportes" no aparece en el menú y la API responde 403.

---

## Entrega 12 · El asistente "Nuevo producto"

### Para qué sirve

Con las pestañas Ítems y Referencias, crear un transformador nuevo exige 12 pasos separados:
6 ítems y 6 referencias, cada una con su lista de materiales, en el orden correcto.
El asistente lo hace en **una sola pantalla**, que está en **Ítems y referencias → pestaña
"Nuevo producto"** (solo el analista).

Las conexiones entre áreas son **fijas**, porque así funciona la planta:

```
Núcleo ──┐
         ├──► Parte activa ──┐
Bobinado ┘                   ├──► Ensamble final (PT)
Metalmecánica ──► Pintura ───┘
```

El usuario solo escribe la descripción de cada parte y elige su **materia prima**.

### Lo nuevo en `catalogo.py` (al final del archivo)

**`PARTES_DEL_PRODUCTO`:** una lista con las 6 partes **en el orden de la planta**. Cada parte dice:
- qué área es;
- cómo se llama ("Tanque", "Tanque pintado"...);
- qué partes de otras áreas consume (`componentes`);
- si debe llevar al menos una materia prima (`mp_obligatoria`).

El orden importa: cuando se crea la Parte activa, el Núcleo y el Bobinado ya deben existir.

| Función | Ruta | Qué hace |
|---|---|---|
| `plantilla_producto` | `GET /api/producto/plantilla` | Los 6 bloques, las materias primas para elegir y los productos que se pueden copiar |
| `copiar_producto` | `GET /api/producto/copiar?referencia=ENSAMBLE-002` | Recorre el árbol de ese producto y, por cada área, devuelve su materia prima y las cantidades de sus conexiones |
| `vista_previa_producto` | `POST /api/producto/vista-previa` | Crea todo, arma el árbol para mostrarlo… y lo **deshace** |
| `crear_producto` | `POST /api/producto` | Crea todo de verdad |

**La idea más importante: reutilizar las reglas.** `armar_parte` **no** escribe sus propios
`INSERT`: llama a las mismas funciones de la entrega 4:

```python
codigo_item = sugerir_codigo_item(...)["codigo"]       # PP-0011
crear_item(conexion, usuario, {...})                   # Mismas validaciones que la pestaña Ítems
codigo_referencia = sugerir_codigo_referencia(...)["codigo"]   # NUCLEO-003
crear_referencia(conexion, usuario, {...})             # Nemotecnia, ciclos, repetidos...
```

Así, todas las reglas del catálogo se cumplen sin escribirlas otra vez.

**Todo o nada, sin código extra.** Si la parte 4 (Metalmecánica) falla, lanza `ValueError` y
`servidor.py` hace `rollback()`. Las partes 1 a 3, que ya se habían creado dentro de la misma
petición, también se deshacen. Nunca queda un producto a medias.

**La revisión no guarda nada.** `vista_previa_producto` crea todo (con las mismas reglas), arma el
árbol y la materia prima, y al final llama a `conexion.rollback()`. Lo que el usuario ve en la
revisión es exactamente lo que se guardará, pero mientras no pulse "Crear producto" no queda nada
en la base.

**Mensajes con el nombre del área.** `armar_producto` atrapa el error de cada parte y le agrega
el área:

```python
except ValueError as error:
    raise ValueError(f"{area['nombre']}: {error}")
```

Así el usuario lee *"Metalmecánica: debe tener al menos una materia prima."* y sabe qué bloque revisar.

**Cambio pequeño:** `buscar_nodo_de_area` se movió de `ordenes.py` a `catalogo.py`, porque ahora
la usan los dos archivos. `ordenes.py` la importa desde `catalogo.py`. Si se dejara en `ordenes.py`,
los dos archivos se importarían mutuamente y Python daría error ("importación circular").

### `catalogo.html` y `asistente.js`

- **La pestaña nueva** se agregó con un botón más (`data-panel="panel-producto"`). La función
  `prepararPestanas` de `comun.js` ya la hace funcionar sin cambios.
- **`asistente.js` es un archivo aparte**, para que `catalogo.js` no sea tan largo. Se carga
  **después** de `catalogo.js`.

  Todos los scripts de una página comparten las mismas variables globales. Por eso los nombres
  de `asistente.js` llevan "Producto" o "Asistente" (`formularioProducto`, `arrancarAsistente`...),
  para no chocar con los de `catalogo.js`. Al crear un producto, `asistente.js` llama a
  `cargarItems()` y `cargarReferencias()` de `catalogo.js`, para que las otras pestañas se actualicen.
- **Paso 1:**
  - al escribir la descripción del producto, `completarDescripciones` llena cada bloque
    ("Núcleo transformador…", "Tanque pintado transformador…");
  - si el usuario edita a mano una descripción, se marca con `dataset.editada` y ya no se
    sobrescribe;
  - **Copiar** llena los bloques con la materia prima y las cantidades del producto elegido.
- **Paso 2:** un bloque por área.
  - Las filas con 🔒 son las conexiones fijas: solo se cambia la cantidad.
  - **+ Agregar materia prima** añade una fila con una lista de solo ítems MP.
  - Si se crea una MP nueva en la pestaña Ítems, aparece al volver a abrir "Nuevo producto".
- **Paso 3:** **Revisar** muestra los códigos que se asignarán, el árbol y la materia prima por unidad.
  - **Cualquier cambio** en el formulario esconde la revisión: hay que volver a revisar antes de crear.
  - **Crear producto** guarda todo, limpia el formulario y muestra enlaces a "Ver estructura" y
    "Crear una OP".
- `novalidate` en el `<form>` le dice al navegador que no muestre sus propios mensajes: los da el
  servidor, con el nombre del área.

### Cómo probarlo (como `analista`)

1. **Ítems y referencias → Nuevo producto**.
2. Escribe *"Transformador monofásico 112,5 kVA"*: las 6 descripciones se llenan solas.
3. En "Copiar materiales" elige **PT-0002 (75 kVA)**: cada bloque se llena con sus materiales.
4. Cambia una cantidad (por ejemplo, la lámina del tanque a 70) y pulsa **Revisar**:
   - se asignarán NUCLEO-003 … ENSAMBLE-004 y PP-0011 … PT-0004;
   - aparece el árbol completo;
   - en la pestaña Referencias todavía **no** hay nada nuevo.
5. Escribe algo en una descripción: la revisión desaparece. Vuelve a revisar.
6. **Errores** (y en todos los casos no se crea nada):
   - quita la materia prima de Metalmecánica → *"Metalmecánica: debe tener al menos una materia prima."*;
   - borra la descripción del producto → *"Ensamble final: El campo «Descripción» es obligatorio."*
7. **Crear producto** → aviso verde con los enlaces.
   - En **Estructura**, ENSAMBLE-004 muestra su árbol.
   - En **Órdenes → Nueva OP**, PT-0004 aparece como completo y se puede crear una OP con él.
8. Crea una MP en la pestaña **Ítems** y vuelve a **Nuevo producto**: ya aparece en las listas.

---

## Patrones de diseño (GRASP y GoF)

### ¿Qué es un patrón de diseño?

Es una **solución probada a un problema que se repite** al programar. No es una librería ni
código que se instala: es una forma de organizar el código que tiene un **nombre conocido**.
Así, cualquier programador entiende de qué hablas cuando dices "aquí usé el patrón Observador".

| | **GRASP** | **GoF** |
|---|---|---|
| Significa | *General Responsibility Assignment Software Patterns* | *Gang of Four* ("la pandilla de los cuatro"), los autores del libro de 1994 |
| Responde a | **¿Quién debe hacer cada cosa?** Qué archivo o función se encarga de qué | **¿Cómo resuelvo este problema concreto?** Recetas para situaciones típicas |
| Cuántos | 9 principios | 23 patrones en 3 familias: creacionales, estructurales y de comportamiento |
| Sirven para | Código ordenado, fácil de cambiar y con poca dependencia entre partes | No reinventar soluciones y poder explicarlas con un nombre |

**¿Patrones sin clases?** Los patrones GoF se describieron originalmente con **clases**. En Python
y en JavaScript las funciones se pueden guardar en variables y en diccionarios, así que la mayoría
de los patrones se puede escribir **solo con funciones y diccionarios**. Así está hecho en este
proyecto, para que el código siga siendo sencillo. Lo que define a un patrón es **la idea**, no si
usa la palabra `class`.

**Cómo encontrarlos en el código:** cada patrón está señalado con un comentario
`Patrón GRASP: ...` o `Patrón GoF: ...`. En VS Code, **Ctrl+Shift+F** y busca `Patrón`.

---

### Patrones GRASP

| Patrón GRASP | Qué dice | Dónde está en el código |
|---|---|---|
| **Controlador** | Un solo punto recibe las peticiones y las reparte | `servidor.py` → `atender_api` |
| **Experto en información** | La tarea la hace quien tiene los datos para hacerla | `inventario.py` (existencias); `ordenes.calcular_requerimientos`; `entregas.avance_del_area` y `calcular_consumos`; `catalogo.contiene_item` |
| **Creador** | Crea un objeto quien lo contiene o tiene sus datos | `ordenes.crear_orden` crea también los `requerimientos` de la OP |
| **Alta cohesión** | Cada módulo hace un solo tipo de cosa | Un `.py` por tema. Se reforzó creando `inventario.py` (ver abajo) |
| **Bajo acoplamiento** | Las partes dependen poco unas de otras | Las páginas solo hablan con el servidor por la API; `entregas.py` usa la fachada de `inventario.py`; el asistente reutiliza `crear_item` y `crear_referencia`; los scripts se avisan con eventos (Observador) |
| **Fabricación pura** | Un módulo "inventado", que no es del negocio, para ordenar el código | `base_datos.py` y `exportar.py` |
| **Indirección** | Un intermediario entre dos partes | `RUTAS` entre HTTP y las reglas; `pedirDatos`/`enviarDatos` entre las páginas y `fetch` |
| **Polimorfismo** | Variantes distintas se usan de la misma forma | Todas las funciones de `RUTAS` tienen la forma `(conexion, usuario, datos)`; todos los formatos de `FORMATOS` tienen las mismas claves |
| **Variaciones protegidas** | Lo que puede cambiar se aísla en un solo lugar | Colores en `:root` (`estilos.css`), `PAGINAS` y `RUTAS` (`servidor.py`), `FORMATOS` (`exportar.py`) |

#### Cambio aplicado: el módulo `inventario.py` (Experto en información + Alta cohesión)

**Antes:**
- `base_datos.py` tenía `cambiar_existencia`. Decidir cómo sube o baja una existencia es una
  **regla del negocio**, no "guardar datos".
- `entregas.py` hacía tres cosas distintas: reportes, panel **e inventario**.

**Ahora:** todo lo de existencias vive en `inventario.py`, el **experto en inventario**:

| Función | Qué hace | Antes estaba en |
|---|---|---|
| `registrar_entrada` / `registrar_salida` | Suben o bajan una existencia y dejan el movimiento | `base_datos.cambiar_existencia` |
| `consultar_inventario` | Existencias con filtros y resumen | `entregas.py` |
| `consultar_movimientos` | Historial de un ítem | `entregas.py` |
| `registrar_entrada_mp` | Compra de materia prima | `entregas.py` |

`registrar_salida` además **nunca deja una existencia en negativo**: es una regla que ahora se
cumple en un solo lugar, para toda la aplicación.

**Detalle técnico (importación circular):** `inventario.py` importa `base_datos.py`, y los datos
de prueba de `base_datos.py` necesitan `inventario.py`. Si los dos se importaran al inicio del
archivo, uno quedaría "a medio cargar". Por eso `base_datos.py` hace `import inventario` **dentro**
de las funciones que lo usan (`insertar_materias_primas` y `mover_inventario_de_prueba`).

---

### Patrones GoF

| Patrón GoF | Familia | Dónde | Nuevo o ya estaba |
|---|---|---|---|
| **Comando** (Command) | Comportamiento | `RUTAS` en `servidor.py` | Ya estaba (ahora señalado) |
| **Fachada** (Facade) | Estructural | `pedirDatos`/`enviarDatos` en `comun.js`; `registrar_entrada`/`registrar_salida` en `inventario.py` | La de JS ya estaba; la de Python es **nueva** |
| **Adaptador** (Adapter) | Estructural | `base_datos.filas_a_diccionarios` | Ya estaba (ahora señalado) |
| **Estrategia** (Strategy) | Comportamiento | `FORMATOS` en `exportar.py` | **Nuevo** |
| **Método plantilla** (Template Method) | Comportamiento | `crear_csv` en `exportar.py` | **Reforzado** |
| **Observador** (Observer) | Comportamiento | `avisar`/`escuchar` en `comun.js`, usados por `catalogo.js` y `asistente.js` | **Nuevo** |

#### Comando (Command)

**Problema:** el servidor recibe ~45 tipos de petición distintos. Con `if` sería una cadena enorme:
`if ruta == "/api/items": ... elif ruta == "/api/ordenes": ...`.

**Solución:** cada petición se convierte en una **orden** (una función) guardada en una tabla.
El servidor busca la orden por su clave y la ejecuta:

```python
RUTAS = {
    "GET /api/items": (catalogo.listar_items, [ANALISTA, SUPERVISOR]),
    "POST /api/ordenes": (ordenes.crear_orden, [ANALISTA, SUPERVISOR]),
    ...
}
funcion, roles_permitidos = RUTAS[clave]      # en atender_api
respuesta = funcion(conexion, usuario, datos)
```

Agregar una función nueva a la API = agregar una línea a la tabla.

#### Fachada (Facade)

**Problema:** usar algo complicado desde muchos lugares obliga a repetir sus detalles.

**Solución:** una función sencilla que esconde lo complicado.
- **En JavaScript:** `pedirDatos("/api/ordenes")` esconde `fetch`, la conversión a JSON, la revisión
  de errores y el regreso al login si se venció la sesión.
- **En Python (nuevo):** `entregas.aprobar_reporte` solo dice:

  ```python
  inventario.registrar_salida(conexion, item_id, consumo, usuario_id, "Consumo de ...")
  ```

  No sabe que por dentro se lee la existencia, se hace un `UPDATE` en `items` y un `INSERT` en
  `movimientos`.

#### Adaptador (Adapter)

**Problema:** SQLite entrega filas en un formato (`sqlite3.Row`) que `json` no sabe convertir.

**Solución:** `filas_a_diccionarios(filas)` las "adapta" a diccionarios normales, que sí se pueden
enviar como JSON. Como un adaptador de enchufe: no cambia la corriente, solo la forma.

#### Estrategia (Strategy) — nuevo

**Problema:** el CSV solo servía para Excel en español. En un computador con Excel en inglés (o en
otros programas) salía todo en una columna.

**Solución:** varias **estrategias** de formato, intercambiables, en un diccionario. Todas tienen
las mismas claves, así el resto del código las usa igual sin preguntar cuál es:

```python
FORMATOS = {
    "excel": {"nombre": "Excel en español", "separador": ";", "decimal": ","},
    "estandar": {"nombre": "CSV estándar", "separador": ",", "decimal": "."},
}
```

- `elegir_formato(datos)` toma la estrategia que pidió la página (`?formato=excel` o `?formato=estandar`).
- En **Reportes** e **Inventario** apareció el selector **"Formato del archivo"**.
- **Agregar un formato nuevo** (por ejemplo, separado por tabuladores) = agregar una entrada a
  `FORMATOS` y una opción al selector. No se toca nada más.

#### Método plantilla (Template Method)

**Problema:** los dos reportes repetían los mismos pasos para armar el archivo.

**Solución:** una función "plantilla" fija **siempre el mismo orden** de pasos, y cada reporte solo
aporta lo que cambia:

```python
def crear_csv(nombre_base, encabezados, filas, formato):
    # Paso 1: crear el archivo en memoria con el separador de la estrategia
    # Paso 2: escribir los encabezados
    # Paso 3: escribir cada fila (valores según la estrategia)
    # Paso 4: codificar en UTF-8 con BOM
    # Paso 5: nombre con la fecha de hoy
```

`exportar_entregas` y `exportar_inventario` solo le pasan su nombre, sus encabezados y sus filas.
Aquí se ven **dos patrones juntos**: la plantilla fija los pasos y la estrategia decide el
separador y el signo decimal.

#### Observador (Observer) — nuevo

**Problema:** al crear un producto, `asistente.js` llamaba **directamente** a `cargarItems()`,
`cargarReferencias()` y `cargarMaterialesDisponibles()` de `catalogo.js`. Si alguien cambiaba el
nombre de una de esas funciones, el asistente se rompía (acoplamiento alto).

**Solución:** quien hace un cambio solo **avisa**, y quien esté interesado **escucha**. Dos funciones
nuevas en `comun.js`:

```js
function avisar(nombreEvento) {
  document.dispatchEvent(new CustomEvent(nombreEvento));
}

function escuchar(nombreEvento, funcion) {
  document.addEventListener(nombreEvento, funcion);
}
```

Cómo se usan en la página Ítems y referencias:

| Quién avisa `"catalogo-cambiado"` | Quién escucha y qué hace |
|---|---|
| `catalogo.js` al guardar un ítem o una referencia | `catalogo.js`: recarga ítems, referencias y materiales |
| `asistente.js` al crear un producto | `asistente.js`: recarga las materias primas y los productos para copiar |

Quien avisa **no sabe quién escucha**. Mañana se podría agregar otra parte que escuche el mismo
aviso sin tocar a quien avisa. Es como un grupo de WhatsApp: el que escribe no necesita saber
quiénes leen.

**Se notó en el uso:** antes, el asistente recargaba sus materias primas solo al hacer clic en su
pestaña. Ahora se actualiza en el momento en que se crea una MP en la pestaña Ítems.

#### Patrones que NO usamos (y por qué)

Saber cuándo **no** usar un patrón también cuenta:

- **Singleton (instancia única):** sería tener una sola conexión a la base para todo el programa.
  Aquí sería un **error**: el servidor atiende varias peticiones a la vez (`ThreadingHTTPServer`) y
  SQLite no permite compartir una conexión entre hilos. Por eso cada petición abre la suya.
- **Abstract Factory, Builder, Prototype, Visitor y otros:** el proyecto no tiene los problemas que
  resuelven. Meterlos a la fuerza haría el código más largo y difícil de entender sin ganar nada.

---

### Resumen de cambios hechos para aplicar los patrones

| Archivo | Cambio | Patrón |
|---|---|---|
| `inventario.py` (**nuevo**) | Entradas, salidas, consulta, historial y entrada de MP | GRASP Experto + Alta cohesión; GoF Fachada |
| `base_datos.py` | Ya no tiene `cambiar_existencia`; los datos de prueba usan `inventario.registrar_entrada/salida` | Alta cohesión |
| `entregas.py` | Sin las funciones de inventario; la aprobación usa la fachada | Bajo acoplamiento; Fachada |
| `servidor.py` | Las rutas de inventario apuntan a `inventario.py`; comentarios de Controlador y Comando | Controlador, Comando |
| `exportar.py` | `FORMATOS`, `elegir_formato`, `crear_csv` con formato | Estrategia, Método plantilla |
| `reportes.html` / `.js`, `inventario.html` / `.js` | Selector "Formato del archivo" | Estrategia |
| `comun.js` | `avisar` y `escuchar` | Observador |
| `catalogo.js`, `asistente.js` | Se avisan con eventos en lugar de llamarse directamente | Observador, Bajo acoplamiento |
| Varios | Comentarios `Patrón GRASP/GoF: ...` donde se aplica cada uno | — |

### Cómo probar los patrones nuevos

1. **Estrategia:**
   - **Inventario** → "Formato del archivo: CSV estándar" → **Exportar**. Ábrelo con el Bloc de
     notas: columnas separadas por **coma** y decimales con **punto**.
   - Con "Excel en español": punto y coma y decimales con coma.
   - Lo mismo en **Reportes**.
2. **Observador:**
   - En **Ítems y referencias** abre la pestaña **Nuevo producto** y mira la lista de materias primas.
   - Ve a la pestaña **Ítems**, crea una MP (por ejemplo, "Barniz aislante").
   - Vuelve a **Nuevo producto**: la MP ya está en las listas.
   - Crea un producto con el asistente: la pestaña **Referencias** ya muestra las 6 referencias nuevas.
3. **Fachada de inventario:** aprueba una entrega en **Aprobaciones** y mira el historial del
   material en **Inventario**. Todo funciona igual que antes, pero el movimiento lo registró
   `inventario.py`.

---

## Mapa completo de la API

Todas las rutas están en el diccionario `RUTAS` de `servidor.py`. Las dos de sesión
(`POST /api/login` y `POST /api/logout`) se atienden aparte porque manejan la cookie.

| Ruta | Función | Roles |
|---|---|---|
| **Sesión** | | |
| `POST /api/login` | `servidor.iniciar_sesion` | Cualquiera |
| `POST /api/logout` | `servidor.cerrar_sesion` | Cualquiera |
| `GET /api/sesion` | `servidor.consultar_sesion` | Todos |
| **Catálogo** (`catalogo.py`) | | |
| `GET /api/listas` | `consultar_listas` | Todos |
| `GET /api/items` | `listar_items` | Analista, Supervisor |
| `GET /api/items/siguiente-codigo` | `sugerir_codigo_item` | Analista |
| `POST /api/items` | `crear_item` | Analista |
| `POST /api/items/editar` | `editar_item` | Analista |
| `GET /api/referencias` | `listar_referencias` | Analista, Supervisor |
| `GET /api/referencia` | `consultar_referencia` | Analista, Supervisor |
| `GET /api/referencias/siguiente-codigo` | `sugerir_codigo_referencia` | Analista |
| `POST /api/referencias` | `crear_referencia` | Analista |
| `POST /api/referencias/materiales` | `cambiar_materiales` | Analista |
| `GET /api/estructura` | `consultar_estructura` | Analista, Supervisor |
| `GET /api/producto/plantilla` | `plantilla_producto` | Analista |
| `GET /api/producto/copiar` | `copiar_producto` | Analista |
| `POST /api/producto/vista-previa` | `vista_previa_producto` | Analista |
| `POST /api/producto` | `crear_producto` | Analista |
| **Órdenes** (`ordenes.py`) | | |
| `GET /api/clientes` | `listar_clientes` | Analista, Supervisor |
| `POST /api/clientes` | `crear_cliente` | Analista, Supervisor |
| `GET /api/ordenes` | `listar_ordenes` | Todos |
| `GET /api/orden` | `consultar_orden` | Todos |
| `GET /api/ordenes/siguiente-numero` | `sugerir_numero_orden` | Analista, Supervisor |
| `GET /api/ordenes/ensambles` | `listar_ensambles` | Analista, Supervisor |
| `GET /api/ordenes/vista-previa` | `vista_previa_orden` | Analista, Supervisor |
| `POST /api/ordenes` | `crear_orden` | Analista, Supervisor |
| **Entregas y panel** (`entregas.py`) | | |
| `GET /api/mi-orden` | `consultar_orden_para_area` | Área |
| `POST /api/reportes` | `crear_reporte` | Área |
| `GET /api/reportes` | `listar_reportes` (cada área ve solo los suyos) | Todos |
| `GET /api/reporte` | `consultar_reporte_para_revision` | Analista |
| `POST /api/reportes/aprobar` | `aprobar_reporte` | Analista |
| `POST /api/reportes/rechazar` | `rechazar_reporte` | Analista |
| `GET /api/panel` | `consultar_panel` | Supervisor, Analista |
| **Inventario** (`inventario.py`) | | |
| `GET /api/inventario` | `consultar_inventario` | Analista, Supervisor |
| `GET /api/inventario/movimientos` | `consultar_movimientos` | Analista, Supervisor |
| `POST /api/inventario/entradas` | `registrar_entrada_mp` | Analista |
| **Exportaciones** (`exportar.py`) | | |
| `GET /api/exportar/entregas/vista-previa` | `vista_previa_entregas` | Analista, Supervisor |
| `GET /api/exportar/entregas?formato=excel\|estandar` | `exportar_entregas` (descarga CSV) | Analista, Supervisor |
| `GET /api/exportar/inventario?formato=excel\|estandar` | `exportar_inventario` (descarga CSV) | Analista, Supervisor |

---

## Preguntas de repaso

Para estudiar en grupo. Al lado de cada pregunta está la entrega donde se explica la respuesta.

**Base de datos y seguridad**
1. ¿Por qué se guarda la tabla `requerimientos` en lugar de calcular lo que debe producir cada
   área cada vez que se consulta una OP? *(Entrega 1)*
2. ¿Qué es la "sal" de una contraseña y qué problema evita? *(Entrega 1)*
3. ¿Por qué en el SQL se escriben `?` en lugar de pegar los valores en el texto? ¿Qué ataque
   evita? *(Entrega 1)*
4. ¿Por qué las fechas se guardan como `"2026-10-26 14:30"` y no como `"26/10/2026"`? ¿Qué
   función del proyecto depende de eso? *(Entregas 1 y 11)*
5. ¿Para qué sirve `escaparHtml` y qué ataque evita? *(Entrega 3)*
6. Si se oculta un botón con `hidden`, ¿un operario ya no puede hacer esa acción? ¿Quién la
   impide de verdad? *(Entregas 2 y 6)*

**Servidor**

7. ¿Qué hace `commit()` y qué hace `rollback()`? Da un ejemplo del proyecto en el que
   `rollback()` evita que el inventario quede mal. *(Entregas 2 y 8)*
8. ¿Qué diferencia hay entre los códigos 401 y 403? *(Entrega 2)*
9. ¿Cómo sabe el servidor quién es el usuario en cada petición? *(Entrega 2)*

**Reglas del negocio**

10. ¿Qué es un ciclo en la lista de materiales y cómo lo detecta `contiene_item`? *(Entrega 4)*
11. ¿Qué es la recursión? Nombra dos funciones del proyecto que la usan. *(Entregas 4 y 5)*
12. Si Núcleo debe 10, tiene 4 aprobadas y 3 en revisión, ¿cuánto puede reportar? ¿Y si además
    le rechazaron 2? *(Entrega 7)*
13. ¿Qué pasa con el inventario al aprobar una entrega? ¿Y al rechazarla? *(Entrega 8)*
14. ¿Por qué `aprobar_reporte` revisa los faltantes **antes** de descontar el primer material?
    *(Entrega 8)*
15. ¿Cuándo un área está "En proceso" en el panel? *(Entrega 9)*
16. ¿Por qué los PP y PT no se pueden ingresar a mano en el inventario? *(Entrega 10)*

**Exportaciones y asistente**

17. ¿Por qué el CSV usa punto y coma y no coma? ¿Qué es el BOM? *(Entrega 11)*
18. ¿Cómo hace el asistente "Nuevo producto" para mostrar una revisión sin guardar nada?
    *(Entrega 12)*
19. ¿Por qué el asistente llama a `crear_item` y `crear_referencia` en lugar de escribir sus
    propios `INSERT`? *(Entrega 12)*
20. ¿Qué es una importación circular y por qué `buscar_nodo_de_area` se movió a `catalogo.py`?
    *(Entrega 12)*

**Patrones de diseño**

21. ¿Qué diferencia hay entre GRASP y GoF? *(Patrones de diseño)*
22. ¿Por qué `RUTAS` es un ejemplo del patrón Comando? ¿Qué pasaría sin él? *(Patrones de diseño)*
23. ¿Qué problema resolvió el patrón Observador entre `asistente.js` y `catalogo.js`?
    *(Patrones de diseño)*
24. En `exportar.py` hay dos patrones trabajando juntos. ¿Cuáles son y qué hace cada uno?
    *(Patrones de diseño)*
25. ¿Por qué se creó `inventario.py`? Nombra los dos principios GRASP y el patrón GoF que aplica.
    *(Patrones de diseño)*
26. ¿Por qué NO se usó el patrón Singleton para la conexión a la base de datos?
    *(Patrones de diseño)*
