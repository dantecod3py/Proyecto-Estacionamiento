from database import init_db 
import vista.clientes as clientes 
import vista.categorias as categorias 
import vista.lugares as lugares 
import vista.pagos as pagos 
import vista.consultas as consultas 
 
def menu_clientes(): 
    while True: 
        print("\n--- SUBMENÚ GESTIÓN DE CLIENTES ---") 
        print("1. Registrar cliente") 
        print("2. Listar clientes") 
        print("3. Buscar cliente") 
        print("4. Modificar cliente") 
        print("5. Eliminar cliente") 
        print("6. Volver al menú principal") 
        op = input("Seleccione opción: ").strip() 
        if op == "1": 
            clientes.registrar_cliente(input("Nombres: "), input("Apellidos: "), input("C.I.: "), input("Teléfono: "), input("Correo: ")) 
        elif op == "2": 
            clientes.consultar_clientes() 
        elif op == "3": 
            clientes.buscar_cliente(input("Término a buscar: ")) 
        elif op == "4": 
            clientes.consultar_clientes() 
            try: 
                id_c = int(input("ID a modificar: ")) 
                clientes.modificar_cliente(id_c, input("Nuevo Nombre: "), input("Nuevo Apellido: "), input("Nueva C.I.: "), input("Nuevo Tel: "), input("Nuevo Correo: ")) 
            except ValueError: 
                print("ID no válido.") 
        elif op == "5": 
            clientes.consultar_clientes() 
            try: 
                id_c = int(input("ID a eliminar: ")) 
                clientes.eliminar_cliente(id_c) 
            except ValueError: 
                print("ID no válido.") 
        elif op == "6": 
            break 
 
def menu_categorias(): 
    while True: 
        print("\n--- SUBMENÚ CATEGORÍAS DE VEHÍCULOS ---") 
        print("1. Registrar categoría") 
        print("2. Listar categorías") 
        print("3. Buscar categoría") 
        print("4. Modificar categoría") 
        print("5. Eliminar categoría") 
        print("6. Volver al menú principal") 
        op = input("Seleccione opción: ").strip() 
        if op == "1": 
            categorias.registrar_categoria(input("Nombre Categoría: "), input("Observación: ")) 
        elif op == "2": 
            categorias.consultar_categorias() 
        elif op == "3": 
            categorias.buscar_categoria(input("Nombre a buscar: ")) 
        elif op == "4": 
            categorias.consultar_categorias() 
            try: 
                id_cat = int(input("ID Categória a modificar: ")) 
                categorias.modificar_categoria(id_cat, input("Nuevo Nombre: "), input("Nueva Obs: ")) 
            except ValueError: 
                print("ID no válido.") 
        elif op == "5": 
            categorias.consultar_categorias() 
            try: 
                id_cat = int(input("ID Categória a eliminar: ")) 
                categorias.eliminar_categoria(id_cat) 
            except ValueError: 
                print("ID no válido.") 
        elif op == "6": 
            break 
 
def menu_lugares(): 
    while True: 
        print("\n--- SUBMENÚ ESPACIOS Y ESTACIONAMIENTO ---") 
        print("1. Consultar lugares disponibles") 
        print("2. Estacionar cliente en lugar disponible") 
        print("3. Volver al menú principal") 
        op = input("Seleccione opción: ").strip() 
        if op == "1": 
            lugares.listar_lugares_disponibles() 
        elif op == "2": 
            lugares.listar_lugares_disponibles() 
            try: 
                id_l = int(input("Ingrese ID del lugar disponible: ")) 
                id_c = int(input("Ingrese ID del cliente: ")) 
                lugares.estacionar_cliente_en_lugar(id_l, id_c) 
            except ValueError: 
                print("Entrada inválida.") 
        elif op == "3": 
            break 
 
def menu_pagos(): 
    while True: 
        print("\n--- SUBMENÚ GESTIÓN DE PAGOS ---") 
        print("1. Registrar nuevo pago") 
        print("2. Consultar historial de pagos") 
        print("3. Volver al menú principal") 
        op = input("Seleccione opción: ").strip() 
        if op == "1": 
            try: 
                id_c = int(input("ID Cliente: ")) 
                tiempo = float(input("Tiempo consumido (en horas/días/meses): ")) 
                reserva = input("Tipo Reserva (hora/dia/mes): ") 
                cat = input("Categoría Vehículo (Motocicleta/Automóvil/Camioneta / SUV/Camión / Autobús): ") 
                metodo = input("Método de Pago (Efectivo/Tarjeta/Transferencia/QR): ") 
                pagos.registrar_pago(id_c, tiempo, reserva, cat, metodo) 
            except ValueError: 
                print("Error en datos numéricos.") 
        elif op == "2": 
            pagos.consultar_estado_pagos() 
        elif op == "3": 
            break 
 
def menu_consultas(): 
    while True: 
        print("\n--- SUBMENÚ CONSULTAS COMBINADAS (SQL JOIN) ---") 
        print("1. Consultar Clientes con sus Reservas") 
        print("2. Consultar Vehículos con su Categoría y Propietario") 
        print("3. Consultar Pagos realizados por cada Cliente") 
        print("4. Volver al menú principal") 
        op = input("Seleccione opción: ").strip() 
        if op == "1": 
            consultas.consultar_clientes_con_reservas() 
        elif op == "2": 
            consultas.consultar_vehiculos_con_categoria() 
        elif op == "3": 
            consultas.consultar_pagos_por_cliente() 
        elif op == "4": 
            break 
 
def main(): 
    init_db() 
    while True: 
        print("\n" + "="*50) 
        print("  SISTEMA INTEGRADO DE GESTIÓN DE ESTACIONAMIENTO") 
        print("="*50) 
        print("1. Módulo de Clientes") 
        print("2. Módulo de Categorías de Vehículos") 
        print("3. Módulo de Lugares y Estacionamiento") 
        print("4. Módulo de Pagos y Tarifas") 
        print("5. Reportes y Consultas SQL Combinadas") 
        print("6. Salir") 
        opcion = input("\nSeleccione opción (1-6): ").strip() 
         
        if opcion == "1": 
            menu_clientes() 
        elif opcion == "2": 
            menu_categorias() 
        elif opcion == "3": 
            menu_lugares() 
        elif opcion == "4": 
            menu_pagos() 
        elif opcion == "5": 
            menu_consultas() 
        elif opcion == "6": 
            print("\n¡Gracias por utilizar el sistema de gestión de estacionamiento!") 
            break 
        else: 
            print("\n[Aviso] Opción no válida.") 
 
if __name__ == "__main__": 
    main() 