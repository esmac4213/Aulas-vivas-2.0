const inputAlumno = document.getElementById("alumno-input");
const btnBuscar = document.getElementById("btnBuscar");

btnBuscar.addEventListener("click", async () => {

    const busqueda = inputAlumno.value.trim();

    if (!busqueda) {
        alert("Ingresa una matrícula");
        return;
    }

    try {

        const respuesta = await fetch(
            `/alumnos/obtener-alumno/?busqueda=${encodeURIComponent(busqueda)}`
        );

        const datos = await respuesta.json();

        if (!respuesta.ok) {
            alert(datos.error);
            return;
        }

        const contenedor = document.getElementById("informacionAlumno");

        contenedor.innerHTML = `
            <div class="info-box">
                ${datos.nombre} · Matrícula ${datos.matricula}
            </div>

            <div class="info-box">
                Grupo: ${datos.grupo}
            </div>
        `;

    } catch (error) {
        console.error("Error:", error);
    }

});


const contenedor = document.getElementById("informacionAlumno");
const boton = document.getElementById("btnCambiar");

let mostrandoFaltas = false;

// Datos de ejemplo
const faltas = [
    { fecha: "10/11/2026", materia: "Matemáticas" },
    { fecha: "12/11/2026", materia: "Historia" },
    { fecha: "15/11/2026", materia: "Programación" },
    { fecha: "18/11/2026", materia: "Inglés Técnico" }
];

boton.addEventListener("click", () => {

    if (!mostrandoFaltas) {

        // Cambiar información por registro de faltas
        contenedor.innerHTML = `
            <table class="tabla-faltas">
                <thead>
                    <tr>
                        <th>Fecha de falta</th>
                        <th>Materia</th>
                    </tr>
                </thead>

                <tbody>
                    ${faltas.map(falta => `
                        <tr>
                            <td>${falta.fecha}</td>
                            <td>${falta.materia}</td>
                        </tr>
                    `).join("")}
                </tbody>
            </table>
        `;

        boton.textContent = "Ver información del alumno";
        mostrandoFaltas = true;

    } else {

        // Restaurar información original
        contenedor.innerHTML = `
            <div class="info-box">
                Luis Pérez · Matrícula 2026002
            </div>

            <div class="info-box">
                Grupo: 3.º A · Estado: Activo
            </div>

            <div class="info-box">
                Asignaturas inscritas: Matemáticas, Historia
            </div>
        `;

        boton.textContent = "Ver registro de faltas";
        mostrandoFaltas = false;
    }

});