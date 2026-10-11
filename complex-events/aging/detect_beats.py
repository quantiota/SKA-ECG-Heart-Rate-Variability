"""Beat detection — kept so that existing imports keep working.

The detection now lives in ska_complex_events.py (r_peaks and detect): each beat is FOUND
on a cleaned copy (50 Hz notch -> 5-20 Hz QRS band -> moving energy) and MEASURED on the
raw signal. It used to live here, while ska_complex_events.detect() took any raw sample
above 0.5 mV for R, which also caught tall T waves; there is now one detection only.
"""
from ska_complex_events import detect, r_peaks      # the beat detection lives there now


def detect_robust(x, fs=1000):
    """Same as ska_complex_events.detect(): [(events, baseline), ...] per beat."""
    return detect(x, fs)
