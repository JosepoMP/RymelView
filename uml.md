# El diagrama UML de RymelView: cómo entenderlo y cómo sustentarlo

## 1. ¿Qué es un diagrama de clases UML?

Es un **plano**. Así como un arquitecto dibuja el plano de una casa antes de construirla, el
diagrama de clases dibuja **qué información guarda el sistema y cómo se conecta**.

Tiene tres cosas:

| En el diagrama | Qué es | Analogía |
|---|---|---|
| **Clase** (cada cuadro) | Un tipo de cosa que el sistema guarda | Un **cajón** de un archivador: "Clientes", "Órdenes"... |
| **Atributo** (cada renglón del cuadro) | Un dato de esa cosa | Una **casilla** de un formulario: nombre, NIT, cantidad |
| **Relación** (cada línea) | Cómo se conectan dos cosas | Un **hilo** que une dos cajones: "esta orden es de este cliente" |

## 2. ¿Cómo pasa el diagrama al código? (la idea clave)

En RymelView **no hay clases de Python**: el diagrama se convirtió en la **base de datos**.
La regla es muy simple:

| En el diagrama | En el código | Ejemplo |
|---|---|---|
| Clase | **Tabla** (`CREATE TABLE`) | Clase `Cliente` → tabla `clientes` |
| Atributo | **Columna** de la tabla | `nit: string` → `nit TEXT NOT NULL UNIQUE` |
| Relación | **Llave foránea** (`REFERENCES`) | Orden → Cliente → `cliente_id INTEGER REFERENCES clientes(id)` |
| Método | **Función de Python** | `validar_nit()` → `def nit_valido(nit):` |

📍 **Todo está en un solo lugar:** [base_datos.py](base_datos.py), de la línea 105 a la 210.

> **Frase para la sustentación:** "Cada clase del diagrama es una tabla de la base de datos,
> cada atributo es una columna y cada relación es una llave foránea. Los métodos son las
> funciones de Python que trabajan con esos datos."

## 3. ¿Qué es una llave foránea? (con analogía)

Piensa en la **cédula**. En vez de copiar todos tus datos en cada documento, solo se escribe
tu número de cédula, y con ese número se encuentra todo lo demás.

En la base de datos pasa igual. La tabla `ordenes` no copia el nombre ni el NIT del cliente:
solo guarda **el número (`id`) del cliente** en la columna `cliente_id`.

```sql
cliente_id INTEGER NOT NULL REFERENCES clientes(id)
```

Se lee así: *"`cliente_id` es un número entero, es obligatorio y **tiene que existir en la
tabla clientes**"*. Si alguien intenta crear una orden con un cliente que no existe, la base
de datos no lo deja. Eso se llama **integridad referencial**.

**Truco para encontrarlas:** toda columna que termina en `_id` (menos el `id` propio) es una
relación del diagrama.

## 4. La multiplicidad: los números de las líneas

Los números en los extremos de cada línea dicen **cuántos** de cada lado.

| Símbolo | Se lee | Analogía |
|---|---|---|
| `1` | exactamente uno | Una persona tiene **una** cédula |
| `0..1` | ninguno o uno | Una persona puede tener **o no** pasaporte |
| `0..*` | ninguno o muchos | Un cliente puede tener **cero o muchas** órdenes |
| `1..*` | al menos uno | Una receta tiene **al menos un** ingrediente |

**Cómo se ve en el código:**
- `NOT NULL` = obligatorio = **1**. Ejemplo: toda orden **debe** tener cliente.
- Sin `NOT NULL` = puede estar vacío = **0..1**. Ejemplo: un movimiento **puede** no tener orden.
- `UNIQUE` = no se repite. Ejemplo: un ítem solo puede ser producido por **una** referencia.

## 5. Los dos tipos de línea

### Asociación (línea normal con flecha)
Dos cosas se conocen, pero **cada una puede existir sola**.
- **Analogía:** un cliente y un banco. Si cierras la cuenta, el cliente sigue existiendo.
- **Ejemplo:** *Cliente → Orden*. El cliente existe aunque no tenga órdenes.

