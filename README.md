# Sereno

> Proof of concept (PoC) de biometría vocal para prevenir la fatiga profesional.

## Estado actual

**Etapa:** motor acústico de prueba de concepto. El repositorio contiene un pipeline local de análisis y una demostración con audio sintético; no incluye aún una aplicación web, API, persistencia, autenticación ni validación con datos reales.

| Área | Estado | Evidencia |
|---|---|---|
| Síntesis de muestras de demostración | Implementada | `voice_synth.py` |
| Extracción de 11 variables acústicas | Implementada | `features.py` |
| Baseline personal y detección de desviación | Implementada | `detector.py` |
| Carga de audio real local | Implementada, sin validación de calidad | `audio_io.py` |
| Demo de punta a punta | Implementada, pendiente de dependencias en este entorno | `sereno_poc.py` |
| Gráfico estático de resultados | Implementado con rutas portables | `make_viz.py` |
| Backend, frontend, base de datos y API | No implementados | Solo especificados en `REQUERIMIENTOS.md` |
| Tests automatizados, empaquetado y CI | No implementados | No hay archivos de pruebas ni manifiesto de dependencias |
| Validación clínica / datos reales | No realizada | La demo usa síntesis paramétrica |

La revisión de este checkout se realizó el 30 de septiembre de 2026. El árbol de Git estaba limpio. La demo no pudo ejecutarse porque el entorno no tiene instaladas `scipy`, `praat-parselmouth`, `scikit-learn`, `librosa`, `matplotlib` ni `soundfile`.

## Qué hace

Sereno no intenta inferir una emoción universal. Para cada persona construye un **baseline vocal** a partir de varias lecturas del mismo texto en un estado habitual y, más tarde, compara nuevas lecturas contra ese perfil. Si la desviación acústica supera un umbral individual, devuelve una recomendación preventiva.

```text
Audio de lectura
      ↓
Extracción acústica (Praat / parselmouth)
      ↓
Perfil basal personal
      ↓
Distancia al basal + factores explicativos
      ↓
OK / ATENCIÓN / PAUSA SUGERIDA
```

El resultado es un indicador exploratorio de desviación vocal. No es un diagnóstico clínico ni hay evidencia en este repositorio que permita usarlo como tal.

## Motor implementado

### Variables acústicas

El extractor devuelve once descriptores:

| Grupo | Variables |
|---|---|
| Frecuencia fundamental | `f0_mean`, `f0_std`, `f0_range`, `voiced_ratio` |
| Estabilidad y calidad | `jitter_local`, `shimmer_local`, `hnr_mean` |
| Energía | `intensity_mean`, `intensity_std` |
| Ritmo | `silence_ratio`, `pause_rate` |

`features.py` usa Praat mediante `parselmouth` para pitch, jitter, shimmer, HNR e intensidad. El ritmo se estima con RMS por ventanas de 20 ms y un umbral relativo de energía.

### Baseline y scoring

`BaselineDetector` construye un baseline con las señales provistas:

1. Calcula mediana y MAD por variable para z-scores robustos.
2. Ajusta una covarianza Ledoit-Wolf y usa distancia de Mahalanobis como score global.
3. Calcula distancias leave-one-out y define el umbral personal como el mayor entre `media + 3 × desvío` y `máximo × 1,05`.
4. Ordena los cuatro factores que más se alinean con el patrón de deterioro definido en el código.

La recomendación actual es `OK` si no excede el umbral; si lo excede, el código usa una severidad normalizada para devolver `ATENCIÓN` o `PAUSA SUGERIDA`.

## Estructura

| Archivo | Responsabilidad |
|---|---|
| `audio_io.py` | Carga audio, convierte a mono, remuestrea a 16 kHz, recorta silencios externos y normaliza pico. |
| `features.py` | Extrae variables acústicas y las convierte en vector ordenado. |
| `detector.py` | Ajusta baseline, calcula scores y recomendaciones. |
| `voice_synth.py` | Genera voces paramétricas para la demo; no pretende simular voz realista. |
| `sereno_poc.py` | Ejecuta baseline sintético y casos de control/fatiga. |
| `make_viz.py` | Produce un PNG estático de scores y z-scores. |
| `REQUERIMIENTOS.md` | Especificación de la futura aplicación web. |
| `BRIEF.md` | Documento conceptual y técnico del PoC. |

## Instalación y ejecución

Se recomienda Python 3.9 a 3.12 y un entorno virtual. Las dependencias están
declaradas en `requirements.txt` para Windows, macOS y Linux.

```bash
python -m venv .venv
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python sereno_poc.py
```

Activación del entorno virtual:

| Sistema / shell | Comando |
|---|---|
| Windows PowerShell | `.venv\\Scripts\\Activate.ps1` |
| Windows cmd | `.venv\\Scripts\\activate.bat` |
| macOS / Linux | `source .venv/bin/activate` |

Para generar la visualización:

```bash
python make_viz.py
```

El gráfico se guarda, por defecto, en `outputs/sereno_resultados.png`. Para elegir
otra ubicación en cualquier plataforma:

```bash
python make_viz.py --output ruta/al/resultado.png
```

## Uso con audio real

La fuente sintética puede reemplazarse por archivos de audio. El repositorio sugiere reunir entre 8 y 10 lecturas del mismo texto para el baseline.

```python
from audio_io import load_audio
from detector import BaselineDetector

baseline = [load_audio(f"basal_{i}.wav")[0] for i in range(10)]
detector = BaselineDetector().fit(baseline, 16000)

signal, sr = load_audio("lectura_actual.wav")
report = detector.score(signal, sr)
status, message = detector.recommend(report)
print(status, message)
print(report["top_drivers"])
```

Actualmente no hay protección explícita para un baseline vacío, ni soporte implementado para los casos de baseline parcial definidos en los requisitos. Tampoco hay controles de duración, SNR, formato confiable o consistencia de micrófono.

## Documentación relacionada

- [Estado detallado y backlog](PENDIENTES.md)
- [Brief técnico](BRIEF.md)
- [Requerimientos de la aplicación futura](REQUERIMIENTOS.md)

## Licencia

El proyecto se distribuye bajo la licencia incluida en [LICENSE](LICENSE).
