// =====================================================================
// panel.js
// Página "Panel de producción" (supervisor y analista):
//   - Indicadores: cuántas áreas están pendientes, en proceso o aprobadas,
//     y cuántos reportes hay por revisar y rechazados.
//   - Matriz: una fila por OP y una columna por área, con el estado y el avance.
//   - Detalle: la misma información en una tabla, fila por fila.
// =====================================================================

const filtroOp = document.getElementById("filtro-op");
const filtroArea = document.getElementById("filtro-area");
const filtroEstado = document.getElementById("filtro-estado");

async function arrancar() {
  await iniciarPagina();
  const listas = await pedirDatos("/api/listas");
  const ordenes = await pedirDatos("/api/ordenes");

  const opcionesOp = [];
  for (const orden of ordenes) {
    opcionesOp.push({ valor: orden.numero, texto: "OP " + orden.numero + " · " + orden.item_codigo });
  }
  llenarSelect(filtroOp, opcionesOp, "Todas las OP");

  const opcionesArea = [];
  for (const area of listas.areas) {
    opcionesArea.push({ valor: area.codigo, texto: area.nombre });
  }
  llenarSelect(filtroArea, opcionesArea, "Todas las áreas");

  filtroOp.addEventListener("change", cargarPanel);
  filtroArea.addEventListener("change", cargarPanel);
  filtroEstado.addEventListener("change", cargarPanel);
  document.getElementById("boton-actualizar").addEventListener("click", cargarPanel);

  cargarPanel();
}

arrancar();

async function cargarPanel() {
  const filtros = { op: filtroOp.value, area: filtroArea.value, estado: filtroEstado.value };
  const panel = await pedirDatos("/api/panel" + armarConsulta(filtros));
  pintarIndicadores(panel.indicadores);
  pintarMatriz(panel.areas, panel.filas);
  pintarDetalle(panel.filas);
}

// Cada indicador tiene id="indicador-CLAVE", donde CLAVE es la que envía el servidor.
// Así un solo ciclo llena los cinco números.
function pintarIndicadores(indicadores) {
  for (const clave in indicadores) {
    document.getElementById("indicador-" + clave).textContent = indicadores[clave];
  }
}

// ---------- Matriz: una fila por OP, una columna por área ----------

function pintarMatriz(areas, filas) {
  // Encabezado: "OP" y luego el nombre de cada área.
  let cabecera = "<tr><th>OP</th>";
  for (const area of areas) {
    cabecera += `<th>${escaparHtml(area.nombre)}</th>`;
  }
  cabecera += "</tr>";
  document.getElementById("matriz-cabecera").innerHTML = cabecera;

  // Se ordenan las filas en un diccionario por OP: { "1001": { producto, celdas: { NUCLEO: fila, ... } } }
  // y se guarda el orden en que aparecen las OP.
  const porOrden = {};
  const ordenDeLasOp = [];
  for (const fila of filas) {
    if (porOrden[fila.orden] === undefined) {
      porOrden[fila.orden] = { producto: fila.producto, celdas: {} };
      ordenDeLasOp.push(fila.orden);
    }
    porOrden[fila.orden].celdas[fila.area_codigo] = fila;
  }

  const cuerpo = document.getElementById("matriz-cuerpo");
  if (ordenDeLasOp.length === 0) {
    cuerpo.innerHTML = filaVacia(areas.length + 1, "No hay resultados con estos filtros.");
    return;
  }

  let html = "";
  for (const numero of ordenDeLasOp) {
    const datos = porOrden[numero];
    html += `<tr><td><strong>OP ${escaparHtml(numero)}</strong><br><small>${escaparHtml(datos.producto)}</small></td>`;
    for (const area of areas) {
      html += "<td>" + crearCelda(datos.celdas[area.codigo]) + "</td>";
    }
    html += "</tr>";
  }
  cuerpo.innerHTML = html;
}

// Una celda: etiqueta de estado, "aprobadas / requeridas" y barra de avance.
// Si el filtro de estado dejó esa celda por fuera, se muestra una raya.
function crearCelda(fila) {
  if (fila === undefined) {
    return '<span class="texto-gris">—</span>';
  }
  return `
    <div class="celda-estado">
      ${etiquetaEstado(fila.estado)}
      <span>${formatearNumero(fila.aprobadas)} / ${formatearNumero(fila.requeridas)}</span>
      ${crearBarraAvance(fila.avance)}
    </div>`;
}

// La barra verde se llena según el porcentaje (style="width: 40%").
function crearBarraAvance(porcentaje) {
  const ancho = Math.min(porcentaje, 100);
  return `<div class="barra-avance" title="${porcentaje}%"><div style="width: ${ancho}%"></div></div>`;
}

// ---------- Detalle ----------

function pintarDetalle(filas) {
  const tabla = document.getElementById("tabla-detalle");
  if (filas.length === 0) {
    tabla.innerHTML = filaVacia(9, "No hay resultados con estos filtros.");
    return;
  }
  let html = "";
  for (const fila of filas) {
    html += `
      <tr>
        <td><strong>${escaparHtml(fila.orden)}</strong></td>
        <td>${escaparHtml(fila.area)}</td>
        <td><strong>${escaparHtml(fila.referencia)}</strong></td>
        <td class="numero">${formatearNumero(fila.requeridas)}</td>
        <td class="numero">${formatearNumero(fila.aprobadas)}</td>
        <td class="numero">${formatearNumero(fila.en_revision)}</td>
        <td class="numero">${fila.reportes_rechazados}</td>
        <td class="numero">${fila.avance}%</td>
        <td>${etiquetaEstado(fila.estado)}</td>
      </tr>`;
  }
  tabla.innerHTML = html;
}
