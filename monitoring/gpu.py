"""
Robust GPU information collection with multiple fallback methods.

This module attempts to gather GPU data using various methods:
1. GPUtil library (primary method)
2. nvidia-smi command-line tool
3. AMD Adrenalin CLI (for AMD GPUs)
4. WMI/PowerShell for system-level GPU sensors
5. External monitor libraries (LibreHardwareMonitor, OpenHardwareMonitor)
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import Optional, Dict, Any, List

try:
    import GPUtil
except ImportError:
    GPUtil = None


class GPUInfo:
    """Container for GPU information."""
    
    def __init__(self):
        self.name: str = "Unknown"
        self.load: float = 0.0
        self.memory_used: int = 0
        self.memory_total: int = 0
        self.temperature: Optional[float] = None
        self.driver_version: str = "Unknown"
        self.serial_number: str = "Unknown"
        self.vbios_version: str = "Unknown"
        self.pci_bus_id: str = "Unknown"
        self.pci_device_id: str = "Unknown"
        self.pci_subsystem_id: str = "Unknown"
        self.memory_util: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'load': round(self.load * 100, 1),
            'memory_used': self.memory_used,
            'memory_total': self.memory_total,
            'temperature': self.temperature,
            'driver_version': self.driver_version,
            'serial_number': self.serial_number,
            'vbios_version': self.vbios_version,
            'pci_bus_id': self.pci_bus_id,
            'pci_device_id': self.pci_device_id,
            'pci_subsystem_id': self.pci_subsystem_id,
        }


def get_gpu_info() -> List[GPUInfo]:
    """
    Attempt to gather GPU information using multiple methods.
    
    Returns a list of GPUInfo objects, or an empty list if no GPUs are found.
    """
    gpus: List[GPUInfo] = []
    
    # Method 1: Try GPUtil first (most reliable for NVIDIA)
    if GPUtil is not None:
        try:
            gpus_list = GPUtil.getGPUs()
            if gpus_list:
                for gpu in gpus_list:
                    info = GPUInfo()
                    info.name = gpu.name
                    info.load = gpu.load
                    info.memory_util = gpu.memoryUtil
                    info.memory_used = gpu.memoryUsed
                    info.memory_total = gpu.memoryTotal
                    info.temperature = getattr(gpu, "temperature", None)
                    gpus.append(info)
                return gpus
        except Exception as e:
            # GPUtil failed, continue with other methods
            pass
    
    # Method 2: Try nvidia-smi (NVIDIA GPUs only)
    try:
        proc = subprocess.run(
            [
                "nvidia-smi",
                "--query-gpu=name,driver_version,memory.total,memory.used,utilization.gpu,temperature.gpu",
                "--format=csv,noheader,nounits",
            ],
            capture_output=True,
            text=True,
            timeout=2,
        )
        
        if proc.returncode == 0 and proc.stdout.strip():
            lines = proc.stdout.strip().split('\n')
            for line in lines:
                parts = [p.strip() for p in line.split(',')]
                if len(parts) >= 6:
                    info = GPUInfo()
                    info.name = parts[0] or "Unknown"
                    try:
                        info.load = float(parts[4])
                        info.memory_total = int(parts[2].replace('MiB', ''))
                        info.memory_used = int(parts[3].replace('MiB', ''))
                        if len(parts) >= 6 and parts[5]:
                            try:
                                info.temperature = float(parts[5])
                            except ValueError:
                                pass
                    except (ValueError, IndexError):
                        continue
                    gpus.append(info)
            return gpus
    except Exception:
        # nvidia-smi failed or not available
        pass
    
    # Method 3: Try AMD Adrenalin CLI
    try:
        proc = subprocess.run(
            [
                "AdrenalinCLI.exe",
                "--get-gpu-info",
            ],
            capture_output=True,
            text=True,
            timeout=2,
            cwd=str(Path(__file__).resolve().parent / "libs" / "amd")
        )
        
        if proc.returncode == 0 and proc.stdout.strip():
            # Parse AMD CLI output
            for line in proc.stdout.split('\n'):
                if 'GPU' in line.upper() or 'Name:' in line.upper():
                    info = GPUInfo()
                    info.name = "AMD GPU"  # Simplified parsing
                    gpus.append(info)
    except Exception:
        pass
    
    # Method 4: Try WMI for system-level GPU sensors (Windows only)
    if sys.platform.startswith("win"):
        try:
            import win32com.client
            wmi_obj = win32com.client.GetObject(r"winmgmts:\\.\root\wmi")
            
            # Try to get GPU information from WMI classes
            query = "SELECT * FROM Win32_VideoController"
            for controller in wmi_obj.ExecQuery(query):
                info = GPUInfo()
                if hasattr(controller, 'Name'):
                    info.name = str(controller.Name) or "Unknown"
                if hasattr(controller, 'DriverVersion'):
                    info.driver_version = str(controller.DriverVersion) or "Unknown"
                gpus.append(info)
        except Exception:
            pass
    
    # Method 5: Try external monitor libraries (fallback for both NVIDIA and AMD)
    try:
        from monitoring.cpu_temp import _from_bundled_hardware_lib, _hardware_lib_dir
        lib_dir = _hardware_lib_dir()
        if lib_dir is not None:
            # Use the same PowerShell script that works for CPU temps
            proc = subprocess.run(
                [
                    "powershell",
                    "-NoProfile",
                    "-ExecutionPolicy",
                    "Bypass",
                    "-File",
                    str(Path(__file__).resolve().parent / "libs" / "hardware" / "read_cpu_temp.ps1"),
                    "-LibDirectory",
                    str(lib_dir),
                ],
                capture_output=True,
                text=True,
                timeout=20,
            )
            
            if proc.returncode == 0 and proc.stdout.strip():
                # Parse output for GPU-related sensors
                for line in proc.stdout.split('\n'):
                    if any(keyword in line.lower() for keyword in ['gpu', 'graphics', 'geforce', 'radeon']):
                        info = GPUInfo()
                        try:
                            value = float(line.strip().split('=')[1].strip())
                            # This might be temperature or other metric
                            info.temperature = value if 0 < value < 150 else None
                        except (ValueError, IndexError):
                            pass
                        gpus.append(info)
    except Exception:
        pass
    
    return gpus


def get_gpu_load() -> float:
    """
    Get the current GPU load as a percentage.
    
    Returns 0.0 if no GPU is found or if detection fails.
    """
    gpus = get_gpu_info()
    if not gpus:
        return 0.0
    
    # Return average load across all GPUs, or the first one's load
    total_load = sum(gpu.load for gpu in gpus)
    return total_load / len(gpus) if gpus else 0.0


def get_gpu_temperature() -> Optional[float]:
    """
    Get the current GPU temperature.
    
    Returns None if no GPU is found or if detection fails.
    """
    gpus = get_gpu_info()
    for gpu in gpus:
        if gpu.temperature is not None:
            return gpu.temperature
    return None


def has_nvidia_gpu() -> bool:
    """
    Check if an NVIDIA GPU is present.
    
    Returns True if an NVIDIA GPU is detected, False otherwise.
    """
    try:
        proc = subprocess.run(
            ["nvidia-smi", "--query-gpu=name",
             "--format=csv,noheader,nounits"],
            capture_output=True,
            text=True,
            timeout=1,
        )
        return proc.returncode == 0 and proc.stdout.strip()
    except Exception:
        return False


def has_amd_gpu() -> bool:
    """
    Check if an AMD GPU is present.
    
    Returns True if an AMD GPU is detected, False otherwise.
    """
    # Try to run AdrenalinCLI (Windows only)
    if sys.platform.startswith("win"):
        try:
            proc = subprocess.run(
                ["AdrenalinCLI.exe", "--get-gpu-info"],
                capture_output=True,
                text=True,
                timeout=1,
                cwd=str(Path(__file__).resolve().parent / "libs" / "amd")
            )
            return proc.returncode == 0
        except Exception:
            pass
    
    # Try WMI for AMD GPUs
    if sys.platform.startswith("win"):
        try:
            import win32com.client
            wmi_obj = win32com.client.GetObject(r"winmgmts:\\.\root\wmi")
            query = "SELECT * FROM Win32_VideoController"
            for controller in wmi_obj.ExecQuery(query):
                if hasattr(controller, 'Name') and any(
                    keyword in str(controller.Name).lower()
                    for keyword in ['amd', 'radeon', 'ati']
                ):
                    return True
        except Exception:
            pass
    
    return False


def get_gpu_name() -> str:
    """
    Get the name of the primary GPU.
    
    Returns a descriptive string about the detected GPU(s).
    """
    gpus = get_gpu_info()
    if not gpus:
        return "No GPU detected"
    
    # Return the first GPU's name, or a combined description
    primary_name = gpus[0].name
    if len(gpus) > 1:
        names = [gpu.name for gpu in gpus]
        return f"{primary_name} + {len(gpus) - 1} other(s)"
    
    return primary_name or "Unknown GPU"


def get_gpu_memory_info() -> Dict[str, Any]:
    """
    Get detailed memory information for all GPUs.
    
    Returns a dictionary with memory details for each GPU.
    """
    gpus = get_gpu_info()
    if not gpus:
        return {}
    
    result = {}
    for gpu in gpus:
        result[gpu.name] = {
            'total': gpu.memory_total,
            'used': gpu.memory_used,
            'free': max(0, gpu.memory_total - gpu.memory_used),
            'utilization_percent': (gpu.memory_used / gpu.memory_total * 100) if gpu.memory_total > 0 else 0,
        }
    return result


if __name__ == "__main__":
    # Test the GPU detection functions
    print("GPU Detection Test")
    print("=" * 50)
    
    gpus = get_gpu_info()
    if gpus:
        for i, gpu in enumerate(gpus, 1):
            print(f"\nGPU {i}:")
            print(f"  Name: {gpu.name}")
            print(f"  Load: {gpu.load:.2f}%")
            print(f"  Memory Used: {gpu.memory_used}/{gpu.memory_total} MiB")
            if gpu.temperature is not None:
                print(f"  Temperature: {gpu.temperature:.1f}°C")
    else:
        print("No GPUs detected.")
