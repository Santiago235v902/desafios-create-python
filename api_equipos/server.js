/*
====================================================
 SISTEMA DE GESTIÓN DE EQUIPOS INFORMÁTICOS
 Backend: Node.js + Express + PostgreSQL

 Funciones:
 GET    - Consultar equipos
 POST   - Registrar equipos
 PUT    - Modificar equipos
 DELETE - Eliminar equipos

 También permite visualizar el frontend HTML,
 CSS y JavaScript desde la carpeta "public".
====================================================
*/


// -------------------------------------------------
// 1. CARGAR VARIABLES DE ENTORNO
// -------------------------------------------------

// Lee los datos de configuración guardados en .env.
// Allí se encuentra la contraseña de PostgreSQL.

require("dotenv").config();


// -------------------------------------------------
// 2. IMPORTAR BIBLIOTECAS
// -------------------------------------------------

// Express permite crear nuestro servidor web.
const express = require("express");

// Pool permite conectarnos a PostgreSQL.
const { Pool } = require("pg");

// Path permite trabajar con rutas de carpetas.
const path = require("path");

// Creamos la aplicación Express.
const app = express();


// -------------------------------------------------
// 3. CONFIGURAR EXPRESS
// -------------------------------------------------

// Permite recibir información en formato JSON.
// Es necesario para POST y PUT.

app.use(express.json());

// Permite mostrar los archivos HTML, CSS y JS
// que se encuentran dentro de la carpeta public.

app.use(express.static(path.join(__dirname, "public")));


// -------------------------------------------------
// 4. CONEXIÓN CON POSTGRESQL
// -------------------------------------------------

// Creamos un conjunto de conexiones a PostgreSQL.
// Los datos se obtienen del archivo .env.

const db = new Pool({

    // Dirección del servidor PostgreSQL.
    host: process.env.DB_HOST,

    // Puerto utilizado por PostgreSQL.
    port: Number(process.env.DB_PORT),

    // Usuario de PostgreSQL.
    user: process.env.DB_USER,

    // Contraseña del usuario.
    password: process.env.DB_PASSWORD,

    // Nombre de la base de datos.
    database: process.env.DB_NAME

});


// -------------------------------------------------
// 5. GET - CONSULTAR EQUIPOS (READ)
// -------------------------------------------------

// Cuando recibimos una solicitud GET en /equipos,
// consultamos todos los registros de PostgreSQL.

app.get("/equipos", async (req, res) => {

    try {

        // Ejecutamos una consulta SQL.
        // SELECT obtiene los registros de la tabla.
        // ORDER BY id los ordena por identificador.

        const datos = await db.query(
            "SELECT * FROM equipos ORDER BY id"
        );

        // Enviamos los registros al frontend
        // en formato JSON.

        res.status(200).json(datos.rows);

    } catch (error) {

        // Mostramos el error en la terminal.
        console.error("Error en GET:", error.message);

        // Informamos al frontend que ocurrió un error.
        res.status(500).json({
            error: "No se pudieron consultar equipos"
        });

    }

});


// -------------------------------------------------
// 6. POST - REGISTRAR EQUIPOS (CREATE)
// -------------------------------------------------

// Recibe los datos enviados desde el formulario
// y los almacena en PostgreSQL.

app.post("/equipos", async (req, res) => {

    // Obtenemos los datos enviados en el JSON.
    // Si no hay cuerpo, utilizamos un objeto vacío.

    const { titular, marca, estado } = req.body || {};

    // Comprobamos que los campos tengan información.

    if (!titular || !marca || !estado) {

        return res.status(400).json({
            error: "Faltan datos obligatorios"
        });

    }

    try {

        // INSERT INTO agrega un registro.
        // $1, $2 y $3 representan los valores.
        // RETURNING devuelve el equipo registrado.

        const sql = `
            INSERT INTO equipos (titular, marca, estado)
            VALUES ($1, $2, $3)
            RETURNING *
        `;

        // Ejecutamos la consulta enviando los valores.

        const datos = await db.query(sql, [
            titular,
            marca,
            estado
        ]);

        // Devolvemos el registro creado.
        // El estado HTTP 201 significa "Creado".

        res.status(201).json(datos.rows[0]);

    } catch (error) {

        console.error("Error en POST:", error.message);

        res.status(500).json({
            error: "No se pudo crear el equipo"
        });

    }

});


