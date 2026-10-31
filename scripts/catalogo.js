// =====================================================================
// catalogo.js
// Página "Ítems y referencias" (solo analista). Dos pestañas:
//   - Ítems: crear y editar ítems MP, PP y PT, y buscarlos.
//   - Referencias: ver una referencia con su lista de materiales,
//     crear referencias nuevas y cambiar su lista de materiales.
// =====================================================================

// Elementos de la pestaña Ítems
const formularioItem = document.getElementById("formulario-item");
const avisoItem = document.getElementById("aviso-item");
const botonCancelarItem = document.getElementById("cancelar-item");
const filtroTipoItem = document.getElementById("filtro-tipo-item");
const filtroTextoItem = document.getElementById("filtro-texto-item");
const tablaItems = document.getElementById("tabla-items");

// Elementos de la pestaña Referencias
const filtroArea = document.getElementById("filtro-area");
const filtroTextoReferencia = document.getElementById("filtro-texto-referencia");
const tablaReferencias = document.getElementById("tabla-referencias");
const vistaVacia = document.getElementById("vista-vacia");
const vistaDetalle = document.getElementById("vista-detalle");
const formularioReferencia = document.getElementById("formulario-referencia");
const avisoReferencia = document.getElementById("aviso-referencia");
const avisoDetalle = document.getElementById("aviso-detalle");
const filasMateriales = document.getElementById("filas-materiales");

// Datos que la página recuerda mientras está abierta
let listas = null;                 // Áreas, tipos y unidades (de /api/listas)
let itemsVisibles = [];            // Los ítems que se ven ahora en la tabla
let itemEnEdicion = null;          // Código del ítem que se edita (null = se está creando uno nuevo)
let referenciaActual = null;       // La referencia abierta en el detalle
let materialesDisponibles = [];    // Ítems MP y PP que se pueden usar como material
let editandoMateriales = false;    // true = el formulario cambia la lista de una referencia que ya existe
let consultaItems = 0;             // Número de la última búsqueda de ítems (ver cargarItems)
let consultaReferencias = 0;       // Número de la última búsqueda de referencias


// "async" permite usar "await" para esperar al servidor antes de seguir.
async function arrancar() {
  await iniciarPagina();
  listas = await pedirDatos("/api/listas");
  prepararPestanas(document.getElementById("pestanas"));
  prepararItems();
  prepararReferencias();

  // Patrón Observador: cuando cualquier parte de la página avisa que el catálogo
  // cambió (un ítem, una referencia o un producto nuevo), se recargan las listas.
  escuchar("catalogo-cambiado", function () {
    cargarItems();
    cargarReferencias();
    cargarMaterialesDisponibles();
  });
}

arrancar();


// =====================================================================
// Pestaña Ítems
// =====================================================================

function prepararItems() {
  const opcionesTipo = [];
  for (const tipo of listas.tipos) {
    opcionesTipo.push({ valor: tipo.codigo, texto: tipo.codigo + " · " + tipo.nombre });
  }
  const opcionesUnidad = [];
  for (const unidad of listas.unidades) {
    opcionesUnidad.push({ valor: unidad, texto: unidad });
  }
  llenarSelect(formularioItem.tipo, opcionesTipo);
  llenarSelect(formularioItem.unidad_medida, opcionesUnidad);
  llenarSelect(filtroTipoItem, opcionesTipo, "Todos los tipos");

  formularioItem.addEventListener("submit", guardarItem);
  formularioItem.tipo.addEventListener("change", sugerirCodigoItem);
  botonCancelarItem.addEventListener("click", salirDeEdicion);
  filtroTipoItem.addEventListener("change", cargarItems);
  filtroTextoItem.addEventListener("input", cargarItems);   // "input" = cada vez que se escribe
  tablaItems.addEventListener("click", alHacerClicEnItems);

  sugerirCodigoItem();
  cargarItems();
}

async function sugerirCodigoItem() {
  const respuesta = await pedirDatos("/api/items/siguiente-codigo" + armarConsulta({ tipo: formularioItem.tipo.value }));
  formularioItem.codigo.value = respuesta.codigo;
}

async function cargarItems() {
  // Al escribir rápido se envían varias búsquedas seguidas y sus respuestas pueden
  // llegar en desorden. Cada búsqueda recibe un número; si al llegar la respuesta
  // ya hay una búsqueda más nueva, esta se descarta para no mostrar datos viejos.
  consultaItems += 1;
  const miConsulta = consultaItems;
  const filtros = { tipo: filtroTipoItem.value, texto: filtroTextoItem.value };
  const items = await pedirDatos("/api/items" + armarConsulta(filtros));
  if (miConsulta !== consultaItems) {
    return;
  }
  itemsVisibles = items;
  pintarItems();
}

