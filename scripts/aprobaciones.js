// =====================================================================
// aprobaciones.js
// Página "Aprobaciones" (solo analista):
//   - Bandeja con los reportes de entrega, filtrados por estado, área y OP.
//   - Ventana de revisión: muestra qué entra y qué sale del inventario, si
//     alcanzan las existencias, y permite aprobar o rechazar (con motivo).
// =====================================================================

const filtroEstado = document.getElementById("filtro-estado");
const filtroArea = document.getElementById("filtro-area");
const filtroOp = document.getElementById("filtro-op");
const tablaReportes = document.getElementById("tabla-reportes");
const avisoBandeja = document.getElementById("aviso-bandeja");

const dialogoRevision = document.getElementById("dialogo-revision");
const formularioDecision = document.getElementById("formulario-decision");
const avisoRevision = document.getElementById("aviso-revision");
const notaRevision = document.getElementById("revision-nota");
const botonAprobar = document.getElementById("boton-aprobar");
const botonRechazar = document.getElementById("boton-rechazar");

let reporteEnRevision = null;   // El número (#) del reporte abierto en la ventana
let puedeAprobar = false;       // Si el reporte abierto tiene existencias suficientes
let consultaActual = 0;         // Para descartar búsquedas viejas (igual que en ordenes.js)

async function arrancar() {
  await iniciarPagina();
  const listas = await pedirDatos("/api/listas");
  const opciones = [];
  for (const area of listas.areas) {
    opciones.push({ valor: area.codigo, texto: area.nombre });
  }
  llenarSelect(filtroArea, opciones, "Todas las áreas");

  filtroEstado.addEventListener("change", cargarReportes);
  filtroArea.addEventListener("change", cargarReportes);
  filtroOp.addEventListener("input", cargarReportes);
  tablaReportes.addEventListener("click", alHacerClicEnReportes);
  document.getElementById("cerrar-revision").addEventListener("click", function () {
    dialogoRevision.close();
  });
  botonAprobar.addEventListener("click", aprobar);
  botonRechazar.addEventListener("click", rechazar);

  cargarReportes();
}

arrancar();


// ---------------------------------------------------------------------
// Bandeja
// ---------------------------------------------------------------------

async function cargarReportes() {
  consultaActual += 1;
  const miConsulta = consultaActual;
  const filtros = { estado: filtroEstado.value, area: filtroArea.value, op: filtroOp.value };
  const reportes = await pedirDatos("/api/reportes" + armarConsulta(filtros));
  if (miConsulta !== consultaActual) {
    return;
  }

  document.getElementById("total-reportes").textContent =
    reportes.length + (reportes.length === 1 ? " reporte" : " reportes");
  if (reportes.length === 0) {
    tablaReportes.innerHTML = filaVacia(9, "No hay reportes con estos filtros.");
    return;
  }

  let html = "";
  for (const reporte of reportes) {
    // Los pendientes tienen botón "Revisar"; los ya revisados, "Ver".
    let textoBoton = "Ver";
    let claseBoton = "boton boton-secundario boton-pequeno";
    if (reporte.estado === "PENDIENTE") {
      textoBoton = "Revisar";
      claseBoton = "boton boton-pequeno";
    }
    html += `
      <tr>
        <td>${reporte.id}</td>
        <td class="sin-salto">${escaparHtml(reporte.fecha_reporte)}</td>
        <td><strong>${escaparHtml(reporte.orden)}</strong></td>
        <td>${escaparHtml(reporte.area)}</td>
        <td><strong>${escaparHtml(reporte.referencia)}</strong><br><small>${escaparHtml(reporte.descripcion)}</small></td>
        <td class="numero">${formatearNumero(reporte.cantidad)}</td>
        <td>${escaparHtml(reporte.reportado_por)}</td>
        <td>${etiquetaEstado(reporte.estado)}</td>
        <td><button type="button" class="${claseBoton}" data-reporte="${reporte.id}">${textoBoton}</button></td>
      </tr>`;
  }
  tablaReportes.innerHTML = html;
}

function alHacerClicEnReportes(evento) {
  const boton = evento.target.closest("[data-reporte]");
  if (boton !== null) {
    abrirRevision(boton.dataset.reporte);
  }
}


// ---------------------------------------------------------------------
// Ventana de revisión
// ---------------------------------------------------------------------

