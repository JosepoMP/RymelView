// =====================================================================
// ordenes.js
// Página "Órdenes de producción". Dos partes:
//   - Consultar OP (todos): lista con filtros y detalle de cada OP por área.
//   - Nueva OP (solo analista y supervisor): formulario, vista previa con
//     la estructura y lo que producirá cada área, y ventana para crear clientes.
// =====================================================================

// Consulta
const filtroOp = document.getElementById("filtro-op");
const filtroCliente = document.getElementById("filtro-cliente");
const filtroArea = document.getElementById("filtro-area");
const filtroEstado = document.getElementById("filtro-estado");
const tablaOrdenes = document.getElementById("tabla-ordenes");
const dialogoOrden = document.getElementById("dialogo-orden");

// Creación
const formularioOrden = document.getElementById("formulario-orden");
const avisoOrden = document.getElementById("aviso-orden");
const botonCrearOrden = document.getElementById("boton-crear-orden");
const avisoVistaPrevia = document.getElementById("aviso-vista-previa");
const vistaPrevia = document.getElementById("vista-previa");
const vistaPreviaVacia = document.getElementById("vista-previa-vacia");

// Nuevo cliente
const dialogoCliente = document.getElementById("dialogo-cliente");
const formularioCliente = document.getElementById("formulario-cliente");
const avisoCliente = document.getElementById("aviso-cliente");

let usuario = null;   // Quién está conectado (para saber su rol y su área)
let consultaActual = 0;   // Número de la última búsqueda (ver cargarOrdenes)

async function arrancar() {
  usuario = await iniciarPagina();
  const listas = await pedirDatos("/api/listas");
  prepararConsulta(listas.areas);

  // Solo el analista y el supervisor pueden crear OP.
  // Ocultar la pestaña es solo visual: el servidor también revisa el rol.
  if (usuario.rol === "ANALISTA" || usuario.rol === "SUPERVISOR") {
    const pestanas = document.getElementById("pestanas");
    pestanas.hidden = false;
    prepararPestanas(pestanas);
    prepararCreacion();
  }
}

arrancar();


// =====================================================================
// Consultar OP
// =====================================================================

function prepararConsulta(areas) {
  const opciones = [];
  for (const area of areas) {
    opciones.push({ valor: area.codigo, texto: area.nombre });
  }
  llenarSelect(filtroArea, opciones, "Todas las áreas");
  // Un operario ve primero su propia área (puede cambiarla).
  if (usuario.area_codigo) {
    filtroArea.value = usuario.area_codigo;
  }

  filtroOp.addEventListener("input", cargarOrdenes);
  filtroCliente.addEventListener("input", cargarOrdenes);
  filtroArea.addEventListener("change", cargarOrdenes);
  filtroEstado.addEventListener("change", cargarOrdenes);
  tablaOrdenes.addEventListener("click", alHacerClicEnOrdenes);
  document.getElementById("cerrar-detalle").addEventListener("click", function () {
    dialogoOrden.close();
  });

  cargarOrdenes();
}

// Etiqueta de color para el estado de una OP.
function etiquetaEstadoOrden(estado) {
  if (estado === "COMPLETA") {
    return '<span class="etiqueta aprobado">Completa</span>';
  }
  return '<span class="etiqueta proceso">Con pendientes</span>';
}

async function cargarOrdenes() {
  // Al escribir rápido se envían varias búsquedas seguidas y sus respuestas pueden
  // llegar en desorden. Cada búsqueda recibe un número; si al llegar la respuesta
  // ya hay una búsqueda más nueva, esta se descarta para no mostrar datos viejos.
  consultaActual += 1;
  const miConsulta = consultaActual;
  const filtros = {
    op: filtroOp.value,
    cliente: filtroCliente.value,
    area: filtroArea.value,
    estado: filtroEstado.value,
  };
  const ordenes = await pedirDatos("/api/ordenes" + armarConsulta(filtros));
  if (miConsulta !== consultaActual) {
    return;
  }

  let total = ordenes.length + (ordenes.length === 1 ? " orden" : " órdenes");
  if (filtroArea.value !== "") {
    total += " · estado y avance del área " + filtroArea.selectedOptions[0].text;
  }
  document.getElementById("total-ordenes").textContent = total;

  if (ordenes.length === 0) {
    tablaOrdenes.innerHTML = filaVacia(7, "No hay órdenes de producción con estos filtros.");
    return;
  }
  let html = "";
  for (const orden of ordenes) {
    html += `
      <tr>
        <td><strong>${escaparHtml(orden.numero)}</strong></td>
        <td>${escaparHtml(orden.cliente_nombre)}<br><small>NIT ${escaparHtml(orden.cliente_nit)}</small></td>
        <td><strong>${escaparHtml(orden.item_codigo)}</strong><br><small>${escaparHtml(orden.descripcion)}</small></td>
        <td class="numero">${formatearNumero(orden.cantidad)}</td>
        <td class="numero">${orden.areas_completas} / ${orden.total_areas}</td>
        <td>${etiquetaEstadoOrden(orden.estado)}</td>
        <td><button type="button" class="boton boton-secundario boton-pequeno" data-orden="${escaparHtml(orden.numero)}">Ver detalle</button></td>
      </tr>`;
  }
  tablaOrdenes.innerHTML = html;
}

