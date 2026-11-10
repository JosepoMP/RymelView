# Resumen para la sustentación

## 1. ¿Qué es RymelView? (dilo en 20 segundos)

Una página web para Rymel S.A.S. donde **el operario reporta lo que entregó**, **el analista lo
aprueba** y, al aprobarlo, **el inventario se actualiza solo**. Así se elimina el día de retraso
que hoy causan los formularios de Google y la transcripción manual al ERP.

## 2. Las 3 partes

| Parte | Tecnología | Qué hace |
|---|---|---|
| **Cliente** (lo que se ve) | HTML + CSS + JavaScript | HTML = estructura, CSS = diseño, JS = qué pasa al hacer clic |
| **Servidor** | Python (`servidor.py`) | Recibe peticiones, revisa quién eres y qué puedes hacer, aplica las reglas |
| **Base de datos** | SQLite (`rymel.db`) | Un solo archivo con 11 tablas |

Solo se usó lo que **Python trae incluido**: nada de `pip install` ni frameworks.

## 3. El viaje de un clic (¡el más importante!)

1. El usuario pulsa un botón → el **JS** envía los datos al servidor en formato **JSON**.
2. `servidor.py` busca la ruta en el diccionario **`RUTAS`** (ej. `"POST /api/reportes"`).
3. Revisa la **sesión** (si no hay → **401**) y el **rol** (si no puede → **403**).
4. Llama a la función del módulo (ej. `entregas.crear_reporte`).
5. Si todo sale bien → **`commit()`** (se guarda). Si hay error → **`rollback()`** (se deshace todo).
6. Responde en JSON y el JS muestra el resultado o el mensaje de error.

## 4. Los archivos de Python

| Archivo | Se encarga de |
|---|---|
| `servidor.py` | La puerta de entrada: rutas, sesiones y permisos |
| `base_datos.py` | Crear las tablas, cifrar contraseñas y los datos de prueba |
| `catalogo.py` | Ítems, referencias y listas de materiales |
| `ordenes.py` | Clientes y órdenes de producción (OP) |
| `entregas.py` | Reportes, aprobación, rechazo y panel |
| `inventario.py` | **Único** lugar que cambia existencias y guarda el historial |
| `exportar.py` | Archivos CSV |

## 5. Roles

- **Operario** (uno por cada una de las 6 áreas): reporta entregas.
- **Analista**: aprueba o rechaza, crea productos, órdenes y entradas de materia prima.
- **Supervisor**: ve el panel, el inventario y descarga reportes.

## 6. Las reglas del negocio

- **El inventario solo cambia al APROBAR.** Al reportar, el reporte queda *pendiente*.
- **No se puede reportar más de lo que falta:** `requerido − aprobado − en revisión`.
  Los rechazados no cuentan.
- **Al aprobar**, primero se revisa que **todos** los materiales alcancen. Luego se descuentan
  los materiales y se suma el producto, todo en una sola operación: o se hace completo o no se hace.
- **El inventario nunca queda en negativo.**
- **Rechazar exige un motivo**, que el operario ve en su historial.

## 7. Seguridad (siempre lo preguntan)

- **Contraseñas:** no se guardan, se guarda un **hash** (PBKDF2, 100.000 repeticiones) con
  una **sal** distinta por usuario. Así, dos contraseñas iguales no se ven iguales.
- **Sesión:** al entrar se crea una **cookie** con una llave aleatoria. `HttpOnly` impide que
  el JS la lea.
- **Permisos:** se revisan en el **servidor**. Ocultar un botón no basta.
- **SQL con `?`:** los valores no se pegan en el texto del SQL. Así se evita la **inyección SQL**.

## 8. Patrones de diseño (aprende estos 4)

| Patrón | Tipo | En una frase | Dónde |
|---|---|---|---|
| **Controlador** | GRASP | Una sola puerta recibe todo y reparte | `atender_api` en `servidor.py` |
| **Comando** | GoF | Una tabla dice qué función atiende cada ruta y quién puede usarla | `RUTAS` |
| **Fachada** | GoF | Una función simple esconde varios pasos | `registrar_entrada` / `registrar_salida` |
| **Observador** | GoF | Cuando algo cambia, se avisa a quien le interesa | `avisar` / `escuchar` en `comun.js` |

**GRASP** responde *¿quién hace cada cosa?* y **GoF** responde *¿cómo resuelvo este problema?*

## 9. Preguntas probables (respuesta corta)

