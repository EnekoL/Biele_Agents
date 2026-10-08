import xml.etree.ElementTree as ET
import csv

def parse_xml_to_csv(xml_file, csv_file):
    # Parsear el XML
    tree = ET.parse(xml_file)
    root = tree.getroot()

    with open(csv_file, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f, delimiter=';')
        
        # Cabeceras: DB_Name en una columna independiente, Variable_Name sin alterar
        writer.writerow(['PLC_Name', 'DB_Number', 'DB_Name', 'Variable_Name', 'Data Type', 'Offset', 'Bit'])

        for process in root.findall('.//process'):
            plc_name = process.get('name')
            
            for group in process.findall('.//group'):
                db_number = group.get('dbnumber') or group.get('number') or 'N/A'
                
                for field in group.findall('.//field'):
                    raw_name = field.get('name')
                    field_type = field.get('type')
                    offset = field.get('offset', '')
                    bit = field.get('bit', '')

                    # 1. Separar el nombre del DB del resto de la jerarquía
                    if raw_name and '.' in raw_name:
                        # Si empieza por punto (ej. ".SortId" en los definitions), el DB es vacío
                        if raw_name.startswith('.'):
                            db_name = ''
                            rest_of_name = raw_name[1:]
                        else:
                            db_name, rest_of_name = raw_name.split('.', 1)
                    else:
                        db_name = 'General' # Variables que no tienen punto en el nombre
                        rest_of_name = raw_name

                    # 2. Asignar BOOL a los bits anidados que no declaran tipo
                    if not field_type and bit:
                        field_type = "BOOL"

                    writer.writerow([plc_name, db_number, db_name, rest_of_name, field_type, offset, bit])

if __name__ == "__main__":
    parse_xml_to_csv('pruebas\\ServerManager.dev.xml', 'Variables_Biele_TIA_Portal.csv')
    print("Extracción completada. Jerarquía de variables conservada con éxito.")