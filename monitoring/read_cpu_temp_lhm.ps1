param(
    [Parameter(Mandatory = $true)]
    [string]$DllDirectory
)

$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $DllDirectory
Add-Type -Path (Join-Path $DllDirectory 'LibreHardwareMonitorLib.dll')

$computer = New-Object LibreHardwareMonitor.Hardware.Computer
$computer.IsCpuEnabled = $true
$computer.Open()

$readings = New-Object System.Collections.Generic.List[double]

function Add-TemperatureSensors($hardware) {
    foreach ($sensor in $hardware.Sensors) {
        if ($sensor.SensorType.ToString() -ne 'Temperature') { continue }
        if ($null -eq $sensor.Value) { continue }
        $value = [double]$sensor.Value
        if ($value -ge 1 -and $value -le 120) {
            [void]$readings.Add($value)
        }
    }
}

foreach ($hardware in $computer.Hardware) {
    if ($hardware.HardwareType.ToString() -ne 'Cpu') { continue }
    $hardware.Update()
    Add-TemperatureSensors $hardware
    foreach ($sub in $hardware.SubHardware) {
        $sub.Update()
        Add-TemperatureSensors $sub
    }
}

$computer.Close()
$readings | ForEach-Object { '{0:F1}' -f $_ }
