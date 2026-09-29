const CLAVE_ALMACENAMIENTO = 'gestionEquiposInformaticos';
const ESTADOS_VALIDOS = ['Operativo', 'En reparación', 'Descartado'];

let listaEquipos = cargarEquipos();
let idEquipoEdicion = null;

const formulario = document.getElementById('equipo-form');
const inputTipo = document.getElementById('tipo');
const inputTitular = document.getElementById('titular');
const inputMarca = document.getElementById('marca');
const inputProcesador = document.getElementById('procesador');
const inputRam = document.getElementById('ram');
const inputAlmacenamiento = document.getElementById('almacenamiento');
const inputPlacaVideo = document.getElementById('placa-video');
const inputPulgadas = document.getElementById('pulgadas');
const inputEstado = document.getElementById('estado');
const btnGuardar = document.getElementById('btn-guardar');
const btnCancelar = document.getElementById('btn-cancelar');
const tituloFormulario = document.getElementById('form-title');
const tablaBody = document.getElementById('tabla-equipos-body');
const inputBuscar = document.getElementById('input-buscar');
const filtroEstado = document.getElementById('filtro-estado');
const archivoJson = document.getElementById('archivo-json');

formulario.addEventListener('submit', evento => {
    evento.preventDefault();
    guardarEquipo();
});
btnCancelar.addEventListener('click', resetearFormulario);
inputBuscar.addEventListener('input', renderizarTabla);
filtroEstado.addEventListener('change', renderizarTabla);
document.getElementById('btn-exportar').addEventListener('click', exportarJSON);
archivoJson.addEventListener('change', importarJSON);

function cargarEquipos() {
    try {
        const datos = JSON.parse(localStorage.getItem(CLAVE_ALMACENAMIENTO) || '[]');
        return Array.isArray(datos) ? datos.map(normalizarEquipo).filter(Boolean) : [];
    } catch (error) {
        console.error('No se pudieron leer los equipos guardados:', error);
        return [];
    }
}

function normalizarEquipo(equipo) {
    if (!equipo || typeof equipo !== 'object') return null;
    const estado = ESTADOS_VALIDOS.includes(equipo.estado) ? equipo.estado : 'Operativo';
    const campos = ['tipo', 'titular', 'marca', 'procesador', 'ram', 'almacenamiento', 'placaVideo', 'pulgadas'];
    if (campos.some(campo => typeof equipo[campo] !== 'string')) return null;
    return { ...equipo, id: equipo.id ?? Date.now() + Math.random(), estado };
}

function guardarEnAlmacenamiento() {
    try {
        localStorage.setItem(CLAVE_ALMACENAMIENTO, JSON.stringify(listaEquipos));
        return true;
    } catch (error) {
        alert('No se pudieron guardar los cambios en el navegador. Verificá el espacio disponible.');
        console.error(error);
        return false;
    }
}

function guardarEquipo() {
    const datosEquipo = {
        id: idEquipoEdicion !== null ? idEquipoEdicion : Date.now(),
        tipo: inputTipo.value.trim(),
        titular: inputTitular.value.trim(),
        marca: inputMarca.value.trim(),
        procesador: inputProcesador.value.trim(),
        ram: inputRam.value.trim(),
        almacenamiento: inputAlmacenamiento.value.trim(),
        placaVideo: inputPlacaVideo.value.trim(),
        pulgadas: inputPulgadas.value.trim(),
        estado: inputEstado.value
    };
    if (idEquipoEdicion === null) listaEquipos.push(datosEquipo);
    else listaEquipos = listaEquipos.map(equipo => equipo.id === idEquipoEdicion ? datosEquipo : equipo);
    guardarEnAlmacenamiento();
    resetearFormulario();
    renderizarTabla();
}

