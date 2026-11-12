PRAGMA foreign_keys = ON;

-- 1. TABLA: Usuario
CREATE TABLE IF NOT EXISTS Usuario (
    Id_Usuario INTEGER PRIMARY KEY AUTOINCREMENT,
    Username TEXT NOT NULL UNIQUE,
    Rol TEXT NOT NULL
);

-- 2. TABLA: Cliente
CREATE TABLE IF NOT EXISTS Cliente (
    Id_Cliente INTEGER PRIMARY KEY AUTOINCREMENT,
    Nombres TEXT NOT NULL,
    Apellidos TEXT NOT NULL,
    Ci TEXT NOT NULL UNIQUE,
    Telefono TEXT,
    Correo TEXT UNIQUE
);

-- 3. TABLA: Tipo_Vehiculos
CREATE TABLE IF NOT EXISTS Tipo_Vehiculos (
    Id_Tipo_Vehiculos INTEGER PRIMARY KEY AUTOINCREMENT,
    Nombre TEXT NOT NULL,
    Observacion TEXT
);

-- 4. TABLA: Tarifa (Tipo_Cobro ej: Por Hora, Por Dia, Tarifa Nocturna)
CREATE TABLE IF NOT EXISTS Tarifa (
    Id_Tarifa INTEGER PRIMARY KEY AUTOINCREMENT,
    Precio REAL NOT NULL,
    Tipo_Cobro TEXT NOT NULL,
    Descripcion TEXT
);

-- 5. TABLA INTERMEDIA: Tarifa_Tipo_Vehiculo (N:M)
CREATE TABLE IF NOT EXISTS Tarifa_Tipo_Vehiculo (
    Id_Tarifa_Tipo_Vehiculo INTEGER PRIMARY KEY AUTOINCREMENT,
    Id_Tarifa INTEGER NOT NULL,
    Id_Tipo_Vehiculos INTEGER NOT NULL,
    FOREIGN KEY (Id_Tarifa) REFERENCES Tarifa(Id_Tarifa) ON DELETE RESTRICT ON UPDATE CASCADE,
    FOREIGN KEY (Id_Tipo_Vehiculos) REFERENCES Tipo_Vehiculos(Id_Tipo_Vehiculos) ON DELETE RESTRICT ON UPDATE CASCADE,
    UNIQUE (Id_Tarifa, Id_Tipo_Vehiculos)
);

-- 6. TABLA: Vehiculo
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

-- 7. TABLA: Lugares
CREATE TABLE IF NOT EXISTS Lugares (
    Id_Lugares INTEGER PRIMARY KEY AUTOINCREMENT,
    Cod_Espacio TEXT NOT NULL UNIQUE,
    Estado TEXT NOT NULL DEFAULT 'Disponible',
    Observacion TEXT
);

-- 8. TABLA: Reservas
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

-- 9. TABLA: Pago
CREATE TABLE IF NOT EXISTS Pago (
    Id_Pago INTEGER PRIMARY KEY AUTOINCREMENT,
    Estado TEXT NOT NULL DEFAULT 'Completado',
    Monto_Total REAL NOT NULL,
    Metodo_Pago TEXT NOT NULL,
    Fecha_Pago DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 10. TABLA: Ticket
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

-- DATOS INICIALES (los mismos que carga database.py)
INSERT OR IGNORE INTO Lugares (Cod_Espacio, Estado, Observacion) VALUES
    ('A-01', 'Disponible', 'Planta Baja - Cerca a salida'),
    ('A-02', 'Disponible', 'Planta Baja'),
    ('A-03', 'Ocupado', 'Planta Baja'),
    ('B-01', 'Disponible', 'Primer Piso'),
    ('B-02', 'Disponible', 'Primer Piso');

INSERT OR IGNORE INTO Usuario (Username, Rol) VALUES ('admin', 'Administrador');