// -------------------------------------------------
// 7. PUT - MODIFICAR EQUIPOS (UPDATE)
// -------------------------------------------------

// Permite modificar un equipo existente.
// El ID se obtiene desde la dirección de la API.
// Ejemplo: PUT /equipos/1

app.put("/equipos/:id", async (req, res) => {

    // Obtenemos el identificador desde la URL.
    const id = Number(req.params.id);

    // Obtenemos los nuevos datos enviados.
    const { titular, marca, estado } = req.body || {};

    // Verificamos el ID y los campos obligatorios.

    if (
        !Number.isInteger(id) ||
        id <= 0 ||
        !titular ||
        !marca ||
        !estado
    ) {

        return res.status(400).json({
            error: "ID o datos inválidos"
        });

    }

    try {

        // UPDATE modifica los datos existentes.
        // WHERE indica qué registro modificar.
        // RETURNING devuelve el equipo actualizado.

        const sql = `
            UPDATE equipos
            SET titular = $1,
                marca = $2,
                estado = $3
            WHERE id = $4
            RETURNING *
        `;

        const datos = await db.query(sql, [
            titular,
            marca,
            estado,
            id
        ]);

        // Si no existe el equipo, informamos el error.

        if (datos.rows.length === 0) {

            return res.status(404).json({
                error: "Equipo no encontrado"
            });

        }

        // Enviamos el equipo actualizado.
        res.status(200).json(datos.rows[0]);

    } catch (error) {

        console.error("Error en PUT:", error.message);

        res.status(500).json({
            error: "No se pudo modificar el equipo"
        });

    }

});


// -------------------------------------------------
// 8. DELETE - ELIMINAR EQUIPOS (DELETE)
// -------------------------------------------------

// Permite eliminar un equipo utilizando su ID.
// Ejemplo: DELETE /equipos/1

app.delete("/equipos/:id", async (req, res) => {

    // Obtenemos el ID desde la URL.
    const id = Number(req.params.id);

    // Comprobamos que sea un número válido.

    if (!Number.isInteger(id) || id <= 0) {

        return res.status(400).json({
            error: "ID inválido"
        });

    }

    try {

        // DELETE elimina un registro.
        // WHERE determina cuál se elimina.
        // RETURNING devuelve el registro eliminado.

        const datos = await db.query(
            "DELETE FROM equipos WHERE id = $1 RETURNING *",
            [id]
        );

        // Comprobamos si el equipo existía.

        if (datos.rows.length === 0) {

            return res.status(404).json({
                error: "Equipo no encontrado"
            });

        }

        // Informamos que el equipo fue eliminado.

        res.status(200).json({
            mensaje: "Equipo eliminado",
            equipo: datos.rows[0]
        });

    } catch (error) {

        console.error("Error en DELETE:", error.message);

        res.status(500).json({
            error: "No se pudo eliminar el equipo"
        });

    }

});


// -------------------------------------------------
// 9. INICIAR EL SERVIDOR
// -------------------------------------------------

// Obtenemos el puerto indicado en .env.
// Si no está definido, utilizamos el 3000.

const puerto = Number(process.env.PORT) || 3000;

// Iniciamos el servidor web.

app.listen(puerto, () => {

    console.log("Servidor iniciado correctamente");

    console.log(
        `Formulario: http://localhost:${puerto}`
    );

    console.log(
        `API REST: http://localhost:${puerto}/equipos`
    );

});