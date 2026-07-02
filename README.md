# Sereno · PoC — detección de fatiga vocal por desviación basal

Prueba de concepto del motor acústico de **Sereno** (ALTTAB): analiza una lectura
de texto fijo (~1–3 min) y detecta desviaciones respecto al **basal personal** del
profesional, sugiriendo pausas preventivas.

## Idea central

No se clasifica una emoción "en abstracto" (eso ronda 60–75% de acierto y depende
mucho de la persona). En cambio se compara **cada persona contra sí misma**:
se graba un basal en estado normal y luego se mide cuánto se aparta cada lectura
nueva. Esto es mucho más robusto y es el estándar en biomarcadores vocales.

## Pipeline

```
audio (lectura texto fijo)
      │
      ▼
 features.py      ── extracción acústica con Praat (parselmouth):
                     F0 (media/desvío/rango), jitter, shimmer, HNR,
                     intensidad, ratio de silencio, tasa de cortes
      │
      ▼
 detector.py      ── baseline por usuario + score de anomalía:
                     · z-score robusto por feature (mediana + MAD) → interpretable
                     · distancia de Mahalanobis (covarianza Ledoit-Wolf) → global
                     · umbral personal por leave-one-out (evita falsos positivos)
      │
      ▼
 recomendación    ── OK / ATENCIÓN / PAUSA SUGERIDA + factores explicativos
```

## Archivos

| archivo            | rol                                                        |
|--------------------|------------------------------------------------------------|
| `features.py`      | extracción de descriptores acústicos (eGeMAPS-like)        |
| `detector.py`      | baseline + detección multivariada de desviación            |
| `audio_io.py`      | carga de audio **real** (wav/mp3) → señal normalizada      |
| `voice_synth.py`   | sintetizador paramétrico (solo para generar muestras demo) |
| `sereno_poc.py`    | demo end-to-end (baseline + progresión de fatiga)          |
| `make_viz.py`      | genera la figura de resultados con branding ALTTAB         |

## Correr la demo

```bash
pip install praat-parselmouth librosa soundfile scikit-learn matplotlib
python3 sereno_poc.py      # salida en consola
python3 make_viz.py        # genera sereno_resultados.png
```

## Usar con audio REAL

El único cambio es la fuente de las señales — el resto es idéntico:

```python
from audio_io import load_audio
from detector import BaselineDetector

# 1) basal: 8–10 lecturas del texto fijo en estado normal
baseline = [load_audio(f"basal_{i}.wav")[0] for i in range(10)]
det = BaselineDetector().fit(baseline, 16000)

# 2) durante la jornada
sig, sr = load_audio("lectura_actual.wav")
rep = det.score(sig, sr)
estado, mensaje = det.recommend(rep)
print(estado, "→", mensaje)
print("factores:", rep["top_drivers"])
```

## Notas técnicas / próximos pasos

- **Basal robusto**: 8–10 tomas capturan la variabilidad natural día a día.
  Conviene refrescarlo periódicamente (voz cambia con estación, resfríos, etc.).
- **Control de calidad de entrada**: mismo micrófono, ruido de fondo acotado.
  Un resfrío o un ambiente ruidoso alteran features → conviene un chequeo de
  calidad de señal antes de puntuar (SNR mínimo, duración mínima de voz).
- **Validación clínica**: el sintético sirve para probar la mecánica. El siguiente
  paso real es recolectar audio de guardia (pre/post jornada) para calibrar
  umbrales y validar contra una medida externa de fatiga (p. ej. escala subjetiva
  o marcadores de desempeño).
- **eGeMAPS completo**: se puede sumar openSMILE (set eGeMAPSv02, 88 features) si
  se quiere un descriptor más rico; el detector no cambia.
```
