import pytest
import pandas as pd
from core.hea_cermet import MaterialProcessor

@pytest.fixture
def processor():
    return MaterialProcessor()

def test_parse_formula_simple(processor):
    comp = processor.parse_formula("AlCoCrFeNi")
    assert len(comp) == 5
    assert comp['Al'] == pytest.approx(0.2)
    assert comp['Ni'] == pytest.approx(0.2)

def test_parse_formula_amounts(processor):
    comp = processor.parse_formula("Al10Co20")
    # Total = 30
    assert comp['Al'] == pytest.approx(10/30)
    assert comp['Co'] == pytest.approx(20/30)

def test_parse_formula_decimals(processor):
    comp = processor.parse_formula("Al1.5Co1.5")
    assert comp['Al'] == pytest.approx(0.5)
    assert comp['Co'] == pytest.approx(0.5)

def test_calculate_properties_hea(processor):
    # Equiatomic AlCoCrFeNi
    # S_mix = R * ln(5) approx 1.609 R
    comp = processor.parse_formula("AlCoCrFeNi")
    props = processor.calculate_properties(comp)
    
    assert props is not None
    assert props['S_mix (R)'] == pytest.approx(1.6094, abs=0.01)
    
    # Check other keys exist
    assert 'VEC' in props
    assert 'Delta (%)' in props

def test_calculate_enthalpy(processor):
    # Just check it runs and returns reasonable number (not crashing)
    comp = processor.parse_formula("AlCo")
    h = processor.calculate_enthalpy(comp)
    # Al-Co is -19 kJ/mol in the simplified DB check in hea_cermet.py
    # 4 * -19 * 0.5 * 0.5 = -19
    assert isinstance(h, float)
    assert h == pytest.approx(-19.0, abs=0.1)

def test_process_batch_extended(processor):
    df = pd.DataFrame({
        'Formula': ['AlCoCrFeNi', 'Al10Co20'],
        'GrainSize': [1.0, 2.0]
    })
    
    results = processor.process_batch_extended(df, 'Formula', 'GrainSize')
    assert 'S_mix (R)' in results.columns
    assert 'Enthalpy_mix (kJ/mol)' in results.columns
    assert len(results) == 2