function alHacerClicEnOrdenes(evento) {
  const boton = evento.target.closest("[data-orden]");
  if (boton !== null) {
    abrirDetalle(boton.dataset.orden);
  }
}

// ---------- Ventana con el detalle de una OP ----------

async function abrirDetalle(numero) {
  const detalle = await pedirDatos("/api/orden" + armarConsulta({ numero: numero }));
  const orden = detalle.orden;

  document.getElementById("detalle-titulo").textContent = "OP " + orden.numero;
  document.getElementById("detalle-cliente").textContent = orden.cliente_nombre + " · NIT " + orden.cliente_nit;
  document.getElementById("detalle-ensamble").textContent = orden.item_codigo + " · " + orden.descripcion;
  document.getElementById("detalle-cantidad").textContent = formatearNumero(orden.cantidad) + " und";
  document.getElementById("detalle-creada").textContent = orden.fecha_creacion + " · " + orden.creada_por;
  document.getElementById("detalle-estado").innerHTML = etiquetaEstadoOrden(detalle.estado);

  // Lista de materiales del ensamble: por unidad y total para la OP.
  let materiales = "";
  for (const material of detalle.materiales) {
    const unidad = " " + escaparHtml(material.unidad_medida);
    materiales += `
      <tr>
        <td><strong>${escaparHtml(material.codigo)}</strong></td>
        <td>${escaparHtml(material.descripcion)}</td>
        <td class="numero">${formatearNumero(material.cantidad)}${unidad}</td>
        <td class="numero">${formatearNumero(material.cantidad * orden.cantidad)}${unidad}</td>
      </tr>`;
  }
  document.getElementById("detalle-materiales").innerHTML = materiales;

  // Una fila por área. La del área del operario se resalta.
  let areas = "";
  for (const area of detalle.areas) {
    let clase = "";
    if (area.area_codigo === usuario.area_codigo) {
      clase = "resaltada";
    }
    areas += `
      <tr class="${clase}">
        <td>${escaparHtml(area.area_nombre)}</td>
        <td><strong>${escaparHtml(area.item_codigo)}</strong> <small>${escaparHtml(area.referencia)}</small><br>
            <small>${escaparHtml(area.descripcion)}</small></td>
        <td class="numero">${formatearNumero(area.cantidad_requerida)}</td>
        <td class="numero">${formatearNumero(area.en_revision)}</td>
        <td class="numero">${formatearNumero(area.aprobadas)}</td>
        <td class="numero">${formatearNumero(area.rechazadas)}</td>
        <td class="numero"><strong>${formatearNumero(area.pendientes)}</strong></td>
      </tr>`;
  }
  document.getElementById("detalle-areas").innerHTML = areas;

  // showModal abre la ventana y oscurece el resto de la página.
  dialogoOrden.showModal();
}


// =====================================================================
// Nueva OP (analista y supervisor)
// =====================================================================

function prepararCreacion() {
  formularioOrden.referencia.addEventListener("change", cargarVistaPrevia);
  formularioOrden.cantidad.addEventListener("input", cargarVistaPrevia);
  formularioOrden.addEventListener("submit", crearOrden);
  prepararDialogoCliente();

  sugerirNumero();
  cargarEnsambles();
  cargarClientes("");
}

async function sugerirNumero() {
  const respuesta = await pedirDatos("/api/ordenes/siguiente-numero");
  formularioOrden.numero.value = respuesta.numero;
}

// Los ensambles incompletos se pueden elegir para ver qué les falta, pero no se pueden guardar.
async function cargarEnsambles() {
  const ensambles = await pedirDatos("/api/ordenes/ensambles");
  const opciones = [];
  for (const ensamble of ensambles) {
    let texto = ensamble.item_codigo + " · " + ensamble.descripcion;
    if (!ensamble.completa) {
      texto += " — incompleta";
    }
    opciones.push({ valor: ensamble.codigo, texto: texto });
  }
  llenarSelect(formularioOrden.referencia, opciones, "Elige un ítem de ensamble");
}

