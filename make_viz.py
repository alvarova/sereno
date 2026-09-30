"""Genera una visualización de los resultados del PoC (branding ALTTAB)."""
import argparse
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from detector import BaselineDetector
from features import FEATURE_ORDER
import sereno_poc as poc

ORANGE = "#E8500A"
NAVY = "#1A2B5F"
GREEN = "#2E9E5B"
AMBER = "#E8A00A"
GREY = "#8892A6"
DEFAULT_OUTPUT = Path(__file__).resolve().parent / "outputs" / "sereno_resultados.png"


def parse_args():
    parser = argparse.ArgumentParser(
        description="Genera la visualización estática de resultados de Sereno.")
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help=f"Archivo PNG de salida (predeterminado: {DEFAULT_OUTPUT}).",
    )
    return parser.parse_args()


def main(output_path):
    """Ejecuta la demo y guarda la figura en una ruta portable."""
    # --- correr pipeline ---
    poc.rng = np.random.default_rng(42)
    baseline = [poc.normal_sample(seed=100 + i)[0] for i in range(10)]
    sr = 16000
    det = BaselineDetector().fit(baseline, sr)

    samples = [
        ("Control\n#1", poc.normal_sample(seed=200)[0]),
        ("Control\n#2", poc.normal_sample(seed=201)[0]),
        ("Fatiga\nleve", poc.fatigued_sample(0.35, seed=300)[0]),
        ("Fatiga\nmoderada", poc.fatigued_sample(0.60, seed=301)[0]),
        ("Fatiga\nmarcada", poc.fatigued_sample(0.90, seed=302)[0]),
    ]
    names, scores, states = [], [], []
    for name, signal in samples:
        report = det.score(signal, sr)
        names.append(name)
        scores.append(report["mahalanobis"])
        states.append(report["is_anomaly"])

    threshold = det.threshold_
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5.2),
                                   gridspec_kw={"width_ratios": [1.15, 1]})
    fig.patch.set_facecolor("white")

    # ---- Panel 1: score vs umbral ----
    colors = [ORANGE if state else NAVY for state in states]
    bars = ax1.bar(names, scores, color=colors, width=0.62, zorder=3,
                   edgecolor="white", linewidth=1.5)
    ax1.axhspan(0, threshold, color=GREEN, alpha=0.08, zorder=0)
    ax1.axhline(threshold, color=GREEN, lw=2, ls="--", zorder=2)
    ax1.text(4.45, threshold + 0.15, f"umbral personal = {threshold:.1f}", color=GREEN,
             fontsize=9.5, ha="right", va="bottom", fontweight="bold")
    for bar, score in zip(bars, scores):
        ax1.text(bar.get_x() + bar.get_width() / 2, score + 0.2, f"{score:.1f}",
                 ha="center", va="bottom", fontsize=10, color=NAVY, fontweight="bold")
    ax1.set_ylabel("Distancia al basal (Mahalanobis)", fontsize=11, color=NAVY)
    ax1.set_title("Desviación respecto al basal por lectura", fontsize=13,
                  color=NAVY, fontweight="bold", pad=12)
    ax1.set_ylim(0, max(scores) * 1.18)
    ax1.spines[["top", "right"]].set_visible(False)
    ax1.spines[["left", "bottom"]].set_color(GREY)
    ax1.tick_params(colors=NAVY)

    # ---- Panel 2: perfil de z-scores (fatiga marcada) ----
    report = det.score(samples[-1][1], sr)
    labels_es = {
        "f0_mean": "Altura de voz", "f0_std": "Entonación", "f0_range": "Rango tonal",
        "voiced_ratio": "Fonación", "jitter_local": "Estab. periodo",
        "shimmer_local": "Estab. amplitud", "hnr_mean": "Claridad (HNR)",
        "intensity_mean": "Energía", "intensity_std": "Dinámica",
        "silence_ratio": "Silencio", "pause_rate": "Cortes",
    }
    z_scores = np.array([report["z_scores"][key] for key in FEATURE_ORDER])
    order = np.argsort(z_scores)
    sorted_z_scores = z_scores[order]
    labels = [labels_es[FEATURE_ORDER[index]] for index in order]
    colors = [ORANGE if value > 0 else NAVY for value in sorted_z_scores]
    ax2.barh(labels, sorted_z_scores, color=colors, zorder=3, height=0.66)
    ax2.axvline(0, color=GREY, lw=1)
    ax2.set_xlabel("z-score vs basal (σ)", fontsize=11, color=NAVY)
    ax2.set_title("Perfil acústico — fatiga marcada", fontsize=13, color=NAVY,
                  fontweight="bold", pad=12)
    ax2.spines[["top", "right"]].set_visible(False)
    ax2.spines[["left", "bottom"]].set_color(GREY)
    ax2.tick_params(colors=NAVY, labelsize=9)

    fig.suptitle("SERENO · biometría vocal para prevención de fatiga  —  ALTTAB",
                 fontsize=14.5, color=NAVY, fontweight="bold", x=0.5, y=0.99)
    plt.tight_layout(rect=[0, 0, 1, 0.96])
    output_path = output_path.expanduser().resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=150, facecolor="white", bbox_inches="tight")
    plt.close(fig)
    print(f"Figura guardada en: {output_path}")


if __name__ == "__main__":
    args = parse_args()
    main(args.output)
