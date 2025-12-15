
import sys
import os

# Add parent directory to path to import core
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.hea_cermet import MaterialProcessor

def test_density():
    mp = MaterialProcessor()
    
    # Test Case: WC-10Co (Weight Percent)
    # Target Theoretical Density approx 14.5-14.6 g/cm3 depending on exact densities used.
    # W density approx 19.25, C density approx 2.26. 
    # BUT WC as a compound density is ~15.63. 
    # If the system only calculates based on elemental densities (W and C separately), the result will be wrong for a ceramic like WC!
    # Let's check how the system handles this.
    # core/hea_cermet.py line 229: rho = self.db.get_property(el, 'rho')
    # If the input is elemental W, C, Co, it uses rho_W, rho_C, rho_Co.
    # W+C as elements have volume V_W + V_C. 
    # V_W = 183.84/19.25 = 9.55. V_C = 12.01/2.26 = 5.31. Total = 14.86 cm3/mol.
    # WC Molar Mass = 195.85. 
    # Density (mixture of elements) = 195.85 / 14.86 = 13.18 g/cm3.
    # Real WC Density = 15.63 g/cm3.
    # So using elemental densities for Cermets (Carbides) is inaccurate if we treat them as just W+C mixture.
    
    # However, the user task was "convert Wt% to Vol% to calculate theoretical density".
    # If the user provides "WC" as a component, does the DB support it?
    # Let's check if the DB has 'WC' density or if I should assume elemental inputs.
    # If the input parses 'WC' as 'W' and 'C', it's elemental.
    
    # Let's try to pass "WC" as a key in composition.
    # BUT parse_formula splits by capital letters. "WC" -> W, C.
    # So it is elemental.
    # Limitation: The current system likely calculates "Elemental Mixture Density" not "Phase Mixture Density".
    # BUT, let's verify if the MATH I added is correct for what the system DOES (even if physics is simplified).
    
    # Let's verify with a simple mix of elemets: pure Co and pure Ni.
    # 50wt% Co, 50wt% Ni.
    # Co rho=8.9, Ni rho=8.9. Result should be 8.9.
    
    print("Test 1: 50wt% Co - 50wt% Ni")
    comp1 = {'Co': 50, 'Ni': 50}
    res1 = mp.calculate_cermet_properties(comp1, is_weight_percent=True)
    print(f"Result 1: {res1}")
    
    # Test 2: Wt% to Vol% check
    # Element A: rho=10, Wt=50. Vol=5.
    # Element B: rho=5, Wt=50. Vol=10.
    # Total Vol = 15. Total Wt = 100.
    # Density = 100/15 = 6.6667.
    # Vol% A = 5/15 = 33.33%.
    # Vol% B = 10/15 = 66.67%.
    
    # I need to mock the db or rely on real elements.
    # Mo (rho~10.28), V (rho~6.11). Close enough to 10 and 5?
    # Or just check the output value for known elements.
    # Mo rho=10.28. Ti rho=4.5.
    # 50wt% Mo, 50wt% Ti.
    # Vol Mo = 50/10.28 = 4.86.
    # Vol Ti = 50/4.5 = 11.11.
    # Total Vol = 15.97.
    # Density = 100 / 15.97 = 6.26.
    
    print("Test 2: 50wt% Mo - 50wt% Ti")
    comp2 = {'Mo': 50, 'Ti': 50}
    res2 = mp.calculate_cermet_properties(comp2, is_weight_percent=True)
    print(f"Result 2: {res2}")
    
if __name__ == "__main__":
    try:
        test_density()
        print("Verification Script Finished.")
    except Exception as e:
        print(f"Error: {e}")