async function cargarClientes(clienteElegido) {
  const clientes = await pedirDatos("/api/clientes");
  const opciones = [];
  for (const cliente of clientes) {
    opciones.push({ valor: cliente.id, texto: cliente.nombre + " · NIT " + cliente.nit });
  }
  llenarSelect(formularioOrden.cliente, opciones, "Elige un cliente");
  formularioOrden.cliente.value = clienteElegido;
}

// ---------- Vista previa: estructura y unidades por área ----------

async function cargarVistaPrevia() {
  ocultarAviso(avisoVistaPrevia);
  botonCrearOrden.disabled = true;
  const referencia = formularioOrden.referencia.value;
  if (referencia === "") {
    vistaPrevia.hidden = true;
    vistaPreviaVacia.hidden = false;
    return;
  }

  try {
    const filtros = { referencia: referencia, cantidad: formularioOrden.cantidad.value };
    const previa = await pedirDatos("/api/ordenes/vista-previa" + armarConsulta(filtros));
    pintarVistaPrevia(referencia, previa);
    // El botón solo se activa si la OP se puede crear.
    botonCrearOrden.disabled = !previa.puede_crear;
    if (!previa.puede_crear) {
      mostrarAviso(avisoVistaPrevia, "No se puede crear la OP. " + previa.problemas.join(" "));
    }
  } catch (error) {
    vistaPrevia.hidden = true;
    vistaPreviaVacia.hidden = false;
    mostrarAviso(avisoVistaPrevia, error.message);
  }
}

function pintarVistaPrevia(referencia, previa) {
  document.getElementById("titulo-vista-previa").textContent =
    referencia + " × " + formatearNumero(formularioOrden.cantidad.value) + " · lo que debe producir cada área";

  let html = "";
  for (const fila of previa.requerimientos) {
    html += `
      <tr>
        <td>${escaparHtml(fila.area_nombre)}</td>
        <td><strong>${escaparHtml(fila.referencia)}</strong><br><small>${escaparHtml(fila.descripcion)}</small></td>
        <td class="numero">${formatearNumero(fila.cantidad_por_unidad)}</td>
        <td class="numero"><strong>${formatearNumero(fila.cantidad_requerida)}</strong></td>
      </tr>`;
  }
  // Las áreas que faltan también se muestran, en rojo.
  for (const area of previa.areas_faltantes) {
    html += `
      <tr>
        <td>${escaparHtml(area)}</td>
        <td colspan="3"><span class="etiqueta rechazado">Sin referencia en la lista de materiales</span></td>
      </tr>`;
  }
  document.getElementById("tabla-vista-previa").innerHTML = html;
  document.getElementById("arbol-vista-previa").innerHTML = crearNodoArbol(previa.arbol);
  vistaPrevia.hidden = false;
  vistaPreviaVacia.hidden = true;
}

// ---------- Guardar la OP ----------

async function crearOrden(evento) {
  evento.preventDefault();
  ocultarAviso(avisoOrden);
  const datos = {
    numero: formularioOrden.numero.value,
    referencia: formularioOrden.referencia.value,
    cantidad: formularioOrden.cantidad.value,
    cliente: formularioOrden.cliente.value,
  };
  try {
    const orden = await enviarDatos("/api/ordenes", datos);
    formularioOrden.reset();
    botonCrearOrden.disabled = true;
    vistaPrevia.hidden = true;
    vistaPreviaVacia.hidden = false;
    mostrarAviso(avisoOrden, "OP " + orden.numero + " creada (cliente: " + orden.cliente_nombre
      + "). Las áreas ya pueden reportar sus entregas.", "exito");
    sugerirNumero();
    cargarOrdenes();
  } catch (error) {
    mostrarAviso(avisoOrden, error.message);
  }
}

// ---------- Ventana para crear un cliente ----------

function prepararDialogoCliente() {
  document.getElementById("boton-nuevo-cliente").addEventListener("click", function () {
    formularioCliente.reset();
    ocultarAviso(avisoCliente);
    dialogoCliente.showModal();
  });
  document.getElementById("cerrar-cliente").addEventListener("click", function () {
    dialogoCliente.close();
  });
  formularioCliente.addEventListener("submit", guardarCliente);
}

async function guardarCliente(evento) {
  evento.preventDefault();
  ocultarAviso(avisoCliente);
  try {
    const cliente = await enviarDatos("/api/clientes", {
      nit: formularioCliente.nit.value,
      nombre: formularioCliente.nombre.value,
    });
    // El cliente nuevo queda elegido en el formulario de la OP.
    await cargarClientes(String(cliente.id));
    dialogoCliente.close();
  } catch (error) {
    mostrarAviso(avisoCliente, error.message);
  }
}
