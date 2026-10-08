using System.Collections.Generic;

namespace B4571.Common.Enums
{
    public static class Workcenter
    {
        public const string StripCutting = "411";
        public const string EdgeBanding = "421";
        public const string WrappingLine1 = "431";
        public const string WrappingLine2 = "432";
        public const string FormatSaw1 = "441";
        public const string FormatSaw2 = "442";
        public const string IMADrillingSideboards = "451";
        public const string IMADrillingShelvesL1 = "461";
        public const string IMADrillingShelvesL2 = "462";

        public static List<string> All => new List<string> { StripCutting, EdgeBanding, WrappingLine1, WrappingLine2, FormatSaw1, FormatSaw2, IMADrillingSideboards, IMADrillingShelvesL1, IMADrillingShelvesL2 };

        private static readonly Dictionary<string, string> DisplayNames = new Dictionary<string, string>
        {
            { StripCutting, "Strip Cutting" },
            { EdgeBanding, "Edge Banding" },
            { WrappingLine1, "Wrapping Line 1" },
            { WrappingLine2, "Wrapping Line 2" },
            { FormatSaw1, "Format Saw 1" },
            { FormatSaw2, "Format Saw 2" },
            { IMADrillingSideboards, "IMA Drilling Sideboards" },
            { IMADrillingShelvesL1, "IMA Drilling Shelves L1" },
            { IMADrillingShelvesL2, "IMA Drilling Shelves L2" }
        };

        public static string GetDisplayName(string workcenter)
        {
            if (workcenter != null && DisplayNames.TryGetValue(workcenter, out string name))
                return name;
            return workcenter;
        }
    }
}
