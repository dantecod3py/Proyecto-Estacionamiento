from database import get_connection 
 
TARIFAS_BASE = { 
    'hora': 10.00, 
    'dia': 50.00, 
    'mes': 300.00 
} 
 
MULTIPLICADOR_CATEGORIA = { 
    'Motocicleta': 0.8, 
    'Automóvil': 1.0, 
    'Camioneta / SUV': 1.3, 
    'Camión / Autobús': 1.8 
} 
 
def registrar_pago(id_cliente: int, tiempo_uso: float, tipo_reserva: str, categoria_vehiculo: str, metodo_pago: str): 
    """Registra un pago calculando el monto según tiempo, categoría y tipo de reserva.""" 
    conn = get_connection() 
    if conn: 
        try: 
            cursor = conn.cursor() 
            tipo_reserva_clean = tipo_reserva.lower() 
            if tipo_reserva_clean not in TARIFAS_BASE: 
                print("\n[Error] Tipo de reserva no válido. Use: hora, dia o mes.") 
                return 
 
            tarifa_unitaria = TARIFAS_BASE[tipo_reserva_clean] 
            factor_cat = MULTIPLICADOR_CATEGORIA.get(categoria_vehiculo, 1.0) 
            monto_total = round(tiempo_uso * tarifa_unitaria * factor_cat, 2) 
 
            cursor.execute( 
                "INSERT INTO Pago (Estado, Monto_Total, Metodo_Pago) VALUES ('Completado', ?, ?)", 
                (monto_total, metodo_pago) 
            ) 
            id_pago = cursor.lastrowid 
            conn.commit() 
 
            print("\n" + "="*55) 
            print("             COMPROBANTE DE PAGO REGISTRADO") 
            print("="*55) 
            print(f"ID Pago: {id_pago} | Estado: Completado") 
            print(f"Cliente ID: {id_cliente} | Categoría Vehículo: {categoria_vehiculo}") 
            print(f"Modalidad: {tipo_reserva.capitalize()} | Tiempo Consumido: {tiempo_uso}") 
            print(f"Método de Pago: {metodo_pago} | MONTO TOTAL: ${monto_total:.2f}") 
            print("="*55) 
        except Exception as e: 
            print(f"\n[Error] Al procesar el pago: {e}") 
        finally: 
            conn.close() 
 
def consultar_estado_pagos(): 
    """Lista el historial de todos los pagos realizados.""" 
    conn = get_connection() 
    if conn: 
        try: 
            cursor = conn.cursor() 
            cursor.execute("SELECT Id_Pago, Monto_Total, Metodo_Pago, Estado, Fecha_Pago FROM Pago") 
            pagos = cursor.fetchall() 
            print("\n" + "="*65) 
            print(f"{'ID':<4} | {'MONTO ($)':<10} | {'MÉT. PAGO':<12} | {'ESTADO':<10} | {'FECHA Y HORA'}") 
            print("="*65) 
            for p in pagos: 
                print(f"{p[0]:<4} | ${p[1]:<9.2f} | {p[2]:<12} | {p[3]:<10} | {p[4]}") 
            print("="*65) 
            return pagos 
        except Exception as e: 
            print(f"\n[Error] Al consultar pagos: {e}") 
        finally: 
            conn.close() 