async function abrirRevision(id) {
  const detalle = await pedirDatos("/api/reporte" + armarConsulta({ id: id }));
  const reporte = detalle.reporte;
  reporteEnRevision = reporte.id;

  document.getElementById("revision-numero").textContent = "Reporte #" + reporte.id + " · " + reporte.fecha_reporte;
  document.getElementById("revision-titulo").textContent = formatearNumero(reporte.cantidad) + " und de " + reporte.referencia;
  document.getElementById("revision-descripcion").textContent = reporte.descripcion;
  document.getElementById("revision-op").textContent = reporte.orden;
  document.getElementById("revision-area").textContent = reporte.area;
  document.getElementById("revision-reportado").textContent = reporte.reportado_por;
  document.getElementById("revision-estado").innerHTML = etiquetaEstado(reporte.estado);

  pintarEntrada(reporte);
  pintarSalidas(detalle.consumos);
  pintarDecision(detalle);

  dialogoRevision.showModal();
}

// El producto que entregó el área: entra al inventario.
function pintarEntrada(reporte) {
  const quedara = reporte.item_existencia + reporte.cantidad;
  document.getElementById("revision-entrada").innerHTML = `
    <tr>
      <td><strong>${escaparHtml(reporte.item_codigo)}</strong></td>
      <td>${escaparHtml(reporte.item_descripcion)}</td>
      <td class="numero">+${formatearNumero(reporte.cantidad)} ${escaparHtml(reporte.unidad_medida)}</td>
      <td class="numero">${formatearNumero(reporte.item_existencia)}</td>
      <td class="numero"><strong>${formatearNumero(quedara)}</strong></td>
    </tr>`;
}

// Los materiales que se consumen: salen del inventario.
function pintarSalidas(consumos) {
  let html = "";
  for (const consumo of consumos) {
    let disponibilidad = '<span class="etiqueta aprobado">Suficiente</span>';
    if (!consumo.suficiente) {
      disponibilidad = '<span class="etiqueta rechazado">Faltan ' + formatearNumero(consumo.consumo - consumo.existencia) + "</span>";
    }
    html += `
      <tr>
        <td><strong>${escaparHtml(consumo.codigo)}</strong></td>
        <td>${escaparHtml(consumo.descripcion)}</td>
        <td class="numero">−${formatearNumero(consumo.consumo)} ${escaparHtml(consumo.unidad_medida)}</td>
        <td class="numero">${formatearNumero(consumo.existencia)}</td>
        <td class="numero"><strong>${formatearNumero(consumo.quedara)}</strong></td>
        <td>${disponibilidad}</td>
      </tr>`;
  }
  document.getElementById("revision-salidas").innerHTML = html;
}

// Qué puede hacer el analista con este reporte.
function pintarDecision(detalle) {
  const reporte = detalle.reporte;
  formularioDecision.reset();
  ocultarAviso(avisoRevision);
  notaRevision.hidden = true;

  // Ya revisado: solo se muestra la información, sin botones.
  if (reporte.estado !== "PENDIENTE") {
    formularioDecision.hidden = true;
    let texto = "Revisado por " + reporte.revisado_por + " el " + reporte.fecha_revision + ".";
    if (reporte.estado === "RECHAZADO") {
      texto += " Motivo: " + reporte.motivo_rechazo;
    }
    mostrarAviso(notaRevision, texto, "exito");
    return;
  }

  formularioDecision.hidden = false;
  // Si falta algún material, no se puede aprobar (pero sí rechazar).
  puedeAprobar = detalle.puede_aprobar;
  botonAprobar.disabled = !puedeAprobar;
  botonRechazar.disabled = false;
  if (!detalle.puede_aprobar) {
    mostrarAviso(notaRevision, "No hay existencias suficientes para aprobar (ver la tabla). Si falta un producto en proceso, "
      + "primero se deben aprobar las entregas del área que lo fabrica; si falta materia prima, hay que registrar "
      + "una entrada en Inventario. También puedes rechazar el reporte.");
  }
}

async function aprobar() {
  await decidir("/api/reportes/aprobar", { id: reporteEnRevision }, "aprobado");
}

async function rechazar() {
  const motivo = formularioDecision.motivo.value.trim();
  if (motivo === "") {
    // Se avisa antes de ir al servidor (el servidor también lo exige).
    mostrarAviso(avisoRevision, "Escribe el motivo del rechazo.");
    formularioDecision.motivo.focus();
    return;
  }
  await decidir("/api/reportes/rechazar", { id: reporteEnRevision, motivo: motivo }, "rechazado");
}

async function decidir(ruta, datos, palabra) {
  ocultarAviso(avisoRevision);
  botonAprobar.disabled = true;
  botonRechazar.disabled = true;
  try {
    await enviarDatos(ruta, datos);
    dialogoRevision.close();
    mostrarAviso(avisoBandeja, "Reporte #" + datos.id + " " + palabra + ".", "exito");
    cargarReportes();
  } catch (error) {
    // Si algo falló, se vuelven a activar los botones para intentar de nuevo.
    mostrarAviso(avisoRevision, error.message);
    botonAprobar.disabled = !puedeAprobar;
    botonRechazar.disabled = false;
  }
}
