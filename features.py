"""
Extractor de features acusticos con Praat (parselmouth).
Devuelve un vector de descriptores tipo eGeMAPS relevantes para
estado animico / fatiga / tension vocal.
"""
import numpy as np
import parselmouth
from parselmouth.praat import call


def extract_features(signal, sr):
    """Extrae features acusticos de una senal mono (float32, -1..1)."""
    snd = parselmouth.Sound(signal.astype(np.float64), sampling_frequency=sr)

    feats = {}

    # ---- Pitch (F0) ----
    pitch = snd.to_pitch(time_step=0.01, pitch_floor=60, pitch_ceiling=400)
    f0 = pitch.selected_array["frequency"]
    f0_voiced = f0[f0 > 0]
    if len(f0_voiced) > 0:
        feats["f0_mean"] = float(np.mean(f0_voiced))
        feats["f0_std"] = float(np.std(f0_voiced))
        feats["f0_range"] = float(np.percentile(f0_voiced, 95) - np.percentile(f0_voiced, 5))
        feats["voiced_ratio"] = float(len(f0_voiced) / len(f0))
    else:
        feats.update({"f0_mean": 0, "f0_std": 0, "f0_range": 0, "voiced_ratio": 0})

    # ---- Jitter & Shimmer (via PointProcess) ----
    try:
        pp = call(snd, "To PointProcess (periodic, cc)", 60, 400)
        feats["jitter_local"] = float(call(pp, "Get jitter (local)", 0, 0, 1e-4, 0.02, 1.3))
        feats["shimmer_local"] = float(
            call([snd, pp], "Get shimmer (local)", 0, 0, 1e-4, 0.02, 1.3, 1.6))
    except Exception:
        feats["jitter_local"] = 0.0
        feats["shimmer_local"] = 0.0

    # ---- HNR (harmonics-to-noise ratio) ----
    try:
        harm = snd.to_harmonicity_cc(time_step=0.01, minimum_pitch=60)
        hnr_vals = harm.values[harm.values != -200]
        feats["hnr_mean"] = float(np.mean(hnr_vals)) if len(hnr_vals) else 0.0
    except Exception:
        feats["hnr_mean"] = 0.0

    # ---- Intensidad / energia ----
    try:
        intensity = snd.to_intensity(time_step=0.01)
        iv = intensity.values[0]
        iv = iv[np.isfinite(iv)]
        feats["intensity_mean"] = float(np.mean(iv)) if len(iv) else 0.0
        feats["intensity_std"] = float(np.std(iv)) if len(iv) else 0.0
    except Exception:
        feats["intensity_mean"] = 0.0
        feats["intensity_std"] = 0.0

    # ---- Ritmo: proporcion de silencio y tasa de pausas ----
    # umbral de energia sobre envolvente RMS
    frame = int(0.02 * sr)
    hop = int(0.01 * sr)
    rms = np.array([
        np.sqrt(np.mean(signal[i:i + frame] ** 2))
        for i in range(0, len(signal) - frame, hop)
    ])
    if len(rms) > 0:
        thr = 0.15 * np.max(rms)
        silent = rms < thr
        feats["silence_ratio"] = float(np.mean(silent))
        # nro de transiciones sonoro->silencio por segundo (tasa de pausas)
        transitions = np.sum((~silent[:-1]) & (silent[1:]))
        dur_s = len(signal) / sr
        feats["pause_rate"] = float(transitions / dur_s)
    else:
        feats["silence_ratio"] = 0.0
        feats["pause_rate"] = 0.0

    return feats


FEATURE_ORDER = [
    "f0_mean", "f0_std", "f0_range", "voiced_ratio",
    "jitter_local", "shimmer_local", "hnr_mean",
    "intensity_mean", "intensity_std",
    "silence_ratio", "pause_rate",
]


def features_to_vector(feats):
    return np.array([feats[k] for k in FEATURE_ORDER], dtype=float)
