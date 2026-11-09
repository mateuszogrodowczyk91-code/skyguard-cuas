"""Priorytety czasu rzeczywistego.

Linux: SCHED_FIFO (wymaga CAP_SYS_NICE / roota albo limitu rtprio w
/etc/security/limits.conf). Windows: klasa HIGH/REALTIME procesu + priorytet
wątku TIME_CRITICAL, opcjonalnie MMCSS (AvSetMmThreadCharacteristicsW "Pro Audio").
macOS: brak SCHED_FIFO dla zwykłych procesów — tylko nice."""
from __future__ import annotations

import os
import platform
import sys


def describe_platform() -> str:
    return f"{platform.system()} {platform.release()} / Python {sys.version.split()[0]}"


def set_realtime_priority(level: int = 50, mmcss_task: str = "Pro Audio") -> str:
    """Próbuje podnieść priorytet bieżącego wątku/procesu. Nigdy nie rzuca wyjątku.

    Zwraca opis, co się udało (do logu)."""
    sysname = platform.system()
    try:
        if sysname == "Linux":
            prio = max(1, min(level, os.sched_get_priority_max(os.SCHED_FIFO)))
            os.sched_setscheduler(0, os.SCHED_FIFO, os.sched_param(prio))
            return f"Linux SCHED_FIFO prio={prio}"
        if sysname == "Windows":
            import ctypes
            k32 = ctypes.windll.kernel32
            HIGH_PRIORITY_CLASS = 0x80
            THREAD_PRIORITY_TIME_CRITICAL = 15
            k32.SetPriorityClass(k32.GetCurrentProcess(), HIGH_PRIORITY_CLASS)
            k32.SetThreadPriority(k32.GetCurrentThread(), THREAD_PRIORITY_TIME_CRITICAL)
            msg = "Windows HIGH_PRIORITY_CLASS + TIME_CRITICAL"
            try:
                avrt = ctypes.windll.avrt
                idx = ctypes.c_ulong(0)
                h = avrt.AvSetMmThreadCharacteristicsW(mmcss_task, ctypes.byref(idx))
                if h:
                    msg += f" + MMCSS '{mmcss_task}'"
            except Exception:
                pass
            return msg
        os.nice(-5)
        return f"{sysname}: nice -5"
    except PermissionError:
        return f"{sysname}: brak uprawnień do priorytetu RT (działa z normalnym priorytetem)"
    except Exception as e:  # pragma: no cover
        return f"{sysname}: nie ustawiono priorytetu ({e.__class__.__name__})"
