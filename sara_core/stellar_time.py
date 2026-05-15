"""
SARA stellar time — UT1 / DUT1 (IERS earth orientation), geospatial Sol geometry,
and a monotonic internal tick (no civil DST; no Gregorian leap rules on the tick).

Civil POSIX/UTC remains the machine sync layer. This module adds a physics-aligned
parallel frame for runtime, cross-node agreement (same inputs → same outputs),
and future security attestation (hash of snapshot + model_versions).

Dependencies: `astropy` (IERS tables; auto-download when online). Optional offline:
  set env SARA_IERS_FILE to a path containing IERS finals2000A.all (or Astropy-bundled).
"""

from __future__ import annotations

import hashlib
import json
import math
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Tuple

# Default SARA tick origin (UTC instant); Gregorian-looking date only defines the epoch
# instant — the *tick* is pure SI seconds from here with no leap-year/DST semantics.
DEFAULT_STELLAR_EPOCH_UTC = "2000-01-01T00:00:00"
DEFAULT_OBSERVER_PATH = os.path.join(
    os.path.expanduser("~"), "sara_nbs", "stellar_observer.json"
)


def _configure_iers() -> None:
    """Prefer local IERS file if provided; otherwise Astropy auto-download when needed."""
    try:
        from astropy.utils import iers

        local = os.environ.get("SARA_IERS_FILE", "").strip()
        if local and os.path.isfile(local):
            iers.conf.auto_download = False
            # Astropy 6+: use earth_orientation_file; older used iers_auto_url only
            if hasattr(iers.conf, "iers_file"):
                iers.conf.iers_file = local
            elif hasattr(iers.conf, "iers_local_file"):
                iers.conf.iers_local_file = local
        # else: keep defaults (auto_download True where supported)
    except Exception:
        pass


def _load_default_observer() -> Tuple[Optional[float], Optional[float], float]:
    try:
        if os.path.isfile(DEFAULT_OBSERVER_PATH):
            with open(DEFAULT_OBSERVER_PATH, "r", encoding="utf-8") as f:
                d = json.load(f)
            lat = float(d["lat"])
            lon = float(d["lon"])
            h = float(d.get("height_m", 0.0))
            return lat, lon, h
    except Exception:
        pass
    return None, None, 0.0


def _save_default_observer(lat: float, lon: float, height_m: float = 0.0) -> None:
    os.makedirs(os.path.dirname(DEFAULT_OBSERVER_PATH), exist_ok=True)
    with open(DEFAULT_OBSERVER_PATH, "w", encoding="utf-8") as f:
        json.dump({"lat": lat, "lon": lon, "height_m": height_m}, f, indent=2)


MODEL_VERSION = "stellar_time/1.0.1+astropy_iers"


def _fmt10(value: Optional[float]) -> Optional[str]:
    """Fixed 10 decimal places for interchange (not added intrinsic accuracy)."""
    if value is None:
        return None
    try:
        return f"{float(value):.10f}"
    except (TypeError, ValueError):
        return None


def stellar_epoch_utc_str() -> str:
    return str(os.environ.get("SARA_STELLAR_EPOCH_UTC", DEFAULT_STELLAR_EPOCH_UTC)).strip()


def _epoch_time():
    from astropy.time import Time

    return Time(stellar_epoch_utc_str(), format="isot", scale="utc")


