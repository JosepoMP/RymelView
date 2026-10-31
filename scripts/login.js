// =====================================================================
// login.js
// Envía el usuario y la contraseña al servidor. Si son correctos, el
// servidor guarda la sesión en una cookie y nos dice a qué página ir.
// =====================================================================

const formularioLogin = document.getElementById("formulario-login");
const avisoLogin = document.getElementById("aviso-login");
const botonIngresar = formularioLogin.querySelector("button");

prepararLogo(document.getElementById("logo"));
pintarPie();

// "submit" ocurre al presionar Ingresar o Enter dentro del formulario.
formularioLogin.addEventListener("submit", iniciarSesion);

async function iniciarSesion(evento) {
  // Sin esto, el navegador recargaría la página (el comportamiento normal de un formulario).
  evento.preventDefault();
  ocultarAviso(avisoLogin);
  botonIngresar.disabled = true;   // Evita que se envíe dos veces con doble clic

  const datos = {
    usuario: formularioLogin.usuario.value,
    contrasena: formularioLogin.contrasena.value,
  };

  try {
    const respuesta = await enviarDatos("/api/login", datos);
    // respuesta.inicio es la página de inicio del rol, por ejemplo "/reporte".
    window.location.href = respuesta.inicio;
  } catch (error) {
    // Usuario o contraseña incorrectos: se muestra el mensaje del servidor.
    mostrarAviso(avisoLogin, error.message);
    botonIngresar.disabled = false;
  }
}
