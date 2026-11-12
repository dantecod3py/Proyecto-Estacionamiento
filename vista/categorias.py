from database import get_connection 
 
def registrar_categoria(nombre: str, observacion: str): 
    conn = get_connection() 
    if conn: 
        try: 
            cursor = conn.cursor() 
            cursor.execute("INSERT INTO Tipo_Vehiculos (Nombre, Observacion) VALUES (?, ?)", (nombre, observacion)) 
            conn.commit() 
            print(f"\n[Éxito] Categoría '{nombre}' registrada con ID: {cursor.lastrowid}") 
        except Exception as e: 
            print(f"\n[Error] Al registrar categoría: {e}") 
        finally: 
            conn.close() 
 
def consultar_categorias(): 
    conn = get_connection() 
    if conn: 
        try: 
            cursor = conn.cursor() 
            cursor.execute("SELECT Id_Tipo_Vehiculos, Nombre, Observacion FROM Tipo_Vehiculos") 
            cats = cursor.fetchall() 
            print("\n" + "="*50) 
            print(f"{'ID':<4} | {'CATEGORÍA':<20} | {'OBSERVACIÓN'}") 
            print("="*50) 
            for c in cats: 
                print(f"{c[0]:<4} | {c[1]:<20} | {c[2] or 'N/A'}") 
            print("="*50) 
            return cats 
        except Exception as e: 
            print(f"\n[Error] Al consultar categorías: {e}") 
        finally: 
            conn.close() 
 
def buscar_categoria(filtro: str): 
    conn = get_connection() 
    if conn: 
        try: 
            cursor = conn.cursor() 
            cursor.execute("SELECT Id_Tipo_Vehiculos, Nombre, Observacion FROM Tipo_Vehiculos WHERE Nombre LIKE ?", (f"%{filtro}%",)) 
            cats = cursor.fetchall() 
            print(f"\n--- Categorías encontradas para '{filtro}' ---") 
            for c in cats: 
                print(f"ID: {c[0]} | Categoría: {c[1]} | Obs: {c[2]}") 
            return cats 
        except Exception as e: 
            print(f"\n[Error] En búsqueda de categoría: {e}") 
        finally: 
            conn.close() 
 
def modificar_categoria(id_cat: int, nombre: str, observacion: str): 
    conn = get_connection() 
    if conn: 
        try: 
            cursor = conn.cursor() 
            cursor.execute("UPDATE Tipo_Vehiculos SET Nombre = ?, Observacion = ? WHERE Id_Tipo_Vehiculos = ?", (nombre, observacion, id_cat)) 
            conn.commit() 
            print(f"\n[Éxito] Categoría ID {id_cat} actualizada.") 
        except Exception as e: 
            print(f"\n[Error] Al modificar categoría: {e}") 
        finally: 
            conn.close() 
 
def eliminar_categoria(id_cat: int): 
    conn = get_connection() 
    if conn: 
        try: 
            cursor = conn.cursor() 
            cursor.execute("DELETE FROM Tipo_Vehiculos WHERE Id_Tipo_Vehiculos = ?", (id_cat,)) 
            conn.commit() 
            print(f"\n[Éxito] Categoría ID {id_cat} eliminada.") 
        except Exception as e: 
            print(f"\n[Error] No se puede eliminar la categoría (en uso por vehículos): {e}") 
        finally: 
            conn.close() 