### Composición (línea con rombo relleno ◆)
Una cosa es **parte** de otra y **no tiene sentido sin ella**.
- **Analogía:** una casa y sus habitaciones. Si demuelen la casa, no quedan habitaciones sueltas.
- **En RymelView hay tres:**
  - *Referencia ◆ LíneaMaterial:* una línea de la receta no existe sin su receta.
  - *Orden ◆ Requerimiento:* lo que debe entregar cada área no existe sin la orden.
  - *Orden ◆ Reporte:* una entrega siempre es de una orden.

📍 En el código, la composición *Orden ◆ Requerimiento* se ve en `crear_orden`
([ordenes.py:165](ordenes.py:165)): la orden y sus requerimientos se guardan **juntos**. Si
algo falla, el servidor deshace los dos (rollback), así que nunca queda una orden sin sus requerimientos.

## 6. Las 11 clases explicadas con analogías

| Clase | Qué es | Analogía |
|---|---|---|
| **Area** | Las 6 áreas de la planta, en orden | Las **estaciones** de una línea de ensamble |
| **Usuario** | Quien entra al sistema y su rol | El **carné** de un empleado |
| **Sesion** | Quién está conectado ahora | La **manilla** de un evento: te identifica mientras estás adentro |
| **Item** | Materias primas, productos en proceso y terminados, con su cantidad | Los **productos de una bodega** con su existencia |
| **Referencia** | Lo que fabrica cada área | Una **ficha técnica**: "el área Núcleo fabrica el núcleo de 45 kVA" |
| **LineaMaterial** | Cada material que necesita una referencia | Un **ingrediente** de una receta |
| **Cliente** | Quién pide los transformadores | El **cliente** de una factura |
| **Orden** | La orden de producción (OP) | Un **pedido** en un restaurante |
| **Requerimiento** | Cuánto debe entregar cada área en una OP | La **comanda** que va a cada estación de la cocina |
| **Reporte** | Lo que un área dice que entregó | El **"listo"** que dice cada cocinero |
| **Movimiento** | Cada vez que sube o baja el inventario | Un renglón del **extracto bancario** |

## 7. Cuenta la historia del diagrama (la mejor forma de sustentarlo)

No expliques las relaciones una por una como una lista. **Cuéntalas como una historia**,
siguiendo un transformador desde que se crea hasta que se entrega:

> **1. Se crea el producto.** Cada **Área** tiene sus **Referencias** (*Área → Referencia*).
> Cada referencia fabrica un **Ítem** (*Ítem → Referencia*) y tiene su receta: sus
> **Líneas de material** (*Referencia ◆ LíneaMaterial*). Cada línea dice qué ítem se usa y
> cuánto (*Ítem → LíneaMaterial*).
>
> **2. Un cliente pide.** El **Cliente** hace una **Orden** (*Cliente → Orden*) de un
> producto terminado (*Referencia → Orden*). Al crearla, el sistema calcula cuánto debe
> entregar cada área y lo guarda en **Requerimientos** (*Orden ◆ Requerimiento*,
> *Área → Requerimiento*).
>
> **3. El operario trabaja.** El **Usuario** entra y se crea su **Sesión**
> (*Usuario → Sesión*). Como pertenece a un área (*Área → Usuario*), reporta lo que entregó:
> se crea un **Reporte** de esa orden y esa área (*Orden ◆ Reporte*, *Área → Reporte*).
>
> **4. El analista aprueba.** Al aprobar, el inventario cambia y cada cambio queda como un
> **Movimiento** (*Ítem → Movimiento*). Así se sabe de qué reporte vino
> (*Reporte → Movimiento*), de qué orden (*Orden → Movimiento*) y quién lo hizo
> (*Usuario → Movimiento*).

Así se cubren **las 16 relaciones** en un minuto y quedan claras.

## 8. Dónde está cada relación en el código

