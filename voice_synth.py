"""
Sintetizador de voz simplificado para generar muestras de prueba.
No pretende sonar realista: pretende producir una señal de la que Praat
pueda extraer pitch / jitter / shimmer / HNR de forma coherente y controlada,
para validar el pipeline de deteccion de desviaciones.

Modelo fuente-filtro:
  - Fuente: tren de pulsos glotales a F0(t), con jitter (perturbacion de periodo)
    y shimmer (perturbacion de amplitud).
  - Filtro: resonadores de formantes (vocal /a/ aprox) -> timbre vocalico.
  - Prosodia: segmentos sonoros ("silabas") separados por pausas -> controla
    velocidad de habla y proporcion de pausa.
  - Aspiracion: ruido gaussiano filtrado -> controla HNR.
"""
import numpy as np
from scipy.signal import lfilter

SR = 16000  # sample rate


def _formant_filter(x, sr, formants=((730, 90), (1090, 110), (2440, 120))):
    """Aplica resonadores de formantes en cascada (vocal /a/ por defecto)."""
    y = x.copy()
    for f, bw in formants:
        r = np.exp(-np.pi * bw / sr)
        theta = 2 * np.pi * f / sr
        a = [1.0, -2 * r * np.cos(theta), r * r]
        b = [1.0 - r]  # ganancia aprox unitaria en resonancia
        y = lfilter(b, a, y)
    return y


def _rosenberg_pulse(length):
    """Pulso glotal suave (Rosenberg): apertura + cierre asimetrico."""
    if length < 4:
        return np.zeros(max(length, 1))
    op = int(0.6 * length)  # fase abierta
    cp = length - op        # fase de cierre
    t1 = np.linspace(0, 1, op, endpoint=False)
    t2 = np.linspace(0, 1, cp, endpoint=False)
    rise = 0.5 * (1 - np.cos(np.pi * t1))          # subida suave
    fall = np.cos(0.5 * np.pi * t2)                 # bajada
    return np.concatenate([rise, fall])


def _glottal_source(dur, sr, f0_mean, f0_std, jitter, shimmer, rng):
    """Genera tren de pulsos glotales (con forma) con jitter y shimmer."""
    n = int(dur * sr)
    src = np.zeros(n)
    t = 0.0
    while True:
        drift = f0_std * np.sin(2 * np.pi * 0.5 * t)
        f0 = f0_mean + drift + rng.normal(0, f0_std * 0.3)
        f0 = max(60, f0)
        period = 1.0 / f0
        # jitter: perturbacion relativa del periodo
        period *= (1.0 + rng.normal(0, jitter))
        plen = max(1, int(period * sr))
        idx = int(t * sr)
        if idx + plen >= n:
            break
        # shimmer: perturbacion de amplitud ciclo a ciclo
        amp = 1.0 * (1.0 + rng.normal(0, shimmer))
        src[idx:idx + plen] += amp * _rosenberg_pulse(plen)
        t += period
    return src


def synth_voice(dur=8.0, sr=SR, f0_mean=140.0, f0_std=18.0,
                jitter=0.012, shimmer=0.04, speech_rate=1.0,
                pause_ratio=0.25, hnr_noise=0.02, energy=1.0, seed=None):
    """
    Sintetiza una muestra de voz-lectura con los parametros dados.

    Parametros (mayor = ...):
      f0_mean     : altura media de la voz (Hz)
      f0_std      : variabilidad de pitch (expresividad/entonacion)
      jitter      : inestabilidad de periodo (fatiga/tension)
      shimmer     : inestabilidad de amplitud (fatiga/tension)
      speech_rate : velocidad de habla (1.0 = normal)
      pause_ratio : proporcion de silencio (fatiga -> mas pausas)
      hnr_noise   : aspiracion/soplo (fatiga -> voz mas "apagada")
      energy      : intensidad global
    """
    rng = np.random.default_rng(seed)
    # estructura silabica: silabas de ~0.18s / speech_rate, con pausas
    syl_dur = 0.18 / speech_rate
    out = []
    t_total = 0.0
    while t_total < dur:
        # silaba sonora
        s = _glottal_source(syl_dur, sr, f0_mean, f0_std, jitter, shimmer, rng)
        s = _formant_filter(s, sr)
        # envolvente suave por silaba
        env = np.hanning(len(s)) if len(s) > 1 else np.ones(len(s))
        s = s * env
        out.append(s)
        t_total += syl_dur
        # pausa probabilistica
        if rng.random() < pause_ratio:
            pause_len = int(rng.uniform(0.08, 0.25) * sr)
            out.append(np.zeros(pause_len))
            t_total += pause_len / sr
    y = np.concatenate(out)[: int(dur * sr)]
    # normalizar y aplicar energia
    if np.max(np.abs(y)) > 0:
        y = y / np.max(np.abs(y))
    # aspiracion (ruido) MODULADA por la envolvente -> baja HNR sin ensuciar pausas
    env = np.abs(y)
    # suavizar envolvente
    win = max(1, int(0.005 * sr))
    env_smooth = np.convolve(env, np.ones(win) / win, mode="same")
    noise = rng.normal(0, hnr_noise, len(y)) * env_smooth
    y = y + noise
    y = y * energy
    # normalizacion final suave
    peak = np.max(np.abs(y))
    if peak > 0:
        y = 0.95 * y / peak
    return y.astype(np.float32), sr
