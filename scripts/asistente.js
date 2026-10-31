// =====================================================================
// asistente.js
// Pestaña "Nuevo producto" de la página Ítems y referencias (solo analista).
// Crea en un solo paso un transformador completo:
//   Paso 1: descripción del producto (y, si se quiere, copiar otro producto).
//   Paso 2: un bloque por área con su descripción y su materia prima.
//   Paso 3: revisar (sin guardar) y crear.
//
// Este archivo se carga DESPUÉS de comun.js y catalogo.js, en la misma página.
// Todos comparten las mismas variables globales; por eso aquí los nombres
// llevan "Producto" o "Asistente", para no chocar con los de catalogo.js.
// Para comunicarse con catalogo.js usa avisos (patrón Observador, ver comun.js),
// no llamadas directas: así ninguno depende de cómo se llaman las funciones del otro.
// =====================================================================

const formularioProducto = document.getElementById("formulario-producto");
const bloquesPartes = document.getElementById("bloques-partes");
const avisoProducto = document.getElementById("aviso-producto");
const revisionProducto = document.getElementById("revision-producto");
const botonCrearProducto = document.getElementById("boton-crear-producto");

let plantilla = null;   // Respuesta de /api/producto/plantilla

async function arrancarAsistente() {
  plantilla = await pedirDatos("/api/producto/plantilla");
  llenarProductosParaCopiar();
  dibujarBloques();
  empezarDeCero();

  formularioProducto.addEventListener("submit", revisarProducto);
  formularioProducto.descripcion.addEventListener("input", completarDescripciones);
  formularioProducto.copiar_de.addEventListener("change", copiarProducto);
  // Cualquier cambio en el formulario esconde la revisión: lo que se crea
  // debe ser exactamente lo último que se revisó.
  formularioProducto.addEventListener("input", alCambiarAlgo);
  formularioProducto.addEventListener("change", alCambiarAlgo);
  bloquesPartes.addEventListener("click", alHacerClicEnBloques);
  botonCrearProducto.addEventListener("click", crearProducto);
  // Patrón Observador: si se crea una materia prima o un producto en otra pestaña,
  // el asistente actualiza sus listas solo.
  escuchar("catalogo-cambiado", recargarMateriasPrimas);
}

arrancarAsistente();


// ---------------------------------------------------------------------
// Dibujar los bloques
// ---------------------------------------------------------------------

function llenarProductosParaCopiar() {
  const opciones = [];
  for (const producto of plantilla.productos) {
    opciones.push({ valor: producto.codigo, texto: producto.item_codigo + " · " + producto.descripcion });
  }
  llenarSelect(formularioProducto.copiar_de, opciones, "No copiar: empezar vacío");
}

// Un bloque (tarjeta) por área, en el orden de la planta.
function dibujarBloques() {
  let html = "";
  let numero = 1;
  for (const parte of plantilla.partes) {
    // Las conexiones fijas con otras áreas: filas con candado, solo se cambia la cantidad.
    let filasFijas = "";
    for (const componente of parte.componentes) {
      filasFijas += `
        <tr class="fila-fija" data-componente="${componente.area}">
          <td>🔒 ${escaparHtml(componente.nombre_parte)} <small>(${escaparHtml(componente.area_nombre)})</small></td>
          <td class="numero"><input class="entrada-numero" type="number" min="0" step="any" value="1"></td>
          <td></td>
        </tr>`;
    }
    let obligatoria = "";
    if (parte.mp_obligatoria) {
      obligatoria = " · al menos una materia prima";
    }
    html += `
      <section class="tarjeta bloque-parte" data-area="${parte.area}">
        <div class="bloque-cabecera">
          ${etiquetaTipo(parte.tipo)}
          <h3>${numero} · ${escaparHtml(parte.area_nombre)}</h3>
          <small class="texto-gris">${escaparHtml(parte.nombre_parte)}${obligatoria}</small>
        </div>
        <label class="campo">
          <span>Descripción</span>
          <input data-descripcion maxlength="150" autocomplete="off">
        </label>
        <div class="tabla-contenedor">
          <table class="tabla">
            <thead><tr><th>Material</th><th class="numero">Cantidad</th><th></th></tr></thead>
            <tbody data-filas>${filasFijas}</tbody>
          </table>
        </div>
        <div><button type="button" class="boton boton-secundario boton-pequeno" data-agregar>+ Agregar materia prima</button></div>
      </section>`;
    numero += 1;
  }
  bloquesPartes.innerHTML = html;
}

function buscarBloque(codigoArea) {
  return bloquesPartes.querySelector(`[data-area="${codigoArea}"]`);
}

function opcionesMateriaPrima() {
  const opciones = [];
  for (const item of plantilla.materias_primas) {
    opciones.push({ valor: item.codigo, texto: item.codigo + " · " + item.descripcion + " (" + item.unidad_medida + ")" });
  }
  return opciones;
}

