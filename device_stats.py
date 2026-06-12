import socket
import time

try:
    import psutil
    _HAS_PSUTIL = True
except ImportError:
    _HAS_PSUTIL = False

from plyer import battery


class DeviceStats:
    def __init__(self):
        self._prev_total = None
        self._prev_idle = None

    def read_device_stats(self):
        battery_pct = self._read_battery_pct()
        is_charging = self._read_charging_state()
        cpu_pct = self._read_cpu_percent()
        memory_pct = self._read_memory_percent()
        network_online, network_latency = self._probe_network()

        return {
            "battery_pct": battery_pct,
            "is_charging": is_charging,
            "cpu_pct": cpu_pct,
            "memory_pct": memory_pct,
            "network_online": network_online,
            "network_latency": network_latency,
        }

    def _read_battery_pct(self):
        try:
            state = battery.status
            if isinstance(state, dict):
                pct = state.get("percentage")
                if isinstance(pct, (int, float)):
                    return max(0, min(100, float(pct)))
        except Exception:
            pass
        return None

    def _read_charging_state(self):
        try:
            state = battery.status
            if isinstance(state, dict):
                return bool(state.get("isCharging") or state.get("is_charging"))
        except Exception:
            pass
        return False

    def _read_cpu_percent(self):
        if _HAS_PSUTIL:
            try:
                return psutil.cpu_percent(interval=None)
            except Exception:
                pass

        try:
            with open("/proc/stat", "r") as stat_file:
                line = stat_file.readline()
            if not line.startswith("cpu "):
                return None
            parts = [int(x) for x in line.split()[1:]]
            idle = parts[3]
            total = sum(parts)
            if self._prev_total is None:
                self._prev_total = total
                self._prev_idle = idle
                return 0
            delta_total = total - self._prev_total
            delta_idle = idle - self._prev_idle
            self._prev_total = total
            self._prev_idle = idle
            if delta_total <= 0:
                return 0
            return max(0, min(100, 100.0 * (delta_total - delta_idle) / delta_total))
        except Exception:
            return None

    def _read_memory_percent(self):
        if _HAS_PSUTIL:
            try:
                mem = psutil.virtual_memory()
                return mem.percent
            except Exception:
                pass

        try:
            info = {}
            with open("/proc/meminfo", "r") as mem_file:
                for line in mem_file:
                    parts = line.split()
                    if len(parts) < 2:
                        continue
                    key = parts[0].rstrip(":")
                    value = int(parts[1])
                    info[key] = value
            total = info.get("MemTotal")
            available = info.get("MemAvailable")
            if total and available:
                used = total - available
                return max(0, min(100, used * 100.0 / total))
        except Exception:
            pass

        return None

    def _probe_network(self):
        host = ("8.8.8.8", 53)
        timeout = 2.0
        try:
            start = time.time()
            sock = socket.create_connection(host, timeout)
            sock.close()
            latency = time.time() - start
            return True, max(0.0, min(5.0, latency))
        except Exception:
            return False, None
