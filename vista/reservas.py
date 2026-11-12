from datetime import datetime
from database import get_connection

ESTADOS_RESERVA = ["Pendiente", "Activa", "Finalizada", "Cancelada"]
FORMATO_FECHA = "%Y-%m-%d %H:%M"

_SELECT_RESERVAS = """
    SELECT r.Id_Reservas, c.Nombres || ' ' || c.Apellidos, l.Cod_Espacio,
           r.Fecha_Inicio, r.Fecha_Fin, r.Estado
    FROM Reservas r
    INNER JOIN Cliente c ON c.Id_Cliente = r.Id_Cliente
    INNER JOIN Lugares l ON l.Id_Lugares = r.Id_Lugares
"""


def _validar(cursor, id_cliente: int, id_lugar: int, fecha_inicio: str,
             fecha_fin: str, estado: str, excluir: int = None):
    """Aplica las mismas reglas que la interfaz. Devuelve (inicio, fin) normalizados
    o lanza ValueError con el motivo."""
    if estado not in ESTADOS_RESERVA:
        raise ValueError(f"Estado no válido. Use: {', '.join(ESTADOS_RESERVA)}.")

    try:
        inicio = datetime.strptime(fecha_inicio.strip(), FORMATO_FECHA)
        fin = datetime.strptime(fecha_fin.strip(), FORMATO_FECHA)
    except ValueError:
        raise ValueError("Las fechas deben tener el formato AAAA-MM-DD HH:MM "
                         "(ejemplo: 2026-11-15 08:30).")
    if fin <= inicio:
        raise ValueError("La fecha de fin debe ser posterior a la de inicio.")

    cursor.execute("SELECT 1 FROM Cliente WHERE Id_Cliente = ?", (id_cliente,))
    if not cursor.fetchone():
        raise ValueError("El cliente especificado no existe.")
    cursor.execute("SELECT 1 FROM Lugares WHERE Id_Lugares = ?", (id_lugar,))
    if not cursor.fetchone():
        raise ValueError("El lugar especificado no existe.")

    inicio_txt = inicio.strftime(FORMATO_FECHA)
    fin_txt = fin.strftime(FORMATO_FECHA)

    # Una reserva Pendiente/Activa no puede cruzarse con otra del mismo lugar
    if estado in ("Pendiente", "Activa"):
        sql = ("SELECT 1 FROM Reservas WHERE Id_Lugares = ? "
               "AND Estado IN ('Pendiente', 'Activa') "
               "AND Fecha_Inicio < ? AND Fecha_Fin > ?")
        params = [id_lugar, fin_txt, inicio_txt]
        if excluir is not None:
            sql += " AND Id_Reservas <> ?"
            params.append(excluir)
        cursor.execute(sql, tuple(params))
        if cursor.fetchone():
            raise ValueError("El lugar ya tiene una reserva que se cruza con ese horario.")

    return inicio_txt, fin_txt


def registrar_reserva(id_cliente: int, id_lugar: int, fecha_inicio: str,
                      fecha_fin: str, estado: str = "Pendiente"):
    conn = get_connection()
    if conn:
        try:
            cursor = conn.cursor()
            inicio, fin = _validar(cursor, id_cliente, id_lugar, fecha_inicio,
                                   fecha_fin, estado)
            cursor.execute(
                "INSERT INTO Reservas (Fecha_Inicio, Fecha_Fin, Estado, Id_Lugares, Id_Cliente) "
                "VALUES (?, ?, ?, ?, ?)",
                (inicio, fin, estado, id_lugar, id_cliente)
            )
            conn.commit()
            print(f"\n[Éxito] Reserva registrada con ID: {cursor.lastrowid}")
            return cursor.lastrowid
        except ValueError as e:
            print(f"\n[Error] {e}")
        except Exception as e:
            print(f"\n[Error] No se pudo registrar la reserva: {e}")
        finally:
            conn.close()