function agregarFilaMateriaPrima(bloque, codigo, cantidad) {
  const fila = document.createElement("tr");
  fila.setAttribute("data-materia-prima", "");
  fila.innerHTML = `
    <td><select></select></td>
    <td class="numero"><input class="entrada-numero" type="number" min="0" step="any"></td>
    <td><button type="button" class="boton-icono" data-quitar title="Quitar">✕</button></td>`;
  llenarSelect(fila.querySelector("select"), opcionesMateriaPrima(), "Elige una materia prima");
  fila.querySelector("select").value = codigo;
  fila.querySelector("input").value = cantidad;
  bloque.querySelector("[data-filas]").appendChild(fila);
}

function alHacerClicEnBloques(evento) {
  const botonAgregar = evento.target.closest("[data-agregar]");
  if (botonAgregar !== null) {
    agregarFilaMateriaPrima(botonAgregar.closest("[data-area]"), "", "");
    ocultarRevision();
  }
  const botonQuitar = evento.target.closest("[data-quitar]");
  if (botonQuitar !== null) {
    botonQuitar.closest("tr").remove();
    ocultarRevision();
  }
}

// Llena un bloque con valores = { materiales: [{item, cantidad}], componentes: {AREA: cantidad} }.
function llenarBloque(parte, valores) {
  const bloque = buscarBloque(parte.area);
  // Se quitan las filas de materia prima que hubiera.
  for (const fila of bloque.querySelectorAll("[data-materia-prima]")) {
    fila.remove();
  }
  // Cantidades de las conexiones fijas (1 si no vienen).
  for (const fila of bloque.querySelectorAll("[data-componente]")) {
    let cantidad = valores.componentes[fila.dataset.componente];
    if (cantidad === undefined) {
      cantidad = 1;
    }
    fila.querySelector("input").value = cantidad;
  }
  for (const material of valores.materiales) {
    agregarFilaMateriaPrima(bloque, material.item, material.cantidad);
  }
  // Donde la materia prima es obligatoria, se deja al menos una fila vacía para llenar.
  if (valores.materiales.length === 0 && parte.mp_obligatoria) {
    agregarFilaMateriaPrima(bloque, "", "");
  }
}

function empezarDeCero() {
  formularioProducto.reset();
  for (const parte of plantilla.partes) {
    const campo = buscarBloque(parte.area).querySelector("[data-descripcion]");
    campo.value = "";
    delete campo.dataset.editada;
    llenarBloque(parte, { materiales: [], componentes: {} });
  }
}

async function recargarMateriasPrimas() {
  const nueva = await pedirDatos("/api/producto/plantilla");
  plantilla.materias_primas = nueva.materias_primas;
  plantilla.productos = nueva.productos;
  // Se actualizan las listas sin perder lo que ya estaba elegido.
  for (const select of bloquesPartes.querySelectorAll("[data-materia-prima] select")) {
    const elegido = select.value;
    llenarSelect(select, opcionesMateriaPrima(), "Elige una materia prima");
    select.value = elegido;
  }
  const copiarDe = formularioProducto.copiar_de.value;
  llenarProductosParaCopiar();
  formularioProducto.copiar_de.value = copiarDe;
}


// ---------------------------------------------------------------------
// Paso 1: descripciones automáticas y copiar otro producto
// ---------------------------------------------------------------------

// "Transformador 112,5 kVA" -> "Núcleo transformador 112,5 kVA", "Tanque transformador...", etc.
// Solo en los bloques que el usuario no haya editado a mano.
function completarDescripciones() {
  const descripcion = formularioProducto.descripcion.value.trim();
  // La primera letra en minúscula para que quede "Núcleo transformador..." y no "Núcleo Transformador...".
  const enMinuscula = descripcion.charAt(0).toLowerCase() + descripcion.slice(1);
  for (const parte of plantilla.partes) {
    const campo = buscarBloque(parte.area).querySelector("[data-descripcion]");
    if (campo.dataset.editada) {
      continue;
    }
    if (parte.tipo === "PT" || descripcion === "") {
      campo.value = descripcion;     // El producto terminado lleva la descripción tal cual
    } else {
      campo.value = parte.nombre_parte + " " + enMinuscula;
    }
  }
}

async function copiarProducto() {
  ocultarAviso(avisoProducto);
  let copia = { partes: {} };
  if (formularioProducto.copiar_de.value !== "") {
    copia = await pedirDatos("/api/producto/copiar" + armarConsulta({ referencia: formularioProducto.copiar_de.value }));
  }
  for (const parte of plantilla.partes) {
    let valores = copia.partes[parte.area];
    if (valores === undefined) {
      valores = { materiales: [], componentes: {} };
    }
    llenarBloque(parte, valores);
  }
}

