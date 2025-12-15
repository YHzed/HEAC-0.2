
import json

data = {
    # Existing
    "Al-Co": -19, "Al-Cr": -10, "Al-Cu": -1, "Al-Fe": -11, "Al-Ni": -22, "Al-Ti": -30,
    "Co-Cr": -4, "Co-Cu": 6, "Co-Fe": -1, "Co-Ni": 0, "Co-Ti": -28,
    "Cr-Fe": -1, "Cr-Ni": -7, "Cr-Ti": -7,
    "Cu-Fe": 13, "Cu-Ni": 4, "Cu-Ti": -9,
    "Fe-Ni": -2, "Fe-Ti": -17,
    "Ni-Ti": -35,
    # Additions
    "Al-Mn": -19, "Al-V": -16, "Al-Nb": -18, "Al-Mo": -5, "Al-Ta": -19, "Al-W": -2, "Al-Zr": -44, "Al-Hf": -39,
    "Co-Mn": -5, "Co-V": -14, "Co-Nb": -25, "Co-Mo": -5, "Co-Ta": -24, "Co-W": -1, "Co-Zr": -41, "Co-Hf": -34,
    "Cr-Mn": 2, "Cr-V": -2, "Cr-Nb": -7, "Cr-Mo": 0, "Cr-Ta": -7, "Cr-W": 1, "Cr-Zr": -12, "Cr-Hf": -9,
    "Cu-Mn": 4, "Cu-V": 5, "Cu-Nb": 3, "Cu-Mo": 19, "Cu-Ta": 2, "Cu-W": 23, "Cu-Zr": -23, "Cu-Hf": -17,
    "Fe-Mn": 0, "Fe-V": -7, "Fe-Nb": -16, "Fe-Mo": -2, "Fe-Ta": -15, "Fe-W": 0, "Fe-Zr": -25, "Fe-Hf": -21,
    "Ni-Mn": -8, "Ni-V": -18, "Ni-Nb": -30, "Ni-Mo": -7, "Ni-Ta": -29, "Ni-W": -3, "Ni-Zr": -49, "Ni-Hf": -42,
    "Ti-Mn": -8, "Ti-V": -2, "Ti-Nb": 2, "Ti-Mo": -4, "Ti-Ta": 1, "Ti-W": -6, "Ti-Zr": 0, "Ti-Hf": 0,
    "Mn-V": -5, "Mn-Nb": -4, "Mn-Mo": 5, "Mn-Ta": -3, "Mn-W": 7, "Mn-Zr": -24, "Mn-Hf": -19,
    "V-Nb": 1, "V-Mo": -6, "V-Ta": 1, "V-W": -8, "V-Zr": -4, "V-Hf": -2,
    "Nb-Mo": -6, "Nb-Ta": 0, "Nb-W": -8, "Nb-Zr": 4, "Nb-Hf": 4,
    "Mo-Ta": -5, "Mo-W": 0, "Mo-Zr": -6, "Mo-Hf": -4,
    "Ta-W": -4, "Ta-Zr": 3, "Ta-Hf": 3,
    "W-Zr": -9, "W-Hf": -6,
    "Zr-Hf": 0
}

# Normalize keys to be alphabetical
normalized_data = {}
for key, value in data.items():
    el1, el2 = key.split('-')
    pair = sorted([el1, el2])
    new_key = f"{pair[0]}-{pair[1]}"
    normalized_data[new_key] = value

with open(r'd:\ML\HEAC 0.2\core\data\enthalpy.json', 'w', encoding='utf-8') as f:
    json.dump(normalized_data, f, indent=4)
