from collections import deque
from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class MonitorState:
    cpu_history: deque = field(default_factory=lambda: deque(maxlen=120))
    memory_history: deque = field(default_factory=lambda: deque(maxlen=120))
    gpu_history: deque = field(default_factory=lambda: deque(maxlen=120))
    disk_history: deque = field(default_factory=lambda: deque(maxlen=120))
    eth_history: deque = field(default_factory=lambda: deque(maxlen=120))
    cpu_core_histories: list = field(default_factory=list)
    cpu_temp_history: deque = field(default_factory=lambda: deque(maxlen=120))
    prev_disk_io: Optional[Any] = None
    prev_net_io: Optional[Any] = None
    last_gpu_data: Optional[Dict[str, Any]] = None
    session_peaks: Dict[str, Any] = field(default_factory=lambda: {"cpu": 0, "gpu": 0, "ram": 0, "cpu_temp": 0, "gpu_temp": 0})


def init_state(monitor, max_history=120):
    # Attach a MonitorState instance to the monitor for centralized state
    state = MonitorState()
    state.cpu_history = deque(maxlen=max_history)
    state.memory_history = deque(maxlen=max_history)
    state.gpu_history = deque(maxlen=max_history)
    state.disk_history = deque(maxlen=max_history)
    state.eth_history = deque(maxlen=max_history)
    state.cpu_temp_history = deque(maxlen=max_history)
    core_count = monitor.cpu_core_count if hasattr(monitor, 'cpu_core_count') else 1
    state.cpu_core_histories = [deque(maxlen=max_history) for _ in range(core_count)]
    state.prev_disk_io = monitor.prev_disk_io if hasattr(monitor, 'prev_disk_io') else None
    state.prev_net_io = monitor.prev_net_io if hasattr(monitor, 'prev_net_io') else None
    state.last_gpu_data = monitor.last_gpu_data if hasattr(monitor, 'last_gpu_data') else None
    monitor.state = state
    return state
