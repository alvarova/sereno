"""
Sereno - Prueba de concepto end-to-end.

Simula el flujo real:
  1) El profesional graba N lecturas del texto fijo en estado normal -> BASELINE
  2) Durante la jornada, cada lectura nueva se compara contra su baseline
  3) El sistema reporta desviacion y sugiere pausa preventiva si corresponde

Como no hay audio real, las muestras se generan con el sintetizador
parametrico (voice_synth). Con audio real, el pipeline es identico:
solo cambia la fuente de las senales.
"""
import numpy as np
from voice_synth import synth_voice
from detector import BaselineDetector

rng = np.random.default_rng(42)


def normal_sample(seed):
    """Muestra en estado normal, con variabilidad natural entre tomas."""
    return synth_voice(
        f0_mean=142 + rng.normal(0, 4),
        f0_std=16 + rng.normal(0, 2),
        jitter=0.012 + abs(rng.normal(0, 0.002)),
        shimmer=0.045 + abs(rng.normal(0, 0.008)),
        speech_rate=1.0 + rng.normal(0, 0.05),
        pause_ratio=0.25 + rng.normal(0, 0.03),
        hnr_noise=0.02 + abs(rng.normal(0, 0.004)),
        seed=seed,
    )[0], 16000


def fatigued_sample(level, seed):
    """
    Muestra fatigada. level in [0,1] interpola de normal -> fatiga marcada.
    """
    L = level
    return synth_voice(
        f0_mean=142 - 28 * L,
        f0_std=16 - 9 * L,
        jitter=0.012 + 0.02 * L,
        shimmer=0.045 + 0.05 * L,
        speech_rate=1.0 - 0.25 * L,
        pause_ratio=0.25 + 0.22 * L,
        hnr_noise=0.02 + 0.05 * L,
        seed=seed,
    )[0], 16000


def main():
    print("=" * 68)
    print("  SERENO · PoC — deteccion de fatiga vocal por desviacion basal")
    print("=" * 68)

    # ---- 1. BASELINE ----
    print("\n[1] Construyendo baseline (10 lecturas en estado normal)...")
    baseline_signals = []
    for i in range(10):
        s, sr = normal_sample(seed=100 + i)
        baseline_signals.append(s)
    det = BaselineDetector().fit(baseline_signals, sr)
    print(f"    Baseline listo. Umbral personal (Mahalanobis) = {det.threshold_:.2f}")
    print(f"    Distancias intra-baseline: media={np.mean(det.baseline_scores_):.2f} "
          f"max={np.max(det.baseline_scores_):.2f}")

    # ---- 2. EVALUACION ----
    print("\n[2] Evaluando muestras nuevas...\n")
    tests = [
        ("Control normal #1", *normal_sample(seed=200)),
        ("Control normal #2", *normal_sample(seed=201)),
        ("Fatiga leve (L=0.35)", *fatigued_sample(0.35, seed=300)),
        ("Fatiga moderada (L=0.6)", *fatigued_sample(0.60, seed=301)),
        ("Fatiga marcada (L=0.9)", *fatigued_sample(0.90, seed=302)),
    ]

    print(f"    {'MUESTRA':<26}{'MAHAL.':>8}{'SEVER.':>8}  {'ESTADO':<16}")
    print(f"    {'-'*26}{'-'*8}{'-'*8}  {'-'*16}")
    results = []
    for name, sig, sr in tests:
        rep = det.score(sig, sr)
        status, msg = det.recommend(rep)
        results.append((name, rep, status, msg))
        flag = "" if not rep["is_anomaly"] else " *"
        print(f"    {name:<26}{rep['mahalanobis']:>8.2f}{rep['severity']:>8.2f}  "
              f"{status:<16}{flag}")

    # ---- 3. DETALLE de la muestra mas desviada ----
    print("\n[3] Detalle — principales factores de desviacion (fatiga marcada):")
    worst = results[-1][1]
    labels = {
        "f0_mean": "altura de voz", "f0_std": "entonacion",
        "f0_range": "rango tonal", "voiced_ratio": "fonacion",
        "jitter_local": "estab. de periodo", "shimmer_local": "estab. de amplitud",
        "hnr_mean": "claridad (HNR)", "intensity_mean": "energia",
        "intensity_std": "dinamica", "silence_ratio": "silencio",
        "pause_rate": "cortes",
    }
    for k, direction, z, dz in worst["top_drivers"]:
        arrow = "↑" if direction == "sube" else "↓"
        print(f"      {arrow} {labels[k]:<20} {direction:<5} (z={z:+.1f})")
    print(f"\n    → {results[-1][2]}: {results[-1][3]}")

    print("\n" + "=" * 68)
    return det, results


if __name__ == "__main__":
    main()