- **¿Por qué SQLite?** Es un solo archivo, viene con Python y no necesita instalar un servidor de base de datos.
- **¿Diferencia entre 401 y 403?** 401 = no has iniciado sesión. 403 = sí iniciaste, pero tu rol no tiene permiso.
- **¿Qué hacen `commit` y `rollback`?** `commit` guarda los cambios; `rollback` los deshace si hubo un error.
- **¿Por qué CSV y no Excel (XLSX)?** XLSX necesita librerías externas. El CSV usa `;` porque Excel en español usa la coma para los decimales, y lleva **BOM** para que Excel muestre bien las tildes.
- **¿Por qué se guarda la tabla `requerimientos`?** Se calcula una sola vez al crear la OP, para que no cambie si después se edita la lista de materiales.
- **¿Por qué no se usó Singleton?** El servidor atiende con varios hilos a la vez y SQLite no comparte una conexión entre hilos, así que cada petición abre la suya.
- **¿Qué falta para usarlo en la planta?** HTTPS, un servidor en la red de la empresa y pruebas con usuarios reales.

## 10. El diagrama UML en el código

Cada **clase** del diagrama es una **tabla** de la base de datos. Cada **relación** es una
**llave foránea**: un campo `_id` que apunta a otra tabla, marcado con `REFERENCES` en
[base_datos.py](base_datos.py). Así se lee cada fila de esta tabla:
- **Llave foránea:** dónde se declara la relación.
- **Dónde se usa:** la función que la aprovecha.

| Relación del diagrama | Llave foránea (`base_datos.py`) | Dónde se usa |
|---|---|---|
| Área *tiene asignados* Usuarios | `usuarios.area_id` (línea 119) | `crear_reporte` toma el área del usuario que inició sesión ([entregas.py:67](entregas.py:67)) |
| Usuario *inicia* Sesiones | `sesiones.usuario_id` (línea 124) | `iniciar_sesion` crea la sesión ([servidor.py:144](servidor.py:144)); `buscar_usuario_de_sesion` la lee en cada petición ([servidor.py:124](servidor.py:124)) |
| Área *ejecuta* Referencias | `referencias.area_id` (línea 141) | `crear_referencia` ([catalogo.py:274](catalogo.py:274)): el código lleva el nombre del área, ej. `NUCLEO-001` |
| Ítem *es producido por* Referencia | `referencias.item_id` con `UNIQUE` (línea 142) | `validar_item_propio` ([catalogo.py:321](catalogo.py:321)): el ítem debe ser del tipo del área y no tener otra referencia |
| Referencia ◆ *define* LíneaMaterial | `lineas_material.referencia_id` (línea 148) | `guardar_materiales` ([catalogo.py:310](catalogo.py:310)) |
| Ítem *se consume en* LíneaMaterial | `lineas_material.item_id` (línea 149) | `validar_materiales` ([catalogo.py:332](catalogo.py:332)) y `contiene_item` ([catalogo.py:360](catalogo.py:360)), que evita ciclos |
| Cliente *solicita* Órdenes | `ordenes.cliente_id` (línea 164) | `crear_orden` ([ordenes.py:165](ordenes.py:165)) revisa que el cliente exista |
| Referencia *se fabrica en* Orden | `ordenes.referencia_id` (línea 163) | `buscar_ensamble` ([ordenes.py:112](ordenes.py:112)): solo se aceptan productos terminados |
| Orden ◆ *congela* Requerimientos | `requerimientos.orden_id` (línea 174) | `crear_orden` guarda la OP y sus requerimientos juntos, calculados por `calcular_requerimientos` ([ordenes.py:62](ordenes.py:62)) |
| Área *responde por* Requerimiento | `requerimientos.area_id` (línea 175) | `requerimiento_del_area` ([entregas.py:27](entregas.py:27)) |
| Orden ◆ *recibe* Reportes | `reportes.orden_id` (línea 184) | `crear_reporte` ([entregas.py:67](entregas.py:67)) y `avance_del_area` ([entregas.py:43](entregas.py:43)) |
| Área *emite* Reportes | `reportes.area_id` (línea 185) | `crear_reporte`: el área sale de la sesión, el operario no la escribe |
| Ítem *altera su existencia por* Movimientos | `movimientos.item_id` (línea 200) | `mover_existencia` ([inventario.py:37](inventario.py:37)): cambia la existencia y guarda el movimiento juntos |
| Reporte *genera* Movimientos | `movimientos.reporte_id` (línea 205) | `aprobar_reporte` ([entregas.py:200](entregas.py:200)) le pasa el reporte a `registrar_entrada` y `registrar_salida` |
| Orden *registra* Movimientos | `movimientos.orden_id` (línea 204) | `aprobar_reporte`. Las compras de materia prima no tienen OP: por eso es `0..1` |
| Usuario *registra* Movimientos | `movimientos.usuario_id` (línea 206) | `registrar_entrada` y `registrar_salida` ([inventario.py:27](inventario.py:27)) guardan quién hizo el cambio |