function renderizarTabla() {
    tablaBody.innerHTML = '';
    const termino = inputBuscar.value.toLocaleLowerCase('es').trim();
    const estadoSeleccionado = filtroEstado.value;
    const equiposFiltrados = listaEquipos.filter(equipo => {
        const coincideTexto = equipo.titular.toLocaleLowerCase('es').includes(termino) ||
            equipo.marca.toLocaleLowerCase('es').includes(termino);
        return coincideTexto && (!estadoSeleccionado || equipo.estado === estadoSeleccionado);
    });
    actualizarContadores();
    if (equiposFiltrados.length === 0) {
        tablaBody.innerHTML = '<tr><td colspan="10" class="no-data">No se encontraron equipos registrados.</td></tr>';
        return;
    }
    equiposFiltrados.forEach(equipo => {
        const fila = document.createElement('tr');
        [equipo.tipo, equipo.titular, equipo.marca, equipo.procesador, equipo.ram,
            equipo.almacenamiento, equipo.placaVideo, equipo.pulgadas, equipo.estado].forEach(valor => {
            const celda = document.createElement('td');
            celda.textContent = valor;
            fila.appendChild(celda);
        });
        const acciones = document.createElement('td');
        const editar = document.createElement('button');
        editar.className = 'btn btn-warning';
        editar.textContent = 'Editar';
        editar.addEventListener('click', () => cargarEquipoParaEditar(equipo.id));
        const eliminar = document.createElement('button');
        eliminar.className = 'btn btn-danger';
        eliminar.textContent = 'Eliminar';
        eliminar.addEventListener('click', () => eliminarEquipo(equipo.id));
        acciones.append(editar, eliminar);
        fila.appendChild(acciones);
        tablaBody.appendChild(fila);
    });
}

function actualizarContadores() {
    document.getElementById('contador-total').textContent = listaEquipos.length;
    document.getElementById('contador-operativo').textContent = listaEquipos.filter(e => e.estado === 'Operativo').length;
    document.getElementById('contador-reparacion').textContent = listaEquipos.filter(e => e.estado === 'En reparación').length;
    document.getElementById('contador-descartado').textContent = listaEquipos.filter(e => e.estado === 'Descartado').length;
}

function cargarEquipoParaEditar(id) {
    const equipo = listaEquipos.find(item => item.id === id);
    if (!equipo) return;
    idEquipoEdicion = equipo.id;
    inputTipo.value = equipo.tipo;
    inputTitular.value = equipo.titular;
    inputMarca.value = equipo.marca;
    inputProcesador.value = equipo.procesador;
    inputRam.value = equipo.ram;
    inputAlmacenamiento.value = equipo.almacenamiento;
    inputPlacaVideo.value = equipo.placaVideo;
    inputPulgadas.value = equipo.pulgadas;
    inputEstado.value = equipo.estado;
    tituloFormulario.textContent = 'Editar Equipo';
    btnGuardar.textContent = 'Guardar Cambios';
    btnCancelar.classList.remove('hidden');
    formulario.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

function eliminarEquipo(id) {
    if (!confirm('¿Está seguro de que desea eliminar este registro?')) return;
    listaEquipos = listaEquipos.filter(equipo => equipo.id !== id);
    if (idEquipoEdicion === id) resetearFormulario();
    guardarEnAlmacenamiento();
    renderizarTabla();
}

function resetearFormulario() {
    formulario.reset();
    idEquipoEdicion = null;
    tituloFormulario.textContent = 'Registrar Nuevo Equipo';
    btnGuardar.textContent = 'Guardar Equipo';
    btnCancelar.classList.add('hidden');
}

function exportarJSON() {
    const contenido = JSON.stringify(listaEquipos, null, 2);
    const archivo = new Blob([contenido], { type: 'application/json' });
    const enlace = document.createElement('a');
    enlace.href = URL.createObjectURL(archivo);
    enlace.download = 'equipos-informaticos.json';
    enlace.click();
    URL.revokeObjectURL(enlace.href);
}

async function importarJSON(evento) {
    const archivo = evento.target.files[0];
    if (!archivo) return;
    try {
        const datos = JSON.parse(await archivo.text());
        if (!Array.isArray(datos)) throw new Error('El archivo debe contener una lista JSON de equipos.');
        const equiposImportados = datos.map(normalizarEquipo);
        if (equiposImportados.some(equipo => equipo === null)) {
            throw new Error('Uno o más registros no tienen el formato esperado. No se modificaron los datos actuales.');
        }
        if (!confirm(`Se cargarán ${equiposImportados.length} equipos y se reemplazará la lista actual. ¿Continuar?`)) return;
        listaEquipos = equiposImportados;
        guardarEnAlmacenamiento();
        resetearFormulario();
        renderizarTabla();
        alert(`Se importaron ${listaEquipos.length} equipos correctamente.`);
    } catch (error) {
        alert(`No se pudo importar el archivo: ${error.message}`);
    } finally {
        archivoJson.value = '';
    }
}

renderizarTabla();