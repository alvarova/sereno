"""
Carga de audio real. Reemplaza al sintetizador cuando hay grabaciones reales.
El resto del pipeline (features, detector) es identico.

Uso:
    from audio_io import load_audio
    sig, sr = load_audio("lectura_juan_01.wav")
    det.fit([sig1, sig2, ...], sr)     # baseline
    rep = det.score(sig_nueva, sr)     # evaluacion
"""
import numpy as np
import librosa

TARGET_SR = 16000


def load_audio(path, target_sr=TARGET_SR, trim_silence=True):
    """
    Carga un archivo de audio (wav/mp3/flac/...), lo pasa a mono,
    resamplea a target_sr y normaliza. Devuelve (signal float32, sr).
    """
    sig, sr = librosa.load(path, sr=target_sr, mono=True)
    if trim_silence:
        # recorta silencios de inicio/fin (no los internos, que son informativos)
        sig, _ = librosa.effects.trim(sig, top_db=30)
    peak = np.max(np.abs(sig)) if len(sig) else 0
    if peak > 0:
        sig = 0.95 * sig / peak
    return sig.astype(np.float32), sr
