# SERENO · Brief del Proyecto

> **Biometría vocal para prevención de fatiga profesional**  
> Proof of Concept — ALTTAB

---

## 1. ¿Qué es Sereno?

Sereno es un **motor acústico** que detecta fatiga vocal en profesionales de la voz (profesores, locutores, teleoperadores, personal de salud) mediante el análisis de grabaciones de voz. En lugar de clasificar emociones en abstracto (enfoque frágil, ~60–75% de acierto), **compara a cada persona contra su propio baseline**, midiendo desviaciones acústicas que correlacionan con fatiga. Este enfoque de "referencia personal" es el estándar en biomarcadores vocales y es mucho más robusto.

**Objetivo:** Sugerir pausas preventivas cuando la voz del profesional se desvía significativamente de su estado normal.

---

## 2. Pipeline de procesamiento

```
┌─────────────────────────────────────────────────────────┐
│  AUDIO (lectura de texto fijo ~1-3 min)                  │
│  - Real: wav/mp3 (audio_io.py)                           │
│  - Sintético: parámetros controlados (voice_synth.py)    │
└─────────────────────┬───────────────────────────────────┘
                      ▼
┌─────────────────────────────────────────────────────────┐
│  features.py — Extracción acústica con Praat             │
│  (parselmouth): 11 descriptores tipo eGeMAPS             │
│  · F0: media, desvío, rango, ratio de fonación          │
│  · Calidad vocal: jitter, shimmer, HNR                  │
│  · Energía: intensidad media, desvío                     │
│  · Ritmo: ratio de silencio, tasa de cortes             │
└─────────────────────┬───────────────────────────────────┘
                      ▼
┌─────────────────────────────────────────────────────────┐
│  detector.py — Baseline + detección multivariada         │
│  1. Fit: construye perfil basal del usuario              │
│     · Mediana + MAD → z-scores robustos por feature      │
│     · Covarianza Ledoit-Wolf → distancia Mahalanobis     │
│     · Umbral personal por leave-one-out                  │
│  2. Score: evalúa muestra nueva contra el baseline       │
│     · Mahalanobis → score global de desviación           │
│     · Severidad normalizada 0..1                        │
│     · Top drivers → factores que más se desvían          │
│  3. Recommend: traduce score a acción                    │
│     · OK / ATENCIÓN / PAUSA SUGERIDA                    │
└─────────────────────┬───────────────────────────────────┘
                      ▼
┌─────────────────────────────────────────────────────────┐
│  SALIDA: recomendación operativa + factores explicativos │
└─────────────────────────────────────────────────────────┘
```

---

## 3. Arquitectura del código

| Archivo | Rol | Dependencias |
|---------|-----|-------------|
| **`features.py`** | Extractor de 11 descriptores acústicos vía Praat (parselmouth). Pitch, jitter, shimmer, HNR, intensidad, ritmo. | `parselmouth`, `numpy` |
| **`detector.py`** | Detector de desviación. Baseline por usuario con estadística robusta (mediana+MAD, Mahalanobis con Ledoit-Wolf, leave-one-out). | `numpy`, `scikit-learn`, `features` |
| **`audio_io.py`** | Carga de audio real (wav/mp3). Resampleo a 16kHz, mono, normalización. | `librosa` |
| **`voice_synth.py`** | Sintetizador paramétrico fuente-filtro para demo. Pulso de Rosenberg + formantes /a/ + jitter/shimmer + ruido HNR. | `scipy`, `numpy` |
| **`sereno_poc.py`** | Demo end-to-end. Construye baseline → evalúa progresión de fatiga (leve→marcada). | `detector`, `voice_synth` |
| **`make_viz.py`** | Genera visualización profesional (2 paneles: scores + perfil z-scores). Branding ALTTAB. | `matplotlib`, `detector` |

---

## 4. Features acústicas (11 descriptores)

Basados en el estándar eGeMAPS, seleccionados por su relevancia comprobada para fatiga/tensión vocal:

| Feature | Descripción | Efecto esperado con fatiga |
|---------|-------------|---------------------------|
| `f0_mean` | Frecuencia fundamental media (Hz) | ↓ más grave |
| `f0_std` | Variabilidad de pitch | ↓ más monótono |
| `f0_range` | Rango tonal (P95-P5) | ↓ menos entonación |
| `voiced_ratio` | Proporción de fonación | ↓ menos sonido |
| `jitter_local` | Inestabilidad de periodo | ↑ más temblor |
| `shimmer_local` | Inestabilidad de amplitud | ↑ más temblor |
| `hnr_mean` | Harmonics-to-Noise Ratio | ↓ voz más ruidosa |
| `intensity_mean` | Energía media | ↓ menos intensidad |
| `intensity_std` | Variabilidad de energía | ↓ menos dinámica |
| `silence_ratio` | Proporción de silencio | ↑ más pausas |
| `pause_rate` | Frecuencia de cortes/s | ↑ más entrecortado |

---

## 5. Métodos de detección (detector.py)

### 5.1 Baseline personal
- Se construye con **8–10 grabaciones** del mismo texto fijo en estado normal
- Captura la **variabilidad natural** del profesional (día a día, hora del día, etc.)

