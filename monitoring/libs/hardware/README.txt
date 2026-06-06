Bundled hardware sensor libraries (used as optional fallbacks).
These were previously used to read sensors from third-party libraries.
LibreHardwareMonitor support has been removed from this project due to antivirus
false-positives; the application now relies on psutil, WMI and OpenHardwareMonitor
when available.

Files that may have been present previously:
  - HidSharp.dll
