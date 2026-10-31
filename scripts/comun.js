// =====================================================================
// comun.js
// Funciones que usan TODAS las páginas. Cada página HTML carga primero
// este archivo y después su propio script, así:
//   <script src="/scripts/comun.js"></script>
//   <script src="/scripts/ordenes.js"></script>
// Por eso las funciones de aquí se pueden llamar desde cualquier página.
// =====================================================================


// ---------------------------------------------------------------------
// 1. Hablar con el servidor
// fetch() envía una petición al servidor y espera la respuesta.
// "async" y "await" sirven para esperar la respuesta sin congelar la página.
//
// Patrón GoF Fachada (Facade): pedirDatos y enviarDatos esconden todo lo difícil
// de fetch (convertir a JSON, revisar errores, volver al login si no hay sesión).
// Las páginas solo dicen "pide esto" o "envía esto".
// También es GRASP Indirección: las páginas no usan fetch directamente.
// ---------------------------------------------------------------------

async function llamarServidor(metodo, ruta, datos) {
  const opciones = { method: metodo, headers: { "Content-Type": "application/json" } };
  if (datos !== undefined) {
    // El servidor espera texto JSON, así que el objeto se convierte con JSON.stringify.
    opciones.body = JSON.stringify(datos);
  }

  const respuesta = await fetch(ruta, opciones);
  const contenido = await respuesta.json();

  // 401 = no hay sesión (o se cerró): se vuelve al login.
  // En el propio login no, porque ahí 401 significa "contraseña incorrecta".
  if (respuesta.status === 401 && ruta !== "/api/login") {
    window.location.href = "/login";
  }
  // Si el servidor respondió con error, se lanza para que la página muestre el mensaje.
  if (!respuesta.ok) {
    throw new Error(contenido.error || "Ocurrió un error inesperado.");
  }
  return contenido;
}

// Consultar datos (GET). Ejemplo: const datos = await pedirDatos("/api/ordenes?op=1001");
function pedirDatos(ruta) {
  return llamarServidor("GET", ruta);
}

// Crear o cambiar datos (POST). Ejemplo: await enviarDatos("/api/clientes", { nit: "...", nombre: "..." });
function enviarDatos(ruta, datos) {
  return llamarServidor("POST", ruta, datos);
}

// Arma la parte "?op=1001&area=NUCLEO" de una dirección a partir de un objeto.
// URLSearchParams se encarga de escribir bien las tildes, los espacios, etc.
function armarConsulta(filtros) {
  return "?" + new URLSearchParams(filtros).toString();
}


// ---------------------------------------------------------------------
// 2. Encabezado, menú y pie de página
// ---------------------------------------------------------------------

const NOMBRES_DE_ROL = { AREA: "Área", ANALISTA: "Analista", SUPERVISOR: "Supervisor" };

// Toda página interna llama a esta función al empezar.
// Pide al servidor quién está conectado, dibuja el encabezado y el pie,
// y devuelve el usuario para que la página sepa su rol y su área.
async function iniciarPagina() {
  const sesion = await pedirDatos("/api/sesion");
  pintarEncabezado(sesion.usuario, sesion.menu);
  pintarPie();
  return sesion.usuario;
}

function pintarEncabezado(usuario, menu) {
  // Un enlace por cada página del menú. La página actual se marca como "activo".
  let enlaces = "";
  for (const opcion of menu) {
    let clase = "";
    if (window.location.pathname === opcion.ruta) {
      clase = "activo";
    }
    enlaces += `<a class="${clase}" href="${opcion.ruta}">${escaparHtml(opcion.titulo)}</a>`;
  }

  // Las áreas muestran su nombre; el analista y el supervisor, su rol.
  let rol = NOMBRES_DE_ROL[usuario.rol];
  if (usuario.area_nombre) {
    rol = "Área · " + usuario.area_nombre;
  }

  const encabezado = document.getElementById("encabezado");
  encabezado.innerHTML = `
    <div class="encabezado-barra">
      <a class="marca" href="/">
        <img src="/imagenes/logo.png" alt="Rymel SAS">
        <span class="marca-nombre">RymelView</span>
      </a>
      <nav class="menu">${enlaces}</nav>
      <div class="usuario">
        <div class="usuario-datos">
          <strong>${escaparHtml(usuario.nombre_completo)}</strong>
          <small>${escaparHtml(rol)}</small>
        </div>
        <button type="button" class="boton boton-secundario boton-pequeno" id="boton-salir">Cerrar sesión</button>
      </div>
    </div>`;

  prepararLogo(encabezado.querySelector(".marca img"));
  document.getElementById("boton-salir").addEventListener("click", cerrarSesion);
}

