"""Radar FMCW/CW: range-Doppler, CFAR, MTI/clutter, FFT kątowe, DBSCAN, mikro-Doppler.

UWAGA: wymaga sprzętu radarowego (np. TI mmWave) — brak budżetu na sprzęt,
moduł gotowy na przyszłość i testowany na danych syntetycznych."""
from .cfar import cfar_1d, cfar_2d
from .fmcw import range_fft, range_doppler_map, range_axis, velocity_axis
from .mti import clutter_removal, mti_filter, BackgroundSubtractor, angle_fft
from .cluster import dbscan, cluster_centroids
from .microdoppler import simulate_rotor_echo, micro_doppler_spectrogram, micro_doppler_features

__all__ = ["cfar_1d", "cfar_2d", "range_fft", "range_doppler_map", "range_axis", "velocity_axis",
           "clutter_removal", "mti_filter", "BackgroundSubtractor", "angle_fft", "dbscan", "cluster_centroids",
           "simulate_rotor_echo", "micro_doppler_spectrogram", "micro_doppler_features"]