def compute_stellar_snapshot(
    utc_instant: Optional[datetime] = None,
    lat_deg: Optional[float] = None,
    lon_deg: Optional[float] = None,
    height_m: Optional[float] = None,
) -> Dict[str, Any]:
    """
    Full physics snapshot at utc_instant (default: now UTC).

    Returns UT1, DUT1 (UT1−UTC), GMST, apparent Sun ecliptic longitude (geocentric),
    optional alt/az if lat/lon given (WGS84 surface), SARA SI tick from configured epoch,
    and an attestation hash for security layers later.
    """
    _configure_iers()
    try:
        from astropy.time import Time
        import astropy.units as u
        from astropy.coordinates import EarthLocation, AltAz, get_sun
    except Exception as e:
        return {
            "success": False,
            "error": f"stellar_time requires astropy and ephemeris: {e}",
            "model_versions": {"stellar_module": MODEL_VERSION},
        }

    if utc_instant is None:
        utc_instant = datetime.now(timezone.utc)
    if utc_instant.tzinfo is None:
        utc_instant = utc_instant.replace(tzinfo=timezone.utc)

    t = Time(utc_instant, format="datetime", scale="utc")

    # DUT1 = UT1 − UTC  (IERS)
    try:
        dut1_sec = float(t.get_delta_ut1_utc().to(u.s).value)
    except Exception:
        dt = t.ut1 - t.utc
        dut1_sec = float(dt.to(u.s).value)

    ut1_iso = t.ut1.isot
    utc_iso = t.utc.isot

    # GMST (Earth rotation angle for navigation astronomy)
    try:
        gmst_rad = t.sidereal_time("mean", "greenwich").rad
        gmst_deg = float(math.degrees(gmst_rad))
    except Exception:
        gmst_deg = None

    # Geocentric true ecliptic longitude of Sun (seasons / equal-split calendar anchor)
    try:
        sun = get_sun(t)
        sun_lon_deg = float(sun.geocentrictrueecliptic.lon.deg)
    except Exception:
        sun_lon_deg = None

    dlat, dlon, dh = _load_default_observer()
    if lat_deg is None:
        lat_deg = dlat
    if lon_deg is None:
        lon_deg = dlon
    if height_m is None:
        height_m = dh

    sun_alt_deg = sun_az_deg = None
    if lat_deg is not None and lon_deg is not None:
        try:
            loc = EarthLocation(
                lat=lat_deg * u.deg,
                lon=lon_deg * u.deg,
                height=(height_m or 0.0) * u.m,
            )
            aa = AltAz(location=loc, obstime=t)
            sun_app = get_sun(t).transform_to(aa)
            sun_alt_deg = float(sun_app.alt.deg)
            sun_az_deg = float(sun_app.az.deg)
        except Exception:
            pass

    # Monotonic SARA tick: SI seconds from stellar epoch (no leap years / no DST in this count)
    try:
        t0 = _epoch_time()
        sara_si_seconds = float((t - t0).to(u.s).value)
    except Exception:
        sara_si_seconds = None

    # Tropical year fraction [0,1) for custom equal-split calendars (not Gregorian)
    tropical_year_fraction: Optional[float] = None
    if sun_lon_deg is not None:
        tropical_year_fraction = (sun_lon_deg % 360.0) / 360.0

    body: Dict[str, Any] = {
        "utc_isot": utc_iso,
        "ut1_isot": ut1_iso,
        "dut1_seconds": dut1_sec,
        "gmst_degrees": gmst_deg,
        "sun_ecliptic_longitude_deg": sun_lon_deg,
        "tropical_year_fraction": tropical_year_fraction,
        "observer": {
            "lat_deg": lat_deg,
            "lon_deg": lon_deg,
            "height_m": height_m,
            "frame": "WGS84",
        },
        "sun_apparent_alt_deg": sun_alt_deg,
        "sun_apparent_az_deg": sun_az_deg,
        "sara_si_seconds_since_epoch": sara_si_seconds,
        "stellar_epoch_utc": stellar_epoch_utc_str(),
        "notes": {
            "civil": "POSIX/TLS/logs still use UTC; this frame is parallel physics truth.",
            "dst": "No DST in sara_si_seconds; local solar uses longitude only if you derive LMST.",
            "leap": "No Gregorian leap rules on the tick; optional calendar overlays use tropical_year_fraction.",
            "precision": "display_10dp strings minimize rounding in logs/handoffs; they do not correct a failed NTP/GPS source — anchor + monotonic drift is a separate fallback.",
        },
        "model_versions": {
            "stellar_module": MODEL_VERSION,
        },
    }

    # Attestation stub for SECURITY later: deterministic hash of canonical JSON
    canon = json.dumps(body, sort_keys=True, default=str)
    body["attestation_sha256"] = hashlib.sha256(canon.encode("utf-8")).hexdigest()
    body["success"] = True
    # Human / secondary-system interchange: 10 dp (after hash — not part of attestation)
    body["display_10dp"] = {
        "_precision_note": (
            "These strings are fixed-format serialization (10 fractional digits). "
            "They preserve sub-millisecond values in JSON/text pipelines; they do not create "
            "new physical accuracy when the host clock or IERS cache is wrong. "
            "If UTC/NTP fails, combine last trusted stellar snapshot with monotonic elapsed time."
        ),
        "dut1_seconds": _fmt10(dut1_sec),
        "gmst_degrees": _fmt10(gmst_deg),
        "sun_ecliptic_longitude_deg": _fmt10(sun_lon_deg),
        "tropical_year_fraction": _fmt10(tropical_year_fraction),
        "sun_apparent_alt_deg": _fmt10(sun_alt_deg),
        "sun_apparent_az_deg": _fmt10(sun_az_deg),
        "sara_si_seconds_since_epoch": _fmt10(sara_si_seconds),
        "observer_lat_deg": _fmt10(float(lat_deg)) if lat_deg is not None else None,
        "observer_lon_deg": _fmt10(float(lon_deg)) if lon_deg is not None else None,
        "observer_height_m": _fmt10(float(height_m if height_m is not None else 0.0)),
    }
    return body


def dut1_now() -> Dict[str, Any]:
    snap = compute_stellar_snapshot()
    if not snap.get("success"):
        return snap
    return {
        "success": True,
        "utc_isot": snap["utc_isot"],
        "ut1_isot": snap["ut1_isot"],
        "dut1_seconds": snap["dut1_seconds"],
        "dut1_seconds_10dp": (snap.get("display_10dp") or {}).get("dut1_seconds"),
        "model_versions": snap.get("model_versions"),
    }


def set_default_observer(lat_deg: float, lon_deg: float, height_m: float = 0.0) -> Dict[str, Any]:
    _save_default_observer(lat_deg, lon_deg, height_m)
    return {"success": True, "path": DEFAULT_OBSERVER_PATH, "lat": lat_deg, "lon": lon_deg, "height_m": height_m}


def get_default_observer() -> Dict[str, Any]:
    lat, lon, h = _load_default_observer()
    return {"success": True, "lat": lat, "lon": lon, "height_m": h, "path": DEFAULT_OBSERVER_PATH}


@dataclass
class StellarTimeConfig:
    """Reserved for future SECURITY binding (nonce + snapshot hash)."""

    stellar_epoch_utc: str = DEFAULT_STELLAR_EPOCH_UTC