function alCambiarAlgo(evento) {
  // Si el usuario escribe en la descripción de una parte, se marca como "editada"
  // para que completarDescripciones no se la cambie.
  if (evento.target.hasAttribute("data-descripcion")) {
    evento.target.dataset.editada = "si";
  }
  ocultarRevision();
}

function ocultarRevision() {
  revisionProducto.hidden = true;
}


// ---------------------------------------------------------------------
// Leer el formulario
// ---------------------------------------------------------------------

// Devuelve { partes: { NUCLEO: {descripcion, componentes, materiales}, ... } }
function leerProducto() {
  const partes = {};
  for (const bloque of bloquesPartes.querySelectorAll("[data-area]")) {
    const componentes = {};
    for (const fila of bloque.querySelectorAll("[data-componente]")) {
      componentes[fila.dataset.componente] = fila.querySelector("input").value;
    }
    const materiales = [];
    for (const fila of bloque.querySelectorAll("[data-materia-prima]")) {
      const item = fila.querySelector("select").value;
      const cantidad = fila.querySelector("input").value;
      // Las filas totalmente vacías se ignoran; las incompletas se envían para que el servidor avise.
      if (item !== "" || cantidad !== "") {
        materiales.push({ item: item, cantidad: cantidad });
      }
    }
    partes[bloque.dataset.area] = {
      descripcion: bloque.querySelector("[data-descripcion]").value,
      componentes: componentes,
      materiales: materiales,
    };
  }
  return { partes: partes };
}


// ---------------------------------------------------------------------
// Paso 3: revisar y crear
// ---------------------------------------------------------------------

async function revisarProducto(evento) {
  evento.preventDefault();
  ocultarAviso(avisoProducto);
  try {
    const vista = await enviarDatos("/api/producto/vista-previa", leerProducto());
    pintarRevision(vista);
    revisionProducto.hidden = false;
    revisionProducto.scrollIntoView({ behavior: "smooth", block: "start" });
  } catch (error) {
    ocultarRevision();
    mostrarAviso(avisoProducto, error.message);
  }
}

function pintarRevision(vista) {
  // Nombres de las áreas para la tabla (vienen en la plantilla).
  const nombres = {};
  for (const parte of plantilla.partes) {
    nombres[parte.area] = parte.area_nombre;
  }
  let html = "";
  for (const parte of vista.partes) {
    html += `
      <tr>
        <td>${escaparHtml(nombres[parte.area])}</td>
        <td class="sin-salto"><strong>${escaparHtml(parte.referencia)}</strong></td>
        <td class="sin-salto">${etiquetaTipo(parte.tipo)} ${escaparHtml(parte.item)}</td>
        <td>${escaparHtml(parte.descripcion)}</td>
      </tr>`;
  }
  document.getElementById("revision-partes").innerHTML = html;
  document.getElementById("revision-arbol").innerHTML = crearNodoArbol(vista.arbol);

  let materia = "";
  for (const linea of vista.materia_prima) {
    materia += `
      <tr>
        <td><strong>${escaparHtml(linea.item.codigo)}</strong></td>
        <td>${escaparHtml(linea.item.descripcion)}</td>
        <td class="numero">${formatearNumero(linea.cantidad_requerida)}</td>
        <td class="numero">${formatearNumero(linea.item.existencia)}</td>
        <td>${escaparHtml(linea.item.unidad_medida)}</td>
      </tr>`;
  }
  document.getElementById("revision-materia-prima").innerHTML = materia;
}

async function crearProducto() {
  ocultarAviso(avisoProducto);
  botonCrearProducto.disabled = true;
  try {
    const creado = await enviarDatos("/api/producto", leerProducto());
    empezarDeCero();
    ocultarRevision();
    mostrarAvisoDeExito(creado);
    avisoProducto.scrollIntoView({ behavior: "smooth", block: "center" });
    // Patrón Observador: el asistente solo AVISA que el catálogo cambió.
    // No llama a las funciones de catalogo.js: cada pestaña escucha y se recarga sola.
    avisar("catalogo-cambiado");
  } catch (error) {
    mostrarAviso(avisoProducto, error.message);
  }
  botonCrearProducto.disabled = false;
}

function mostrarAvisoDeExito(creado) {
  const primera = creado.partes[0];
  const ultima = creado.partes[creado.partes.length - 1];
  mostrarAviso(avisoProducto, "", "exito");
  // Aquí se usa innerHTML porque el aviso lleva enlaces. Los textos pasan por escaparHtml.
  avisoProducto.innerHTML = `
    Producto creado: <strong>${escaparHtml(ultima.item)} · ${escaparHtml(ultima.descripcion)}</strong>
    (${creado.partes.length} referencias, de ${escaparHtml(primera.referencia)} a ${escaparHtml(ultima.referencia)}).
    <a href="/estructura${armarConsulta({ referencia: creado.ensamble })}">Ver estructura ↗</a> ·
    <a href="/ordenes">Crear una OP con este producto ↗</a>`;
}
