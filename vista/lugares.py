from database import get_connection 
 
def listar_lugares_disponibles(): 
    """Consulta y muestra únicamente los espacios en estado 'Disponible'.""" 
    conn = get_connection() 
    if conn: 
        try: 
            cursor = conn.cursor() 
            cursor.execute("SELECT Id_Lugares, Cod_Espacio, Estado, Observacion FROM Lugares WHERE Estado = 'Disponible'") 
            lugares = cursor.fetchall() 
            print("\n" + "="*50) 
            print("         LUGARES DISPONIBLES PARA ESTACIONAR") 
            print("="*50) 
            if not lugares: 
                print("Atención: No hay lugares disponibles en este momento.") 
            for l in lugares: 
                print(f"ID: {l[0]} | Código Espacio: {l[1]} | Estado: {l[2]} | Obs: {l[3]}") 
            print("="*50) 
            return lugares 
        except Exception as e: 
            print(f"\n[Error] Al consultar lugares disponibles: {e}") 
        finally: 
            conn.close() 
 
def estacionar_cliente_en_lugar(id_lugar: int, id_cliente: int): 
    """Asigna un lugar disponible a un cliente cambiando su estado a 'Ocupado'.""" 
    conn = get_connection() 
    if conn: 
        try: 
            cursor = conn.cursor() 
            # Verificar si el lugar está disponible 
            cursor.execute("SELECT Cod_Espacio, Estado FROM Lugares WHERE Id_Lugares = ?", (id_lugar,)) 
            lugar = cursor.fetchone() 
            if not lugar: 
                print("\n[Error] El lugar especificado no existe.") 
                return 
            if lugar[1] != 'Disponible': 
                print(f"\n[Error] El lugar {lugar[0]} no está disponible (Estado actual: {lugar[1]}).") 
                return 
 
            cursor.execute("UPDATE Lugares SET Estado = 'Ocupado' WHERE Id_Lugares = ?", (id_lugar,)) 
            conn.commit() 
            print(f"\n[Éxito] El cliente ID {id_cliente} ha estacionado exitosamente en el lugar {lugar[0]}.") 
        except Exception as e: 
            print(f"\n[Error] Al asignar lugar al cliente: {e}") 
        finally: 
            conn.close() 