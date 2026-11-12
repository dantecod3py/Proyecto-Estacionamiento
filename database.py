import sqlite3
from sqlite3 import Error

DB_NAME = "gestion_estacionamiento.db"


def get_connection():
    """Establece y retorna la conexion con la base de datos SQLite."""
    try:
        conn = sqlite3.connect(DB_NAME)
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn
    except Error as e:
        print(f"Error de conexion con SQLite: {e}")
        return None


def init_db():
    """Crea e inicializa todas las tablas de la base de datos si no existen."""
    tables_sql = [
        """
        CREATE TABLE IF NOT EXISTS Usuario (
            Id_Usuario INTEGER PRIMARY KEY AUTOINCREMENT,
            Username TEXT NOT NULL UNIQUE,
            Rol TEXT NOT NULL
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS Cliente (
            Id_Cliente INTEGER PRIMARY KEY AUTOINCREMENT,
            Nombres TEXT NOT NULL,
            Apellidos TEXT NOT NULL,
            Ci TEXT NOT NULL UNIQUE,
            Telefono TEXT,
            Correo TEXT UNIQUE
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS Tipo_Vehiculos (
            Id_Tipo_Vehiculos INTEGER PRIMARY KEY AUTOINCREMENT,
            Nombre TEXT NOT NULL,
            Observacion TEXT
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS Tarifa (
            Id_Tarifa INTEGER PRIMARY KEY AUTOINCREMENT,
            Precio REAL NOT NULL,
            Tipo_Cobro TEXT NOT NULL,
            Descripcion TEXT
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS Tarifa_Tipo_Vehiculo (
            Id_Tarifa_Tipo_Vehiculo INTEGER PRIMARY KEY AUTOINCREMENT,
            Id_Tarifa INTEGER NOT NULL,
            Id_Tipo_Vehiculos INTEGER NOT NULL,
            FOREIGN KEY (Id_Tarifa) REFERENCES Tarifa(Id_Tarifa) ON DELETE RESTRICT ON UPDATE CASCADE,
            FOREIGN KEY (Id_Tipo_Vehiculos) REFERENCES Tipo_Vehiculos(Id_Tipo_Vehiculos) ON DELETE RESTRICT ON UPDATE CASCADE,
            UNIQUE (Id_Tarifa, Id_Tipo_Vehiculos)
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS Vehiculo (
            Id_Vehiculo INTEGER PRIMARY KEY AUTOINCREMENT,
            Matricula TEXT NOT NULL UNIQUE,
            Marca TEXT,
            Modelo TEXT,
            Anio INTEGER,
            Color TEXT,
            Id_Cliente INTEGER NOT NULL,
            Id_Tipo_Vehiculos INTEGER NOT NULL,
            FOREIGN KEY (Id_Cliente) REFERENCES Cliente(Id_Cliente) ON DELETE CASCADE ON UPDATE CASCADE,
            FOREIGN KEY (Id_Tipo_Vehiculos) REFERENCES Tipo_Vehiculos(Id_Tipo_Vehiculos) ON DELETE RESTRICT ON UPDATE CASCADE
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS Lugares (
            Id_Lugares INTEGER PRIMARY KEY AUTOINCREMENT,
            Cod_Espacio TEXT NOT NULL UNIQUE,
            Estado TEXT NOT NULL DEFAULT 'Disponible',
            Observacion TEXT
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS Reservas (
            Id_Reservas INTEGER PRIMARY KEY AUTOINCREMENT,
            Fecha_reserva DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            Fecha_Inicio DATETIME NOT NULL,
            Fecha_Fin DATETIME NOT NULL,
            Estado TEXT NOT NULL DEFAULT 'Pendiente',
            Id_Lugares INTEGER NOT NULL,
            Id_Cliente INTEGER NOT NULL,
            FOREIGN KEY (Id_Lugares) REFERENCES Lugares(Id_Lugares) ON DELETE RESTRICT ON UPDATE CASCADE,
            FOREIGN KEY (Id_Cliente) REFERENCES Cliente(Id_Cliente) ON DELETE CASCADE ON UPDATE CASCADE
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS Pago (
            Id_Pago INTEGER PRIMARY KEY AUTOINCREMENT,
            Estado TEXT NOT NULL DEFAULT 'Completado',
            Monto_Total REAL NOT NULL,
            Metodo_Pago TEXT NOT NULL,
            Fecha_Pago DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS Ticket (
            Id_Ticket INTEGER PRIMARY KEY AUTOINCREMENT,
            Fecha_Ingreso DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            Fecha_Salida DATETIME,
            Estado TEXT NOT NULL DEFAULT 'Activo',
            Id_Usuario INTEGER NOT NULL,
            Id_Vehiculo INTEGER NOT NULL,
            Id_Lugares INTEGER NOT NULL,
            Id_Tarifa_Tipo_Vehiculo INTEGER NOT NULL,
            Id_Pago INTEGER,
            Id_Reservas INTEGER,
            FOREIGN KEY (Id_Usuario) REFERENCES Usuario(Id_Usuario) ON DELETE RESTRICT ON UPDATE CASCADE,
            FOREIGN KEY (Id_Vehiculo) REFERENCES Vehiculo(Id_Vehiculo) ON DELETE RESTRICT ON UPDATE CASCADE,
            FOREIGN KEY (Id_Lugares) REFERENCES Lugares(Id_Lugares) ON DELETE RESTRICT ON UPDATE CASCADE,
            FOREIGN KEY (Id_Tarifa_Tipo_Vehiculo) REFERENCES Tarifa_Tipo_Vehiculo(Id_Tarifa_Tipo_Vehiculo) ON DELETE RESTRICT ON UPDATE CASCADE,
            FOREIGN KEY (Id_Pago) REFERENCES Pago(Id_Pago) ON DELETE SET NULL ON UPDATE CASCADE,
            FOREIGN KEY (Id_Reservas) REFERENCES Reservas(Id_Reservas) ON DELETE SET NULL ON UPDATE CASCADE
        );
        """
    ]

    conn = get_connection()
    if conn:
        cursor = conn.cursor()
        for statement in tables_sql:
            cursor.execute(statement)

        # Poblar lugares por defecto si la tabla esta vacia
        cursor.execute("SELECT COUNT(*) FROM Lugares;")
        if cursor.fetchone()[0] == 0:
            lugares_iniciales = [
                ('A-01', 'Disponible', 'Planta Baja - Cerca a salida'),
                ('A-02', 'Disponible', 'Planta Baja'),
                ('A-03', 'Ocupado', 'Planta Baja'),
                ('B-01', 'Disponible', 'Primer Piso'),
                ('B-02', 'Disponible', 'Primer Piso')
            ]
            cursor.executemany(
                "INSERT INTO Lugares (Cod_Espacio, Estado, Observacion) VALUES (?, ?, ?);",
                lugares_iniciales
            )

        # Poblar usuario admin por defecto
        cursor.execute("SELECT COUNT(*) FROM Usuario;")
        if cursor.fetchone()[0] == 0:
            cursor.execute("INSERT INTO Usuario (Username, Rol) VALUES ('admin', 'Administrador');")

        conn.commit()
        conn.close()