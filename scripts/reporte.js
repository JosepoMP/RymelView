// =====================================================================
// reporte.js
// Página "Reportar entrega" (rol Área). El operario:
//   1. Busca una OP y ve qué referencia le toca, qué consume y cuánto falta.
//   2. Escribe la cantidad entregada (los consumos se recalculan al escribir).
//   3. Envía el reporte, que queda PENDIENTE hasta que el analista lo revise.
// Abajo ve el historial de reportes de su área.
// =====================================================================

const formularioBuscar = document.getElementById("formulario-buscar");
const avisoBuscar = document.getElementById("aviso-buscar");
const formularioEntrega = document.getElementById("formulario-entrega");
const avisoEntrega = document.getElementById("aviso-entrega");
const filtroEstado = document.getElementById("filtro-estado");

let consulta = null;   // Lo que respondió el servidor para la OP buscada

async function arrancar() {
  const usuario = await iniciarPagina();
  document.getElementById("antetitulo-area").textContent = "Módulo 1 · Área " + usuario.area_nombre;

  formularioBuscar.addEventListener("submit", function (evento) {
    evento.preventDefault();
    consultarOrden(formularioBuscar.numero.value.trim());
  });
  // Cada vez que se escribe la cantidad, se recalcula cuánto material se consumirá.
  formularioEntrega.cantidad.addEventListener("input", pintarMateriales);
  formularioEntrega.addEventListener("submit", enviarReporte);
  filtroEstado.addEventListener("change", cargarMisReportes);

  cargarSugerenciasDeOrdenes();
  cargarMisReportes();
}

arrancar();

// Llena el <datalist>: al escribir en el campo de OP aparecen las que existen.
async function cargarSugerenciasDeOrdenes() {
  const ordenes = await pedirDatos("/api/ordenes");
  let html = "";
  for (const orden of ordenes) {
    html += `<option value="${escaparHtml(orden.numero)}">${escaparHtml(orden.descripcion + " · " + orden.cliente_nombre)}</option>`;
  }
  document.getElementById("lista-ordenes").innerHTML = html;
}

// ---------- Consultar una OP ----------

async function consultarOrden(numero) {
  ocultarAviso(avisoBuscar);
  try {
    consulta = await pedirDatos("/api/mi-orden" + armarConsulta({ numero: numero }));
    pintarConsulta();
  } catch (error) {
    consulta = null;
    document.getElementById("resultado").hidden = true;
    document.getElementById("sin-consulta").hidden = false;
    mostrarAviso(avisoBuscar, error.message);
  }
}

function pintarConsulta() {
  const orden = consulta.orden;
  const avance = consulta.avance;

  document.getElementById("orden-titulo").textContent = "OP " + orden.numero;
  document.getElementById("orden-descripcion").textContent =
    orden.descripcion + " · " + orden.cantidad + " und a despachar · Cliente: " + orden.cliente_nombre;

  document.getElementById("referencia-codigo").textContent = avance.referencia;
  document.getElementById("referencia-descripcion").textContent = avance.descripcion;
  document.getElementById("referencia-item").innerHTML = etiquetaTipo(avance.item_tipo) + " " + escaparHtml(avance.item_codigo);
  document.getElementById("referencia-unidad").textContent = avance.unidad_medida;

  document.getElementById("cantidad-requerida").textContent = formatearNumero(avance.cantidad_requerida);
  document.getElementById("cantidad-aprobada").textContent = formatearNumero(avance.aprobadas);
  document.getElementById("cantidad-revision").textContent = formatearNumero(avance.en_revision);
  document.getElementById("cantidad-disponible").textContent = formatearNumero(avance.disponible);

  formularioEntrega.reset();
  // El navegador no deja escribir más de lo disponible (el servidor también lo revisa).
  formularioEntrega.cantidad.max = avance.disponible;
  // Si ya no queda nada por reportar, se bloquea el formulario.
  const bloquear = avance.disponible === 0;
  formularioEntrega.cantidad.disabled = bloquear;
  formularioEntrega.querySelector("button").disabled = bloquear;
  ocultarAviso(avisoEntrega);
  if (bloquear) {
    mostrarAviso(avisoEntrega, "Tu área ya reportó todo lo requerido en esta OP (o está en revisión).", "exito");
  }

  pintarMateriales();
  document.getElementById("sin-consulta").hidden = true;
  document.getElementById("resultado").hidden = false;
}

// Materiales de la referencia: por unidad y lo que se consumirá con la cantidad escrita.
function pintarMateriales() {
  const cantidad = Number(formularioEntrega.cantidad.value) || 0;   // Si está vacío, 0
  let html = "";
  for (const material of consulta.avance.materiales) {
    html += `
      <tr>
        <td><strong>${escaparHtml(material.codigo)}</strong></td>
        <td>${escaparHtml(material.descripcion)}</td>
        <td class="numero">${formatearNumero(material.cantidad)}</td>
        <td class="numero"><strong>${formatearNumero(material.cantidad * cantidad)}</strong></td>
        <td>${escaparHtml(material.unidad_medida)}</td>
      </tr>`;
  }
  document.getElementById("tabla-materiales").innerHTML = html;
}

// ---------- Enviar el reporte ----------

async function enviarReporte(evento) {
  evento.preventDefault();
  ocultarAviso(avisoEntrega);
  try {
    const reporte = await enviarDatos("/api/reportes", {
      orden: consulta.orden.numero,
      cantidad: formularioEntrega.cantidad.value,
    });
    // Se vuelve a consultar la OP para ver el avance actualizado.
    await consultarOrden(consulta.orden.numero);
    mostrarAviso(avisoEntrega, "Reporte #" + reporte.id + " enviado: " + reporte.cantidad
      + " und. Queda pendiente de aprobación.", "exito");
    cargarMisReportes();
  } catch (error) {
    mostrarAviso(avisoEntrega, error.message);
  }
}

// ---------- Historial de mi área ----------

async function cargarMisReportes() {
  // El servidor solo devuelve los reportes del área del usuario.
  const reportes = await pedirDatos("/api/reportes" + armarConsulta({ estado: filtroEstado.value }));
  const tabla = document.getElementById("tabla-mis-reportes");
  if (reportes.length === 0) {
    tabla.innerHTML = filaVacia(7, "Tu área aún no tiene reportes con este estado.");
    return;
  }
  let html = "";
  for (const reporte of reportes) {
    html += `
      <tr>
        <td>${reporte.id}</td>
        <td class="sin-salto">${escaparHtml(reporte.fecha_reporte)}</td>
        <td><strong>${escaparHtml(reporte.orden)}</strong></td>
        <td><strong>${escaparHtml(reporte.referencia)}</strong></td>
        <td class="numero">${formatearNumero(reporte.cantidad)}</td>
        <td>${etiquetaEstado(reporte.estado)}</td>
        <td>${escaparHtml(reporte.motivo_rechazo)}</td>
      </tr>`;
  }
  tabla.innerHTML = html;
}
