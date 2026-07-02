"""Genera una visualizacion de los resultados del PoC (branding ALTTAB)."""
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager

from detector import BaselineDetector
from features import FEATURE_ORDER
import sereno_poc as poc

ORANGE = "#E8500A"
NAVY = "#1A2B5F"
GREEN = "#2E9E5B"
AMBER = "#E8A00A"
GREY = "#8892A6"

# --- correr pipeline ---
poc.rng = np.random.default_rng(42)
baseline = [poc.normal_sample(seed=100 + i)[0] for i in range(10)]
sr = 16000
det = BaselineDetector().fit(baseline, sr)

samples = [
    ("Control\n#1", poc.normal_sample(seed=200)[0], "n"),
    ("Control\n#2", poc.normal_sample(seed=201)[0], "n"),
    ("Fatiga\nleve", poc.fatigued_sample(0.35, seed=300)[0], "f"),
    ("Fatiga\nmoderada", poc.fatigued_sample(0.60, seed=301)[0], "f"),
    ("Fatiga\nmarcada", poc.fatigued_sample(0.90, seed=302)[0], "f"),
]
names, scores, states = [], [], []
for nm, sig, kind in samples:
    rep = det.score(sig, sr)
    names.append(nm)
    scores.append(rep["mahalanobis"])
    states.append(rep["is_anomaly"])

thr = det.threshold_

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5.2),
                               gridspec_kw={"width_ratios": [1.15, 1]})
fig.patch.set_facecolor("white")

# ---- Panel 1: score vs umbral ----
colors = [ORANGE if s else NAVY for s in states]
bars = ax1.bar(names, scores, color=colors, width=0.62, zorder=3,
               edgecolor="white", linewidth=1.5)
# banda basal
ax1.axhspan(0, thr, color=GREEN, alpha=0.08, zorder=0)
ax1.axhline(thr, color=GREEN, lw=2, ls="--", zorder=2)
ax1.text(4.45, thr + 0.15, f"umbral personal = {thr:.1f}", color=GREEN,
         fontsize=9.5, ha="right", va="bottom", fontweight="bold")
for b, sc in zip(bars, scores):
    ax1.text(b.get_x() + b.get_width() / 2, sc + 0.2, f"{sc:.1f}",
             ha="center", va="bottom", fontsize=10, color=NAVY, fontweight="bold")
ax1.set_ylabel("Distancia al basal (Mahalanobis)", fontsize=11, color=NAVY)
ax1.set_title("Desviación respecto al basal por lectura", fontsize=13,
              color=NAVY, fontweight="bold", pad=12)
ax1.set_ylim(0, max(scores) * 1.18)
ax1.spines[["top", "right"]].set_visible(False)
ax1.spines[["left", "bottom"]].set_color(GREY)
ax1.tick_params(colors=NAVY)

# ---- Panel 2: perfil de z-scores (fatiga marcada) ----
rep = det.score(samples[-1][1], sr)
labels_es = {
    "f0_mean": "Altura de voz", "f0_std": "Entonación", "f0_range": "Rango tonal",
    "voiced_ratio": "Fonación", "jitter_local": "Estab. periodo",
    "shimmer_local": "Estab. amplitud", "hnr_mean": "Claridad (HNR)",
    "intensity_mean": "Energía", "intensity_std": "Dinámica",
    "silence_ratio": "Silencio", "pause_rate": "Cortes",
}
z = np.array([rep["z_scores"][k] for k in FEATURE_ORDER])
order = np.argsort(z)
zs = z[order]
lab = [labels_es[FEATURE_ORDER[i]] for i in order]
bcol = [ORANGE if v > 0 else NAVY for v in zs]
ax2.barh(lab, zs, color=bcol, zorder=3, height=0.66)
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
plt.savefig("/home/claude/sereno_resultados.png", dpi=150,
            facecolor="white", bbox_inches="tight")
print("Figura guardada.")
