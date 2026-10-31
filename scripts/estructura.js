// =====================================================================
// estructura.js
// Página "Estructura" (analista y supervisor): muestra el árbol de una
// referencia (PT -> PP -> MP) y el total de materia prima.
// Se puede abrir ya filtrada desde otra página, por ejemplo:
//   /estructura?referencia=ENSAMBLE-001&cantidad=10
// =====================================================================

const formularioEstructura = document.getElementById("formulario-estructura");
const avisoEstructura = document.getElementById("aviso-estructura");
const estructuraVacia = document.getElementById("estructura-vacia");
const resultado = document.getElementById("resultado");
const arbol = document.getElementById("arbol");

async function arrancar() {
  await iniciarPagina();
  const referencias = await pedirDatos("/api/referencias");
  llenarReferencias(referencias);
  leerParametrosDeLaDireccion();

  formularioEstructura.addEventListener("submit", function (evento) {
    evento.preventDefault();
    consultarEstructura();
  });
  document.getElementById("expandir-todo").addEventListener("click", function () {
    abrirRamas(arbol, true);
  });
  document.getElementById("contraer-todo").addEventListener("click", function () {
    abrirRamas(arbol, false);
  });

  if (referencias.length > 0) {
    consultarEstructura();
  }
}

arrancar();

// Dos grupos en la lista: primero los productos terminados, luego los productos en proceso.
// <optgroup> muestra un título gris dentro del <select>.
function llenarReferencias(referencias) {
  let terminados = "";
  let enProceso = "";
  for (const referencia of referencias) {
    const opcion = `<option value="${escaparHtml(referencia.codigo)}">${escaparHtml(referencia.codigo)} · ${escaparHtml(referencia.descripcion)}</option>`;
    if (referencia.item_tipo === "PT") {
      terminados += opcion;
    } else {
      enProceso += opcion;
    }
  }
  formularioEstructura.referencia.innerHTML =
    `<optgroup label="Productos terminados">${terminados}</optgroup>` +
    `<optgroup label="Productos en proceso">${enProceso}</optgroup>`;
}

// Si la dirección trae ?referencia=...&cantidad=..., se usan esos valores.
function leerParametrosDeLaDireccion() {
  const parametros = new URLSearchParams(window.location.search);
  const referencia = parametros.get("referencia");
  const cantidad = parametros.get("cantidad");
  if (referencia !== null) {
    formularioEstructura.referencia.value = referencia;
  }
  if (cantidad !== null) {
    formularioEstructura.cantidad.value = cantidad;
  }
}

async function consultarEstructura() {
  ocultarAviso(avisoEstructura);
  const filtros = {
    referencia: formularioEstructura.referencia.value,
    cantidad: formularioEstructura.cantidad.value,
  };
  try {
    const estructura = await pedirDatos("/api/estructura" + armarConsulta(filtros));
    document.getElementById("titulo-resultado").textContent =
      estructura.referencia + " × " + formatearNumero(estructura.cantidad);
    arbol.innerHTML = crearNodoArbol(estructura.arbol);   // crearNodoArbol está en comun.js
    pintarMateriaPrima(estructura.materia_prima);
    estructuraVacia.hidden = true;
    resultado.hidden = false;
  } catch (error) {
    mostrarAviso(avisoEstructura, error.message);
  }
}

function pintarMateriaPrima(materiaPrima) {
  const tabla = document.getElementById("tabla-materia-prima");
  if (materiaPrima.length === 0) {
    tabla.innerHTML = filaVacia(6, "Esta estructura no tiene materia prima.");
    return;
  }
  let html = "";
  for (const linea of materiaPrima) {
    const item = linea.item;
    html += `
      <tr>
        <td><strong>${escaparHtml(item.codigo)}</strong></td>
        <td>${escaparHtml(item.descripcion)}</td>
        <td class="numero">${formatearNumero(linea.cantidad_requerida)}</td>
        <td class="numero">${formatearNumero(item.existencia)}</td>
        <td>${escaparHtml(item.unidad_medida)}</td>
        <td>${etiquetaDisponibilidad(linea.cantidad_requerida, item.existencia)}</td>
      </tr>`;
  }
  tabla.innerHTML = html;
}

// Verde si alcanza la existencia; rojo con lo que falta si no alcanza.
function etiquetaDisponibilidad(requerida, existencia) {
  if (existencia >= requerida) {
    return '<span class="etiqueta aprobado">Suficiente</span>';
  }
  return '<span class="etiqueta rechazado">Faltan ' + formatearNumero(requerida - existencia) + "</span>";
}