function pintarItems() {
  if (itemsVisibles.length === 0) {
    tablaItems.innerHTML = filaVacia(6, "No hay ítems que coincidan con el filtro.");
    return;
  }
  let html = "";
  for (const item of itemsVisibles) {
    // data-editar guarda el código en el botón, para saber qué ítem editar al hacer clic.
    html += `
      <tr>
        <td><strong>${escaparHtml(item.codigo)}</strong></td>
        <td>${escaparHtml(item.descripcion)}</td>
        <td>${etiquetaTipo(item.tipo)}</td>
        <td>${escaparHtml(item.unidad_medida)}</td>
        <td class="numero">${formatearNumero(item.existencia)}</td>
        <td><button type="button" class="boton boton-secundario boton-pequeno" data-editar="${escaparHtml(item.codigo)}">Editar</button></td>
      </tr>`;
  }
  tablaItems.innerHTML = html;
}

// Un solo "escuchador" para toda la tabla: revisa si el clic fue en un botón Editar.
function alHacerClicEnItems(evento) {
  const boton = evento.target.closest("[data-editar]");
  if (boton !== null) {
    empezarEdicion(boton.dataset.editar);
  }
}

function empezarEdicion(codigo) {
  let item = null;
  for (const posible of itemsVisibles) {
    if (posible.codigo === codigo) {
      item = posible;
    }
  }
  itemEnEdicion = codigo;
  formularioItem.tipo.value = item.tipo;
  formularioItem.codigo.value = item.codigo;
  formularioItem.descripcion.value = item.descripcion;
  formularioItem.unidad_medida.value = item.unidad_medida;
  // El tipo y el código identifican al ítem: no se pueden cambiar.
  formularioItem.tipo.disabled = true;
  formularioItem.codigo.disabled = true;
  document.getElementById("titulo-item").textContent = "Editar ítem " + codigo;
  botonCancelarItem.hidden = false;
  ocultarAviso(avisoItem);
  formularioItem.descripcion.focus();
}

function salirDeEdicion() {
  itemEnEdicion = null;
  formularioItem.reset();
  formularioItem.tipo.disabled = false;
  formularioItem.codigo.disabled = false;
  document.getElementById("titulo-item").textContent = "Nuevo ítem";
  botonCancelarItem.hidden = true;
  sugerirCodigoItem();
}

async function guardarItem(evento) {
  evento.preventDefault();
  ocultarAviso(avisoItem);

  const datos = {
    tipo: formularioItem.tipo.value,
    codigo: formularioItem.codigo.value,
    descripcion: formularioItem.descripcion.value,
    unidad_medida: formularioItem.unidad_medida.value,
  };

  try {
    let item;
    let mensaje;
    if (itemEnEdicion === null) {
      item = await enviarDatos("/api/items", datos);
      mensaje = "Ítem " + item.codigo + " creado.";
    } else {
      item = await enviarDatos("/api/items/editar", datos);
      mensaje = "Ítem " + item.codigo + " actualizado.";
    }
    salirDeEdicion();
    mostrarAviso(avisoItem, mensaje, "exito");
    // Patrón Observador: se avisa el cambio y cada parte interesada se actualiza sola
    // (la tabla de ítems, los materiales de las referencias y el asistente).
    avisar("catalogo-cambiado");
  } catch (error) {
    mostrarAviso(avisoItem, error.message);
  }
}


// =====================================================================
// Pestaña Referencias
// =====================================================================

function prepararReferencias() {
  const opcionesArea = [];
  for (const area of listas.areas) {
    opcionesArea.push({ valor: area.codigo, texto: area.nombre });
  }
  llenarSelect(filtroArea, opcionesArea, "Todas las áreas");
  llenarSelect(formularioReferencia.area, opcionesArea);

  filtroArea.addEventListener("change", cargarReferencias);
  filtroTextoReferencia.addEventListener("input", cargarReferencias);
  tablaReferencias.addEventListener("click", alHacerClicEnReferencias);
  document.getElementById("boton-nueva-referencia").addEventListener("click", abrirFormularioNuevo);
  document.getElementById("boton-editar-materiales").addEventListener("click", abrirFormularioMateriales);
  document.getElementById("boton-agregar-material").addEventListener("click", function () {
    agregarFilaMaterial("", "");
  });
  document.getElementById("cancelar-referencia").addEventListener("click", cancelarFormularioReferencia);
  formularioReferencia.area.addEventListener("change", alCambiarArea);
  formularioReferencia.addEventListener("submit", guardarReferencia);
  filasMateriales.addEventListener("click", quitarFilaMaterial);

  cargarReferencias();
  cargarMaterialesDisponibles();
}

