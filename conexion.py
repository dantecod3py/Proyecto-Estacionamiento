import sqlite3

def conectar():
    conexion = sqlite3.connect("gestion_alquileres.db")
    conexion.execute("PRAGMA foreign_keys = ON;")
    return conexion #Hola
    