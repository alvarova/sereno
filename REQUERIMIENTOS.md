# REQUERIMIENTOS · Sereno UI

> Interfaz web para el sistema de biometría vocal Sereno (ALTTAB)  
> Documento de requerimientos funcionales y técnicos

---

## 📋 Índice

1. [Resumen ejecutivo](#1-resumen-ejecutivo)
2. [Arquitectura general](#2-arquitectura-general)
3. [Historias de usuario](#3-historias-de-usuario)
4. [Requerimientos funcionales detallados](#4-requerimientos-funcionales-detallados)
5. [Flujo de la aplicación](#5-flujo-de-la-aplicación)
6. [Diseño de pantallas (wireframe funcional)](#6-diseño-de-pantallas-wireframe-funcional)
7. [API Backend (endpoints)](#7-api-backend-endpoints)
8. [Modelo de datos](#8-modelo-de-datos)
9. [Requerimientos no funcionales](#9-requerimientos-no-funcionales)
10. [Plan de implementación](#10-plan-de-implementación)

---

## 1. Resumen ejecutivo

### 1.1 Propósito

Construir una **interfaz web** que permita a profesionales de la voz gestionar su perfil biométrico vocal: registrar grabaciones de línea base (baseline), subir nuevas muestras de audio y recibir evaluaciones de fatiga vocal en tiempo real.

### 1.2 Usuarios target

- Profesores
- Locutores / presentadores
- Teleoperadores / call centers
- Personal de salud (médicos, enfermeras en guardia)
- Cualquier profesional que use la voz como herramienta de trabajo

### 1.3 Stack técnico propuesto

| Capa | Tecnología |
|------|-----------|
| **Frontend** | HTML + CSS + JavaScript (vanilla o React) |
| **Backend** | Python (FastAPI / Flask) |
| **Motor acústico** | `sereno` (features.py + detector.py + audio_io.py) |
| **Base de datos** | SQLite (desarrollo) / PostgreSQL (producción) |
| **Almacenamiento** | Sistema de archivos local / S3 |
| **Autenticación** | JWT + bcrypt |

---

## 2. Arquitectura general

```
┌─────────────────────────────────────────────────────────┐
│                    NAVEGADOR (UI)                         │
│  · Login / Registro                                      │
│  · Dashboard del usuario                                 │
│  · Gestor de tomas (baseline)                           │
│  · Evaluación (subir audio + ver resultado)             │
│  · Historial de evaluaciones                            │
└─────────────────────┬───────────────────────────────────┘
                      │ HTTP / JSON
                      ▼
┌─────────────────────────────────────────────────────────┐
│              BACKEND (FastAPI / Flask)                    │
│                                                          │
│  · /auth        → registro, login, refresh token        │
│  · /users       → CRUD usuarios                         │
│  · /baseline    → gestión de tomas baseline              │
│  · /evaluate    → evaluar muestra de audio              │
│  · /history     → historial de evaluaciones             │
└──────────┬──────────────────────────┬───────────────────┘
           │                          │
           ▼                          ▼
┌─────────────────────┐   ┌──────────────────────────────┐
│   Base de datos      │   │  Motor Sereno (Python)       │
│   (SQLite / PG)      │   │                              │
│                      │   │  · audio_io.py → carga audio │
│  · usuarios          │   │  · features.py → extracción  │
│  · grabaciones       │   │  · detector.py → baseline +  │
│  · evaluaciones      │   │    score + recomendación     │
│  · sesiones          │   │                              │
└─────────────────────┘   └──────────────────────────────┘
```

---

## 3. Historias de usuario

### HU-01: Registro de usuario
> *"Como profesional de la voz, quiero registrarme con mi correo y una contraseña para tener mi perfil personal."*

**Criterios de aceptación:**
- Formulario con: nombre, email, contraseña, confirmación, ocupación (opcional)
- Validación de email único
- Contraseña mínima 8 caracteres, con al menos 1 número y 1 mayúscula
- Confirmación por email (opcional para MVP)
- Redirección al dashboard post-registro

### HU-02: Inicio de sesión
> *"Como usuario registrado, quiero iniciar sesión con mi email y contraseña para acceder a mi perfil."*

**Criterios de aceptación:**
- Formulario email + contraseña
- Manejo de errores: "Credenciales inválidas", "Usuario no encontrado"
- Recordar sesión (JWT con refresh token)
- Cerrar sesión

### HU-03: Ver progreso del baseline
> *"Como usuario nuevo, quiero ver cuántas grabaciones de baseline me faltan para completar mi perfil vocal."*

**Criterios de aceptación:**
- Indicador visual de progreso: "3/8 grabaciones completadas"
- Barra de progreso animada
- Mensaje de estado: "Faltan N grabaciones", "¡Perfil completo!",
  "Perfil parcial: disponible con limitaciones"

### HU-04: Realizar una grabación de baseline
> *"Como usuario, quiero grabar o subir un audio del texto fijo para añadirlo a mi baseline."*

**Criterios de aceptación:**
- Mostrar el **texto fijo** sugerido para leer
- Dos modalidades:
  a) **Grabación directa** desde el navegador (micrófono)
  b) **Subir archivo** (wav/mp3)
- Validar formato y duración mínima (~30s)
- Al subir, el backend procesa el audio y lo asigna al baseline
- Feedback inmediato: "Grabación #4 recibida correctamente"
- Si el audio es inválido (silencio, muy corto, ruido): mensaje de error descriptivo

### HU-05: Evaluar voz (baseline completo)
> *"Como usuario con baseline completo, quiero subir una grabación actual y recibir una evaluación de fatiga vocal."*

**Criterios de aceptación:**
- Subir archivo de audio (wav/mp3) o grabar en vivo
- El backend procesa: carga → extrae features → compara contra baseline → genera reporte
- Resultado visual con:
  - **Estado:** OK (🟢) / ATENCIÓN (🟡) / PAUSA SUGERIDA (🔴)
  - **Score Mahalanobis** con referencia al umbral personal
  - **Top factores** que contribuyen a la desviación (gráfico de barras)
  - **Severidad** (0–100%)
- Guardar en historial

### HU-06: Evaluar voz (baseline parcial)
> *"Como usuario que aún no completa las 8 tomas, quiero poder evaluar mi voz aunque sea contra una sola muestra de referencia."*

**Criterios de aceptación:**
- Si hay al menos 1 grabación en baseline, permitir evaluación
- Mostrar advertencia clara: "Evaluación basada en N muestras. Se recomienda completar las 8 para mayor precisión."
- El score puede tener menor confianza estadística (el umbral LOO requiere ≥2 muestras)
- Para N=1: usar la muestra única como referencia, sin umbral LOO (solo distancia absoluta)
- Para 2≤N<8: baseline funcional pero con confianza reducida

### HU-07: Ver historial de evaluaciones
> *"Como usuario, quiero ver un histórico de todas mis evaluaciones anteriores para observar mi evolución."*

**Criterios de aceptación:**
- Tabla/listado cronológico: fecha, estado, score Mahalanobis, severidad
- Posibilidad de hacer clic en una evaluación para ver su detalle completo
- Gráfico de tendencia (opcional, post-MVP)

### HU-08: Gestionar texto de lectura
> *"Como administrador/usuario, quiero ver el texto fijo sugerido para las grabaciones."*

**Criterios de aceptación:**
- Texto estandarizado de ~150–200 palabras (~1–3 min de lectura)
- Visible en la pantalla de grabación
- Posibilidad de cambiar el texto (solo admin, post-MVP)

---

## 4. Requerimientos funcionales detallados

### 4.1 Módulo de Autenticación (RF-AUTH)

| ID | Requerimiento | Prioridad |
|----|--------------|-----------|
| RF-AUTH-01 | Registro con nombre, email, contraseña, ocupación | Alta |
| RF-AUTH-02 | Login con email + contraseña | Alta |
| RF-AUTH-03 | JWT con expiración (access: 1h, refresh: 7d) | Alta |
| RF-AUTH-04 | Cerrar sesión (invalidar token) | Alta |
| RF-AUTH-05 | Recuperación de contraseña (post-MVP) | Baja |

### 4.2 Módulo de Baseline (RF-BASE)

| ID | Requerimiento | Prioridad |
|----|--------------|-----------|
| RF-BASE-01 | Mostrar indicador de progreso (X/8) | Alta |
| RF-BASE-02 | Permitir subir archivo de audio (wav/mp3) | Alta |
| RF-BASE-03 | Permitir grabación directa desde navegador (MediaRecorder API) | Alta |
| RF-BASE-04 | Validar calidad del audio (SNR mínimo, duración mínima 20s, máxima 5min) | Alta |
| RF-BASE-05 | Almacenar cada grabación con metadata (fecha, duración, tamaño) | Alta |
| RF-BASE-06 | Cuando se completa el baseline (8/8), mostrar mensaje de felicitaciones y "Listo para evaluar" | Alta |
| RF-BASE-07 | Permitir re-grabar una toma (borrar y reemplazar) | Media |
| RF-BASE-08 | Mostrar el texto de lectura sugerido en la pantalla de grabación | Alta |
| RF-BASE-09 | Almacenar features extraídos en DB para no reprocesar | Media |

### 4.3 Módulo de Evaluación (RF-EVAL)

| ID | Requerimiento | Prioridad |
|----|--------------|-----------|
| RF-EVAL-01 | Subir archivo de audio para evaluar | Alta |
| RF-EVAL-02 | Grabar desde navegador para evaluar | Alta |
| RF-EVAL-03 | Comparar contra baseline (mínimo 1 muestra requerida) | Alta |
| RF-EVAL-04 | Mostrar resultado: estado (OK/ATENCIÓN/PAUSA) | Alta |
| RF-EVAL-05 | Mostrar score Mahalanobis vs umbral personal | Alta |
| RF-EVAL-06 | Mostrar top 4 factores de desviación con dirección (↑/↓) | Alta |
| RF-EVAL-07 | Mostrar severidad como porcentaje / barra | Alta |
| RF-EVAL-08 | Si baseline < 8 muestras, mostrar advertencia de confianza reducida | Alta |
| RF-EVAL-09 | Si baseline = 0 muestras, bloquear evaluación con mensaje | Alta |
| RF-EVAL-10 | Guardar cada evaluación en historial | Alta |
| RF-EVAL-11 | Opción de descargar reporte en PDF (post-MVP) | Baja |

### 4.4 Módulo de Visualización (RF-VIZ)

| ID | Requerimiento | Prioridad |
|----|--------------|-----------|
| RF-VIZ-01 | Panel izquierdo: barras de distancia Mahalanobis por evaluación | Alta |
| RF-VIZ-02 | Panel derecho: perfil de z-scores de la última evaluación | Alta |
| RF-VIZ-03 | Línea de umbral personal (verde discontinua) en gráfico | Alta |
| RF-VIZ-04 | Colores: normal (azul), anómalo (naranja/rojo) | Alta |
| RF-VIZ-05 | Tooltips con valores exactos al pasar el mouse | Media |
| RF-VIZ-06 | Vista responsiva (móvil, tablet, desktop) | Alta |

---

## 5. Flujo de la aplicación

### 5.1 Flujo principal (usuario nuevo)

```
REGISTRO → DASHBOARD (progreso 0/8)
              │
              ▼
         GRABACIÓN #1
         (subir o grabar texto fijo)
              │
              ▼
         GRABACIÓN #2 ... #8
              │
              ▼
    ┌── BASELINE COMPLETO (8/8) ──┐
    │  ✅ ¡Perfil vocal listo!     │
    │  "Ya puedes comenzar a       │
    │   evaluar tu voz"            │
    └──────────────────────────────┘
              │
              ▼
         EVALUACIÓN
         (subir audio nuevo)
              │
              ▼
    ┌── RESULTADO ─────────────────┐
    │  🟢 OK / 🟡 ATENCIÓN / 🔴 PAUSA │
    │  Score: 4.2 (umbral: 3.5)   │
    │  Top factores:              │
    │    ↑ shimmer (+2.1σ)        │
    │    ↓ f0_mean (-1.8σ)        │
    │    ↑ silence_ratio (+1.5σ)  │
    └──────────────────────────────┘
```

### 5.2 Flujo alternativo (usuario sin baseline completo)

```
DASHBOARD (progreso 3/8)
    │
    ├── Seguir grabando → completar baseline
    │
    └── EVALUACIÓN PARCIAL ⚠️
        │
        ┌──────────────────────────────────────┐
        │  "Evaluación basada en 3 muestras.   │
        │   Confianza reducida.                │
        │   Se recomienda completar las 8."    │
        └──────────────────────────────────────┘
```

---

## 6. Diseño de pantallas (wireframe funcional)

### 6.1 Login / Registro

```
┌─────────────────────────────────────────┐
│  ┌─────────────────────────────────┐    │
│  │       SERENO · ALTTAB           │    │
│  │   Biometría vocal profesional    │    │
│  │                                 │    │
│  │   [Email]                       │    │
│  │   [Contraseña]                  │    │
│  │                                 │    │
│  │   [  INICIAR SESIÓN  ]         │    │
│  │                                 │    │
│  │   ¿No tienes cuenta? Regístrate │    │
│  └─────────────────────────────────┘    │
└─────────────────────────────────────────┘
```

### 6.2 Dashboard — Progreso de baseline

```
┌─────────────────────────────────────────┐
│  ← Cerrar sesión                        │
│                                         │
│  👤 María González                      │
│  📍 Docente                             │
│                                         │
│  ┌─────────────────────────────────┐    │
│  │   📊 CONFIGURACIÓN DE BASELINE  │    │
│  │                                 │    │
│  │   Progreso:                     │    │
│  │   ████████░░░░  5 / 8           │    │
│  │                                 │    │
│  │   Faltan 3 grabaciones para     │    │
│  │   completar tu perfil vocal.    │    │
│  │                                 │    │
│  │   [  SUBIR GRABACIÓN  ]        │    │
│  │                                 │    │
│  │   📋 Texto de referencia:       │    │
│  │   "El cielo está... (leer en   │    │
│  │    voz natural y constante)"   │    │
│  └─────────────────────────────────┘    │
│                                         │
│  ⚠️ Evaluación parcial disponible      │
│  [Evaluar voz →]                       │
└─────────────────────────────────────────┘
```

### 6.3 Dashboard — Baseline completo

```
┌─────────────────────────────────────────┐
│  ← Cerrar sesión                        │
│                                         │
│  👤 María González                      │
│                                         │
│  ┌─────────────────────────────────┐    │
│  │   ✅  BASELINE COMPLETO         │    │
│  │                                 │    │
│  │   ████████████████  8 / 8       │    │
│  │                                 │    │
│  │   ¡Tu perfil vocal está listo!  │    │
│  │   Ya puedes evaluar tu voz      │    │
│  │   cuando lo necesites.          │    │
│  │                                 │    │
│  │   [  EVALUAR VOZ AHORA  ]      │    │
│  │                                 │    │
│  │   Última evaluación: 12 Jul     │    │
│  │   Estado: ✅ OK                 │    │
│  └─────────────────────────────────┘    │
└─────────────────────────────────────────┘
```

### 6.4 Pantalla de grabación / subida

```
┌─────────────────────────────────────────┐
│  ← Volver al dashboard                  │
│                                         │
│  NUEVA GRABACIÓN — BASELINE #6          │
│                                         │
│  📋 Lee el siguiente texto en voz       │
│  natural, como si estuvieras en tu      │
│  jornada laboral normal:               │
│                                         │
│  ┌─────────────────────────────────┐    │
│  │ "El cielo está despejado y el   │    │
│  │  sol brilla con fuerza sobre    │    │
│  │  la ciudad. Los pájaros cantan  │    │
│  │  mientras la gente camina por   │    │
│  │  las calles. Es un día          │    │
│  │  tranquilo y el ambiente se     │    │
│  │  siente en cada rincón..."      │    │
│  └─────────────────────────────────┘    │
│                                         │
│  ┌─────────────────────────────────┐    │
│  │  [ 🎤 GRABAR ]  o  [ 📁 SUBIR ] │    │
│  │                                 │    │
│  │  Formatos aceptados: .wav, .mp3 │    │
│  │  Duración sugerida: 1–3 min     │    │
│  └─────────────────────────────────┘    │
└─────────────────────────────────────────┘
```

### 6.5 Pantalla de resultado de evaluación

```
┌─────────────────────────────────────────┐
│  ← Volver al dashboard                  │
│                                         │
│  RESULTADO DE EVALUACIÓN                │
│  📅 13 de julio, 2026 — 15:30          │
│                                         │
│  ┌─────────────────────────────────┐    │
│  │    🟡  ATENCIÓN                 │    │
│  │    Desviación leve respecto     │    │
│  │    al basal. Conviene una       │    │
│  │    micro-pausa en el próximo    │    │
│  │    punto de corte.              │    │
│  └─────────────────────────────────┘    │
│                                         │
│  Score Mahalanobis:  4.8                │
│  Umbral personal:    3.2                │
│  Severidad:          ████░░░░ 42%      │
│                                         │
│  ┌─ Factores principales ──────────┐    │
│  │  ↑ Shimmer (estab. amplitud)    │    │
│  │    └ z = +2.1σ                  │    │
│  │  ↓ Altura de voz (F0)          │    │
│  │    └ z = -1.8σ                  │    │
│  │  ↑ Silencio (pausas)           │    │
│  │    └ z = +1.5σ                  │    │
│  │  ↑ Jitter (estab. periodo)     │    │
│  │    └ z = +1.2σ                  │    │
│  └─────────────────────────────────┘    │
│                                         │
│  ┌─────────────────────────────────┐    │
│  │    [  NUEVA EVALUACIÓN  ]       │    │
│  │    [  VER HISTORIAL     ]       │    │
│  └─────────────────────────────────┘    │
└─────────────────────────────────────────┘
```

### 6.6 Historial de evaluaciones

```
┌─────────────────────────────────────────┐
│  ← Volver al dashboard                  │
│                                         │
│  📋 HISTORIAL DE EVALUACIONES           │
│                                         │
│  ┌─────────────────────────────────┐    │
│  │  FECHA      ESTADO     SCORE   │    │
│  ├─────────────────────────────────┤    │
│  │  13 Jul ✅ OK          2.1    │    │
│  │  12 Jul 🟡 ATENCIÓN    4.8    │    │
│  │  10 Jul 🔴 PAUSA       7.2    │    │
│  │  09 Jul ✅ OK          1.9    │    │
│  │  08 Jul ✅ OK          2.5    │    │
│  └─────────────────────────────────┘    │
│                                         │
│  [Ver tendencia →] (post-MVP)          │
└─────────────────────────────────────────┘
```

---

## 7. API Backend (endpoints)

### 7.1 Autenticación

| Método | Endpoint | Body | Respuesta |
|--------|----------|------|-----------|
| `POST` | `/api/auth/register` | `{name, email, password, occupation?}` | `{user, token}` |
| `POST` | `/api/auth/login` | `{email, password}` | `{user, token}` |
| `POST` | `/api/auth/refresh` | `{refresh_token}` | `{access_token}` |
| `POST` | `/api/auth/logout` | — | `{message}` |

### 7.2 Baseline

| Método | Endpoint | Body/Params | Respuesta |
|--------|----------|-------------|-----------|
| `GET` | `/api/baseline/status` | — | `{total:8, count:N, is_complete:bool}` |
| `POST` | `/api/baseline/upload` | `multipart: audio_file` | `{sample_id, count, features}` |
| `GET` | `/api/baseline/samples` | — | `[{id, date, duration, status}]` |
| `DELETE` | `/api/baseline/samples/{id}` | — | `{message}` |
| `GET` | `/api/baseline/text` | — | `{text}` |

### 7.3 Evaluación

| Método | Endpoint | Body/Params | Respuesta |
|--------|----------|-------------|-----------|
| `POST` | `/api/evaluate` | `multipart: audio_file` | `{estado, mensaje, mahalanobis, threshold, severity, is_anomaly, top_drivers[...], z_scores{...}}` |
| `GET` | `/api/evaluate/history` | `?page, ?limit` | `[{id, date, estado, score, severity}]` |
| `GET` | `/api/evaluate/{id}` | — | `{reporte_completo}` |

### 7.4 Usuario

| Método | Endpoint | Body/Params | Respuesta |
|--------|----------|-------------|-----------|
| `GET` | `/api/users/me` | — | `{profile}` |
| `PUT` | `/api/users/me` | `{name?, occupation?}` | `{profile}` |

---

## 8. Modelo de datos

### 8.1 Tabla: `users`

```sql
CREATE TABLE users (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    name         TEXT NOT NULL,
    email        TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    occupation   TEXT,
    created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 8.2 Tabla: `baseline_samples`

```sql
CREATE TABLE baseline_samples (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id      INTEGER NOT NULL REFERENCES users(id),
    file_path    TEXT NOT NULL,         -- ruta al archivo de audio
    duration_s   REAL,                  -- duración en segundos
    sample_rate  INTEGER DEFAULT 16000,
    features_json TEXT,                  -- features extraídos (JSON)
    created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_baseline_user ON baseline_samples(user_id);
```

### 8.3 Tabla: `evaluations`

```sql
CREATE TABLE evaluations (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id         INTEGER NOT NULL REFERENCES users(id),
    file_path       TEXT NOT NULL,
    duration_s      REAL,
    sample_rate     INTEGER DEFAULT 16000,
    mahalanobis     REAL NOT NULL,
    threshold       REAL NOT NULL,
    severity        REAL NOT NULL,
    is_anomaly      BOOLEAN NOT NULL,
    estado          TEXT NOT NULL,       -- 'OK', 'ATENCIÓN', 'PAUSA SUGERIDA'
    mensaje         TEXT,
    top_drivers_json TEXT,               -- factores principales (JSON)
    z_scores_json   TEXT,                -- z-scores completo (JSON)
    baseline_count  INTEGER NOT NULL,    -- N muestras en baseline al evaluar
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_eval_user ON evaluations(user_id);
CREATE INDEX idx_eval_date ON evaluations(created_at);
```

### 8.4 Tabla: `settings`

```sql
CREATE TABLE settings (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

-- Ejemplo: texto de lectura fijo
INSERT INTO settings (key, value) VALUES (
    'reading_text',
    'El cielo está despejado y el sol brilla con fuerza sobre la ciudad. Los pájaros cantan mientras la gente camina por las calles. Es un día tranquilo y el ambiente se siente en cada rincón. Las nubes blancas se desplazan lentamente, y el viento sopla con suavidad. En el parque, los niños juegan y ríen sin preocupaciones. Los árboles mecen sus ramas al compás de la brisa. Todo parece estar en armonía, como si la naturaleza misma celebrara la vida. Leeré este texto con mi voz natural, manteniendo un ritmo constante y una entonación clara, para que el sistema pueda registrar las características acústicas de mi voz en este momento.'
);
```

---

## 9. Requerimientos no funcionales

### 9.1 Rendimiento

| ID | Requerimiento |
|----|--------------|
| RNF-01 | El procesamiento de audio (features + score) debe tomar ≤5s para archivos de hasta 3 min |
| RNF-02 | La interfaz debe cargar en ≤2s en conexiones 4G |
| RNF-03 | El backend debe soportar ≥10 evaluaciones simultáneas |

### 9.2 Seguridad

| ID | Requerimiento |
|----|--------------|
| RNF-04 | Contraseñas almacenadas con bcrypt (cost factor ≥12) |
| RNF-05 | JWT firmado con clave secreta de 256 bits |
| RNF-06 | Validación de tipo de archivo en subida (solo wav/mp3) |
| RNF-07 | Límite de tamaño de archivo: 20MB |
| RNF-08 | Sanitización de nombres de archivo |

### 9.3 UX / Diseño

| ID | Requerimiento |
|----|--------------|
| RNF-09 | Paleta de colores ALTTAB: naranja `#E8500A`, azul marino `#1A2B5F`, verde `#2E9E5B`, ámbar `#E8A00A` |
| RNF-10 | Diseño responsivo (mobile-first: 320px → desktop: 1440px) |
| RNF-11 | Feedback visual inmediato en acciones (spinners, toasts, animaciones) |
| RNF-12 | Accesibilidad: contraste WCAG AA, labels en formularios, estados de foco visibles |
| RNF-13 | Todos los textos en español latinoamericano |
| RNF-14 | Micro-interacciones: hover en cards, transiciones suaves en cambios de estado |

### 9.4 Almacenamiento

| ID | Requerimiento |
|----|--------------|
| RNF-15 | Los archivos de audio se almacenan en `uploads/{user_id}/baseline/` y `uploads/{user_id}/evaluations/` |
| RNF-16 | Los features extraídos se cachean en DB para evitar reprocesamiento |
| RNF-17 | Backup diario de la base de datos (post-MVP) |

---

## 10. Plan de implementación

### Fase 1 — MVP (Prioridad Alta)

| Paso | Descripción | Dependencias |
|------|-------------|-------------|
| 1.1 | Backend: modelo de datos + migraciones | Ninguna |
| 1.2 | Backend: endpoints de autenticación (registro/login) | 1.1 |
| 1.3 | Backend: endpoints de baseline (subir audio, status) | 1.1, motor Sereno |
| 1.4 | Backend: endpoint de evaluación + integración con `detector.py` | 1.1, motor Sereno |
| 1.5 | Frontend: HTML login/registro | 1.2 |
| 1.6 | Frontend: dashboard con progreso de baseline | 1.3 |
| 1.7 | Frontend: pantalla de grabación/subida de audio | 1.3 |
| 1.8 | Frontend: pantalla de resultado de evaluación | 1.4 |
| 1.9 | Integración y pruebas end-to-end | 1.1–1.8 |

### Fase 2 — Mejoras UX (Prioridad Media)

| Paso | Descripción |
|------|-------------|
| 2.1 | Grabación directa desde navegador (MediaRecorder API) |
| 2.2 | Historial de evaluaciones con tabla |
| 2.3 | Visualización de perfil de z-scores (gráfico de barras) |
| 2.4 | Advertencias de confianza para baseline parcial |
| 2.5 | Estados de carga y manejo de errores en toda la UI |

### Fase 3 — Post-MVP (Prioridad Baja)

| Paso | Descripción |
|------|-------------|
| 3.1 | Gráfico de tendencia de evaluaciones en el tiempo |
| 3.2 | Exportar reporte PDF |
| 3.3 | Recuperación de contraseña |
| 3.4 | Panel de administración (gestión de usuarios, texto de lectura) |
| 3.5 | Soporte para múltiples textos de lectura |
| 3.6 | Despliegue en producción (Docker, CI/CD) |

---

## Anexo A: Texto de lectura sugerido

> *"El cielo está despejado y el sol brilla con fuerza sobre la ciudad. Los pájaros cantan mientras la gente camina por las calles. Es un día tranquilo y el ambiente se siente en cada rincón. Las nubes blancas se desplazan lentamente, y el viento sopla con suavidad. En el parque, los niños juegan y ríen sin preocupaciones. Los árboles mecen sus ramas al compás de la brisa. Todo parece estar en armonía, como si la naturaleza misma celebrara la vida. Leeré este texto con mi voz natural, manteniendo un ritmo constante y una entonación clara, para que el sistema pueda registrar las características acústicas de mi voz en este momento."*

**Especificaciones:**
- ~150 palabras
- Tiempo estimado de lectura: 60–90 segundos
- Contiene variedad de fonemas y entonación natural
- Sin palabras técnicas ni difíciles de pronunciar
- Tono neutro para minimizar sesgo emocional

---

## Anexo B: Notas técnicas sobre baseline parcial

Cuando el usuario tiene **menos de 8 muestras** en el baseline:

| Muestras | Comportamiento |
|----------|---------------|
| **0** | ❌ Bloquear evaluación completamente |
| **1** | ⚠️ Evaluación disponible. No se puede calcular umbral LOO (necesita ≥2). Se usa la muestra única como vector de referencia. El score es distancia euclídea simple (no Mahalanobis, pues no hay covarianza estimable). |
| **2 a 7** | ⚠️ Evaluación disponible. Se calcula Mahalanobis con LedoitWolf. El umbral LOO es menos estable (con n pequeña). Se muestra advertencia y el score tiene una banda de confianza más amplia. |
| **8+** | ✅ Evaluación completa. Umbral LOO robusto. Sin advertencias. |

---

*Documento de requerimientos v1.0 — Generado a partir del análisis del código fuente de Sereno PoC (ALTTAB)*
