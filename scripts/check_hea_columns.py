import pandas as pd
import os

file_path = r'd:\ML\HEAC 0.2\training data\HEA.xlsx'

try:
    df = pd.read_excel(file_path)
    print("Successfully read Excel file.")
    print("Columns:", df.columns.tolist())
    print("First 3 rows:")
    print(df.head(3))
except Exception as e:
    print(f"Error: {e}")
