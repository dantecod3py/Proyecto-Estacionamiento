import sqlite3
from datetime import datetime
from tkinter import ttk, messagebox

import customtkinter as ctk

from database import get_connection, init_db

# ==========================================================
# CONFIGURACIÓN GENERAL
# ==========================================================

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

MONEDA = "G"  # Cambiá a "G." si querés mostrar guaraníes

# Mismas tarifas que en pagos.py
TARIFAS_BASE = {"hora": 10.000, "dia": 50.000, "mes": 300.000}
METODOS_PAGO = ["Efectivo", "Tarjeta", "Transferencia", "QR"]
TIPOS_RESERVA = ["hora", "dia", "mes"]
ESTADOS_RESERVA = ["Pendiente", "Activa", "Finalizada", "Cancelada"]
FORMATO_FECHA = "%Y-%m-%d %H:%M"


def factor_categoria(nombre):
    """Multiplicador de tarifa según la categoría del vehículo (igual que pagos.py)."""
    exactos = {
        "Motocicleta": 0.8,
        "Automóvil": 1.0,
        "Camioneta / SUV": 1.3,
        "Camión / Autobús": 1.8,
    }
    if nombre in exactos:
        return exactos[nombre]
    n = nombre.lower()
    if "moto" in n:
        return 0.8
    if "camioneta" in n or "suv" in n:
        return 1.3
    if "cami" in n or "bus" in n:
        return 1.8
    return 1.0


# ==========================================================
# ACCESO A LA BASE DE DATOS
# ==========================================================

def consultar(sql, params=()):
    conn = get_connection()
    if conn is None:
        raise RuntimeError("No se pudo conectar con la base de datos.")
    try:
        cur = conn.cursor()
        cur.execute(sql, params)
        return cur.fetchall()
    finally:
        conn.close()


def ejecutar(sql, params=()):
    """Ejecuta INSERT/UPDATE/DELETE. Devuelve (último id, filas afectadas)."""
    conn = get_connection()
    if conn is None:
        raise RuntimeError("No se pudo conectar con la base de datos.")
    try:
        cur = conn.cursor()
        cur.execute(sql, params)
        conn.commit()
        return cur.lastrowid, cur.rowcount
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


# ==========================================================
# REPORTES DE LA SECCIÓN CONSULTAS (JOIN)
# ==========================================================

REPORTES = {
    "Clientes con reservas": (
        """
        SELECT c.Id_Cliente, c.Nombres || ' ' || c.Apellidos, c.Ci,
               r.Id_Reservas, l.Cod_Espacio, r.Fecha_Inicio, r.Fecha_Fin, r.Estado
        FROM Cliente c
        INNER JOIN Reservas r ON c.Id_Cliente = r.Id_Cliente
        INNER JOIN Lugares l ON r.Id_Lugares = l.Id_Lugares
        """,
        [("id", "ID", 50), ("cliente", "Cliente", 190), ("ci", "C.I.", 100),
         ("reserva", "N° Reserva", 90), ("espacio", "Espacio", 90),
         ("inicio", "Desde", 140), ("fin", "Hasta", 140), ("estado", "Estado", 100)],
    ),
    "Vehículos con categoría y propietario": (
        """
        SELECT v.Id_Vehiculo, v.Matricula, v.Marca, v.Modelo, v.Color,
               tv.Nombre, c.Nombres || ' ' || c.Apellidos
        FROM Vehiculo v
        INNER JOIN Tipo_Vehiculos tv ON v.Id_Tipo_Vehiculos = tv.Id_Tipo_Vehiculos
        INNER JOIN Cliente c ON v.Id_Cliente = c.Id_Cliente
        """,
        [("id", "ID", 50), ("matricula", "Matrícula", 110), ("marca", "Marca", 120),
         ("modelo", "Modelo", 120), ("color", "Color", 100),
         ("categoria", "Categoría", 150), ("propietario", "Propietario", 200)],
    ),
    "Pagos por cliente": (
        """
        SELECT c.Id_Cliente, c.Nombres || ' ' || c.Apellidos,
               t.Id_Ticket, p.Id_Pago, ROUND(p.Monto_Total, 2), p.Metodo_Pago, p.Fecha_Pago
        FROM Cliente c
        INNER JOIN Vehiculo v ON c.Id_Cliente = v.Id_Cliente
        INNER JOIN Ticket t ON v.Id_Vehiculo = t.Id_Vehiculo
        INNER JOIN Pago p ON t.Id_Pago = p.Id_Pago
        """,
        [("id", "ID", 50), ("cliente", "Cliente", 200), ("ticket", "N° Ticket", 90),
         ("pago", "N° Pago", 90), ("monto", "Monto", 110),
         ("metodo", "Método", 120), ("fecha", "Fecha", 160)],
    ),
}


# ==========================================================
# APLICACIÓN
# ==========================================================