| Relación | Línea de código | Archivo y línea | Se usa en |
|---|---|---|---|
| Área → Usuario | `area_id INTEGER REFERENCES areas(id)` | `base_datos.py`, 119 | `crear_reporte` ([entregas.py:67](entregas.py:67)) |
| Usuario → Sesión | `usuario_id INTEGER NOT NULL REFERENCES usuarios(id)` | `base_datos.py`, 124 | `iniciar_sesion` ([servidor.py:144](servidor.py:144)) |
| Área → Referencia | `area_id INTEGER NOT NULL REFERENCES areas(id)` | `base_datos.py`, 141 | `crear_referencia` ([catalogo.py:274](catalogo.py:274)) |
| Ítem → Referencia | `item_id INTEGER NOT NULL UNIQUE REFERENCES items(id)` | `base_datos.py`, 142 | `validar_item_propio` ([catalogo.py:321](catalogo.py:321)) |
| Referencia ◆ LíneaMaterial | `referencia_id INTEGER NOT NULL REFERENCES referencias(id)` | `base_datos.py`, 148 | `guardar_materiales` ([catalogo.py:310](catalogo.py:310)) |
| Ítem → LíneaMaterial | `item_id INTEGER NOT NULL REFERENCES items(id)` | `base_datos.py`, 149 | `validar_materiales` ([catalogo.py:332](catalogo.py:332)) |
| Referencia → Orden | `referencia_id INTEGER NOT NULL REFERENCES referencias(id)` | `base_datos.py`, 163 | `buscar_ensamble` ([ordenes.py:112](ordenes.py:112)) |
| Cliente → Orden | `cliente_id INTEGER NOT NULL REFERENCES clientes(id)` | `base_datos.py`, 164 | `crear_orden` ([ordenes.py:165](ordenes.py:165)) |
| Orden ◆ Requerimiento | `orden_id INTEGER NOT NULL REFERENCES ordenes(id)` | `base_datos.py`, 174 | `crear_orden` ([ordenes.py:165](ordenes.py:165)) |
| Área → Requerimiento | `area_id INTEGER NOT NULL REFERENCES areas(id)` | `base_datos.py`, 175 | `requerimiento_del_area` ([entregas.py:27](entregas.py:27)) |
| Orden ◆ Reporte | `orden_id INTEGER NOT NULL REFERENCES ordenes(id)` | `base_datos.py`, 184 | `crear_reporte` ([entregas.py:67](entregas.py:67)) |
| Área → Reporte | `area_id INTEGER NOT NULL REFERENCES areas(id)` | `base_datos.py`, 185 | `crear_reporte` ([entregas.py:67](entregas.py:67)) |
| Ítem → Movimiento | `item_id INTEGER NOT NULL REFERENCES items(id)` | `base_datos.py`, 200 | `mover_existencia` ([inventario.py:37](inventario.py:37)) |
| Orden → Movimiento | `orden_id INTEGER REFERENCES ordenes(id)` | `base_datos.py`, 204 | `aprobar_reporte` ([entregas.py:200](entregas.py:200)) |
| Reporte → Movimiento | `reporte_id INTEGER REFERENCES reportes(id)` | `base_datos.py`, 205 | `aprobar_reporte` ([entregas.py:200](entregas.py:200)) |
| Usuario → Movimiento | `usuario_id INTEGER NOT NULL REFERENCES usuarios(id)` | `base_datos.py`, 206 | `registrar_entrada` ([inventario.py:27](inventario.py:27)) |

**Los métodos del diagrama:**

| Método | Función real | Archivo y línea | Qué hace |
|---|---|---|---|
| `cifrar_contrasena()` | `cifrar_contrasena` | `base_datos.py`, 83 | Convierte la contraseña en un código secreto |
| `es_valida()` | `buscar_usuario_de_sesion` | `servidor.py`, 124 | Revisa a qué usuario corresponde la sesión |
| `validar_nemotecnia()` | `tiene_formato` | `catalogo.py`, 66 | Revisa el formato del código, ej. `NUCLEO-001` |
| `validar_ciclos()` | `contiene_item` | `catalogo.py`, 360 | Evita que un producto sea material de sí mismo |
| `validar_nit()` | `nit_valido` | `ordenes.py`, 32 | Revisa que el NIT sea válido |
| `calcular_avance()` | `avance_del_area` | `entregas.py`, 43 | Calcula cuánto lleva entregado un área |
| `calcular_consumos()` | `calcular_consumos` | `entregas.py`, 161 | Calcula los materiales que se gastan al aprobar |