async function cargarReferencias() {
  consultaReferencias += 1;            // Igual que en cargarItems: se descartan respuestas viejas
  const miConsulta = consultaReferencias;
  const filtros = { area: filtroArea.value, texto: filtroTextoReferencia.value };
  const referencias = await pedirDatos("/api/referencias" + armarConsulta(filtros));
  if (miConsulta !== consultaReferencias) {
    return;
  }
  if (referencias.length === 0) {
    tablaReferencias.innerHTML = filaVacia(2, "No hay referencias que coincidan con el filtro.");
    return;
  }
  let html = "";
  for (const referencia of referencias) {
    // La fila de la referencia abierta se resalta.
    let clase = "";
    if (referenciaActual !== null && referenciaActual.codigo === referencia.codigo) {
      clase = "resaltada";
    }
    html += `
      <tr class="${clase}" data-referencia="${escaparHtml(referencia.codigo)}">
        <td><strong>${escaparHtml(referencia.codigo)}</strong><br><small>${escaparHtml(referencia.descripcion)}</small></td>
        <td class="sin-salto">${etiquetaTipo(referencia.item_tipo)} ${escaparHtml(referencia.item_codigo)}</td>
      </tr>`;
  }
  tablaReferencias.innerHTML = html;
}

// Los ítems MP y PP: son los únicos que pueden ser material (un PT no se consume).
async function cargarMaterialesDisponibles() {
  const todos = await pedirDatos("/api/items");
  materialesDisponibles = [];
  for (const item of todos) {
    if (item.tipo !== "PT") {
      materialesDisponibles.push(item);
    }
  }
}

function alHacerClicEnReferencias(evento) {
  const fila = evento.target.closest("[data-referencia]");
  if (fila !== null) {
    abrirReferencia(fila.dataset.referencia);
  }
}

// Muestra solo una de las tres vistas de la derecha.
function mostrarVista(nombre) {
  vistaVacia.hidden = nombre !== "vacia";
  vistaDetalle.hidden = nombre !== "detalle";
  formularioReferencia.hidden = nombre !== "formulario";
  // En tablet la vista queda debajo de la lista: se baja hasta ella.
  // "nearest" no mueve la página si la vista ya se ve (en computador).
  const vistas = { vacia: vistaVacia, detalle: vistaDetalle, formulario: formularioReferencia };
  vistas[nombre].scrollIntoView({ behavior: "smooth", block: "nearest" });
}

async function abrirReferencia(codigo) {
  referenciaActual = await pedirDatos("/api/referencia" + armarConsulta({ codigo: codigo }));
  ocultarAviso(avisoDetalle);
  pintarDetalle();
  mostrarVista("detalle");
  cargarReferencias();   // Para resaltar la fila elegida
}

function pintarDetalle() {
  const referencia = referenciaActual;
  document.getElementById("detalle-area").textContent = referencia.area_nombre;
  document.getElementById("detalle-codigo").textContent = referencia.codigo;
  document.getElementById("detalle-descripcion").textContent = referencia.descripcion;
  document.getElementById("detalle-item").textContent = referencia.item_codigo + " · " + referencia.item_descripcion;
  document.getElementById("detalle-tipo").innerHTML = etiquetaTipo(referencia.item_tipo);
  document.getElementById("enlace-estructura").href = "/estructura" + armarConsulta({ referencia: referencia.codigo });

  let html = "";
  for (const material of referencia.materiales) {
    html += `
      <tr>
        <td><strong>${escaparHtml(material.codigo)}</strong></td>
        <td>${escaparHtml(material.descripcion)}</td>
        <td>${etiquetaTipo(material.tipo)}</td>
        <td class="numero">${formatearNumero(material.cantidad)}</td>
        <td>${escaparHtml(material.unidad_medida)}</td>
      </tr>`;
  }
  document.getElementById("detalle-materiales").innerHTML = html;
}


// ---------- Formulario: crear referencia ----------

function abrirFormularioNuevo() {
  editandoMateriales = false;
  formularioReferencia.reset();
  activarCamposDeReferencia(true);
  document.getElementById("titulo-referencia").textContent = "Nueva referencia";
  filasMateriales.innerHTML = "";
  agregarFilaMaterial("", "");
  ocultarAviso(avisoReferencia);
  mostrarVista("formulario");
  alCambiarArea();
}

