using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace B4571.Common.Enums
{
    public enum RejectStatus
    {
        Pending = 0,
        Running = 1,
        Paused = 2,
        Canceled = 3
    }

    public enum StackStatus
    {
        Pending= 0,
        Started = 1,
        Finished = 2,
        Canceled = 3
    }
}
