
import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.system_architecture import DesignSpace, PhysicsEngine, AIPredictor, InverseOptimizer

def test_single_pass():
    print("--- Testing Single Pass ---")
    # 1. Define Design
    design = DesignSpace(
        hea_composition={'Co': 1.5, 'Ni': 1.0, 'Cr': 0.5},
        sinter_temp_c=1400
    )
    print(f"Design Created: {design}")
    
    # 2. Physics Engine
    engine = PhysicsEngine()
    features = engine.compute_features(design)
    print("Computed Features:")
    for k, v in features.items():
        print(f"  {k}: {round(v, 4)}")
        
    # 3. Predictor
    predictor = AIPredictor()
    predictions = predictor.predict(features)
    print("Predictions:")
    for k, v in predictions.items():
        print(f"  {k}: {round(v, 4)}")
        
def test_optimization():
    print("\n--- Testing Inverse Optimization (NSGA-II) ---")
    optimizer = InverseOptimizer()
    
    # Run optimization
    best_trials = optimizer.optimize(n_trials=20)
    
    print(f"Optimization Complete. Found {len(best_trials)} best trials (Pareto Front).")
    
    for i, trial in enumerate(best_trials):
        print(f"\nSolution {i+1}:")
        print(f"  Params: {trial.params}")
        print(f"  Values (HV, K1C): {trial.values}")

if __name__ == "__main__":
    test_single_pass()
    test_optimization()
