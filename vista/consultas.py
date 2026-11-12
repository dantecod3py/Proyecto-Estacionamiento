from database import get_connection 
 
def consultar_clientes_con_reservas(): 
    """Consulta 1: Clientes combinados con sus reservas y lugar asignado.""" 
    conn = get_connection() 
    if conn: 
        try: 
            cursor = conn.cursor() 
            query = """ 
                SELECT c.Id_Cliente, c.Nombres || ' ' || c.Apellidos AS Cliente, c.Ci, 
                       r.Id_Reservas, l.Cod_Espacio, r.Fecha_Inicio, r.Fecha_Fin, r.Estado 
                FROM Cliente c 
                INNER JOIN Reservas r ON c.Id_Cliente = r.Id_Cliente 
                INNER JOIN Lugares l ON r.Id_Lugares = l.Id_Lugares; 
            """ 
            cursor.execute(query) 
            resultados = cursor.fetchall() 
            print("\n=== REPORTE 1: CLIENTES CON SUS RESERVAS ===") 
            if not resultados: 
                print("No existen registros de reservas actualmente.") 
            for row in resultados: 
                print(f"Cliente: {row[1]} (CI: {row[2]}) | Reserva ID: {row[3]} | Espacio: {row[4]} | Desde: {row[5]} Hasta: {row[6]} | Estado: {row[7]}") 
        except Exception as e: 
            print(f"\n[Error] En Consulta 1: {e}") 
        finally: 
            conn.close() 
 
def consultar_vehiculos_con_categoria(): 
    """Consulta 2: Vehículos combinados con su categoría, cliente y detalles.""" 
    conn = get_connection() 
    if conn: 
        try: 
            cursor = conn.cursor() 
            query = """ 
                SELECT v.Id_Vehiculo, v.Matricula, v.Marca, v.Modelo, v.Color, 
                       tv.Nombre AS Categoria, c.Nombres || ' ' || c.Apellidos AS Propietario 
                FROM Vehiculo v 
                INNER JOIN Tipo_Vehiculos tv ON v.Id_Tipo_Vehiculos = tv.Id_Tipo_Vehiculos 
                INNER JOIN Cliente c ON v.Id_Cliente = c.Id_Cliente; 
            """ 
            cursor.execute(query) 
            resultados = cursor.fetchall() 
            print("\n=== REPORTE 2: VEHÍCULOS CON SU CATEGORÍA Y PROPIETARIO ===") 
            if not resultados: 
                print("No existen vehículos registrados actualmente.") 
            for row in resultados: 
                print(f"Matrícula: {row[1]} | Marca/Modelo: {row[2]} {row[3]} ({row[4]}) | Categoría: {row[5]} | Propietario: {row[6]}") 
        except Exception as e: 
            print(f"\n[Error] En Consulta 2: {e}") 
        finally: 
            conn.close() 
 
def consultar_pagos_por_cliente(): 
    """Consulta 3: Pagos consolidados asociados a los clientes mediante Tickets.""" 
    conn = get_connection() 
    if conn: 
        try: 
            cursor = conn.cursor() 
            query = """ 
                SELECT c.Id_Cliente, c.Nombres || ' ' || c.Apellidos AS Cliente, 
                       p.Id_Pago, p.Monto_Total, p.Metodo_Pago, p.Fecha_Pago, t.Id_Ticket 
                FROM Cliente c 
                INNER JOIN Vehiculo v ON c.Id_Cliente = v.Id_Cliente 
                INNER JOIN Ticket t ON v.Id_Vehiculo = t.Id_Vehiculo 
                INNER JOIN Pago p ON t.Id_Pago = p.Id_Pago; 
            """ 
            cursor.execute(query) 
            resultados = cursor.fetchall() 
            print("\n=== REPORTE 3: PAGOS REALIZADOS POR CADA CLIENTE ===") 
            if not resultados: 
                print("No hay registros de pagos consolidados en la base de datos.") 
            for row in resultados: 
                print(f"Cliente: {row[1]} | Ticket ID: {row[6]} | Pago ID: {row[2]} | Monto: ${row[3]:.2f} | Método: {row[4]} | Fecha: {row[5]}") 
        except Exception as e: 
            print(f"\n[Error] En Consulta 3: {e}") 
        finally: 
            conn.close() 