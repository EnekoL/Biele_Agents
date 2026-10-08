import asyncio
from asyncua import Server, ua

async def main():
    # 1. Inicializamos el servidor local
    server = Server()
    await server.init()
    server.set_endpoint("opc.tcp://localhost:4840/freeopcua/server/")
    server.set_server_name("Simulador PLC Biele S7-1500")

    # 2. Configuramos el espacio de nombres (Namespace)
    uri = "http://biele.digital/plc"
    idx = await server.register_namespace(uri)

    # 3. Creamos el Bloque de Datos (DB) y las variables
    db_obj = await server.nodes.objects.add_object(idx, "DB_OperationAssistant")
    
    # Añadimos las variables simulando la estructura del S7-1500
    var_of = await db_obj.add_variable(idx, "Active_WO", "WO-Inicial")
    var_seguridad = await db_obj.add_variable(idx, "Safety_Status", "RUN")
    
    # Hacemos que se puedan modificar
    await var_of.set_writable()
    await var_seguridad.set_writable()

    print(f"==================================================")
    print(f"[PLC FALSO] Servidor OPC-UA iniciado con éxito.")
    print(f"[PLC FALSO] Endpoint: opc.tcp://localhost:4840/freeopcua/server/")
    print(f"[PLC FALSO] NodeID Orden Fab: {var_of.nodeid}")
    print(f"[PLC FALSO] NodeID Seguridad: {var_seguridad.nodeid}")
    print(f"==================================================\n")

    # 4. Bucle infinito simulando la producción de la máquina
    async with server:
        contador_of = 88000
        while True:
            await asyncio.sleep(5) # Cada 5 segundos cambia de orden
            contador_of += 1
            nueva_of = f"WO-{contador_of}"
            
            # Escribimos el nuevo valor en el "PLC"
            await var_of.write_value(nueva_of)
            print(f"[PLC FALSO] Producción avanzada -> Orden actual: {nueva_of}")

if __name__ == "__main__":
    asyncio.run(main())