**Los métodos del diagrama** son funciones de Python, porque el proyecto no usa clases:

| Método en el diagrama | Función real |
|---|---|
| `Usuario.cifrar_contrasena()` | `cifrar_contrasena` ([base_datos.py:83](base_datos.py:83)) |
| `Reporte.calcular_consumos()` | `calcular_consumos` ([entregas.py:161](entregas.py:161)) |
| `Sesion.es_valida()` | `buscar_usuario_de_sesion` ([servidor.py:124](servidor.py:124)) |
| `Referencia.validar_nemotecnia()` | `tiene_formato` ([catalogo.py:66](catalogo.py:66)) |
| `Referencia.validar_ciclos()` | `contiene_item` ([catalogo.py:360](catalogo.py:360)) |
| `Cliente.validar_nit()` | `nit_valido` ([ordenes.py:32](ordenes.py:32)) |
| `Orden.calcular_avance()` | `avance_del_area` ([entregas.py:43](entregas.py:43)) |

**Rombo relleno (◆) = composición:** la parte no existe sin el todo. No hay líneas de materiales
sin referencia, ni requerimientos o reportes sin OP.

---

# Notas por entrega

## Entrega 1 · `base_datos.py`

### ¿Qué es una base de datos SQLite?

Es un **solo archivo** (`rymel.db`) que guarda la información en **tablas**, como hojas
de Excel: cada fila es un registro y cada columna, un dato. Python trae el módulo
`sqlite3` para usarla, así que no hay que instalar nada.

### Cómo se conecta con los demás archivos

- `servidor.py` llamará a `preparar_base_datos()` al arrancar y usará `cifrar_contrasena()`
  para el inicio de sesión.
- `catalogo.py`, `ordenes.py`, `entregas.py` y `exportar.py` usarán `conectar()` para
  consultar y `fecha_actual()` para las fechas.


´´´

## Entrega 2 · `servidor.py`

### ¿Qué es un servidor web?

Un programa que **espera peticiones** del navegador y las **responde**. Cada vez que
escribes una dirección o una página pide datos, el navegador envía una petición:


´´´

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


´´´

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


´´´

## Entrega 5 · La página "Estructura" (el árbol)

### ¿De dónde sale el árbol?

Nadie lo dibuja a mano: **se arma solo** con lo que ya está en la base de datos.

1. La referencia `ENSAMBLE-001` produce el ítem `PT-0001` → es la **raíz**.
2. Su lista de materiales dice que consume `PP-0003`, `PP-0005` y `MP-0007` → son sus **hijos**.
3. `PP-0003` tiene su propia referencia (`PACTIVA-001`), con su propia lista → se baja otro nivel.
4. La **materia prima** no tiene referencia → ahí se detiene la rama (es una **hoja**).

Si creas ítems y referencias en el catálogo (entrega 4), el árbol del producto nuevo
aparece aquí automáticamente.


´´´

## Entrega 12 · El asistente "Nuevo producto"

### Para qué sirve

Con las pestañas Ítems y Referencias, crear un transformador nuevo exige 12 pasos separados:
6 ítems y 6 referencias, cada una con su lista de materiales, en el orden correcto.
El asistente lo hace en **una sola pantalla**, que está en **Ítems y referencias → pestaña
"Nuevo producto"** (solo el analista).

Las conexiones entre áreas son **fijas**, porque así funciona la planta:


´´´

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

### Patrones GoF

| Patrón GoF | Familia | Dónde | Nuevo o ya estaba |
|---|---|---|---|
| **Comando** (Command) | Comportamiento | `RUTAS` en `servidor.py` | Ya estaba (ahora señalado) |
| **Fachada** (Facade) | Estructural | `pedirDatos`/`enviarDatos` en `comun.js`; `registrar_entrada`/`registrar_salida` en `inventario.py` | La de JS ya estaba; la de Python es **nueva** |
| **Adaptador** (Adapter) | Estructural | `base_datos.filas_a_diccionarios` | Ya estaba (ahora señalado) |
| **Estrategia** (Strategy) | Comportamiento | `FORMATOS` en `exportar.py` | **Nuevo** |
| **Método plantilla** (Template Method) | Comportamiento | `crear_csv` en `exportar.py` | **Reforzado** |
| **Observador** (Observer) | Comportamiento | `avisar`/`escuchar` en `comun.js`, usados por `catalogo.js` y `asistente.js` | **Nuevo** |

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