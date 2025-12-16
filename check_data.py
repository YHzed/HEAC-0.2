import pandas as pd

# Read the original Excel file
df = pd.read_excel(r'd:\ML\HEAC 0.2\training data\HEA.xlsx')

print("Original data shape:", df.shape)
print("\nColumn names:")
print(df.columns.tolist())

# Find composition column
comp_col = None
for c in df.columns:
    if 'comp' in c.lower():
        comp_col = c
        break

print(f"\nComposition column: {comp_col}")

if comp_col:
    print(f"\nFirst 20 {comp_col} values:")
    print(df[comp_col].head(20))
    print(f"\nUnique values sample:")
    print(df[comp_col].value_counts().head(10))
