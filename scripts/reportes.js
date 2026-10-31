// =====================================================================
// reportes.js
// Página "Reportes" (analista y supervisor): vista previa de las entregas
// aprobadas con filtros, y el botón para descargarlas en CSV.
// =====================================================================

const filtros = document.getElementById("filtros-entregas");
const avisoEntregas = document.getElementById("aviso-entregas");
const enlaceExportar = document.getElementById("enlace-exportar");

// Columnas que no se deben partir en dos líneas (códigos y fechas).
const COLUMNAS_SIN_SALTO = ["Fecha de aprobación", "OP", "Referencia", "Ítem"];

async function arrancar() {
  await iniciarPagina();
  const listas = await pedirDatos("/api/listas");
  const opciones = [];
  for (const area of listas.areas) {
    opciones.push({ valor: area.codigo, texto: area.nombre });
  }
  llenarSelect(filtros.area, opciones, "Todas las áreas");

  // "change" en el formulario: se dispara cuando cambia cualquiera de sus campos.
  filtros.addEventListener("change", cargarVistaPrevia);
  cargarVistaPrevia();
}

arrancar();

function leerFiltros() {
  return {
    desde: filtros.desde.value,
    hasta: filtros.hasta.value,
    area: filtros.area.value,
    formato: filtros.formato.value,   // La estrategia de formato (la vista previa no la usa)
  };
}

async function cargarVistaPrevia() {
  ocultarAviso(avisoEntregas);
  try {
    const vista = await pedirDatos("/api/exportar/entregas/vista-previa" + armarConsulta(leerFiltros()));
    pintarEntregas(vista);
    // Sin resultados no tiene sentido descargar un archivo vacío.
    actualizarEnlace(vista.filas.length > 0);
  } catch (error) {
    // Por ejemplo: la fecha "Desde" es posterior a "Hasta".
    mostrarAviso(avisoEntregas, error.message);
    actualizarEnlace(false);
  }
}

// El botón es un enlace (<a download>). Su dirección lleva los mismos filtros de la vista previa,
// así el archivo trae exactamente lo que se ve en la tabla.
function actualizarEnlace(habilitado) {
  enlaceExportar.href = "/api/exportar/entregas" + armarConsulta(leerFiltros());
  enlaceExportar.classList.toggle("deshabilitado", !habilitado);
}

function pintarEntregas(vista) {
  const cantidad = vista.filas.length;
  document.getElementById("total-entregas").textContent =
    cantidad + (cantidad === 1 ? " entrega aprobada" : " entregas aprobadas")
    + " · " + formatearNumero(vista.total_unidades) + " unidades";

  // Encabezados de la tabla (los mismos del CSV).
  let cabecera = "<tr>";
  for (const encabezado of vista.encabezados) {
    let clase = "";
    if (encabezado === "Cantidad aprobada") {
      clase = ' class="numero"';
    }
    cabecera += `<th${clase}>${escaparHtml(encabezado)}</th>`;
  }
  document.getElementById("cabecera-entregas").innerHTML = cabecera + "</tr>";

  const tabla = document.getElementById("tabla-entregas");
  if (cantidad === 0) {
    tabla.innerHTML = filaVacia(vista.encabezados.length, "No hay entregas aprobadas con estos filtros.");
    return;
  }
  let html = "";
  for (const fila of vista.filas) {
    html += "<tr>";
    // Se recorre cada valor junto con su posición, para saber a qué columna pertenece.
    for (let posicion = 0; posicion < fila.length; posicion++) {
      html += crearCelda(fila[posicion], vista.encabezados[posicion]);
    }
    html += "</tr>";
  }
  tabla.innerHTML = html;
}

function crearCelda(valor, encabezado) {
  if (typeof valor === "number") {
    return `<td class="numero">${formatearNumero(valor)}</td>`;
  }
  let clase = "";
  if (COLUMNAS_SIN_SALTO.includes(encabezado)) {
    clase = ' class="sin-salto"';
  }
  return `<td${clase}>${escaparHtml(valor)}</td>`;
}