## 9. Cómo demostrarlo en vivo

Si el jurado pide **"muéstrame en el código"**, sigue estos tres pasos:

1. Abre [base_datos.py](base_datos.py) en la **línea 160** (tabla `ordenes`).
2. Señala `cliente_id INTEGER NOT NULL REFERENCES clientes(id)` y di:
   *"Esta es la línea Cliente → Orden del diagrama. `REFERENCES` obliga a que el cliente exista
   y `NOT NULL` es el `1` de la multiplicidad: toda orden tiene cliente."*
3. Abre [ordenes.py](ordenes.py) en la **línea 165** (`crear_orden`) y muestra el `INSERT`
   que guarda la orden y, justo después, los requerimientos. *"Aquí se ve la composición:
   se guardan juntos."*

En VS Code, **Ctrl + G** te lleva a un número de línea y **Ctrl + Shift + F** busca en todo el proyecto (por ejemplo, `REFERENCES`).

## 10. Preguntas que te pueden hacer

**¿Por qué es un diagrama de clases si el código no usa clases?**
Porque el diagrama de clases sirve para modelar la información. Aquí cada clase se implementó
como una tabla y los métodos como funciones. Se eligieron funciones para que el código fuera
más sencillo.

**¿Qué diferencia hay entre asociación y composición?**
En la asociación cada parte existe sola (un cliente sin órdenes). En la composición la parte
no existe sin el todo (un requerimiento sin su orden).

**¿Por qué `orden_id` en Movimiento puede estar vacío?**
Porque cuando llega materia prima de un proveedor se crea un movimiento de entrada que no
viene de ninguna orden. Por eso es `0..1`.

**¿Por qué el Ítem → Referencia tiene `UNIQUE`?**
Para que cada ítem sea fabricado por una sola referencia. Así no hay dos áreas fabricando
la misma pieza.

**¿Qué pasa si se intenta guardar un dato que apunta a algo que no existe?**
`REFERENCES` lo impide. Además, el código lo revisa antes y muestra un mensaje claro, por
ejemplo: *"Selecciona un cliente de la lista."*

**¿Por qué Requerimiento se guarda y no se calcula cada vez?**
Porque se calcula una vez al crear la orden y queda "congelado". Si después alguien cambia la
receta del producto, las órdenes que ya existen no cambian.

## 11. Ojo: diferencias entre el diagrama y el código

Si el jurado compara con cuidado, puede encontrar esto. Es mejor saberlo:

- **Faltan 4 líneas en el diagrama**, aunque sí están en el código:
  - *Requerimiento → Referencia* (`base_datos.py`, 176)
  - *Reporte → Referencia* (186)
  - *Reporte → Usuario* (191 y 193)
  - *Orden → Usuario* (167)
- **Área → Usuario** debería ser `0..1`, porque el analista y el supervisor no tienen área.
- **Ítem → Referencia** debería ser `1 — 0..1`, porque las materias primas no tienen referencia.
- **Orden → Movimiento** se llama "imputa_costo", pero el sistema no maneja costos.
- Los **nombres de los métodos** no son iguales a los de las funciones (tabla de la sección 8).

**Respuesta si lo preguntan:** *"El diagrama muestra las relaciones principales del negocio.
En el código hay algunas llaves foráneas más, por ejemplo para saber quién creó una orden o
quién revisó un reporte. Sirven para la trazabilidad."*

## 12. Resumen en 5 frases (para memorizar)

1. Cada **clase** es una **tabla**, cada **atributo** una **columna** y cada **relación** una **llave foránea** (`REFERENCES`).
2. Todo está en **`base_datos.py`**, entre las líneas 105 y 210.
3. `NOT NULL` es multiplicidad **1**, sin `NOT NULL` es **0..1** y `UNIQUE` evita repetidos.
4. El **rombo relleno** es **composición**: la parte no existe sin el todo (Orden ◆ Requerimiento).
5. Los **métodos** son **funciones de Python** en los módulos `catalogo.py`, `ordenes.py`, `entregas.py` y `servidor.py`.
