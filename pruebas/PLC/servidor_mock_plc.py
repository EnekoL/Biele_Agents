import asyncio
import json
from pathlib import Path
from asyncua import Server

async def main():
    server = Server()
    await server.init()
    server.set_endpoint("opc.tcp://127.0.0.1:4840")
    
    ruta_json = Path(__file__).resolve().with_name("catalogo_plc_ai.json")

    try:
        with open(ruta_json, 'r', encoding='utf-8') as f:
            catalogo = json.load(f)
    except Exception as e:
        print(f"[❌] Ezin izan da katalogoa kargatu: {e}")
        return

    await server.register_namespace("urn:biele:plc-mock:reserved")
    idx = await server.register_namespace("http://biele.com/UA/")
    if idx != 3:
        raise RuntimeError(f"El catálogo espera NodeIds ns=3, pero el servidor registró el namespace Biele como ns={idx}.")
    objects = server.nodes.objects
    
    print("🚀 Levantando gemelo digital de PLCs (Sincronizado con IA)...")
    
    for maquina, info in catalogo.items():
        print(f"\n📦 Construyendo máquina: {maquina}")
        obj = await objects.add_object(idx, maquina)
        variables = info.get("variables", {})
        
        for var_info in variables.values():
            node_id = var_info["node_id"]
            try:
                # Nodoa sortu JSON-ak esaten duen ID zehatzarekin eta 2 balioa (Running) jarri adibide gisa
                my_var = await obj.add_variable(node_id, var_info.get("descripcion_ia", "Variable"), 2)
                await my_var.set_writable()
                print(f"   [+] Nodo creado: {node_id}")
            except Exception as e:
                print(f"   [❌] No se pudo crear el nodo {node_id}: {e}")

    print("\n✅ Servidor OPC-UA Mock corriendo perfectamente en opc.tcp://127.0.0.1:4840")
    
    async with server:
        while True:
            await asyncio.sleep(1)

if __name__ == "__main__":
    asyncio.run(main())