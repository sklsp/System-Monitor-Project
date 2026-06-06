import sys, subprocess, json
out = {'python': sys.executable}
try:
    import GPUtil
    out['gputil'] = {'version': getattr(GPUtil, '__version__', 'unknown'), 'module': getattr(GPUtil, '__file__', None)}
    try:
        g = GPUtil.getGPUs()
        out['gputil_gpus'] = [{'name': getattr(x,'name',None),'load':getattr(x,'load',None),'memoryUtil':getattr(x,'memoryUtil',None),'memoryUsed':getattr(x,'memoryUsed',None),'memoryTotal':getattr(x,'memoryTotal',None),'temperature':getattr(x,'temperature',None)} for x in g]
    except Exception as e:
        out['gputil_error'] = str(e)
except Exception as e:
    out['gputil_import_error'] = str(e)
# nvidia-smi
try:
    p = subprocess.run(['nvidia-smi','--query-gpu=name,utilization.gpu','--format=csv,noheader,nounits'], capture_output=True, text=True, timeout=2)
    out['nvidia_smi'] = {'rc': p.returncode, 'stdout': p.stdout.strip(), 'stderr': p.stderr.strip()}
except Exception as e:
    out['nvidia_smi_error'] = str(e)
print(json.dumps(out, indent=2))
