import streamlit as st
import pandas as pd
import os
import sys

# 确保core可被导入
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# 统一导入core模块
from core import MaterialProcessor

st.set_page_config(page_title="Data Processing Agent", layout="wide")

st.title("🛠️ HEA Data Preprocessing Agent")

file_path = r'd:\ML\HEAC 0.2\training data\HEA.xlsx'
output_path = r'd:\ML\HEAC 0.2\datasets\hea_processed.csv'

if os.path.exists(file_path):
    st.success(f"Found file: `{file_path}`")
    
    if st.button("🚀 Process HEA Data"):
        try:
            # Read
            df = pd.read_excel(file_path)
            st.write("Original Data (First 5 rows):", df.head())
            
            # Initialize Processor
            processor = MaterialProcessor()
            
            # Identify Composition Column
            cols = df.columns.tolist()
            comp_col = next((c for c in cols if 'composition' in c.lower() or 'formula' in c.lower()), None)
            
            if comp_col:
                st.info(f"Processing column: **{comp_col}**")
                
                # Custom Parser for Cermet Strings (e.g. "WC-10Co", "b WC 25 Co")
                def parse_cermet_row(row):
                    raw = str(row[comp_col]).strip()
                    
                    # Common Hard Phases
                    hard_phases = ['WC', 'TiC', 'Ti(C,N)', 'TiCN', 'TaC', 'NbC', 'Cr3C2', 'VC', 'Mo2C']
                    # Common Binder Elements
                    binders = ['Co', 'Ni', 'Fe', 'Cr', 'Mo', 'Al', 'V', 'Ti', 'Mn']
                    
                    current_hard = 'WC' # Default
                    hard_amount = 0.0
                    binder_comp = {}
                    
                    # Pre-processing cleanup
                    # Remove 'b ' prefix if present (from user image)
                    if raw.lower().startswith('b '):
                        raw = raw[2:].strip()
                        
                    # Split by separators (-, space, +)
                    import re
                    tokens = re.split(r'[+\-\s]+', raw)
                    
                    total_binder_wt = 0.0
                    
                    # Logic: scan tokens
                    for i, token in enumerate(tokens):
                        if not token: continue
                        
                        # Check ceramic
                        is_ceramic = False
                        for hp in hard_phases:
                            if hp.lower() == token.lower() or hp.lower() in token.lower(): # Exact match preferred or containment
                                current_hard = hp
                                is_ceramic = True
                                # Look ahead/behind for number? 
                                # In "WC 25 Co", "25" is next.
                                break
                        if is_ceramic: continue
                        
                        # Check Number
                        # If token is number, look ahead for Binder Element
                        try:
                            val = float(token)
                            # Valid number. Check next token for Element?
                            if i + 1 < len(tokens):
                                next_tok = tokens[i+1]
                                if next_tok in binders:
                                    # "25 Co" case
                                    binder_comp[next_tok] = binder_comp.get(next_tok, 0.0) + val
                                    total_binder_wt += val
                                    continue
                        except ValueError:
                            pass

                        # Check Binder+Number combined (10Co)
                        match_pre = re.match(r'^(\d+(?:\.\d+)?)([A-Za-z]+)$', token)
                        match_post = re.match(r'^([A-Za-z]+)(\d+(?:\.\d+)?)$', token)
                        
                        if match_pre:
                            b_amt = float(match_pre.group(1))
                            b_el = match_pre.group(2)
                            if b_el in binders:
                                binder_comp[b_el] = binder_comp.get(b_el, 0.0) + b_amt
                                total_binder_wt += b_amt
                        elif match_post:
                            b_el = match_post.group(1)
                            b_amt = float(match_post.group(2))
                            if b_el in binders:
                                binder_comp[b_el] = binder_comp.get(b_el, 0.0) + b_amt
                                total_binder_wt += b_amt
                             
                    # Calculate Hard Phase Amount if missing
                    # If we have binder weights (e.g. 10+5=15), assume remainder is hard phase (85)
                    if hard_amount == 0 and total_binder_wt > 0:
                        hard_amount = 100.0 - total_binder_wt
                    
                    # Normalize Binder
                    normalized_binder = {}
                    if total_binder_wt > 0:
                        normalized_binder = {k: v/total_binder_wt for k, v in binder_comp.items()}
                    else:
                        normalized_binder = {'Co': 1.0} # Default/Err
                        
                    return {
                        'Ceramic_Type': current_hard,
                        'Ceramic_Vol_Frac': hard_amount / 100.0, # Approx Wt as Vol for input
                        'Ceramic_Wt_Pct': hard_amount,
                        'Binder_Composition': normalized_binder
                    }

                # Apply Parsing
                with st.spinner("Parsing Composition Strings..."):
                    parsed_df = df.apply(parse_cermet_row, axis=1, result_type='expand')
                    df = pd.concat([df, parsed_df], axis=1)
                
                st.write("Parsed Composition Preview:", df[['Ceramic_Type', 'Ceramic_Wt_Pct', 'Binder_Composition']].head())
                
                # --- Feature Calculation ---
                from core.system_architecture import DesignSpace, PhysicsEngine
                engine = PhysicsEngine()
                
                feature_rows = []
                
                # Identify Process Columns
                col_map = {}
                for c in df.columns:
                    c_low = c.lower()
                    if 'd,' in c_low or 'grain' in c_low: col_map['grain'] = c
                    if 't,' in c_low or ('sinter' in c_low and 'temp' in c_low): col_map['temp'] = c
                    if 'time' in c_low: col_map['time'] = c
                
                st.info(f"Mapped Columns: {col_map}")
                
                for idx in df.index:
                    try:
                        # Access Parsed Data directly from parsed_df
                        b_comp = parsed_df.loc[idx, 'Binder_Composition']
                        c_type = parsed_df.loc[idx, 'Ceramic_Type']
                        c_wt = parsed_df.loc[idx, 'Ceramic_Wt_Pct']
                        
                        if not b_comp: b_comp = {'Co': 1.0}
                        
                        # Helper for safe conversion
                        def safe_float(val, default):
                            try:
                                s = str(val).strip()
                                if not s or s == '-' or s.lower() == 'nan':
                                    return default
                                return float(val)
                            except:
                                return default

                        # Process params
                        temp = safe_float(df.loc[idx, col_map['temp']], 1400.0) if 'temp' in col_map else 1400.0
                        time = safe_float(df.loc[idx, col_map['time']], 60.0) if 'time' in col_map else 60.0
                        grain = safe_float(df.loc[idx, col_map['grain']], 1.0) if 'grain' in col_map else 1.0
                        
                        # Image has 'd, mm'. If val is small (e.g. 2.2), likely microns? 
                        # Or really mm? 2.2mm is huge. Usually 'd' refers to WC grain size in microns.
                        # I will assume microns for the physics model unless > 100.
                        if grain > 50: grain = grain # Maybe actally microns
                        
                        ds = DesignSpace(
                            hea_composition=b_comp,
                            is_mass_fraction=True,
                            ceramic_type=c_type if pd.notna(c_type) else 'WC',
                            ceramic_vol_fraction=float(c_wt)/100.0 if pd.notna(c_wt) else 0.5,
                            grain_size_um=grain,
                            sinter_temp_c=temp,
                            sinter_time_min=time
                        )
                        
                        feats = engine.compute_features(ds)
                        # Add metadata
                        feats['Parsed_Ceramic'] = c_type
                        feature_rows.append(feats)
                        
                    except Exception as ex:
                        feature_rows.append({'Error': str(ex)})
                
                feat_df = pd.DataFrame(feature_rows)
                df_final = pd.concat([df, feat_df], axis=1)
                # Remove duplicate columns
                df_final = df_final.loc[:, ~df_final.columns.duplicated()]
                
                st.success("Analysis Complete!")
                st.write("Result Preview:", df_final.head())
                df_final.to_csv(output_path, index=False)
                
            else:
                st.error("Could not find 'Composition' column.")

                    
        except Exception as e:
            st.error(f"An error occurred: {e}")
            import traceback
            st.code(traceback.format_exc())
else:
    st.error(f"File not found: {file_path}")
