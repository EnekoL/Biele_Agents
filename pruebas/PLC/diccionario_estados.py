# diccionario_estados.py

ESTADOS_ZONA = {
    0: "Manual",
    1: "Stopped",
    2: "Running",
    3: "SafetyNoOk",
    4: "FaultStopped",
    5: "FaultStopping",
    6: "RunningCtrldStop",
    7: "StoppedWaittingAirPreesure",
    8: "LineMayorFaultOrRecovering"
}

ESTADOS_ORDEN = {
    0: "Pending",
    1: "Running",
    2: "Paused",
    3: "Canceled"
}

ESTADOS_PILA = {
    0: "Pending",
    1: "Started",
    2: "Finished",
    3: "Canceled"
}

# Función de ayuda para inferir el tipo de estado según el nombre de la variable
def traducir_estado(nombre_variable: str, valor_numerico: int) -> str:
    nombre_lower = nombre_variable.lower()
    
    # Si la variable tiene que ver con un "status" de zona, rodillo o bogie
    if "status" in nombre_lower or "zone" in nombre_lower or "roller" in nombre_lower:
        if valor_numerico in ESTADOS_ZONA:
            return f"{valor_numerico} ({ESTADOS_ZONA[valor_numerico]})"
            
    # Si es el estado de un Work Order / Receta
    elif "workorder" in nombre_lower or "order" in nombre_lower:
        if valor_numerico in ESTADOS_ORDEN:
            return f"{valor_numerico} ({ESTADOS_ORDEN[valor_numerico]})"
            
    # Si es el estado de una Pila (Stack)
    elif "stack" in nombre_lower:
        if valor_numerico in ESTADOS_PILA:
            return f"{valor_numerico} ({ESTADOS_PILA[valor_numerico]})"
            
    # Si no encaja en los patrones conocidos, devolvemos el número crudo
    return str(valor_numerico)