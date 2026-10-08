using System.Collections.Generic;
using System.Linq;

namespace B4571.Common.Enums
{
    // Una entidad PLC. Es la unica fuente de verdad para las alarmas:
    //   - Id  -> valor que se guarda en dbo.Warnings.Source (identifica al PLC).
    //   - Name-> clave estable usada en el XML (atributo plc="...") y en logs.
    // El Id se asigna a mano como codigo estable; NO se deriva de la IP (un PLC
    // futuro en otra subred podria repetir el ultimo octeto). Ver Plcs.Validate().
    public class PlcDevice
    {
        public int Id { get; set; }
        public string Name { get; set; }
        public string DisplayName { get; set; }
        public string Ip { get; set; }
    }

    public static class Plcs
    {
        // 14 PLCs fisicos (PLC16 Right/Left comparten IP -> una sola entrada).
        // Anadir un PLC futuro = anadir una fila aqui + una linea <process> en el XML.
        public static readonly List<PlcDevice> All = new List<PlcDevice>
        {
            new PlcDevice { Id = 19, Name = "PLC_LineInput",       DisplayName = "Line Input",          Ip = "10.139.221.19" },
            new PlcDevice { Id = 2,  Name = "PLC_StripCutting",    DisplayName = "Strip Cutting",       Ip = "10.139.221.2"  },
            new PlcDevice { Id = 4,  Name = "PLC4_EdgeBanding",    DisplayName = "Edge Banding 4",      Ip = "10.139.221.4"  },
            new PlcDevice { Id = 5,  Name = "PLC5_EdgeBanding",    DisplayName = "Edge Banding 5",      Ip = "10.139.221.5"  },
            new PlcDevice { Id = 3,  Name = "PLC_Buffer2",         DisplayName = "Buffer 2",            Ip = "10.139.221.3"  },
            new PlcDevice { Id = 8,  Name = "PLC8_WrappingLine1",  DisplayName = "Wrapping Line 1 (8)", Ip = "10.139.221.8"  },
            new PlcDevice { Id = 9,  Name = "PLC9_WrappingLine1",  DisplayName = "Wrapping Line 1 (9)", Ip = "10.139.222.9"  },
            new PlcDevice { Id = 10, Name = "PLC10_WrappingLine2", DisplayName = "Wrapping Line 2 (10)",Ip = "10.139.221.10" },
            new PlcDevice { Id = 11, Name = "PLC11_WrappingLine2", DisplayName = "Wrapping Line 2 (11)",Ip = "10.139.222.11" },
            new PlcDevice { Id = 12, Name = "PLC12_Buffer3",       DisplayName = "Buffer 3 (12)",       Ip = "10.139.222.12" },
            new PlcDevice { Id = 14, Name = "PLC14_Buffer3",       DisplayName = "Buffer 3 (14)",       Ip = "10.139.222.14" },
            new PlcDevice { Id = 13, Name = "PLC13_FormatSaw",     DisplayName = "Format Saw (13)",     Ip = "10.139.222.13" },
            new PlcDevice { Id = 15, Name = "PLC15_FormatSaw",     DisplayName = "Format Saw (15)",     Ip = "10.139.222.15" },
            new PlcDevice { Id = 16, Name = "PLC16_Buffer4",       DisplayName = "Buffer 4 (16)",       Ip = "10.139.222.16" },
        };

        public static PlcDevice ByName(string name)
        {
            if (string.IsNullOrWhiteSpace(name)) return null;
            return All.FirstOrDefault(p => p.Name == name);
        }

        public static PlcDevice ById(int id)
        {
            return All.FirstOrDefault(p => p.Id == id);
        }

        // Guard de unicidad. NO lanza excepcion (el catalogo lo usa tambien la HMI):
        // devuelve la lista de problemas para que el lado server los loguee al arrancar.
        public static IEnumerable<string> Validate()
        {
            var problems = new List<string>();

            var dupIds = All.GroupBy(p => p.Id).Where(g => g.Count() > 1).Select(g => g.Key);
            foreach (var id in dupIds)
                problems.Add($"Id duplicado: {id}");

            var dupNames = All.GroupBy(p => p.Name).Where(g => g.Count() > 1).Select(g => g.Key);
            foreach (var name in dupNames)
                problems.Add($"Name duplicado: {name}");

            return problems;
        }
    }
}
