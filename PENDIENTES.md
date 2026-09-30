# Sereno · Pendientes y plan de implementación

## Diagnóstico de partida

El repositorio implementa el núcleo experimental de Sereno, pero no el producto definido en `REQUERIMIENTOS.md`. El alcance funcional actual es: procesar señales en memoria, construir un baseline con un conjunto de muestras y emitir un reporte. Todo lo relativo a usuarios, archivos persistidos, navegación web, seguridad y operación es especificación pendiente.

## Bloqueadores para una demo reproducible

- [x] Declarar dependencias con rangos compatibles en `requirements.txt` y documentar Python 3.9–3.12.
- [x] Corregir `make_viz.py`: ahora usa una ruta portable bajo `outputs/` y permite `--output`.
- [ ] Añadir una prueba de humo que instale dependencias y ejecute `sereno_poc.py` y `make_viz.py`.
- [x] Definir una estructura de salida para artefactos generados: los PNG nuevos se escriben bajo `outputs/`, que está ignorado por Git.

## Endurecimiento del motor acústico

### Validaciones necesarias

- [ ] Validar entrada vacía, demasiado corta, silenciosa o no finita antes de extraer variables.
- [ ] Establecer duración mínima/máxima y medición de SNR; los requisitos proponen 20 s a 5 min para baseline.
- [ ] Validar que todas las variables extraídas sean finitas y registrar errores de Praat en lugar de convertir silenciosamente algunos fallos a cero.
- [ ] Añadir controles para baseline vacío e insuficiente. `BaselineDetector.fit()` asume que hay muestras suficientes para Ledoit-Wolf y leave-one-out.
- [ ] Implementar la política de baseline parcial descrita en `REQUERIMIENTOS.md`: bloquear con 0 muestras, estrategia de referencia con 1 y advertencia de confianza con 2 a 7.
- [ ] Definir la conducta ante cambios de sample rate, canales, clipping y micrófonos distintos.

### Calidad estadística y explicabilidad

- [ ] Validar con audio real que la dirección de deterioro asumida para cada feature sea correcta por población y caso de uso.
- [ ] Calibrar umbrales, la normalización de severidad y el corte entre `ATENCIÓN` y `PAUSA SUGERIDA` con datos etiquetados.
- [ ] Revisar la interpretación de `top_drivers`: la dirección se deriva del signo del z-score, no de la dirección de deterioro; puede resultar confusa para variables cuyo deterioro esperado es una disminución.
- [ ] Evaluar la estabilidad de Mahalanobis/LOO con 8–10 muestras y documentar la incertidumbre.
- [ ] Versionar esquema de features, parámetros acústicos y modelo de baseline para garantizar comparabilidad histórica.
- [ ] Añadir refresco, expiración o recalibración del baseline.
- [ ] Evaluar integrar eGeMAPS completo mediante openSMILE si la validación justifica más variables.

### Pruebas

- [ ] Unit tests para `audio_io`, extracción de variables, conversiones de vector, baseline, umbrales y recomendaciones.
- [ ] Casos de regresión: silencio, audio corto, audio corrupto, señal saturada, baseline de 0/1/2/N muestras y valores extremos.
- [ ] Fixtures de audio sintético y, cuando exista autorización, un conjunto anonimizado de audio real.
- [ ] Medir rendimiento frente al objetivo de ≤5 s por archivo de hasta 3 min y ≥10 evaluaciones concurrentes.

## MVP de aplicación web (prioridad alta)

### Backend y datos

- [ ] Elegir FastAPI o Flask y crear la estructura de aplicación.
- [ ] Implementar migraciones y modelo de datos para `users`, `baseline_samples`, `evaluations` y `settings`.
- [ ] Implementar registro, login, refresh y logout con passwords bcrypt y JWT.
- [ ] Implementar almacenamiento seguro de audio y metadatos; cachear las features para no reprocesar.
- [ ] Implementar `GET /api/baseline/status`, carga/listado/eliminación de muestras y lectura del texto estándar.
- [ ] Implementar `POST /api/evaluate`, historial paginado y detalle de evaluación.
- [ ] Proteger rutas por usuario, validar tamaño (máximo 20 MB), extensión/tipo real, nombres de archivo y errores de carga.

### Frontend

- [ ] Login y registro en español.
- [ ] Dashboard con progreso de baseline (meta: 8 tomas) y estado de evaluación.
- [ ] Pantalla para subir audio y mostrar el texto de lectura estándar.
- [ ] Resultado con estado, mensaje, score vs. umbral, severidad y cuatro factores explicativos.
- [ ] Historial de evaluaciones y vista de detalle.
- [ ] Diseño responsivo y accesible (WCAG AA, foco visible, labels, estados de carga y errores).

## Mejoras posteriores al MVP

- [ ] Captura de micrófono desde el navegador con MediaRecorder.
- [ ] Reemplazo de tomas del baseline y trazabilidad de sus cambios.
- [ ] Tooltips y gráficos interactivos de z-scores e historial.
- [ ] Tendencia temporal, exportación de informe PDF y recuperación de contraseña.
- [ ] Panel administrativo y soporte de múltiples textos de lectura.
- [ ] Docker, CI/CD, observabilidad, backup diario y despliegue de producción.

## Validación, privacidad y seguridad

- [ ] Diseñar estudio de validación con profesionales reales, consentimiento informado y medida externa de fatiga.
- [ ] Definir métricas de éxito (sensibilidad, especificidad, tasa de falsas alertas y utilidad operativa) antes de promover el sistema como detector de fatiga.
- [ ] Establecer políticas de consentimiento, retención, borrado, acceso y cifrado para biometría de voz.
- [ ] Realizar revisión legal y de seguridad aplicable al país/sector antes de producción.
- [ ] Comunicar en la UI que es una recomendación preventiva y no un diagnóstico médico.

## Orden recomendado

1. Reproducibilidad: dependencias, rutas portables y prueba de humo.
2. Robustez del motor: validación de audio y baseline parcial/vacío.
3. Validación científica con datos reales y calibración de umbrales.
4. Backend, persistencia y seguridad.
5. Frontend e integración end-to-end.
6. Automatización, observabilidad y despliegue.

El orden 1–3 reduce el riesgo de construir una interfaz sobre señales o umbrales aún no validados.
