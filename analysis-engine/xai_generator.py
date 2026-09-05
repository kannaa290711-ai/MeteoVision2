import sys
import os
import pandas as pd
import numpy as np

# Path setup
sys.path.append(os.path.abspath(os.path.dirname(__file__)))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.database import SessionLocal
from backend.app.models import AnomalyFlag, XAINarrative, RawReading, Station

UNIT_MAP = {
    "temperature": "°C",
    "humidity": "%",
    "pressure": "hPa"
}

def get_confidence_phrasing(conf: float) -> tuple[str, str]:
    """
    Returns (verb_phrase, strength_phrase) scaled according to ml_confidence level:
    - conf >= 0.80: High confidence (confident phrasing)
    - 0.60 <= conf < 0.80: Moderate confidence (moderate phrasing)
    - conf < 0.60: Low confidence (hedged / cautious phrasing)
    """
    if conf >= 0.80:
        return "strongly indicates a", "(high ML confidence)"
    elif conf >= 0.60:
        return "suggests a likely", "(moderate ML confidence)"
    else:
        return "may indicate a potential", "(low ML confidence edge case)"

def generate_narrative_text(flag, raw_val, station_name):
    var = flag.variable
    unit = UNIT_MAP.get(var, "")
    ft = flag.predicted_fault_type
    t_score = flag.temporal_score
    s_score = flag.spatial_score
    f_score = flag.frozen_score
    d_score = flag.drift_score
    nagree = flag.neighbor_agreement
    conf = flag.ml_confidence
    ts_str = flag.timestamp.strftime("%Y-%m-%d %H:%M")

    verb, strength = get_confidence_phrasing(conf)
    nagree_pct = int(round(nagree * 100))
    n_match = int(round(nagree * 3))

    if ft == "drift":
        if nagree < 0.50:
            # Low neighbor agreement (< 50%) -> Single-station fault
            text = (
                f"Flagged as sensor drift ({var}): telemetry accumulated a sustained baseline deviation "
                f"(drift score: {d_score:.2f}, spatial score: {s_score:.2f}), with only {n_match} of 3 neighboring "
                f"stations showing a similar shift (neighbor agreement: {nagree_pct}%). This spatial divergence {verb} "
                f"single-station sensor calibration drift rather than a regional synoptic weather front {strength} (ML Confidence: {conf*100:.1f}%)."
            )
        else:
            # High neighbor agreement (>= 50%) -> Regional synoptic event (Model edge case if classified as drift)
            text = (
                f"Flagged as sensor drift ({var}): telemetry accumulated a baseline deviation (drift score: {d_score:.2f}, "
                f"spatial score: {s_score:.2f}), but {n_match} of 3 neighboring stations show a matching shift "
                f"(neighbor agreement: {nagree_pct}%). High neighbor agreement {verb} regional atmospheric weather event "
                f"(synoptic front) rather than a localized sensor fault {strength} (ML Confidence: {conf*100:.1f}%)."
            )

    elif ft == "spike":
        raw_str = f"{raw_val:.2f}{unit}" if raw_val is not None else "telemetry"
        text = (
            f"Flagged as sensor spike ({var}): reading ({raw_str}) exhibited a sharp temporal rate-of-change "
            f"discontinuity (temporal score: {t_score:.2f}) at {ts_str}, while surrounding neighbor stations remained "
            f"physically stable (spatial score: {s_score:.2f}, neighbor agreement: {nagree_pct}%). This {verb} "
            f"instantaneous hardware voltage transient or impulse error {strength} (ML Confidence: {conf*100:.1f}%)."
        )

    elif ft == "frozen":
        raw_str = f"{raw_val:.2f}{unit}" if raw_val is not None else "value"
        text = (
            f"Flagged as frozen sensor ({var}): sensor output remained static at {raw_str} over a trailing 3-hour "
            f"window with near-zero rolling variance (frozen score: {f_score:.2f}). This flat-line signature {verb} "
            f"hardware sensor lockup violating physical micro-variability expectations {strength} (ML Confidence: {conf*100:.1f}%)."
        )

    elif ft == "missing":
        text = (
            f"Flagged as missing telemetry ({var}): data stream was unrecorded or null at {ts_str} for station {station_name}. "
            f"Passed to self-healing spatial-temporal interpolation engine {strength} (ML Confidence: {conf*100:.1f}%)."
        )

    else:  # none / synoptic weather event
        text = (
            f"Verified normal telemetry / regional weather event ({var}): observed shift is corroborated by {nagree_pct}% "
            f"neighbor agreement across surrounding stations (spatial score: {s_score:.2f}). Confirmed as a legitimate "
            f"meteorological atmospheric shift rather than a localized sensor fault {strength} (ML Confidence: {conf*100:.1f}%)."
        )

    return text

def generate_xai_narratives():
    print("=" * 65)
    print("  AETHERIX SENTINEL - Phase 3 Explainable AI (XAI) Narrative Generator")
    print("=" * 65)
    
    db = SessionLocal()
    try:
        stations = {s.station_id: s.name for s in db.query(Station).all()}
        raw_readings = {(r.station_id, r.timestamp): r for r in db.query(RawReading).all()}
        
        print("[1/2] Querying anomaly flags & generating confidence-scaled narratives...")
        flags = db.query(AnomalyFlag).filter(AnomalyFlag.flagged == True).all()
        
        print(f"      Generating XAI explanations for {len(flags)} flagged anomaly events...")
        
        db.query(XAINarrative).delete()
        db.commit()
        
        narrative_records = []
        for flag in flags:
            r = raw_readings.get((flag.station_id, flag.timestamp))
            raw_val = None
            if r:
                raw_val = getattr(r, flag.variable, None)
                
            st_name = stations.get(flag.station_id, flag.station_id)
            narrative = generate_narrative_text(flag, raw_val, st_name)
            
            narrative_records.append({
                "flag_id": flag.id,
                "station_id": flag.station_id,
                "variable": flag.variable,
                "timestamp": flag.timestamp,
                "predicted_fault_type": flag.predicted_fault_type,
                "explanation_text": narrative
            })
            
        print("[2/2] Saving updated XAI narratives to database...")
        db.bulk_insert_mappings(XAINarrative, narrative_records)
        db.commit()
        print(f"      Successfully saved {len(narrative_records)} XAI narratives!")
        print("=" * 65 + "\n")
        
        return narrative_records
        
    finally:
        db.close()

if __name__ == "__main__":
    generate_xai_narratives()
