using System.Collections.Generic;
using System.Linq;

namespace B4571.Common.Enums
{
    // Mapa zona -> PLCs cuyo Plcs.Id se guarda en dbo.Warnings.Source.
    // La pantalla de alarmas del HMI selecciona por zona (workcenter o zona
    // solo-alarmas) y el filtrado real contra la tabla es por estos sources.
    //
    //  - LineInput cuelga del workcenter 411 (StripCutting), por decision de planta.
    //  - Los Buffers no son workcenters: son zonas solo-alarmas (claves Buffer2/3/4,
    //    las anade el combo de la pantalla de Warnings, no Workcenter.All).
    //  - Los workcenters IMA (451/461/462) no tienen PLC de alarmas todavia ->
    //    sin entrada (GetSources devuelve lista vacia y la pantalla no pide nada).
    //
    // Anadir un PLC futuro = una fila en Plcs.All + su nombre en la zona que toque.
    public static class WarningSources
    {
        // Zonas solo-alarmas (no existen en Workcenter.All).
        public const string Buffer2 = "Buffer2";
        public const string Buffer3 = "Buffer3";
        public const string Buffer4 = "Buffer4";

        private static readonly Dictionary<string, string[]> PlcsByZone = new Dictionary<string, string[]>
        {
            { Workcenter.StripCutting,  new[] { "PLC_StripCutting", "PLC_LineInput" } },
            { Workcenter.EdgeBanding,   new[] { "PLC4_EdgeBanding", "PLC5_EdgeBanding" } },
            { Workcenter.WrappingLine1, new[] { "PLC8_WrappingLine1", "PLC9_WrappingLine1" } },
            { Workcenter.WrappingLine2, new[] { "PLC10_WrappingLine2", "PLC11_WrappingLine2" } },
            { Workcenter.FormatSaw1,    new[] { "PLC13_FormatSaw" } },
            { Workcenter.FormatSaw2,    new[] { "PLC15_FormatSaw" } },
            { Buffer2,                  new[] { "PLC_Buffer2" } },
            { Buffer3,                  new[] { "PLC12_Buffer3", "PLC14_Buffer3" } },
            { Buffer4,                  new[] { "PLC16_Buffer4" } },
        };

        // Sources (Plcs.Id) de una zona; lista vacia si la zona no tiene PLCs de alarmas.
        // Se resuelve contra el catalogo Plcs por Name para no duplicar los Ids aqui.
        public static List<int> GetSources(string zoneKey)
        {
            if (string.IsNullOrWhiteSpace(zoneKey) || !PlcsByZone.TryGetValue(zoneKey, out var plcNames))
                return new List<int>();

            return plcNames.Select(Plcs.ByName).Where(p => p != null).Select(p => p.Id).ToList();
        }
    }
}
