// =====================================================================
// inventario.js
// Página "Inventario" (analista y supervisor):
//   - Resumen por tipo de ítem y tabla de existencias con filtros.
//   - Historial de movimientos de cada ítem (en una ventana).
//   - Entrada de materia prima (solo el analista).
// =====================================================================

const filtroTipo = document.getElementById("filtro-tipo");
const filtroTexto = document.getElementById("filtro-texto");
const tablaExistencias = document.getElementById("tabla-existencias");
const dialogoHistorial = document.getElementById("dialogo-historial");
const formularioEntrada = document.getElementById("formulario-entrada");
const avisoEntrada = document.getElementById("aviso-entrada");

let consultaActual = 0;   // Para descartar búsquedas viejas (igual que en ordenes.js)

async function arrancar() {
  const usuario = await iniciarPagina();

  filtroTipo.addEventListener("change", cargarExistencias);
  filtroTexto.addEventListener("input", cargarExistencias);
  tablaExistencias.addEventListener("click", alHacerClicEnTabla);
  // Al cambiar el formato, el enlace de descarga pide esa estrategia al servidor.
  document.getElementById("formato-inventario").addEventListener("change", function (evento) {
    document.getElementById("enlace-exportar-inventario").href =
      "/api/exportar/inventario" + armarConsulta({ formato: evento.target.value });
  });
  document.getElementById("cerrar-historial").addEventListener("click", function () {
    dialogoHistorial.close();
  });

  // La entrada de materia prima solo la registra el analista (el servidor también lo revisa).
  if (usuario.rol === "ANALISTA") {
    document.getElementById("seccion-entrada").hidden = false;
    formularioEntrada.addEventListener("submit", registrarEntrada);
    cargarMateriasPrimas();
  }

  cargarExistencias();
}

arrancar();


// ---------------------------------------------------------------------
// Existencias
// ---------------------------------------------------------------------

async function cargarExistencias() {
  consultaActual += 1;
  const miConsulta = consultaActual;
  const filtros = { tipo: filtroTipo.value, texto: filtroTexto.value };
  const respuesta = await pedirDatos("/api/inventario" + armarConsulta(filtros));
  if (miConsulta !== consultaActual) {
    return;
  }
  pintarResumen(respuesta.resumen);
  pintarExistencias(respuesta.items);
}

// resumen = { MP: {items: 7, sin_existencia: 0}, PP: {...}, PT: {...} }
function pintarResumen(resumen) {
  for (const tipo in resumen) {
    document.getElementById("resumen-" + tipo).textContent = resumen[tipo].items;
    document.getElementById("resumen-" + tipo + "-cero").textContent =
      "ítems · " + resumen[tipo].sin_existencia + " sin existencia";
  }
}

function pintarExistencias(items) {
  if (items.length === 0) {
    tablaExistencias.innerHTML = filaVacia(6, "No hay ítems que coincidan con el filtro.");
    return;
  }
  let html = "";
  for (const item of items) {
    // Los ítems en cero llevan una etiqueta roja para que se noten.
    let sinExistencia = "";
    if (item.existencia <= 0) {
      sinExistencia = ' <span class="etiqueta rechazado">Sin existencia</span>';
    }
    html += `
      <tr>
        <td><strong>${escaparHtml(item.codigo)}</strong></td>
        <td>${escaparHtml(item.descripcion)}</td>
        <td>${etiquetaTipo(item.tipo)}</td>
        <td class="numero"><strong>${formatearNumero(item.existencia)}</strong>${sinExistencia}</td>
        <td>${escaparHtml(item.unidad_medida)}</td>
        <td><button type="button" class="boton boton-secundario boton-pequeno" data-historial="${escaparHtml(item.codigo)}">Historial</button></td>
      </tr>`;
  }
  tablaExistencias.innerHTML = html;
}

function alHacerClicEnTabla(evento) {
  const boton = evento.target.closest("[data-historial]");
  if (boton !== null) {
    abrirHistorial(boton.dataset.historial);
  }
}


// ---------------------------------------------------------------------
// Historial de un ítem
// ---------------------------------------------------------------------

async function abrirHistorial(codigo) {
  const historial = await pedirDatos("/api/inventario/movimientos" + armarConsulta({ codigo: codigo }));
  const item = historial.item;
  const unidad = " " + item.unidad_medida;

  document.getElementById("historial-codigo").textContent = item.codigo;
  document.getElementById("historial-descripcion").textContent = item.descripcion;
  document.getElementById("historial-entradas").textContent = formatearNumero(historial.total_entradas) + unidad;
  document.getElementById("historial-salidas").textContent = formatearNumero(historial.total_salidas) + unidad;
  document.getElementById("historial-existencia").textContent = formatearNumero(item.existencia) + unidad;

  const tabla = document.getElementById("historial-movimientos");
  if (historial.movimientos.length === 0) {
    tabla.innerHTML = filaVacia(7, "Este ítem todavía no tiene movimientos.");
  } else {
    let html = "";
    for (const movimiento of historial.movimientos) {
      // Entrada: etiqueta verde y signo +. Salida: etiqueta roja y signo −.
      let etiqueta = '<span class="etiqueta entrada">Entrada</span>';
      let signo = "+";
      if (movimiento.tipo === "SALIDA") {
        etiqueta = '<span class="etiqueta salida">Salida</span>';
        signo = "−";
      }
      html += `
        <tr>
          <td class="sin-salto">${escaparHtml(movimiento.fecha)}</td>
          <td>${etiqueta}</td>
          <td class="numero">${signo}${formatearNumero(movimiento.cantidad)}</td>
          <td class="numero">${formatearNumero(movimiento.existencia_resultante)}</td>
          <td>${escaparHtml(movimiento.orden || "—")}</td>
          <td>${escaparHtml(movimiento.concepto)}</td>
          <td>${escaparHtml(movimiento.usuario)}</td>
        </tr>`;
    }
    tabla.innerHTML = html;
  }
  dialogoHistorial.showModal();
}


// ---------------------------------------------------------------------
// Entrada de materia prima (analista)
// ---------------------------------------------------------------------

async function cargarMateriasPrimas() {
  const respuesta = await pedirDatos("/api/inventario" + armarConsulta({ tipo: "MP" }));
  const opciones = [];
  for (const item of respuesta.items) {
    opciones.push({ valor: item.codigo, texto: item.codigo + " · " + item.descripcion + " (" + item.unidad_medida + ")" });
  }
  llenarSelect(formularioEntrada.item, opciones, "Elige una materia prima");
}

async function registrarEntrada(evento) {
  evento.preventDefault();
  ocultarAviso(avisoEntrada);
  try {
    const resultado = await enviarDatos("/api/inventario/entradas", {
      item: formularioEntrada.item.value,
      cantidad: formularioEntrada.cantidad.value,
      concepto: formularioEntrada.concepto.value,
    });
    formularioEntrada.reset();
    mostrarAviso(avisoEntrada, "Entrada registrada: +" + formatearNumero(resultado.cantidad) + " de "
      + resultado.item + ". Nueva existencia: " + formatearNumero(resultado.existencia) + ".", "exito");
    cargarExistencias();
  } catch (error) {
    mostrarAviso(avisoEntrada, error.message);
  }
}