class Aplicacion(ctk.CTk):

    def __init__(self):
        super().__init__()

        self.title("SISTEMA DE GESTIÓN DE ESTACIONAMIENTO")
        self.geometry("1250x780")
        self.minsize(1100, 650)

        self.color_fondo = "#F4F6F9"
        self.color_menu = "#172B4D"
        self.color_titulo = "#172B4D"
        self.color_primario = "#087E8B"
        self.color_verde = "#198754"
        self.color_rojo = "#DC3545"
        self.color_naranja = "#F39C12"

        self.botones_estilo = {
            "verde": (self.color_verde, "#146C43"),
            "azul": (self.color_primario, "#06616B"),
            "rojo": (self.color_rojo, "#A52834"),
            "gris": ("#6C757D", "#565E64"),
            "naranja": (self.color_naranja, "#C77C00"),
        }

        self.configure(fg_color=self.color_fondo)

        self.id_cliente_sel = None
        self.id_categoria_sel = None
        self.id_lugar_sel = None

        self.estilo_tablas()
        self.crear_interfaz()
        self.mostrar_inicio()

    # ======================================================
    # ESTRUCTURA PRINCIPAL
    # ======================================================

    def estilo_tablas(self):
        estilo = ttk.Style()
        estilo.theme_use("clam")
        estilo.configure("Treeview", background="white", foreground="#333333",
                         rowheight=32, fieldbackground="white", font=("Arial", 10))
        estilo.configure("Treeview.Heading", background="#172B4D", foreground="white",
                         font=("Arial", 10, "bold"), padding=8)
        estilo.map("Treeview", background=[("selected", "#087E8B")],
                   foreground=[("selected", "white")])

    def crear_interfaz(self):
        self.menu_lateral = ctk.CTkFrame(self, width=230, corner_radius=0,
                                         fg_color=self.color_menu)
        self.menu_lateral.pack(side="left", fill="y")
        self.menu_lateral.pack_propagate(False)

        ctk.CTkLabel(self.menu_lateral, text="ESTACIONAMIENTO\nINTEGRADO",
                     font=("Arial", 22, "bold"), text_color="white"
                     ).pack(pady=(35, 35))

        opciones = [
            ("Inicio", self.mostrar_inicio),
            ("Clientes", self.mostrar_clientes),
            ("Categorías", self.mostrar_categorias),
            ("Lugares", self.mostrar_lugares),
            ("Reservas", self.mostrar_reservas),
            ("Pagos", self.mostrar_pagos),
            ("Consultas", self.mostrar_consultas),
        ]
        for texto, comando in opciones:
            ctk.CTkButton(self.menu_lateral, text=texto, height=42, corner_radius=8,
                          anchor="w", fg_color="transparent", hover_color="#29466E",
                          text_color="white", font=("Arial", 14), command=comando
                          ).pack(fill="x", padx=15, pady=4)

        ctk.CTkButton(self.menu_lateral, text="Cerrar sistema", height=42,
                      fg_color="#B02A37", hover_color="#842029", text_color="white",
                      command=self.destroy).pack(side="bottom", fill="x", padx=15, pady=25)

        self.contenido = ctk.CTkFrame(self, fg_color=self.color_fondo, corner_radius=0)
        self.contenido.pack(side="right", fill="both", expand=True)

    def limpiar_contenido(self):
        for widget in self.contenido.winfo_children():
            widget.destroy()

    # ======================================================
    # AYUDANTES DE INTERFAZ
    # ======================================================

    def encabezado(self, texto):
        """Título de la sección. Devuelve la etiqueta de la derecha (totales)."""
        fila = ctk.CTkFrame(self.contenido, fg_color="transparent")
        fila.pack(fill="x", padx=25, pady=(20, 10))
        ctk.CTkLabel(fila, text=texto, font=("Arial", 26, "bold"),
                     text_color=self.color_titulo).pack(side="left")
        etiqueta = ctk.CTkLabel(fila, text="", font=("Arial", 14, "bold"),
                                text_color=self.color_primario)
        etiqueta.pack(side="right")
        return etiqueta

    def tarjeta(self):
        return ctk.CTkFrame(self.contenido, fg_color="white", corner_radius=12)

    def subtitulo(self, padre, texto):
        return ctk.CTkLabel(padre, text=texto, font=("Arial", 17, "bold"),
                            text_color=self.color_titulo)

    def campo(self, padre, titulo, fila, columna, ancho=380):
        ctk.CTkLabel(padre, text=titulo, font=("Arial", 13, "bold"),
                     text_color="#333333").grid(row=fila * 2, column=columna,
                                                sticky="w", padx=20, pady=(5, 3))
        entrada = ctk.CTkEntry(padre, width=ancho, height=38, placeholder_text=titulo)
        entrada.grid(row=fila * 2 + 1, column=columna, sticky="w", padx=20, pady=(0, 5))
        return entrada

    def etiqueta_combo(self, padre, titulo, fila, columna, valores, ancho=380):
        ctk.CTkLabel(padre, text=titulo, font=("Arial", 13, "bold"),
                     text_color="#333333").grid(row=fila * 2, column=columna,
                                                sticky="w", padx=20, pady=(5, 3))
        combo = ctk.CTkComboBox(padre, width=ancho, height=38, values=valores,
                                state="readonly")
        combo.grid(row=fila * 2 + 1, column=columna, sticky="w", padx=20, pady=(0, 5))
        return combo

    def fila_botones(self, padre, acciones):
        marco = ctk.CTkFrame(padre, fg_color="transparent")
        for texto, estilo, comando in acciones:
            color, hover = self.botones_estilo[estilo]
            ctk.CTkButton(marco, text=texto, width=115, height=38, fg_color=color,
                          hover_color=hover, command=comando).pack(side="left", padx=5)
        return marco

    def barra_busqueda(self, placeholder, comando):
        marco = ctk.CTkFrame(self.contenido, fg_color="transparent")
        marco.pack(fill="x", padx=25, pady=(15, 5))
        entrada = ctk.CTkEntry(marco, placeholder_text=placeholder, width=400, height=38)
        entrada.pack(side="left", padx=(0, 10))
        entrada.bind("<KeyRelease>", lambda e: comando())

        def mostrar_todos():
            entrada.delete(0, "end")
            comando()

        ctk.CTkButton(marco, text="Buscar", width=100, height=38,
                      command=comando).pack(side="left", padx=5)
        ctk.CTkButton(marco, text="Mostrar todos", width=120, height=38,
                      fg_color="#6C757D", hover_color="#565E64",
                      command=mostrar_todos).pack(side="left", padx=5)
        return entrada

    def crear_tabla(self, padre, columnas):
        """columnas: lista de (id, título, ancho)."""
        ids = [c[0] for c in columnas]
        tabla = ttk.Treeview(padre, columns=ids, show="headings")
        for cid, titulo, ancho in columnas:
            tabla.heading(cid, text=titulo)
            tabla.column(cid, width=ancho, anchor="center")
        scroll = ttk.Scrollbar(padre, orient="vertical", command=tabla.yview)
        tabla.configure(yscrollcommand=scroll.set)
        tabla.pack(side="left", fill="both", expand=True, padx=(10, 0), pady=10)
        scroll.pack(side="right", fill="y", padx=(0, 10), pady=10)
        return tabla

    @staticmethod
    def vaciar_tabla(tabla):
        for item in tabla.get_children():
            tabla.delete(item)

    @staticmethod
    def llenar(entradas, valores):
        for entrada, valor in zip(entradas, valores):
            entrada.delete(0, "end")
            if valor is not None:
                entrada.insert(0, str(valor))

    @staticmethod
    def sin_none(fila):
        return tuple("" if v is None else v for v in fila)

    def error(self, titulo, mensaje, error):
        messagebox.showerror(titulo, f"{mensaje}\n{error}")

    # ======================================================
    # INICIO
    # ======================================================

    def mostrar_inicio(self):
        self.limpiar_contenido()

        ctk.CTkLabel(self.contenido, text="Panel principal", font=("Arial", 28, "bold"),
                     text_color=self.color_titulo).pack(anchor="w", padx=35, pady=(35, 10))
        ctk.CTkLabel(self.contenido,
                     text="Sistema integrado de gestión de estacionamiento",
                     font=("Arial", 15), text_color="#666666"
                     ).pack(anchor="w", padx=35, pady=(0, 25))

        clientes = categorias = disponibles = total_lugares = 0
        recaudado = 0.0
        try:
            clientes = consultar("SELECT COUNT(*) FROM Cliente")[0][0]
            categorias = consultar("SELECT COUNT(*) FROM Tipo_Vehiculos")[0][0]
            lug = consultar("SELECT SUM(CASE WHEN Estado='Disponible' THEN 1 ELSE 0 END), "
                            "COUNT(*) FROM Lugares")[0]
            disponibles, total_lugares = lug[0] or 0, lug[1] or 0
            recaudado = consultar("SELECT COALESCE(SUM(Monto_Total),0) FROM Pago "
                                  "WHERE Estado='Completado'")[0][0]
        except Exception as e:
            self.error("Error", "No se pudieron cargar los datos del panel:", e)

        datos = [
            ("CLIENTES", f"{clientes} registrados", self.color_primario),
            ("CATEGORÍAS", f"{categorias} tipos de vehículo", "#198754"),
            ("LUGARES", f"{disponibles} libres de {total_lugares}", "#F39C12"),
            ("PAGOS", f"{MONEDA} {recaudado:,.3f} recaudados", "#6F42C1"),
        ]

        tarjetas = ctk.CTkFrame(self.contenido, fg_color="transparent")
        tarjetas.pack(fill="x", padx=25, pady=15)
        for titulo, subtitulo, color in datos:
            tarjeta = ctk.CTkFrame(tarjetas, fg_color="white", corner_radius=12,
                                   border_width=1, border_color="#E1E5EA")
            tarjeta.pack(side="left", fill="both", expand=True, padx=8, pady=8)
            ctk.CTkLabel(tarjeta, text=titulo, font=("Arial", 19, "bold"),
                         text_color=color).pack(pady=(25, 8))
            ctk.CTkLabel(tarjeta, text=subtitulo, font=("Arial", 13),
                         text_color="#666666").pack(pady=(0, 25))

        ctk.CTkLabel(self.contenido, text="Bienvenido al sistema de estacionamiento",
                     font=("Arial", 20, "bold"), text_color=self.color_titulo
                     ).pack(pady=60)

    # ======================================================
    # MÓDULO CLIENTES
    # ======================================================

    def mostrar_clientes(self):
        self.limpiar_contenido()
        self.id_cliente_sel = None
        self.lbl_total_clientes = self.encabezado("GESTIÓN DE CLIENTES")

        formulario = self.tarjeta()
        formulario.pack(fill="x", padx=25, pady=10)
        self.subtitulo(formulario, "DATOS DEL CLIENTE").grid(
            row=0, column=0, columnspan=2, sticky="w", padx=20, pady=(15, 10))

        self.e_cli_nombres = self.campo(formulario, "Nombres", 1, 0)
        self.e_cli_apellidos = self.campo(formulario, "Apellidos", 1, 1)
        self.e_cli_ci = self.campo(formulario, "C.I.", 2, 0)
        self.e_cli_telefono = self.campo(formulario, "Teléfono", 2, 1)
        self.e_cli_correo = self.campo(formulario, "Correo electrónico", 3, 0)

        self.fila_botones(formulario, [
            ("Registrar", "verde", self.registrar_cliente),
            ("Modificar", "azul", self.modificar_cliente),
            ("Eliminar", "rojo", self.eliminar_cliente),
            ("Limpiar", "gris", self.limpiar_form_cliente),
        ]).grid(row=8, column=0, columnspan=2, sticky="e", padx=20, pady=(10, 20))

        self.e_busq_cliente = self.barra_busqueda(
            "Buscar por nombre, apellido o C.I...", self.listar_clientes)

        marco = self.tarjeta()
        marco.pack(fill="both", expand=True, padx=25, pady=(5, 20))
        self.tabla_clientes = self.crear_tabla(marco, [
            ("id", "ID", 50), ("nombres", "Nombres", 150), ("apellidos", "Apellidos", 150),
            ("ci", "C.I.", 110), ("telefono", "Teléfono", 120), ("correo", "Correo", 220)])
        self.tabla_clientes.bind("<<TreeviewSelect>>", self.seleccionar_cliente)

        self.listar_clientes()

    def datos_form_cliente(self):
        nombres = self.e_cli_nombres.get().strip()
        apellidos = self.e_cli_apellidos.get().strip()
        ci = self.e_cli_ci.get().strip()
        telefono = self.e_cli_telefono.get().strip() or None
        correo = self.e_cli_correo.get().strip() or None
        if not nombres or not apellidos or not ci:
            messagebox.showwarning("Datos incompletos",
                                   "Nombres, apellidos y C.I. son obligatorios.")
            return None
        return nombres, apellidos, ci, telefono, correo

    def listar_clientes(self):
        if not hasattr(self, "tabla_clientes"):
            return
        self.vaciar_tabla(self.tabla_clientes)
        try:
            p = f"%{self.e_busq_cliente.get().strip()}%"
            filas = consultar("""
                SELECT Id_Cliente, Nombres, Apellidos, Ci, Telefono, Correo
                FROM Cliente
                WHERE Nombres LIKE ? OR Apellidos LIKE ? OR Ci LIKE ?
                ORDER BY Id_Cliente""", (p, p, p))
            for fila in filas:
                self.tabla_clientes.insert("", "end", values=self.sin_none(fila))
            self.lbl_total_clientes.configure(text=f"Total: {len(filas)} clientes")
        except Exception as e:
            self.error("Error", "No se pudieron listar los clientes:", e)

    def registrar_cliente(self):
        datos = self.datos_form_cliente()
        if not datos:
            return
        try:
            nuevo_id, _ = ejecutar(
                "INSERT INTO Cliente (Nombres, Apellidos, Ci, Telefono, Correo) "
                "VALUES (?, ?, ?, ?, ?)", datos)
            messagebox.showinfo("Registro exitoso",
                                f"Cliente registrado con ID {nuevo_id}.")
            self.limpiar_form_cliente()
            self.listar_clientes()
        except sqlite3.IntegrityError:
            messagebox.showerror("No se pudo registrar",
                                 "Ya existe un cliente con esa C.I. o ese correo.")
        except Exception as e:
            self.error("Error", "No se pudo registrar el cliente:", e)

    def seleccionar_cliente(self, evento=None):
        sel = self.tabla_clientes.selection()
        if not sel:
            return
        self.id_cliente_sel = int(self.tabla_clientes.item(sel[0], "values")[0])
        try:
            fila = consultar("SELECT Nombres, Apellidos, Ci, Telefono, Correo "
                             "FROM Cliente WHERE Id_Cliente = ?", (self.id_cliente_sel,))
            if fila:
                self.llenar([self.e_cli_nombres, self.e_cli_apellidos, self.e_cli_ci,
                             self.e_cli_telefono, self.e_cli_correo], fila[0])
        except Exception as e:
            self.error("Error", "No se pudieron cargar los datos:", e)

    def modificar_cliente(self):
        if self.id_cliente_sel is None:
            messagebox.showwarning("Seleccionar cliente",
                                   "Primero seleccioná un cliente de la tabla.")
            return
        datos = self.datos_form_cliente()
        if not datos:
            return
        if not messagebox.askyesno("Confirmar modificación",
                                   "¿Deseás guardar los cambios del cliente seleccionado?"):
            return
        try:
            _, filas = ejecutar(
                "UPDATE Cliente SET Nombres=?, Apellidos=?, Ci=?, Telefono=?, Correo=? "
                "WHERE Id_Cliente=?", datos + (self.id_cliente_sel,))
            if filas:
                messagebox.showinfo("Modificación exitosa",
                                    "Los datos del cliente fueron actualizados.")
            else:
                messagebox.showwarning("Aviso", "No se encontró el cliente.")
            self.limpiar_form_cliente()
            self.listar_clientes()
        except sqlite3.IntegrityError:
            messagebox.showerror("No se pudo modificar",
                                 "Ya existe otro cliente con esa C.I. o ese correo.")
        except Exception as e:
            self.error("Error", "No se pudo modificar el cliente:", e)

    def eliminar_cliente(self):
        if self.id_cliente_sel is None:
            messagebox.showwarning("Seleccionar cliente",
                                   "Primero seleccioná un cliente de la tabla.")
            return
        if not messagebox.askyesno(
                "Eliminar cliente",
                "¿Estás seguro de eliminar el cliente seleccionado?\n\n"
                "También se eliminarán sus vehículos y reservas.\n"
                "Esta operación no se puede deshacer."):
            return
        try:
            ejecutar("DELETE FROM Cliente WHERE Id_Cliente = ?", (self.id_cliente_sel,))
            messagebox.showinfo("Eliminación exitosa", "El cliente fue eliminado.")
            self.limpiar_form_cliente()
            self.listar_clientes()
        except sqlite3.IntegrityError:
            messagebox.showerror("No se puede eliminar",
                                 "El cliente tiene vehículos con tickets asociados.")
        except Exception as e:
            self.error("Error", "No se pudo eliminar el cliente:", e)

    def limpiar_form_cliente(self):
        for e in (self.e_cli_nombres, self.e_cli_apellidos, self.e_cli_ci,
                  self.e_cli_telefono, self.e_cli_correo):
            e.delete(0, "end")
        self.id_cliente_sel = None
        for item in self.tabla_clientes.selection():
            self.tabla_clientes.selection_remove(item)

    # ======================================================
    # MÓDULO CATEGORÍAS DE VEHÍCULOS
    # ======================================================

    def mostrar_categorias(self):
        self.limpiar_contenido()
        self.id_categoria_sel = None
        self.lbl_total_categorias = self.encabezado("CATEGORÍAS DE VEHÍCULOS")

        formulario = self.tarjeta()
        formulario.pack(fill="x", padx=25, pady=10)
        self.subtitulo(formulario, "DATOS DE LA CATEGORÍA").grid(
            row=0, column=0, columnspan=2, sticky="w", padx=20, pady=(15, 10))

        self.e_cat_nombre = self.campo(formulario, "Nombre de la categoría", 1, 0)
        self.e_cat_obs = self.campo(formulario, "Observación (opcional)", 1, 1)

        self.fila_botones(formulario, [
            ("Registrar", "verde", self.registrar_categoria),
            ("Modificar", "azul", self.modificar_categoria),
            ("Eliminar", "rojo", self.eliminar_categoria),
            ("Limpiar", "gris", self.limpiar_form_categoria),
        ]).grid(row=4, column=0, columnspan=2, sticky="e", padx=20, pady=(10, 20))

        self.e_busq_categoria = self.barra_busqueda(
            "Buscar por ID o nombre de categoría...", self.listar_categorias)

        marco = self.tarjeta()
        marco.pack(fill="both", expand=True, padx=25, pady=(5, 20))
        self.tabla_categorias = self.crear_tabla(marco, [
            ("id", "ID", 60), ("nombre", "Categoría", 260), ("obs", "Observación", 420)])
        self.tabla_categorias.bind("<<TreeviewSelect>>", self.seleccionar_categoria)

        self.listar_categorias()

    def listar_categorias(self):
        if not hasattr(self, "tabla_categorias"):
            return
        self.vaciar_tabla(self.tabla_categorias)
        try:
            dato = self.e_busq_categoria.get().strip()
            filas = consultar("""
                SELECT Id_Tipo_Vehiculos, Nombre, Observacion
                FROM Tipo_Vehiculos
                WHERE CAST(Id_Tipo_Vehiculos AS TEXT) = ? OR Nombre LIKE ?
                ORDER BY Id_Tipo_Vehiculos""", (dato, f"%{dato}%"))
            for fila in filas:
                self.tabla_categorias.insert("", "end", values=self.sin_none(fila))
            self.lbl_total_categorias.configure(text=f"Total: {len(filas)} categorías")
        except Exception as e:
            self.error("Error", "No se pudieron listar las categorías:", e)

    def registrar_categoria(self):
        nombre = self.e_cat_nombre.get().strip()
        obs = self.e_cat_obs.get().strip() or None
        if not nombre:
            messagebox.showwarning("Dato obligatorio",
                                   "El nombre de la categoría es obligatorio.")
            return
        try:
            if consultar("SELECT 1 FROM Tipo_Vehiculos WHERE LOWER(Nombre)=LOWER(?)",
                         (nombre,)):
                messagebox.showwarning("Categoría existente",
                                       "Ya existe una categoría con ese nombre.")
                return
            nuevo_id, _ = ejecutar(
                "INSERT INTO Tipo_Vehiculos (Nombre, Observacion) VALUES (?, ?)",
                (nombre, obs))
            messagebox.showinfo("Registro exitoso",
                                f"Categoría registrada con ID {nuevo_id}.")
            self.limpiar_form_categoria()
            self.listar_categorias()
        except Exception as e:
            self.error("Error", "No se pudo registrar la categoría:", e)

    def seleccionar_categoria(self, evento=None):
        sel = self.tabla_categorias.selection()
        if not sel:
            return
        self.id_categoria_sel = int(self.tabla_categorias.item(sel[0], "values")[0])
        try:
            fila = consultar("SELECT Nombre, Observacion FROM Tipo_Vehiculos "
                             "WHERE Id_Tipo_Vehiculos = ?", (self.id_categoria_sel,))
            if fila:
                self.llenar([self.e_cat_nombre, self.e_cat_obs], fila[0])
        except Exception as e:
            self.error("Error", "No se pudieron cargar los datos:", e)

    def modificar_categoria(self):
        if self.id_categoria_sel is None:
            messagebox.showwarning("Seleccionar categoría",
                                   "Primero seleccioná una categoría de la tabla.")
            return
        nombre = self.e_cat_nombre.get().strip()
        obs = self.e_cat_obs.get().strip() or None
        if not nombre:
            messagebox.showwarning("Dato obligatorio", "El nombre no puede quedar vacío.")
            return
        if not messagebox.askyesno("Confirmar modificación",
                                   "¿Deseás guardar los cambios de la categoría?"):
            return
        try:
            if consultar("SELECT 1 FROM Tipo_Vehiculos WHERE LOWER(Nombre)=LOWER(?) "
                         "AND Id_Tipo_Vehiculos <> ?", (nombre, self.id_categoria_sel)):
                messagebox.showwarning("Categoría existente",
                                       "Ya existe otra categoría con ese nombre.")
                return
            ejecutar("UPDATE Tipo_Vehiculos SET Nombre=?, Observacion=? "
                     "WHERE Id_Tipo_Vehiculos=?", (nombre, obs, self.id_categoria_sel))
            messagebox.showinfo("Modificación exitosa",
                                "La categoría fue modificada correctamente.")
            self.limpiar_form_categoria()
            self.listar_categorias()
        except Exception as e:
            self.error("Error", "No se pudo modificar la categoría:", e)

    def eliminar_categoria(self):
        if self.id_categoria_sel is None:
            messagebox.showwarning("Seleccionar categoría",
                                   "Primero seleccioná una categoría de la tabla.")
            return
        if not messagebox.askyesno(
                "Confirmar eliminación",
                "¿Estás seguro de eliminar la categoría seleccionada?\n\n"
                "Si está en uso por vehículos o tarifas, no se podrá eliminar."):
            return
        try:
            ejecutar("DELETE FROM Tipo_Vehiculos WHERE Id_Tipo_Vehiculos = ?",
                     (self.id_categoria_sel,))
            messagebox.showinfo("Eliminación exitosa", "La categoría fue eliminada.")
            self.limpiar_form_categoria()
            self.listar_categorias()
        except sqlite3.IntegrityError:
            messagebox.showerror("No se puede eliminar",
                                 "Esta categoría está en uso por vehículos o tarifas.")
        except Exception as e:
            self.error("Error", "No se pudo eliminar la categoría:", e)

    def limpiar_form_categoria(self):
        self.e_cat_nombre.delete(0, "end")
        self.e_cat_obs.delete(0, "end")
        self.id_categoria_sel = None
        for item in self.tabla_categorias.selection():
            self.tabla_categorias.selection_remove(item)

    # ======================================================
    # MÓDULO LUGARES Y ESTACIONAMIENTO
    # ======================================================

    def mostrar_lugares(self):
        self.limpiar_contenido()
        self.id_lugar_sel = None
        self.lbl_total_lugares = self.encabezado("LUGARES Y ESTACIONAMIENTO")

        # Registrar lugar nuevo
        formulario = self.tarjeta()
        formulario.pack(fill="x", padx=25, pady=(5, 8))
        self.subtitulo(formulario, "NUEVO LUGAR").grid(
            row=0, column=0, columnspan=3, sticky="w", padx=20, pady=(15, 5))
        self.e_lug_codigo = self.campo(formulario, "Código del espacio (ej: C-01)", 1, 0, 300)
        self.e_lug_obs = self.campo(formulario, "Observación (opcional)", 1, 1, 380)
        ctk.CTkButton(formulario, text="Registrar lugar", width=140, height=38,
                      fg_color=self.color_verde, hover_color="#146C43",
                      command=self.registrar_lugar).grid(
            row=3, column=2, sticky="w", padx=10, pady=(0, 5))
        ctk.CTkLabel(formulario, text="").grid(row=4, column=0, pady=2)

        # Estacionar / liberar
        accion = self.tarjeta()
        accion.pack(fill="x", padx=25, pady=8)
        self.subtitulo(accion, "ESTACIONAR CLIENTE").pack(anchor="w", padx=20, pady=(15, 5))
        fila = ctk.CTkFrame(accion, fg_color="transparent")
        fila.pack(fill="x", padx=20, pady=(0, 15))
        self.combo_cliente_lugar = ctk.CTkComboBox(fila, width=420, height=38,
                                                   values=[""], state="readonly")
        self.combo_cliente_lugar.pack(side="left", padx=(0, 10))
        ctk.CTkButton(fila, text="Estacionar en lugar seleccionado", height=38,
                      fg_color=self.color_primario, hover_color="#06616B",
                      command=self.estacionar_cliente).pack(side="left", padx=5)
        ctk.CTkButton(fila, text="Liberar lugar seleccionado", height=38,
                      fg_color=self.color_naranja, hover_color="#C77C00",
                      command=self.liberar_lugar).pack(side="left", padx=5)

        # Filtro y tabla
        filtro = ctk.CTkFrame(self.contenido, fg_color="transparent")
        filtro.pack(fill="x", padx=25, pady=(8, 0))
        ctk.CTkLabel(filtro, text="Mostrar:", font=("Arial", 13, "bold"),
                     text_color="#333333").pack(side="left", padx=(0, 8))
        self.combo_filtro_lugar = ctk.CTkComboBox(
            filtro, width=180, height=36, values=["Todos", "Disponible", "Ocupado"],
            state="readonly", command=lambda v: self.listar_lugares())
        self.combo_filtro_lugar.set("Todos")
        self.combo_filtro_lugar.pack(side="left")

        marco = self.tarjeta()
        marco.pack(fill="both", expand=True, padx=25, pady=(8, 20))
        self.tabla_lugares = self.crear_tabla(marco, [
            ("id", "ID", 60), ("codigo", "Código", 150),
            ("estado", "Estado", 150), ("obs", "Observación", 420)])
        self.tabla_lugares.tag_configure("Disponible", foreground=self.color_verde)
        self.tabla_lugares.tag_configure("Ocupado", foreground=self.color_rojo)
        self.tabla_lugares.bind("<<TreeviewSelect>>", self.seleccionar_lugar)

        self.cargar_clientes_lugares()
        self.listar_lugares()

    def cargar_clientes_lugares(self):
        try:
            filas = consultar("SELECT Id_Cliente, Nombres, Apellidos, Ci FROM Cliente "
                              "ORDER BY Nombres, Apellidos")
        except Exception as e:
            self.error("Error", "No se pudieron cargar los clientes:", e)
            filas = []
        self.mapa_clientes_lugares = {
            f"{f[0]} - {f[1]} {f[2]} (C.I. {f[3]})": f[0] for f in filas}
        valores = list(self.mapa_clientes_lugares) or ["Sin clientes registrados"]
        self.combo_cliente_lugar.configure(values=valores)
        self.combo_cliente_lugar.set(valores[0])

    def listar_lugares(self):
        if not hasattr(self, "tabla_lugares"):
            return
        self.vaciar_tabla(self.tabla_lugares)
        try:
            filtro = self.combo_filtro_lugar.get()
            sql = "SELECT Id_Lugares, Cod_Espacio, Estado, Observacion FROM Lugares"
            params = ()
            if filtro in ("Disponible", "Ocupado"):
                sql += " WHERE Estado = ?"
                params = (filtro,)
            filas = consultar(sql + " ORDER BY Cod_Espacio", params)
            for fila in filas:
                self.tabla_lugares.insert("", "end", values=self.sin_none(fila),
                                          tags=(fila[2],))
            libres = consultar("SELECT COUNT(*) FROM Lugares WHERE Estado='Disponible'")[0][0]
            total = consultar("SELECT COUNT(*) FROM Lugares")[0][0]
            self.lbl_total_lugares.configure(
                text=f"Disponibles: {libres} de {total} lugares")
        except Exception as e:
            self.error("Error", "No se pudieron listar los lugares:", e)

    def seleccionar_lugar(self, evento=None):
        sel = self.tabla_lugares.selection()
        if sel:
            self.id_lugar_sel = int(self.tabla_lugares.item(sel[0], "values")[0])

    def registrar_lugar(self):
        codigo = self.e_lug_codigo.get().strip().upper()
        obs = self.e_lug_obs.get().strip() or None
        if not codigo:
            messagebox.showwarning("Dato obligatorio", "El código del espacio es obligatorio.")
            return
        try:
            ejecutar("INSERT INTO Lugares (Cod_Espacio, Estado, Observacion) "
                     "VALUES (?, 'Disponible', ?)", (codigo, obs))
            messagebox.showinfo("Registro exitoso", f"Lugar {codigo} registrado.")
            self.e_lug_codigo.delete(0, "end")
            self.e_lug_obs.delete(0, "end")
            self.listar_lugares()
        except sqlite3.IntegrityError:
            messagebox.showerror("No se pudo registrar", "Ya existe un lugar con ese código.")
        except Exception as e:
            self.error("Error", "No se pudo registrar el lugar:", e)

    def estacionar_cliente(self):
        if self.id_lugar_sel is None:
            messagebox.showwarning("Seleccionar lugar",
                                   "Seleccioná un lugar disponible de la tabla.")
            return
        id_cliente = self.mapa_clientes_lugares.get(self.combo_cliente_lugar.get())
        if not id_cliente:
            messagebox.showwarning("Seleccionar cliente", "Seleccioná un cliente.")
            return
        try:
            fila = consultar("SELECT Cod_Espacio, Estado FROM Lugares WHERE Id_Lugares=?",
                             (self.id_lugar_sel,))
            if not fila:
                messagebox.showerror("Error", "El lugar especificado no existe.")
                return
            codigo, estado = fila[0]
            if estado != "Disponible":
                messagebox.showerror("Lugar no disponible",
                                     f"El lugar {codigo} no está disponible "
                                     f"(estado actual: {estado}).")
                return
            ejecutar("UPDATE Lugares SET Estado='Ocupado' WHERE Id_Lugares=?",
                     (self.id_lugar_sel,))
            messagebox.showinfo("Éxito",
                                f"El cliente ID {id_cliente} fue estacionado en el "
                                f"lugar {codigo}.")
            self.id_lugar_sel = None
            self.listar_lugares()
        except Exception as e:
            self.error("Error", "No se pudo asignar el lugar:", e)

    def liberar_lugar(self):
        if self.id_lugar_sel is None:
            messagebox.showwarning("Seleccionar lugar",
                                   "Seleccioná un lugar ocupado de la tabla.")
            return
        try:
            fila = consultar("SELECT Cod_Espacio, Estado FROM Lugares WHERE Id_Lugares=?",
                             (self.id_lugar_sel,))
            if not fila:
                return
            codigo, estado = fila[0]
            if estado == "Disponible":
                messagebox.showinfo("Información", f"El lugar {codigo} ya está disponible.")
                return
            if not messagebox.askyesno("Confirmar", f"¿Liberar el lugar {codigo}?"):
                return
            ejecutar("UPDATE Lugares SET Estado='Disponible' WHERE Id_Lugares=?",
                     (self.id_lugar_sel,))
            messagebox.showinfo("Éxito", f"El lugar {codigo} ahora está disponible.")
            self.id_lugar_sel = None
            self.listar_lugares()
        except Exception as e:
            self.error("Error", "No se pudo liberar el lugar:", e)

    # ======================================================
    # MÓDULO RESERVAS
    # ======================================================

    def mostrar_reservas(self):
        self.limpiar_contenido()
        self.id_reserva_sel = None
        self.lbl_total_reservas = self.encabezado("GESTIÓN DE RESERVAS")

        formulario = self.tarjeta()
        formulario.pack(fill="x", padx=25, pady=10)
        self.subtitulo(formulario, "DATOS DE LA RESERVA").grid(
            row=0, column=0, columnspan=2, sticky="w", padx=20, pady=(15, 10))

        self.combo_res_cliente = self.etiqueta_combo(formulario, "Cliente", 1, 0, [""])
        self.combo_res_lugar = self.etiqueta_combo(formulario, "Lugar", 1, 1, [""])
        self.e_res_inicio = self.campo(formulario, "Inicio (AAAA-MM-DD HH:MM)", 2, 0)
        self.e_res_fin = self.campo(formulario, "Fin (AAAA-MM-DD HH:MM)", 2, 1)
        self.combo_res_estado = self.etiqueta_combo(
            formulario, "Estado", 3, 0, ESTADOS_RESERVA, 220)
        self.combo_res_estado.set("Pendiente")

        self.fila_botones(formulario, [
            ("Registrar", "verde", self.registrar_reserva),
            ("Modificar", "azul", self.modificar_reserva),
            ("Cancelar", "naranja", self.cancelar_reserva),
            ("Eliminar", "rojo", self.eliminar_reserva),
            ("Limpiar", "gris", self.limpiar_form_reserva),
        ]).grid(row=8, column=0, columnspan=2, sticky="e", padx=20, pady=(10, 20))

        self.e_busq_reserva = self.barra_busqueda(
            "Buscar por N°, cliente o lugar...", self.listar_reservas)

        marco = self.tarjeta()
        marco.pack(fill="both", expand=True, padx=25, pady=(5, 20))
        self.tabla_reservas = self.crear_tabla(marco, [
            ("id", "N°", 60), ("cliente", "Cliente", 220), ("lugar", "Lugar", 100),
            ("inicio", "Inicio", 160), ("fin", "Fin", 160), ("estado", "Estado", 120)])
        self.tabla_reservas.tag_configure("Pendiente", foreground=self.color_naranja)
        self.tabla_reservas.tag_configure("Activa", foreground=self.color_verde)
        self.tabla_reservas.tag_configure("Cancelada", foreground=self.color_rojo)
        self.tabla_reservas.tag_configure("Finalizada", foreground="#6C757D")
        self.tabla_reservas.bind("<<TreeviewSelect>>", self.seleccionar_reserva)

        self.cargar_combos_reservas()
        self.listar_reservas()

    def cargar_combos_reservas(self):
        try:
            clientes = consultar("SELECT Id_Cliente, Nombres, Apellidos, Ci FROM Cliente "
                                 "ORDER BY Nombres, Apellidos")
            lugares = consultar("SELECT Id_Lugares, Cod_Espacio FROM Lugares "
                                "ORDER BY Cod_Espacio")
        except Exception as e:
            self.error("Error", "No se pudieron cargar clientes y lugares:", e)
            clientes, lugares = [], []

        self.mapa_clientes_res = {
            f"{f[0]} - {f[1]} {f[2]} (C.I. {f[3]})": f[0] for f in clientes}
        valores = list(self.mapa_clientes_res) or ["Sin clientes registrados"]
        self.combo_res_cliente.configure(values=valores)
        self.combo_res_cliente.set(valores[0])

        self.mapa_lugares_res = {f"{f[0]} - {f[1]}": f[0] for f in lugares}
        valores = list(self.mapa_lugares_res) or ["Sin lugares registrados"]
        self.combo_res_lugar.configure(values=valores)
        self.combo_res_lugar.set(valores[0])

    def listar_reservas(self):
        if not hasattr(self, "tabla_reservas"):
            return
        self.vaciar_tabla(self.tabla_reservas)
        try:
            dato = self.e_busq_reserva.get().strip()
            p = f"%{dato}%"
            filas = consultar("""
                SELECT r.Id_Reservas, c.Nombres || ' ' || c.Apellidos, l.Cod_Espacio,
                       r.Fecha_Inicio, r.Fecha_Fin, r.Estado
                FROM Reservas r
                INNER JOIN Cliente c ON c.Id_Cliente = r.Id_Cliente
                INNER JOIN Lugares l ON l.Id_Lugares = r.Id_Lugares
                WHERE CAST(r.Id_Reservas AS TEXT) = ? OR c.Nombres LIKE ?
                   OR c.Apellidos LIKE ? OR l.Cod_Espacio LIKE ?
                ORDER BY r.Fecha_Inicio DESC""", (dato, p, p, p))
            for fila in filas:
                self.tabla_reservas.insert("", "end", values=self.sin_none(fila),
                                           tags=(fila[5],))
            self.lbl_total_reservas.configure(text=f"Total: {len(filas)} reservas")
        except Exception as e:
            self.error("Error", "No se pudieron listar las reservas:", e)

    def datos_form_reserva(self):
        id_cliente = self.mapa_clientes_res.get(self.combo_res_cliente.get())
        id_lugar = self.mapa_lugares_res.get(self.combo_res_lugar.get())
        if not id_cliente or not id_lugar:
            messagebox.showwarning("Datos incompletos", "Seleccioná un cliente y un lugar.")
            return None
        try:
            inicio = datetime.strptime(self.e_res_inicio.get().strip(), FORMATO_FECHA)
            fin = datetime.strptime(self.e_res_fin.get().strip(), FORMATO_FECHA)
        except ValueError:
            messagebox.showwarning(
                "Fechas inválidas", "Usá el formato AAAA-MM-DD HH:MM\nEjemplo: 2026-11-15 08:30")
            return None
        if fin <= inicio:
            messagebox.showwarning("Fechas inválidas", "El fin debe ser posterior al inicio.")
            return None
        return (id_cliente, id_lugar, inicio.strftime(FORMATO_FECHA),
                fin.strftime(FORMATO_FECHA), self.combo_res_estado.get())

    @staticmethod
    def hay_conflicto_reserva(id_lugar, inicio, fin, excluir=None):
        """Comprueba cruces con reservas pendientes o activas del mismo lugar."""
        sql = ("SELECT 1 FROM Reservas WHERE Id_Lugares = ? "
               "AND Estado IN ('Pendiente', 'Activa') "
               "AND Fecha_Inicio < ? AND Fecha_Fin > ?")
        params = [id_lugar, fin, inicio]
        if excluir is not None:
            sql += " AND Id_Reservas <> ?"
            params.append(excluir)
        return bool(consultar(sql, tuple(params)))

    def registrar_reserva(self):
        datos = self.datos_form_reserva()
        if not datos:
            return
        id_cliente, id_lugar, inicio, fin, estado = datos
        try:
            if estado in ("Pendiente", "Activa") and self.hay_conflicto_reserva(
                    id_lugar, inicio, fin):
                messagebox.showwarning(
                    "Lugar reservado", "Ese lugar ya tiene una reserva que se cruza con el horario elegido.")
                return
            nuevo_id, _ = ejecutar(
                "INSERT INTO Reservas (Fecha_Inicio, Fecha_Fin, Estado, Id_Lugares, Id_Cliente) "
                "VALUES (?, ?, ?, ?, ?)", (inicio, fin, estado, id_lugar, id_cliente))
            messagebox.showinfo("Registro exitoso",
                                f"Reserva N° {nuevo_id} registrada correctamente.")
            self.limpiar_form_reserva()
            self.listar_reservas()
        except Exception as e:
            self.error("Error", "No se pudo registrar la reserva:", e)

    def seleccionar_reserva(self, evento=None):
        sel = self.tabla_reservas.selection()
        if not sel:
            return
        self.id_reserva_sel = int(self.tabla_reservas.item(sel[0], "values")[0])
        try:
            fila = consultar(
                "SELECT Id_Cliente, Id_Lugares, Fecha_Inicio, Fecha_Fin, Estado "
                "FROM Reservas WHERE Id_Reservas = ?", (self.id_reserva_sel,))
            if not fila:
                return
            id_cliente, id_lugar, inicio, fin, estado = fila[0]
            for mapa, combo, valor in (
                    (self.mapa_clientes_res, self.combo_res_cliente, id_cliente),
                    (self.mapa_lugares_res, self.combo_res_lugar, id_lugar)):
                etiqueta = next((k for k, v in mapa.items() if v == valor), None)
                if etiqueta:
                    combo.set(etiqueta)
            self.llenar([self.e_res_inicio, self.e_res_fin], [inicio[:16], fin[:16]])
            self.combo_res_estado.set(estado)
        except Exception as e:
            self.error("Error", "No se pudieron cargar los datos:", e)

    def modificar_reserva(self):
        if self.id_reserva_sel is None:
            messagebox.showwarning("Seleccionar reserva", "Primero seleccioná una reserva de la tabla.")
            return
        datos = self.datos_form_reserva()
        if not datos:
            return
        id_cliente, id_lugar, inicio, fin, estado = datos
        if not messagebox.askyesno("Confirmar modificación", "¿Deseás guardar los cambios de la reserva?"):
            return
        try:
            if estado in ("Pendiente", "Activa") and self.hay_conflicto_reserva(
                    id_lugar, inicio, fin, excluir=self.id_reserva_sel):
                messagebox.showwarning(
                    "Lugar reservado", "Ese lugar ya tiene una reserva que se cruza con el horario elegido.")
                return
            ejecutar("UPDATE Reservas SET Fecha_Inicio=?, Fecha_Fin=?, Estado=?, "
                     "Id_Lugares=?, Id_Cliente=? WHERE Id_Reservas=?",
                     (inicio, fin, estado, id_lugar, id_cliente, self.id_reserva_sel))
            messagebox.showinfo("Modificación exitosa", "La reserva fue modificada correctamente.")
            self.limpiar_form_reserva()
            self.listar_reservas()
        except Exception as e:
            self.error("Error", "No se pudo modificar la reserva:", e)

    def cancelar_reserva(self):
        if self.id_reserva_sel is None:
            messagebox.showwarning("Seleccionar reserva", "Primero seleccioná una reserva de la tabla.")
            return
        if not messagebox.askyesno("Cancelar reserva", f"¿Cancelar la reserva N° {self.id_reserva_sel}?"):
            return
        try:
            ejecutar("UPDATE Reservas SET Estado='Cancelada' WHERE Id_Reservas=?",
                     (self.id_reserva_sel,))
            messagebox.showinfo("Reserva cancelada", "La reserva fue cancelada.")
            self.limpiar_form_reserva()
            self.listar_reservas()
        except Exception as e:
            self.error("Error", "No se pudo cancelar la reserva:", e)

    def eliminar_reserva(self):
        if self.id_reserva_sel is None:
            messagebox.showwarning("Seleccionar reserva", "Primero seleccioná una reserva de la tabla.")
            return
        if not messagebox.askyesno(
                "Eliminar reserva", "¿Estás seguro de eliminar la reserva seleccionada?\n\n"
                "Esta operación no se puede deshacer."):
            return
        try:
            ejecutar("DELETE FROM Reservas WHERE Id_Reservas = ?", (self.id_reserva_sel,))
            messagebox.showinfo("Eliminación exitosa", "La reserva fue eliminada.")
            self.limpiar_form_reserva()
            self.listar_reservas()
        except Exception as e:
            self.error("Error", "No se pudo eliminar la reserva:", e)

    def limpiar_form_reserva(self):
        self.e_res_inicio.delete(0, "end")
        self.e_res_fin.delete(0, "end")
        self.combo_res_estado.set("Pendiente")
        self.id_reserva_sel = None
        for item in self.tabla_reservas.selection():
            self.tabla_reservas.selection_remove(item)

    # ======================================================
    # MÓDULO PAGOS Y TARIFAS
    # ======================================================

    def mostrar_pagos(self):
        self.limpiar_contenido()
        self.lbl_total_pagos = self.encabezado("PAGOS Y TARIFAS")

        formulario = self.tarjeta()
        formulario.pack(fill="x", padx=25, pady=10)
        self.subtitulo(formulario, "REGISTRAR PAGO").grid(
            row=0, column=0, columnspan=3, sticky="w", padx=20, pady=(15, 10))

        self.combo_pago_cliente = self.etiqueta_combo(
            formulario, "Cliente", 1, 0, [""], 380)
        self.combo_pago_reserva = self.etiqueta_combo(
            formulario, "Tipo de reserva", 1, 1, TIPOS_RESERVA, 220)
        self.combo_pago_reserva.set("hora")
        self.e_pago_tiempo = self.campo(formulario, "Tiempo consumido (horas/días/meses)",
                                        1, 2, 260)
        self.combo_pago_categoria = self.etiqueta_combo(
            formulario, "Categoría del vehículo", 2, 0, [""], 380)
        self.combo_pago_metodo = self.etiqueta_combo(
            formulario, "Método de pago", 2, 1, METODOS_PAGO, 220)
        self.combo_pago_metodo.set(METODOS_PAGO[0])

        self.lbl_monto_calculado = ctk.CTkLabel(
            formulario, text=f"MONTO: {MONEDA} 0.00", font=("Arial", 20, "bold"),
            text_color=self.color_primario)
        self.lbl_monto_calculado.grid(row=6, column=0, sticky="w", padx=20, pady=(15, 15))

        self.fila_botones(formulario, [
            ("Calcular", "azul", self.calcular_monto),
            ("Registrar pago", "verde", self.registrar_pago),
            ("Limpiar", "gris", self.limpiar_form_pago),
        ]).grid(row=6, column=1, columnspan=2, sticky="e", padx=20, pady=(15, 15))

        ctk.CTkLabel(self.contenido, text="HISTORIAL DE PAGOS", font=("Arial", 18, "bold"),
                     text_color=self.color_titulo).pack(anchor="w", padx=30, pady=(8, 0))

        marco = self.tarjeta()
        marco.pack(fill="both", expand=True, padx=25, pady=(5, 20))
        self.tabla_pagos = self.crear_tabla(marco, [
            ("id", "ID", 60), ("monto", "Monto", 140), ("metodo", "Método de pago", 160),
            ("estado", "Estado", 130), ("fecha", "Fecha y hora", 200)])

        self.cargar_combos_pago()
        self.listar_pagos()

    def cargar_combos_pago(self):
        try:
            clientes = consultar("SELECT Id_Cliente, Nombres, Apellidos, Ci FROM Cliente "
                                 "ORDER BY Nombres, Apellidos")
            categorias = consultar("SELECT Nombre FROM Tipo_Vehiculos ORDER BY Nombre")
        except Exception as e:
            self.error("Error", "No se pudieron cargar clientes y categorías:", e)
            clientes, categorias = [], []

        self.mapa_clientes_pago = {
            f"{f[0]} - {f[1]} {f[2]} (C.I. {f[3]})": f[0] for f in clientes}
        valores = list(self.mapa_clientes_pago) or ["Sin clientes registrados"]
        self.combo_pago_cliente.configure(values=valores)
        self.combo_pago_cliente.set(valores[0])

        self.lista_categorias_pago = [c[0] for c in categorias]
        valores = self.lista_categorias_pago or ["Sin categorías registradas"]
        self.combo_pago_categoria.configure(values=valores)
        self.combo_pago_categoria.set(valores[0])

    def calcular_monto(self, silencioso=False):
        """Devuelve el monto calculado o None si los datos no son válidos."""
        try:
            tiempo = float(self.e_pago_tiempo.get().strip().replace(",", "."))
            if tiempo <= 0:
                raise ValueError
        except ValueError:
            if not silencioso:
                messagebox.showwarning("Tiempo inválido",
                                       "Ingresá un tiempo numérico mayor que cero.")
            return None
        categoria = self.combo_pago_categoria.get()
        if categoria not in self.lista_categorias_pago:
            if not silencioso:
                messagebox.showwarning("Categoría requerida",
                                       "Registrá y seleccioná una categoría de vehículo.")
            return None
        tarifa = TARIFAS_BASE[self.combo_pago_reserva.get()]
        monto = round(tiempo * tarifa * factor_categoria(categoria), 2)
        self.lbl_monto_calculado.configure(text=f"MONTO: {MONEDA} {monto:,.3f}")
        return monto

    def registrar_pago(self):
        id_cliente = self.mapa_clientes_pago.get(self.combo_pago_cliente.get())
        if not id_cliente:
            messagebox.showwarning("Cliente requerido", "Seleccioná un cliente.")
            return
        monto = self.calcular_monto()
        if monto is None:
            return
        metodo = self.combo_pago_metodo.get()
        if not messagebox.askyesno(
                "Confirmar pago",
                f"¿Registrar el pago por {MONEDA} {monto:,.2f} con {metodo}?"):
            return
        try:
            id_pago, _ = ejecutar(
                "INSERT INTO Pago (Estado, Monto_Total, Metodo_Pago) "
                "VALUES ('Completado', ?, ?)", (monto, metodo))
            messagebox.showinfo(
                "Comprobante de pago",
                f"Pago N° {id_pago} registrado\n\n"
                f"Cliente ID: {id_cliente}\n"
                f"Categoría: {self.combo_pago_categoria.get()}\n"
                f"Modalidad: {self.combo_pago_reserva.get().capitalize()}\n"
                f"Tiempo: {self.e_pago_tiempo.get().strip()}\n"
                f"Método: {metodo}\n"
                f"MONTO TOTAL: {MONEDA} {monto:,.2f}")
            self.limpiar_form_pago()
            self.listar_pagos()
        except Exception as e:
            self.error("Error", "No se pudo procesar el pago:", e)

    def listar_pagos(self):
        self.vaciar_tabla(self.tabla_pagos)
        try:
            filas = consultar("SELECT Id_Pago, Monto_Total, Metodo_Pago, Estado, Fecha_Pago "
                              "FROM Pago ORDER BY Id_Pago DESC")
            for id_pago, monto, metodo, estado, fecha in filas:
                self.tabla_pagos.insert("", "end", values=(
                    id_pago, f"{MONEDA} {monto:,.3f}", metodo, estado, fecha))
            total = sum(f[1] for f in filas if f[3] == "Completado")
            self.lbl_total_pagos.configure(
                text=f"Recaudado: {MONEDA} {total:,.2f}  |  {len(filas)} pagos")
        except Exception as e:
            self.error("Error", "No se pudo cargar el historial:", e)

    def limpiar_form_pago(self):
        self.e_pago_tiempo.delete(0, "end")
        self.combo_pago_reserva.set("hora")
        self.combo_pago_metodo.set(METODOS_PAGO[0])
        self.lbl_monto_calculado.configure(text=f"MONTO: {MONEDA} 0.00")

    # ======================================================
    # MÓDULO CONSULTAS COMBINADAS (JOIN)
    # ======================================================

    def mostrar_consultas(self):
        self.limpiar_contenido()
        self.lbl_total_consulta = self.encabezado("CONSULTAS COMBINADAS")

        barra = self.tarjeta()
        barra.pack(fill="x", padx=25, pady=10)
        self.subtitulo(barra, "SELECCIONAR REPORTE").pack(anchor="w", padx=20, pady=(15, 8))
        fila = ctk.CTkFrame(barra, fg_color="transparent")
        fila.pack(fill="x", padx=20, pady=(0, 15))
        for nombre in REPORTES:
            ctk.CTkButton(fila, text=nombre, height=38, fg_color=self.color_primario,
                          hover_color="#06616B",
                          command=lambda n=nombre: self.ejecutar_reporte(n)
                          ).pack(side="left", padx=(0, 10))

        self.lbl_reporte = ctk.CTkLabel(self.contenido, text="Elegí un reporte para verlo.",
                                        font=("Arial", 16, "bold"),
                                        text_color=self.color_titulo)
        self.lbl_reporte.pack(anchor="w", padx=30, pady=(5, 0))

        self.marco_reporte = self.tarjeta()
        self.marco_reporte.pack(fill="both", expand=True, padx=25, pady=(5, 20))

    def ejecutar_reporte(self, nombre):
        sql, columnas = REPORTES[nombre]
        for widget in self.marco_reporte.winfo_children():
            widget.destroy()
        tabla = self.crear_tabla(self.marco_reporte, columnas)
        self.lbl_reporte.configure(text=nombre.upper())
        try:
            filas = consultar(sql)
            for fila in filas:
                tabla.insert("", "end", values=self.sin_none(fila))
            self.lbl_total_consulta.configure(text=f"Total: {len(filas)} registros")
            if not filas:
                messagebox.showinfo("Sin resultados",
                                    "No hay registros para este reporte por ahora.")
        except Exception as e:
            self.error("Error", f"No se pudo ejecutar el reporte:", e)


# ==========================================================
# INICIAR SISTEMA
# ==========================================================

if __name__ == "__main__":
    init_db()
    aplicacion = Aplicacion()
    aplicacion.mainloop()