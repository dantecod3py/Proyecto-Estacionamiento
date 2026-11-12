from database import get_connection 
 
def registrar_cliente(nombres: str, apellidos: str, ci: str, telefono: str, correo: str): 
    conn = get_connection() 
    if conn: 
        try: 
            cursor = conn.cursor() 
            query = "INSERT INTO Cliente (Nombres, Apellidos, Ci, Telefono, Correo) VALUES (?, ?, ?, ?, ?)" 
            cursor.execute(query, (nombres, apellidos, ci, telefono, correo)) 
            conn.commit() 
            print(f"\n[Éxito] Cliente {nombres} {apellidos} registrado con ID: {cursor.lastrowid}") 
        except Exception as e: 
            print(f"\n[Error] No se pudo registrar el cliente: {e}") 
        finally: 
            conn.close() 
 
def consultar_clientes(): 
    conn = get_connection() 
    if conn: 
        try: 
            cursor = conn.cursor() 
            cursor.execute("SELECT Id_Cliente, Nombres, Apellidos, Ci, Telefono, Correo FROM Cliente") 
            clientes = cursor.fetchall() 
            print("\n" + "="*60) 
            print(f"{'ID':<4} | {'NOMBRE Y APELLIDO':<25} | {'C.I.':<12} | {'TELÉFONO'}") 
            print("="*60) 
            for c in clientes: 
                nombre_completo = f"{c[1]} {c[2]}" 
                print(f"{c[0]:<4} | {nombre_completo:<25} | {c[3]:<12} | {c[4]}") 
            print("="*60) 
            return clientes 
        except Exception as e: 
            print(f"\n[Error] Al consultar clientes: {e}") 
        finally: 
            conn.close() 
 
def buscar_cliente(filtro: str): 
    conn = get_connection() 
    if conn: 
        try: 
            cursor = conn.cursor() 
            query = "SELECT Id_Cliente, Nombres, Apellidos, Ci, Telefono, Correo FROM Cliente WHERE Ci LIKE ? OR Nombres LIKE ? OR Apellidos LIKE ?" 
            param = f"%{filtro}%" 
            cursor.execute(query, (param, param, param)) 
            clientes = cursor.fetchall() 
            print(f"\n--- Resultados de búsqueda para '{filtro}' ---") 
            if not clientes: 
                print("No se encontraron clientes coincidentes.") 
                return [] 
            for c in clientes: 
                print(f"ID: {c[0]} | Nombre: {c[1]} {c[2]} | C.I.: {c[3]} | Tel: {c[4]} | Correo: {c[5]}") 
            return clientes 
        except Exception as e: 
            print(f"\n[Error] En la búsqueda: {e}") 
        finally: 
            conn.close() 
 
def modificar_cliente(id_cliente: int, nombres: str, apellidos: str, ci: str, telefono: str, correo: str): 
    conn = get_connection() 
    if conn: 
        try: 
            cursor = conn.cursor() 
            query = "UPDATE Cliente SET Nombres = ?, Apellidos = ?, Ci = ?, Telefono = ?, Correo = ? WHERE Id_Cliente = ?" 
            cursor.execute(query, (nombres, apellidos, ci, telefono, correo, id_cliente)) 
            conn.commit() 
            if cursor.rowcount > 0: 
                print(f"\n[Éxito] Cliente ID {id_cliente} actualizado correctamente.") 
            else: 
                print(f"\n[Aviso] No se encontró cliente con ID {id_cliente}.") 
        except Exception as e: 
            print(f"\n[Error] Al modificar cliente: {e}") 
        finally: 
            conn.close() 
 
def eliminar_cliente(id_cliente: int): 
    conn = get_connection() 
    if conn: 
        try: 
            cursor = conn.cursor() 
            cursor.execute("DELETE FROM Cliente WHERE Id_Cliente = ?", (id_cliente,)) 
            conn.commit() 
            if cursor.rowcount > 0: 
                print(f"\n[Éxito] Cliente ID {id_cliente} eliminado correctamente.") 
            else: 
                print(f"\n[Aviso] No se encontró cliente con ID {id_cliente}.") 
        except Exception as e: 
            print(f"\n[Error] No se puede eliminar el cliente (posibles dependencias en Vehículos/Reservas): {e}") 
        finally: 
            conn.close() 