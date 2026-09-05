import sys
import os

# Path setup
sys.path.append(os.path.abspath(os.path.dirname(__file__)))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.database import engine, Base
from imputation_engine import run_self_healing_imputation
from health_scorer import calculate_sensor_health_scores
from xai_generator import generate_xai_narratives

def main():
    print("=" * 70)
    print("  AETHERIX SENTINEL — Phase 3 Execution Pipeline")
    print("  (Self-Healing Imputation + Physics Check + Health Scoring + XAI)")
    print("=" * 70)
    
    # 0. Ensure tables exist in database
    print("\n[0/4] Verifying database tables schema...")
    Base.metadata.create_all(bind=engine)
    print("      Database tables verified/created.")
    
    # 1. Run Self-Healing Imputation Engine + Physics Sanity Check
    print("\n[1/4] Running Self-Healing Imputation Engine...")
    imputed_records = run_self_healing_imputation()
    
    # 2. Run Sensor Health Scoring
    print("\n[2/4] Running Sensor Health Scorer...")
    health_scores = calculate_sensor_health_scores()
    
    # 3. Run XAI Narrative Generator
    print("\n[3/4] Running XAI Narrative Generator...")
    narratives = generate_xai_narratives()
    
    print("\n" + "=" * 70)
    print("  PHASE 3 PIPELINE COMPLETED SUCCESSFULLY!")
    print(f"  - Imputed Records Generated : {len(imputed_records)}")
    print(f"  - Sensor Health Scores      : {len(health_scores)}")
    print(f"  - XAI Narratives Generated  : {len(narratives)}")
    print("=" * 70 + "\n")

if __name__ == "__main__":
    main()