// Al elegir el área se sugiere el código y se cargan los ítems que puede producir.
async function alCambiarArea() {
  const area = formularioReferencia.area.value;
  const respuesta = await pedirDatos("/api/referencias/siguiente-codigo" + armarConsulta({ area: area }));
  formularioReferencia.codigo.value = respuesta.codigo;

  // Ensamble final produce un PT; las demás áreas, un PP. Solo se muestran
  // los ítems de ese tipo que todavía no tienen referencia.
  let tipo = "PP";
  if (area === "ENSAMBLE") {
    tipo = "PT";
  }
  const libres = await pedirDatos("/api/items" + armarConsulta({ tipo: tipo, sin_referencia: "si" }));
  const opciones = [];
  for (const item of libres) {
    opciones.push({ valor: item.codigo, texto: item.codigo + " · " + item.descripcion });
  }
  if (opciones.length === 0) {
    llenarSelect(formularioReferencia.item, [], "No hay ítems " + tipo + " libres: créalo en la pestaña Ítems");
  } else {
    llenarSelect(formularioReferencia.item, opciones);
  }
}

// ---------- Formulario: cambiar la lista de materiales ----------

function abrirFormularioMateriales() {
  const referencia = referenciaActual;
  editandoMateriales = true;
  formularioReferencia.area.value = referencia.area_codigo;
  formularioReferencia.codigo.value = referencia.codigo;
  llenarSelect(formularioReferencia.item, [{ valor: referencia.item_codigo, texto: referencia.item_codigo + " · " + referencia.item_descripcion }]);
  formularioReferencia.descripcion.value = referencia.descripcion;
  // Solo se cambian los materiales: el resto de la referencia queda bloqueado.
  activarCamposDeReferencia(false);
  document.getElementById("titulo-referencia").textContent = "Editar lista de materiales · " + referencia.codigo;

  filasMateriales.innerHTML = "";
  for (const material of referencia.materiales) {
    agregarFilaMaterial(material.codigo, material.cantidad);
  }
  ocultarAviso(avisoReferencia);
  mostrarVista("formulario");
}

function activarCamposDeReferencia(activos) {
  formularioReferencia.area.disabled = !activos;
  formularioReferencia.codigo.disabled = !activos;
  formularioReferencia.item.disabled = !activos;
  formularioReferencia.descripcion.disabled = !activos;
}

function cancelarFormularioReferencia() {
  if (referenciaActual !== null) {
    mostrarVista("detalle");
  } else {
    mostrarVista("vacia");
  }
}

// ---------- Filas de materiales ----------

function agregarFilaMaterial(codigo, cantidad) {
  const opciones = [];
  for (const item of materialesDisponibles) {
    opciones.push({ valor: item.codigo, texto: item.codigo + " · " + item.descripcion + " (" + item.unidad_medida + ")" });
  }
  // Se crea la fila con document.createElement para poder agregarla sin borrar las demás.
  const fila = document.createElement("tr");
  fila.innerHTML = `
    <td><select data-material></select></td>
    <td class="numero"><input data-cantidad class="entrada-numero" type="number" min="0" step="any"></td>
    <td><button type="button" class="boton-icono" data-quitar title="Quitar material">✕</button></td>`;
  llenarSelect(fila.querySelector("[data-material]"), opciones, "Elige un material");
  fila.querySelector("[data-material]").value = codigo;
  fila.querySelector("[data-cantidad]").value = cantidad;
  filasMateriales.appendChild(fila);
}

function quitarFilaMaterial(evento) {
  const boton = evento.target.closest("[data-quitar]");
  if (boton !== null) {
    boton.closest("tr").remove();
  }
}

// Lee las filas y devuelve [{item: "MP-0001", cantidad: "80"}, ...].
// Las filas totalmente vacías se ignoran; las incompletas se envían para que el servidor avise.
function leerMateriales() {
  const materiales = [];
  for (const fila of filasMateriales.querySelectorAll("tr")) {
    const item = fila.querySelector("[data-material]").value;
    const cantidad = fila.querySelector("[data-cantidad]").value;
    if (item !== "" || cantidad !== "") {
      materiales.push({ item: item, cantidad: cantidad });
    }
  }
  return materiales;
}

// ---------- Guardar ----------

async function guardarReferencia(evento) {
  evento.preventDefault();
  ocultarAviso(avisoReferencia);

  try {
    let mensaje;
    if (editandoMateriales) {
      referenciaActual = await enviarDatos("/api/referencias/materiales", {
        codigo: referenciaActual.codigo,
        materiales: leerMateriales(),
      });
      mensaje = "Lista de materiales actualizada.";
    } else {
      referenciaActual = await enviarDatos("/api/referencias", {
        area: formularioReferencia.area.value,
        codigo: formularioReferencia.codigo.value,
        item: formularioReferencia.item.value,
        descripcion: formularioReferencia.descripcion.value,
        materiales: leerMateriales(),
      });
      mensaje = "Referencia " + referenciaActual.codigo + " creada.";
    }
    pintarDetalle();
    mostrarVista("detalle");
    mostrarAviso(avisoDetalle, mensaje, "exito");
    avisar("catalogo-cambiado");   // Patrón Observador
  } catch (error) {
    mostrarAviso(avisoReferencia, error.message);
  }
}
