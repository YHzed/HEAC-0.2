# Materials Project API (MP-API) Reference

This document provides a quick reference for using the `mp-api` python client to interact with the Materials Project database.

## 1. Installation

```bash
pip install mp-api
```

## 2. Setup

Ensure you have your API key ready. It is best practice to store it in an environment variable `MP_API_KEY`.

## 3. Basic Usage

### Connecting to the API

```python
from mp_api.client import MPRester

# With API key as an argument (not recommended for shared code)
# with MPRester("YOUR_API_KEY") as mpr:
#     pass

# With API key in environment variable "MP_API_KEY" (Recommended)
with MPRester() as mpr:
    # Your code here
    pass
```

### Searching for Materials

The primary endpoint for searching is `mpr.materials.summary`.

#### Common Search Arguments:

*   `elements` (List[str]): List of element symbols (e.g., `["Ti", "C"]`).
*   `chemsys` (str): Chemical system string (e.g., `"Ti-C"` or `"Ti-*-*"`).
*   `formula` (str): Specific formula (e.g., `"TiC"`).
*   `fields` (List[str]): List of specific fields to retrieve (reduces download size).

#### Example: Searching by Elements

```python
with MPRester() as mpr:
    # Search for materials containing EXACTLY Ti and C
    docs = mpr.materials.summary.search(chemsys="Ti-C")
    
    # Search for materials containing AT LEAST Ti and C
    docs = mpr.materials.summary.search(elements=["Ti", "C"])
```

### Retrieving Data

The search returns a list of `SummaryDoc` objects. You can access properties as attributes.

Common Fields:
*   `material_id` (str): The MP ID (e.g., "mp-1234").
*   `formula_pretty` (str): Human-readable formula.
*   `formation_energy_per_atom` (float): Formation energy in eV/atom.
*   `is_stable` (bool): Whether the material is thermodynamically stable.
*   `symmetry` (object): Symmetry information.
*   `structure` (Structure): Pymatgen Structure object.

```python
for doc in docs:
    print(f"{doc.material_id}: {doc.formula_pretty} ({doc.formation_energy_per_atom} eV/atom)")
```

## 4. Specific Examples

### Fetching High Entropy Alloy/Ceramic Candidates

To find constituents for a High Entropy system (e.g., Ti-Zr-Hf-Nb-Ta-C), search for the binary or ternary building blocks:

```python
constituents = ["Ti", "Zr", "Hf", "Nb", "Ta"]
target_anion = "C"

with MPRester() as mpr:
    for metal in constituents:
        docs = mpr.materials.summary.search(
            chemsys=f"{metal}-{target_anion}", 
            fields=["material_id", "formula_pretty", "is_stable"]
        )
        # Process docs...
```