### 5.2 Z-score robusto por feature
- Usa **mediana + MAD** (desviación absoluta mediana) en lugar de media+sigma
- MAD incluye factor de consistencia 1.4826 para ser equivalente a desvío estándar bajo normalidad
- **Ventaja:** mucho más robusto ante outliers que la media tradicional

### 5.3 Distancia de Mahalanobis (score global)
- Distancia multivariada que considera **correlaciones entre features**
- Covarianza estabilizada con **shrinkage Ledoit-Wolf** → funciona bien con pocas muestras
- Una sola muestra nueva con desviación atípica no dispara falsos positivos

### 5.4 Umbral personal por Leave-One-Out (LOO)
- Para cada muestra del baseline: se entrena con las otras `n-1` y se mide su distancia
- El umbral = `media(LOO) + 3σ` (con piso en `max(LOO) * 1.05`)
- **Crítico:** evita el sesgo optimista de medir contra el mismo set de entrenamiento

### 5.5 Interpretación (severidad)

| Mahalanobis vs umbral | Severidad | Recomendación |
|----------------------|-----------|---------------|
| Dentro del umbral | — | **OK** — Sin señales de fatiga |
| Supera umbral, severidad < 0.5 | Leve | **ATENCIÓN** — Micro-pausa sugerida |
| Supera umbral, severidad ≥ 0.5 | Marcada | **PAUSA SUGERIDA** — Pausa preventiva |

---

## 6. Demo sintética (sereno_poc.py)

La demo genera 10 muestras de baseline "normal" con variabilidad natural, luego evalúa:

| Muestra | Mahalanobis | Estado |
|---------|-------------|--------|
| Control normal #1 | ~2.5 | OK |
| Control normal #2 | ~2.8 | OK |
| Fatiga leve (L=0.35) | ~4.0 | ATENCIÓN |
| Fatiga moderada (L=0.6) | ~6.5 | PAUSA SUGERIDA |
| Fatiga marcada (L=0.9) | ~10.0 | PAUSA SUGERIDA |

Los **top drivers** en fatiga marcada suelen ser:
- ↑ shimmer (inestabilidad amplitud)
- ↓ f0_mean (voz más grave)
- ↑ silence_ratio (más pausas)
- ↑ jitter (inestabilidad periodo)

---

## 7. Sintetizador paramétrico (voice_synth.py)

Modelo **fuente-filtro** simplificado para generar muestras de prueba:

- **Fuente:** Pulso glotal de Rosenberg (apertura asimétrica + cierre suave)
- **Jitter:** Perturbación relativa del periodo ciclo a ciclo (~N(0, jitter))
- **Shimmer:** Perturbación de amplitud ciclo a ciclo (~N(0, shimmer))
- **Filtro:** 3 formantes en cascada (vocal /a/: 730, 1090, 2440 Hz)
- **Prosodia:** Sílabas de ~180ms con pausas probabilísticas
- **HNR:** Ruido gaussiano modulado por envolvente → voz "aspirada"

El sintetizador **no suena realista** pero produce señales de las que Praat puede extraer features coherentes con los parámetros de entrada → permite validar el pipeline.

---

## 8. Visualización (make_viz.py)

Genera una figura profesional con dos paneles:

1. **Panel izquierdo:** Barras de distancia Mahalanobis para cada muestra vs umbral personal (línea verde discontinua). Colores: azul (normal) / naranja (anomalía).

2. **Panel derecho:** Perfil de z-scores de la muestra más desviada. Barras horizontales: naranja (z>0, hacia fatiga) / azul (z<0, opuesto a fatiga).

Branding ALTTAB con paleta: naranja `#E8500A`, azul marino `#1A2B5F`, verde `#2E9E5B`.

---

## 9. Uso con audio real

El pipeline es idéntico, solo cambia la fuente de audio:

```python
from audio_io import load_audio
from detector import BaselineDetector

# Basal: 8–10 lecturas normales
baseline = [load_audio(f"basal_{i}.wav")[0] for i in range(10)]
det = BaselineDetector().fit(baseline, 16000)

# Evaluación durante la jornada
sig, sr = load_audio("lectura_actual.wav")
rep = det.score(sig, sr)
estado, mensaje = det.recommend(rep)
```

---

## 10. Próximos pasos (del README original)

1. **Basal robusto:** 8–10 tomas para capturar variabilidad natural. Refrescar periódicamente.
2. **Control de calidad de entrada:** Mismo micrófono, SNR mínimo, duración mínima de voz.
3. **Validación clínica:** Recolectar audio de guardia (pre/post jornada) para calibrar umbrales contra escala subjetiva de fatiga.
4. **eGeMAPS completo:** Integrar openSMILE (88 features) para descriptor más rico; el detector no cambia.

---

## 11. Requisitos técnicos

```bash
pip install -r requirements.txt
```

- Python 3.9–3.12
- `parselmouth` (wrapper de Praat para extracción acústica)
- `librosa` (carga de audio real)
- `scikit-learn` (Ledoit-Wolf, Mahalanobis)
- `matplotlib` (visualización)

---

*Brief generado a partir del análisis del código fuente. Proyecto: [Sereno PoC — ALTTAB](https://github.com/alvarova/sereno)*
