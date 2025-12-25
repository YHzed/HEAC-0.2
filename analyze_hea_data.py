"""分析 HEA.xlsx 数据集结构 - 避免编码问题"""
import pandas as pd
import os
import sys

# 设置输出编码
sys.stdout.reconfigure(encoding='utf-8')

# 检查文件
file_path = 'training data/HEA.xlsx'
print(f"File exists: {os.path.exists(file_path)}")

# 读取数据
try:
    df = pd.read_excel(file_path)
    print(f"\nDataset shape: {df.shape}")
    print(f"Total columns: {len(df.columns)}")
    
    print("\n" + "="*80)
    print("Column Names:")
    print("="*80)
    for i, col in enumerate(df.columns):
        print(f"{i+1:2d}. {col}")
    
    print("\n" + "="*80)
    print("Data Types:")
    print("="*80)
    for col, dtype in df.dtypes.items():
        print(f"{col}: {dtype}")
    
    print("\n" + "="*80)
    print("First 3 Rows:")
    print("="*80)
    # 使用 to_csv 导出到临时文件避免编码问题
    preview_file = 'temp_preview.csv'
    df.head(3).to_csv(preview_file, index=False, encoding='utf-8')
    print(f"Preview saved to: {preview_file}")
    
    print("\n" + "="*80)
    print("Missing Values:")
    print("="*80)
    missing = df.isnull().sum()
    total = len(df)
    for col in df.columns:
        if missing[col] > 0:
            pct = (missing[col] / total * 100)
            print(f"{col}: {missing[col]} ({pct:.2f}%)")
    
    print("\n" + "="*80)
    print("Numeric Columns Summary:")
    print("="*80)
    numeric_cols = df.select_dtypes(include=['number']).columns
    print(f"Total numeric columns: {len(numeric_cols)}")
    for col in numeric_cols[:10]:  # 只显示前10个
        print(f"  - {col}")
    if len(numeric_cols) > 10:
        print(f"  ... and {len(numeric_cols) - 10} more")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
