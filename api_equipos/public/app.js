
// Elementos del HTML
const formulario = document.getElementById('formEquipo');
const tabla = document.getElementById('tablaEquipos');
const mensaje = document.getElementById('mensaje');

const inputId = document.getElementById('equipo-id');
const inputTitular = document.getElementById('titular');
const inputMarca = document.getElementById('marca');
const inputEstado = document.getElementById('estado');

const btnGuardar = document.getElementById('btn-guardar');
const btnCancelar = document.getElementById('btn-cancelar');

const formTitle = document.getElementById('form-title');

const estadoLista = document.getElementById('estadoLista');
const contadorR = document.getElementById('estadoLista_R');
const contadorO = document.getElementById('contador_O');
const contadorD = document.getElementById('contador_D');

const inputBuscar = document.getElementById('input-buscar');
const filtroEstado = document.getElementById('filtro-estado');

let equiposActuales = [];

// Mostrar mensajes
function mostrarMensaje(texto, tipo) {
    mensaje.textContent = texto;
    mensaje.className = tipo;
}

// GET: consultar equipos
async function cargarEquipos() {
    try {
        const respuesta = await fetch('/equipos');

        if (!respuesta.ok) {
            throw new Error('Error al consultar equipos');
        }

        equiposActuales = await respuesta.json();

        actualizarContadores();
        mostrarEquipos();

    } catch (error) {
        console.error('Error al cargar equipos:', error);
        mostrarMensaje('No se pudieron cargar los datos.', 'error');
    }
}

// Actualizar contadores
function actualizarContadores() {
    estadoLista.textContent = equiposActuales.length;

    contadorR.textContent = equiposActuales.filter(
        equipo => equipo.estado.trim() === 'En reparación'
    ).length;

    contadorO.textContent = equiposActuales.filter(
        equipo => equipo.estado.trim() === 'Operativo'
    ).length;

    contadorD.textContent = equiposActuales.filter(
        equipo => equipo.estado.trim() === 'Descartado'
    ).length;
}

// Mostrar tabla y aplicar filtros
function mostrarEquipos() {
    tabla.innerHTML = '';

    const busqueda = inputBuscar.value.toLowerCase().trim();
    const estado = filtroEstado.value;

    const equiposFiltrados = equiposActuales.filter(equipo => {

        const coincideTexto =
            equipo.titular.toLowerCase().includes(busqueda) ||
            equipo.marca.toLowerCase().includes(busqueda);

        const coincideEstado =
            !estado || equipo.estado === estado;

        return coincideTexto && coincideEstado;
    });

    if (equiposFiltrados.length === 0) {
        const fila = document.createElement('tr');
        const celda = document.createElement('td');

        celda.colSpan = 5;
        celda.textContent = 'No se encontraron equipos.';
        celda.className = 'no-data';

        fila.appendChild(celda);
        tabla.appendChild(fila);

        return;
    }

    equiposFiltrados.forEach(equipo => {
        const fila = document.createElement('tr');

        [equipo.id, equipo.titular, equipo.marca, equipo.estado]
            .forEach(valor => {
                const celda = document.createElement('td');
                celda.textContent = valor;
                fila.appendChild(celda);
            });

        // Acciones
        const acciones = document.createElement('td');

        // Editar
        const botonEditar = document.createElement('button');
        botonEditar.textContent = 'Editar';
        botonEditar.className = 'btn btn-edit';

        botonEditar.addEventListener('click', () => {
            editarEquipo(equipo);
        });

        // Eliminar
        const botonEliminar = document.createElement('button');
        botonEliminar.textContent = 'Eliminar';
        botonEliminar.className = 'btn btn-danger';

        botonEliminar.addEventListener('click', () => {
            eliminarEquipo(equipo.id);
        });

        acciones.append(botonEditar, botonEliminar);
        fila.appendChild(acciones);
        tabla.appendChild(fila);
    });
}

// POST y PUT: registrar o actualizar
formulario.addEventListener('submit', async (evento) => {
    evento.preventDefault();

    mostrarMensaje('', '');

    const id = inputId.value;

    const equipo = {
        titular: inputTitular.value.trim(),
        marca: inputMarca.value.trim(),
        estado: inputEstado.value
    };

    if (!equipo.titular || !equipo.marca) {
        mostrarMensaje('Completá todos los campos.', 'error');
        return;
    }

    try {
        const respuesta = await fetch(
            id ? `/equipos/${id}` : '/equipos',
            {
                method: id ? 'PUT' : 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(equipo)
            }
        );

        const resultado = await respuesta.json();

        if (!respuesta.ok) {
            throw new Error(resultado.error || 'Error en la operación');
        }

        mostrarMensaje(
            id
                ? 'Equipo actualizado correctamente.'
                : 'Equipo registrado correctamente.',
            'exito'
        );

        cancelarEdicion(false);

        await cargarEquipos();

    } catch (error) {
        console.error('Error al guardar equipo:', error);
        mostrarMensaje('No se pudo completar la operación.', 'error');
    }
});

// Cargar datos en el formulario
function editarEquipo(equipo) {

    inputId.value = equipo.id;
    inputTitular.value = equipo.titular;
    inputMarca.value = equipo.marca;
    inputEstado.value = equipo.estado;

    formTitle.textContent = 'Editar equipo';
    btnGuardar.textContent = 'Actualizar equipo';

    btnCancelar.classList.remove('hidden');

    mostrarMensaje('', '');

    // Subir hasta el formulario
    document.getElementById('seccion-formulario').scrollIntoView({
        behavior: 'smooth',
        block: 'start'
    });
}

// Cancelar edición
function cancelarEdicion(limpiarMensaje = true) {

    formulario.reset();

    inputId.value = '';

    formTitle.textContent = 'Registrar equipo';
    btnGuardar.textContent = 'Guardar equipo';

    btnCancelar.classList.add('hidden');

    if (limpiarMensaje) {
        mostrarMensaje('', '');
    }
}

// Botón cancelar
btnCancelar.addEventListener('click', () => {
    cancelarEdicion();
});

// DELETE: eliminar equipo
async function eliminarEquipo(id) {

    if (!confirm('¿Deseás eliminar este equipo?')) {
        return;
    }

    try {
        const respuesta = await fetch(`/equipos/${id}`, {
            method: 'DELETE'
        });

        const resultado = await respuesta.json();

        if (!respuesta.ok) {
            throw new Error(resultado.error || 'Error al eliminar');
        }

        mostrarMensaje('Equipo eliminado correctamente.', 'exito');

        await cargarEquipos();

    } catch (error) {
        console.error('Error al eliminar equipo:', error);
        mostrarMensaje('No se pudo completar la operación.', 'error');
    }
}

// Buscador y filtro
inputBuscar.addEventListener('input', mostrarEquipos);
filtroEstado.addEventListener('change', mostrarEquipos);
// Modo día y noche
const btnTema = document.getElementById('btn-tema');

// Recuperar tema guardado
let temaOscuro = localStorage.getItem('tema') === 'noche';

function cambiarTema() {

    document.body.classList.toggle('modo-noche', temaOscuro);

    btnTema.textContent = temaOscuro
        ? '☀️ Modo día'
        : '🌙 Modo noche';

    localStorage.setItem('tema', temaOscuro ? 'noche' : 'dia');
}

// Aplicar tema inicial
cambiarTema();

// Cambiar tema al presionar
btnTema.addEventListener('click', () => {

    temaOscuro = !temaOscuro;

    cambiarTema();

});
// Cargar registros al iniciar
cargarEquipos();