def consultar_reservas():
    conn = get_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute(_SELECT_RESERVAS + " ORDER BY r.Fecha_Inicio DESC")
            reservas = cursor.fetchall()
            print("\n" + "=" * 85)
            print(f"{'ID':<4} | {'CLIENTE':<22} | {'LUGAR':<7} | {'INICIO':<16} | {'FIN':<16} | {'ESTADO'}")
            print("=" * 85)
            for r in reservas:
                print(f"{r[0]:<4} | {r[1]:<22} | {r[2]:<7} | {r[3]:<16} | {r[4]:<16} | {r[5]}")
            print("=" * 85)
            return reservas
        except Exception as e:
            print(f"\n[Error] Al consultar reservas: {e}")
        finally:
            conn.close()


def buscar_reserva(filtro: str):
    conn = get_connection()
    if conn:
        try:
            cursor = conn.cursor()
            param = f"%{filtro}%"
            cursor.execute(
                _SELECT_RESERVAS +
                " WHERE CAST(r.Id_Reservas AS TEXT) = ? OR c.Nombres LIKE ? "
                "OR c.Apellidos LIKE ? OR l.Cod_Espacio LIKE ? "
                "ORDER BY r.Fecha_Inicio DESC",
                (filtro, param, param, param)
            )
            reservas = cursor.fetchall()
            print(f"\n--- Reservas encontradas para '{filtro}' ---")
            if not reservas:
                print("No se encontraron reservas coincidentes.")
                return []
            for r in reservas:
                print(f"ID: {r[0]} | Cliente: {r[1]} | Lugar: {r[2]} | "
                      f"Desde: {r[3]} Hasta: {r[4]} | Estado: {r[5]}")
            return reservas
        except Exception as e:
            print(f"\n[Error] En la búsqueda de reservas: {e}")
        finally:
            conn.close()


def modificar_reserva(id_reserva: int, id_cliente: int, id_lugar: int,
                      fecha_inicio: str, fecha_fin: str, estado: str):
    conn = get_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM Reservas WHERE Id_Reservas = ?", (id_reserva,))
            if not cursor.fetchone():
                print(f"\n[Aviso] No se encontró reserva con ID {id_reserva}.")
                return
            inicio, fin = _validar(cursor, id_cliente, id_lugar, fecha_inicio,
                                   fecha_fin, estado, excluir=id_reserva)
            cursor.execute(
                "UPDATE Reservas SET Fecha_Inicio = ?, Fecha_Fin = ?, Estado = ?, "
                "Id_Lugares = ?, Id_Cliente = ? WHERE Id_Reservas = ?",
                (inicio, fin, estado, id_lugar, id_cliente, id_reserva)
            )
            conn.commit()
            print(f"\n[Éxito] Reserva ID {id_reserva} actualizada correctamente.")
        except ValueError as e:
            print(f"\n[Error] {e}")
        except Exception as e:
            print(f"\n[Error] Al modificar reserva: {e}")
        finally:
            conn.close()


def cancelar_reserva(id_reserva: int):
    conn = get_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("UPDATE Reservas SET Estado = 'Cancelada' WHERE Id_Reservas = ?",
                           (id_reserva,))
            conn.commit()
            if cursor.rowcount > 0:
                print(f"\n[Éxito] Reserva ID {id_reserva} cancelada.")
            else:
                print(f"\n[Aviso] No se encontró reserva con ID {id_reserva}.")
        except Exception as e:
            print(f"\n[Error] Al cancelar reserva: {e}")
        finally:
            conn.close()


def eliminar_reserva(id_reserva: int):
    conn = get_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM Reservas WHERE Id_Reservas = ?", (id_reserva,))
            conn.commit()
            if cursor.rowcount > 0:
                print(f"\n[Éxito] Reserva ID {id_reserva} eliminada correctamente.")
            else:
                print(f"\n[Aviso] No se encontró reserva con ID {id_reserva}.")
        except Exception as e:
            print(f"\n[Error] No se puede eliminar la reserva: {e}")
        finally:
            conn.close()