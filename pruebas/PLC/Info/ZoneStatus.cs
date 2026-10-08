namespace B4571.Common.Enums
{
    public enum ZoneStatus
    {
        Manual = 0,
        Stopped = 1,
        Running = 2,
        SafetyNoOk = 3,
        FaultStopped = 4,
        FaultStopping = 5,
        RunningCtrldStop = 6,
        StoppedWaittingAirPreesure = 7,
        LineMayorFaultOrRecovering = 8
    }
}