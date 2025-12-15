# Using the Materials Project API (Official Guide)

*Source: https://docs.materialsproject.org/downloading-data/using-the-api*

This document illustrates how to access Materials Project data through the API using the officially supported Python client package `mp-api`.

## 1. Getting Started

### Installation

The `mp-api` package can be installed using pip:

```bash
pip install mp-api
```

Alternatively, install from source:

```bash
git clone https://github.com/materialsproject/api
cd api
pip install -e .
```

### Setup API Key

An API key is needed to use the client. You can find your key on your [profile dashboard](https://next-gen.materialsproject.org/dashboard).

It is best practice to set the `MP_API_KEY` environment variable:

```bash
export MP_API_KEY="your_api_key_here"
```

### Connecting

Use the `MPRester` class. It is preferred to use the context manager:

```python
from mp_api.client import MPRester

# Option 1: Use environment variable (Recommended)
with MPRester() as mpr:
    # do stuff with mpr
    pass

# Option 2: Pass API key directly
# with MPRester("your_api_key_here") as mpr:
#     pass
```

## 2. Querying Data

Materials Project data can be queried through specific Materials Project IDs or property filters.
Most material property data is available as **summary data**.

### Searching by Material ID

To query summary data with Materials Project IDs:

```python
with MPRester() as mpr:
    docs = mpr.materials.summary.search(material_ids=["mp-149", "mp-13", "mp-22526"])
    
    example_doc = docs[0]
    mpid = example_doc.material_id
    formula = example_doc.formula_pretty
    print(f"{mpid}: {formula}")
```

### Searching by Properties (Filters)

You can filter by elements, band gap, volume, etc.

Example: Find materials containing Si and O with a band gap between 0.5 and 1.0 eV.

```python
with MPRester() as mpr:
    docs = mpr.materials.summary.search(
        elements=["Si", "O"], 
        band_gap=(0.5, 1.0)
    )
```

### Limiting Returned Fields

To speed up retrieval, request only the fields you need using the `fields` argument.

```python
with MPRester() as mpr:
    docs = mpr.materials.summary.search(
        elements=["Si", "O"], 
        band_gap=(0.5, 1.0), 
        fields=["material_id", "band_gap", "volume"]
    )

example_doc = docs[0]
print(example_doc.material_id, example_doc.band_gap, example_doc.volume)
```

## 3. Advanced & Other Data

### Determining Functional (PBE vs r2SCAN)

Use the `origins` field to trace the calculation task and its run type.

```python
from mp_api.client import MPRester

mp_id_to_task_id = {}
with MPRester() as mpr:
    # 1. Get summary with origins
    summary_docs = mpr.materials.summary.search(
        material_ids=["mp-149", "mp-13"], 
        fields=["material_id", "structure", "origins"]
    )
    
    for doc in summary_docs:
        for prop in doc.origins:
            if prop.name == "structure":
                mp_id_to_task_id[doc.material_id] = {
                    "task_id": prop.task_id, 
                    "structure": doc.structure
                }
                break
    
    # 2. Check thermo docs for run_type
    thermo_docs = mpr.materials.thermo.search(
        material_ids=["mp-149", "mp-13"], 
        fields=["material_id", "entries"]
    )
    
    for doc in thermo_docs:
        mpid = doc.material_id
        for entry in doc.entries.values():
            if entry.data["task_id"] == mp_id_to_task_id[mpid]["task_id"]:
                 print(f"{mpid} run type: {entry.parameters['run_type']}")
```

### Convenience Functions

MPRester also provides convenience methods for common queries.

```python
# Get initial structures
with MPRester() as mpr:
    docs = mpr.materials.search(material_ids=["mp-149"], fields=["initial_structures"])
    initial_struct = docs[0].initial_structures[0]
```