// Si todavía no existe imagenes/logo.png, se muestra el texto "RYMEL" en su lugar.
function prepararLogo(imagen) {
  // Caso 1: la imagen ya intentó cargar y falló (complete = terminó, naturalWidth 0 = sin imagen).
  if (imagen.complete && imagen.naturalWidth === 0) {
    cambiarLogoPorTexto(imagen);
    return;
  }
  // Caso 2: todavía está cargando; si falla, se cambia en ese momento.
  imagen.addEventListener("error", function () {
    cambiarLogoPorTexto(imagen);
  });
}

function cambiarLogoPorTexto(imagen) {
  imagen.outerHTML = '<span class="logo-texto">RYMEL</span>';
}

function pintarPie() {
  const anio = new Date().getFullYear();
  document.getElementById("pie").innerHTML = `
    <div class="contenedor">
      <span>© ${anio} Rymel S.A.S. · RymelView, sistema de inventario y producción</span>
      <span>Uso interno exclusivo del personal autorizado</span>
    </div>`;
}

async function cerrarSesion() {
  await enviarDatos("/api/logout", {});
  window.location.href = "/login";
}


// ---------------------------------------------------------------------
// 3. Ayudas para escribir HTML
// ---------------------------------------------------------------------

// MUY IMPORTANTE: todo texto que venga de la base de datos se pasa por aquí
// antes de meterlo en el HTML. Si alguien escribió "<script>" en una descripción,
// se muestra como texto y no se ejecuta.
function escaparHtml(texto) {
  if (texto === null || texto === undefined) {
    return "";
  }
  return String(texto)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

// 1680.5 -> "1.680,5" (formato de Colombia, con máximo 3 decimales)
function formatearNumero(numero) {
  return Number(numero).toLocaleString("es-CO", { maximumFractionDigits: 3 });
}

// Muestra un mensaje en un recuadro de aviso. tipo: "error" (rojo) o "exito" (verde).
function mostrarAviso(elemento, mensaje, tipo) {
  if (tipo === undefined) {
    tipo = "error";
  }
  elemento.textContent = mensaje;
  elemento.className = "aviso " + tipo;
  elemento.hidden = false;
}

function ocultarAviso(elemento) {
  elemento.hidden = true;
}

// Llena un <select> con opciones. opciones = [{ valor: "NUCLEO", texto: "Núcleo" }, ...]
// Si se da textoVacio, primero agrega una opción vacía (ej. "Todas las áreas").
function llenarSelect(select, opciones, textoVacio) {
  let html = "";
  if (textoVacio !== undefined) {
    html += `<option value="">${escaparHtml(textoVacio)}</option>`;
  }
  for (const opcion of opciones) {
    html += `<option value="${escaparHtml(opcion.valor)}">${escaparHtml(opcion.texto)}</option>`;
  }
  select.innerHTML = html;
}

// Una fila de tabla con un mensaje, para cuando no hay resultados.
function filaVacia(columnas, texto) {
  return `<tr><td colspan="${columnas}" class="vacia">${escaparHtml(texto)}</td></tr>`;
}

// Etiqueta de color para el tipo de ítem: MP, PP o PT.
function etiquetaTipo(tipo) {
  return `<span class="etiqueta ${tipo.toLowerCase()}">${escaparHtml(tipo)}</span>`;
}

// Etiqueta de color para un estado.
const ESTADOS = {
  PENDIENTE: { clase: "pendiente", texto: "Pendiente" },
  EN_PROCESO: { clase: "proceso", texto: "En proceso" },
  APROBADO: { clase: "aprobado", texto: "Aprobado" },
  RECHAZADO: { clase: "rechazado", texto: "Rechazado" },
};

function etiquetaEstado(estado) {
  const datos = ESTADOS[estado];
  return `<span class="etiqueta ${datos.clase}">${datos.texto}</span>`;
}

// Botones de pestañas: cada botón tiene data-panel="id-del-panel".
// Al hacer clic se muestra ese panel y se ocultan los demás.
function prepararPestanas(contenedor) {
  const botones = contenedor.querySelectorAll("[data-panel]");
  for (const boton of botones) {
    boton.addEventListener("click", function () {
      for (const otro of botones) {
        const esElElegido = otro === boton;
        otro.classList.toggle("activa", esElElegido);
        document.getElementById(otro.dataset.panel).hidden = !esElElegido;
      }
    });
  }
}


// ---------------------------------------------------------------------
// 4. Árbol de estructura (lo usan Estructura, Órdenes y Nuevo producto)
// El servidor envía el árbol como objetos dentro de objetos:
//   { item: {...}, cantidad_total: 10, hijos: [ {item: ..., hijos: [...]}, ... ] }
// Se dibuja como listas <ul> dentro de otras <ul>.
// ---------------------------------------------------------------------

// Devuelve el HTML de un nodo y, dentro de él, el de todos sus hijos.
// La función se llama a sí misma para cada hijo (recursión), igual que en Python.
function crearNodoArbol(nodo) {
  const tarjeta = crearTarjetaNodo(nodo);
  if (nodo.hijos.length === 0) {
    return `<li>${tarjeta}</li>`;
  }
  let hijos = "";
  for (const hijo of nodo.hijos) {
    hijos += crearNodoArbol(hijo);
  }
  // <details open> = rama abierta. Al hacer clic en <summary> se abre o se cierra sola.
  return `
    <li>
      <details open>
        <summary>${tarjeta}</summary>
        <ul>${hijos}</ul>
      </details>
    </li>`;
}

function crearTarjetaNodo(nodo) {
  const item = nodo.item;
  const unidad = escaparHtml(item.unidad_medida);
  return `
    <div class="nodo ${item.tipo.toLowerCase()}">
      <span class="nodo-flecha"></span>
      <div>
        <div>${etiquetaTipo(item.tipo)} <strong>${escaparHtml(item.codigo)}</strong>
          <span class="nodo-descripcion">${escaparHtml(item.descripcion)}</span></div>
        <div class="nodo-origen">${describirOrigen(nodo)}</div>
      </div>
      <div class="nodo-cantidad">
        <strong>${formatearNumero(nodo.cantidad_total)} ${unidad}</strong>
        <small>${describirCantidadPorUnidad(nodo, unidad)}</small>
      </div>
    </div>`;
}

function describirOrigen(nodo) {
  if (nodo.referencia !== null) {
    return "Referencia " + escaparHtml(nodo.referencia) + " · " + escaparHtml(nodo.area);
  }
  if (nodo.item.tipo === "MP") {
    return "Materia prima comprada";
  }
  return "Sin referencia asignada";
}

function describirCantidadPorUnidad(nodo, unidad) {
  if (nodo.cantidad_por_unidad === null) {
    return "Cantidad a fabricar";
  }
  return formatearNumero(nodo.cantidad_por_unidad) + " " + unidad + " por unidad del nivel superior";
}

// Abre (true) o cierra (false) todas las ramas de un árbol.
function abrirRamas(arbol, abrir) {
  for (const rama of arbol.querySelectorAll("details")) {
    rama.open = abrir;
  }
}


// ---------------------------------------------------------------------
// 5. Avisos entre partes de una misma página
// Patrón GoF Observador (Observer): una parte "avisa" que algo pasó y las
// partes interesadas, que se "suscribieron" antes con escuchar(), reaccionan.
// Quien avisa NO sabe quién escucha: así las partes no dependen unas de otras
// (GRASP Bajo acoplamiento).
// Ejemplo: el asistente "Nuevo producto" avisa "catalogo-cambiado" y la pestaña
// Referencias se recarga sola, sin que el asistente conozca sus funciones.
// ---------------------------------------------------------------------

// Avisa a todos los que estén escuchando ese evento.
function avisar(nombreEvento) {
  document.dispatchEvent(new CustomEvent(nombreEvento));
}

// Se suscribe: cada vez que alguien avise ese evento, se ejecuta la función.
function escuchar(nombreEvento, funcion) {
  document.addEventListener(nombreEvento, funcion);
}
