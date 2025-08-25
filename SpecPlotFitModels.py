# fit_models.py
from __future__ import annotations
import numpy as np

try:
    from scipy.optimize import curve_fit
except Exception:  # pragma: no cover
    curve_fit = None

# ---- Models ----
def gaussian(x, A, x0, sigma, B):
    # A * exp(-(x-x0)^2 / (2 sigma^2)) + B
    return A * np.exp(-0.5 * ((x - x0) / np.maximum(sigma, 1e-12)) ** 2) + B

def hill(x, y0, A, K, n):
    # y = y0 + A * x^n / (K^n + x^n)   (increasing Hill)
    x = np.asarray(x, dtype=float)
    xn = np.power(np.maximum(x, 0.0), np.maximum(n, 1e-9))
    Kn = np.power(np.maximum(K, 1e-12), np.maximum(n, 1e-9))
    return y0 + A * xn / (Kn + xn)

# ---- Guessers ----
def _guess_gaussian(x, y):
    x = np.asarray(x); y = np.asarray(y)
    B = float(np.nanpercentile(y, 10))
    y2 = y - B
    i = int(np.nanargmax(y2))
    x0 = float(x[i]); A = float(max(y2[i], 1e-6))
    # crude width: FWHM from half-maximum crossings
    half = B + A/2.0
    above = y >= half
    if np.any(above):
        idx = np.where(above)[0]
        width = np.clip(x[idx[-1]] - x[idx[0]], 1e-6, np.ptp(x))
    else:
        width = np.ptp(x) * 0.1
    sigma = float(width / 2.354820045)  # FWHM = 2*sqrt(2ln2)*sigma
    return (A, x0, sigma, B)

def _guess_hill(x, y):
    x = np.asarray(x); y = np.asarray(y)
    y0 = float(np.nanmin(y))
    ymax = float(np.nanmax(y))
    A = float(max(ymax - y0, 1e-6))
    # K near mid x or where y crosses ~half amplitude
    half = y0 + 0.5 * A
    try:
        K = float(np.interp(half, y, x))
    except Exception:
        K = float(np.median(x))
    n = 2.0
    return (y0, A, max(K, 1e-9), n)

# ---- Public: fit(x, y, model) ----
def fit_curve(x, y, model: str):
    """
    Returns dict:
      {'model': 'gaussian'|'hill', 'popt': array, 'pcov': array|None,
       'params': {name: value}, 'stderr': {name: se}|None,
       'x0': center, 'fwhm': fwhm_or_None, 'r2': r2}
    """
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    good = np.isfinite(x) & np.isfinite(y)
    x, y = x[good], y[good]
    if x.size < 3:
        raise ValueError("Not enough data points to fit.")

    if model == "gaussian":
        fn = gaussian
        p0 = _guess_gaussian(x, y)
        names = ("A", "x0", "sigma", "B")
        bounds = (-np.inf, np.inf)
    elif model == "hill":
        fn = hill
        p0 = _guess_hill(x, y)
        names = ("y0", "A", "K", "n")
        # reasonable bounds to keep it stable
        lb = (-np.inf, 0.0, 1e-12, 0.5)
        ub = ( np.inf,  np.inf, np.inf, 6.0)
        bounds = (lb, ub)
    else:
        raise ValueError(f"Unknown model: {model}")

    if curve_fit is None:
        raise RuntimeError("scipy is required for fitting (pip install scipy)")

    popt, pcov = curve_fit(fn, x, y, p0=p0, bounds=bounds, maxfev=10000)

    yhat = fn(x, *popt)
    ss_res = float(np.sum((y - yhat) ** 2))
    ss_tot = float(np.sum((y - np.mean(y)) ** 2)) or 1.0
    r2 = 1.0 - ss_res / ss_tot

    stderr = None
    if pcov is not None and np.all(np.isfinite(pcov)):
        se = np.sqrt(np.clip(np.diag(pcov), 0.0, np.inf))
        stderr = {n: float(s) for n, s in zip(names, se)}

    params = {n: float(v) for n, v in zip(names, popt)}
    center = params.get("x0", params.get("K", float(np.median(x))))
    fwhm = None
    if model == "gaussian":
        fwhm = 2.354820045 * params["sigma"]

    return dict(
        model=model, popt=popt, pcov=pcov,
        params=params, stderr=stderr, x0=float(center),
        fwhm=(float(fwhm) if fwhm is not None else None), r2=float(r2)
    )
