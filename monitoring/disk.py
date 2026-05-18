import subprocess

def get_disk_busy_percent():
    try:
        proc = subprocess.run(
            ["typeperf", "-sc", "1", r"\\PhysicalDisk(_Total)\\% Disk Time"],
            capture_output=True,
            text=True,
            timeout=3,
        )
        if proc.returncode == 0 and proc.stdout:
            lines = [line.strip() for line in proc.stdout.splitlines() if line.strip()]
            if len(lines) >= 2:
                fields = [field.strip() for field in lines[1].split(',')]
                if len(fields) >= 2:
                    value = fields[1].strip().strip('"')
                    return float(value)
    except Exception:
        pass
    return None
