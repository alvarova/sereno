"""
Detector de desviaciones respecto al baseline personal.

Enfoque:
  - Se construye un BASELINE por usuario con N grabaciones en estado normal
    (misma lectura de texto fijo).
  - Para una muestra nueva se calcula:
      * z-score robusto por feature (mediana + MAD) -> interpretable
      * score de anomalia multivariado (distancia de Mahalanobis con
        covarianza estabilizada por shrinkage Ledoit-Wolf) -> deteccion global
  - El umbral se deriva del propio baseline (percentil de las distancias
    intra-baseline), de modo que cada persona tiene su propio criterio.
"""
import numpy as np
from sklearn.covariance import LedoitWolf
from features import extract_features, features_to_vector, FEATURE_ORDER

# Direccion de "deterioro" esperada por feature (signo del z-score que
# indica fatiga/tension). Se usa solo para explicar el resultado, no para
# la deteccion en si.
DETERIORATION_SIGN = {
    "f0_mean": -1,        # pitch baja
    "f0_std": -1,         # voz mas monotona
    "f0_range": -1,       # menos rango entonativo
    "voiced_ratio": -1,   # menos fonacion
    "jitter_local": +1,   # mas inestabilidad de periodo
    "shimmer_local": +1,  # mas inestabilidad de amplitud
    "hnr_mean": -1,       # voz mas ruidosa/apagada
    "intensity_mean": -1, # menos energia
    "intensity_std": -1,  # menos dinamica
    "silence_ratio": +1,  # mas pausas
    "pause_rate": +1,     # mas cortes
}


class BaselineDetector:
    def __init__(self):
        self.median_ = None
        self.mad_ = None
        self.cov_ = None
        self.mean_ = None
        self.threshold_ = None
        self.baseline_scores_ = None

    def fit(self, signals, sr):
        """Construye el baseline a partir de una lista de senales normales."""
        X = np.array([features_to_vector(extract_features(s, sr)) for s in signals])
        self.X_ = X
        self.mean_ = np.mean(X, axis=0)
        self.median_ = np.median(X, axis=0)
        # MAD robusto (con factor de consistencia para ~sigma normal)
        self.mad_ = 1.4826 * np.median(np.abs(X - self.median_), axis=0)
        self.mad_[self.mad_ == 0] = 1e-6
        # covarianza estabilizada (shrinkage) para Mahalanobis
        lw = LedoitWolf().fit(X)
        self.cov_ = lw
        # --- umbral por LEAVE-ONE-OUT ---
        # Para cada muestra i, se estima la covarianza con las otras n-1 y se
        # mide su distancia. Asi el umbral refleja una muestra normal NO vista
        # (evita el sesgo optimista de reusar el mismo set).
        loo_scores = []
        n = len(X)
        for i in range(n):
            Xo = np.delete(X, i, axis=0)
            lw_o = LedoitWolf().fit(Xo)
            loo_scores.append(float(lw_o.mahalanobis(X[i].reshape(1, -1))[0] ** 0.5))
        self.loo_scores_ = np.array(loo_scores)
        # umbral: media LOO + 3*sigma  (piso en el maximo LOO observado)
        mu, sd = np.mean(self.loo_scores_), np.std(self.loo_scores_)
        self.threshold_ = float(max(mu + 3 * sd, np.max(self.loo_scores_) * 1.05))
        self.baseline_scores_ = lw.mahalanobis(X) ** 0.5
        return self

    def score(self, signal, sr):
        """Evalua una muestra nueva y devuelve un reporte."""
        feats = extract_features(signal, sr)
        x = features_to_vector(feats)
        # z-scores robustos por feature
        z = (x - self.median_) / self.mad_
        # score global (Mahalanobis)
        maha = float(self.cov_.mahalanobis(x.reshape(1, -1))[0] ** 0.5)
        # deteccion
        is_anomaly = maha > self.threshold_
        # severidad normalizada 0..1 (relativa al umbral)
        severity = float(min(maha / (self.threshold_ * 2), 1.0))
        # contribuciones alineadas con "deterioro"
        contribs = {}
        for i, k in enumerate(FEATURE_ORDER):
            aligned = z[i] * DETERIORATION_SIGN[k]  # >0 => hacia fatiga
            contribs[k] = {"value": float(x[i]), "z": float(z[i]),
                           "deterioration_z": float(aligned),
                           "direction": "sube" if z[i] > 0 else "baja"}
        # top drivers hacia deterioro
        drivers = sorted(contribs.items(),
                         key=lambda kv: kv[1]["deterioration_z"], reverse=True)
        return {
            "mahalanobis": maha,
            "threshold": self.threshold_,
            "is_anomaly": bool(is_anomaly),
            "severity": severity,
            "z_scores": {k: contribs[k]["z"] for k in FEATURE_ORDER},
            "top_drivers": [(k, contribs[k]["direction"], contribs[k]["z"],
                             contribs[k]["deterioration_z"])
                            for k, v in drivers[:4]],
        }

    def recommend(self, report):
        """Traduce el score a una recomendacion operativa (Sereno)."""
        s = report["severity"]
        if not report["is_anomaly"]:
            return ("OK", "Voz dentro del rango basal. Sin señales de fatiga.")
        if s < 0.5:
            return ("ATENCIÓN",
                    "Desviación leve respecto al basal. Conviene una micro-pausa "
                    "en el próximo punto de corte.")
        return ("PAUSA SUGERIDA",
                "Desviación marcada respecto al basal. Se sugiere una pausa "
                "preventiva antes de continuar.")
