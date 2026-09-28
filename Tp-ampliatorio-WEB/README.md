# Sistema de Gestión de Equipos Informáticos

**Espacio Curricular:** Web  
**Curso:** 4° 3°  
**Profesor:** Cristian Carrió

Aplicación web para administrar equipos informáticos con HTML, CSS y JavaScript sin frameworks.

## Funcionalidades

- Alta, consulta, edición y eliminación de equipos.
- Búsqueda en tiempo real por titular o marca.
- Filtro por estado: Operativo, En reparación o Descartado.
- Contadores del total y de equipos por estado.
- Guardado automático en `localStorage`; los registros permanecen al recargar la página en el mismo navegador.
- Exportación de todos los registros a `equipos-informaticos.json`.
- Importación de una lista JSON con confirmación antes de reemplazar los registros actuales.

## Archivos

- `index.html`: estructura de la aplicación, formulario, indicadores y tabla.
- `style.css`: diseño visual y adaptación a pantallas pequeñas.
- `script.js`: operaciones CRUD, búsqueda, filtro, contadores, importación/exportación y persistencia.

## Uso

Abrí `index.html` en un navegador moderno. Completá el formulario y elegí el estado del equipo para guardarlo. Usá el buscador y el filtro sobre la tabla. Los botones de cada fila permiten editar o eliminar. Exportá los datos para guardar una copia JSON; al importar una lista válida, la aplicación pide confirmación y reemplaza los registros actuales.

Para comprobar la persistencia, agregá un equipo y actualizá la página: el registro debe seguir visible. Los datos se guardan localmente en el navegador y no se sincronizan entre dispositivos.

## Formato JSON

La exportación contiene una lista de objetos. Cada equipo incluye `id`, `tipo`, `titular`, `marca`, `procesador`, `ram`, `almacenamiento`, `placaVideo`, `pulgadas` y `estado`. La importación espera una lista JSON con esos campos de texto; si un registro no es válido, la lista actual no se reemplaza.

## Presentación y publicación

En la defensa, recorré la estructura de archivos, el formulario CRUD, búsqueda, filtro, indicadores, persistencia y los botones JSON. Para publicar: creá o abrí el repositorio en GitHub, agregá los archivos del proyecto, registrá un commit y subí los cambios. Verificá en GitHub que estén visibles `index.html`, `style.css`, `script.js` y este README. Entregá el enlace del repositorio y el enlace del video con acceso habilitado para el docente en la plataforma indicada.
