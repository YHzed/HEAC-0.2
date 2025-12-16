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

# Suppress Streamlit threading warnings caused by Matminer/joblib
import logging
logging.getLogger("streamlit.runtime.scriptrunner_utils.script_run_context").setLevel(logging.ERROR)


training_data_dir = r'd:\ML\HEAC 0.2\training data'
output_path = r'd:\ML\HEAC 0.2\datasets\hea_processed.csv'

# 文件输入选项
st.subheader("📁 选择或上传数据文件")
input_method = st.radio(
    "选择输入方式:",
    ["从training data目录选择", "上传新文件"],
    horizontal=True
)

file_path = None

if input_method == "从training data目录选择":
    # 获取training data目录中的所有文件
    if os.path.exists(training_data_dir):
        available_files = [f for f in os.listdir(training_data_dir) 
                          if os.path.isfile(os.path.join(training_data_dir, f)) 
                          and (f.endswith('.xlsx') or f.endswith('.csv') or f.endswith('.xls'))]
        
        if available_files:
            selected_file = st.selectbox(
                "选择文件:",
                options=available_files,
                index=0 if 'HEA.xlsx' in available_files else 0
            )
            file_path = os.path.join(training_data_dir, selected_file)
            st.info(f"已选择文件: `{file_path}`")
        else:
            st.warning(f"在 `{training_data_dir}` 目录中没有找到Excel或CSV文件")
    else:
        st.error(f"Training data目录不存在: `{training_data_dir}`")

elif input_method == "上传新文件":
    uploaded_file = st.file_uploader(
        "上传Excel或CSV文件",
        type=['xlsx', 'xls', 'csv'],
        help="文件将被保存到training data目录"
    )
    
    if uploaded_file is not None:
        # 确保目录存在
        os.makedirs(training_data_dir, exist_ok=True)
        
        # 保存文件到training data目录
        file_path = os.path.join(training_data_dir, uploaded_file.name)
        
        with open(file_path, 'wb') as f:
            f.write(uploaded_file.getbuffer())
        
        st.success(f"✅ 文件已保存到: `{file_path}`")

st.divider()

if file_path and os.path.exists(file_path):
    st.success(f"✓ 当前文件: `{os.path.basename(file_path)}`")
    
    if st.button("🚀 Process HEA Data"):
        try:
            # Read file based on extension
            if file_path.endswith('.csv'):
                df = pd.read_csv(file_path)
            else:  # .xlsx or .xls
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
                        
                    # ⚠️ 重要：体积分数计算
                    # 不能简单地将重量分数当作体积分数！
                    # Ceramic_Vol_Frac 应该从 Binder vol-% 列计算
                    # 这里先返回重量分数，后续会从原始列中读取正确的体积分数
                    
                    return {
                        'Ceramic_Type': current_hard,
                        'Ceramic_Wt_Pct': hard_amount,
                        'Binder_Composition': normalized_binder,
                        'Binder_Wt_Pct': total_binder_wt  # 添加粘结相重量分数
                    }

                # Apply Parsing
                with st.spinner("Parsing Composition Strings..."):
                    parsed_df = df.apply(parse_cermet_row, axis=1, result_type='expand')
                    
                    # ========== 修复体积分数计算 ==========
                    # 从原始数据的 "Binder, vol-%" 列读取正确的粘结相体积分数
                    binder_vol_col = None
                    for c in df.columns:
                        if 'binder' in c.lower() and 'vol' in c.lower():
                            binder_vol_col = c
                            break
                    
                    if binder_vol_col:
                        # 安全转换函数：处理字符串、NaN等非数值
                        def safe_float(val, default):
                            try:
                                s = str(val).strip()
                                if not s or s == '-' or s.lower() == 'nan':
                                    return default
                                return float(val)
                            except:
                                return default
                        
                        # 使用原始数据的体积分数，并安全转换为浮点数
                        parsed_df['Binder_Vol_Pct'] = df[binder_vol_col].apply(lambda x: safe_float(x, 0.0))
                        parsed_df['Ceramic_Vol_Frac'] = (100.0 - parsed_df['Binder_Vol_Pct']) / 100.0
                        st.success(f"✓ 使用列 '{binder_vol_col}' 计算体积分数（物理正确）")
                    else:
                        # 后备方案：用重量分数近似（不准确但不会报错）
                        st.warning("⚠️ 未找到 'Binder vol-%' 列，使用重量分数近似体积分数（可能不准确）")
                        parsed_df['Ceramic_Vol_Frac'] = parsed_df['Ceramic_Wt_Pct'] / 100.0
                        parsed_df['Binder_Vol_Pct'] = parsed_df['Binder_Wt_Pct']
                    
                    df = pd.concat([df, parsed_df], axis=1)
                
                st.write("Parsed Composition Preview:", df[['Ceramic_Type', 'Ceramic_Wt_Pct', 'Binder_Composition']].head())
                
                # --- Feature Generation using Matminer ---
                st.divider()
                st.subheader("🔬 Generating Features with Matminer")
                
                st.info("将分别对**硬质相**和**粘结相**进行特征化")
                
                with st.spinner("Preparing compositions for featurization..."):
                    from pymatgen.core import Composition
                    
                    # 创建两组 Composition 对象：硬质相和粘结相
                    ceramic_compositions = []
                    binder_compositions = []
                    
                    for idx in df.index:
                        # 获取硬质相类型（从 parsed_df 中的 dict 对象，不是字符串）
                        ceramic_type = parsed_df.loc[idx, 'Ceramic_Type']
                        
                        # 获取粘结相成分（dict 对象）
                        binder_comp_dict = parsed_df.loc[idx, 'Binder_Composition']
                        
                        # 创建硬质相 Composition
                        try:
                            if pd.notna(ceramic_type) and ceramic_type:
                                ceramic_compositions.append(Composition(ceramic_type))
                            else:
                                ceramic_compositions.append(None)
                        except Exception as e:
                            st.warning(f"Row {idx}: Failed to create ceramic composition - {e}")
                            ceramic_compositions.append(None)
                        
                        # 创建粘结相 Composition
                        try:
                            if isinstance(binder_comp_dict, dict) and binder_comp_dict:
                                binder_compositions.append(Composition(binder_comp_dict))
                            else:
                                binder_compositions.append(None)
                        except Exception as e:
                            st.warning(f"Row {idx}: Failed to create binder composition - {e}")
                            binder_compositions.append(None)
                    
                    df['ceramic_comp'] = ceramic_compositions
                    df['binder_comp'] = binder_compositions
                    
                    # 统计有效成分
                    valid_ceramic = sum(1 for c in ceramic_compositions if c is not None)
                    valid_binder = sum(1 for c in binder_compositions if c is not None)
                    st.success(f"✓ 创建了 {valid_ceramic} 个有效硬质相成分, {valid_binder} 个有效粘结相成分")
                
                # 过滤有效行
                valid_df = df[(df['ceramic_comp'].notnull()) & (df['binder_comp'].notnull())].copy()
                
                if len(valid_df) == 0:
                    st.error("No valid compositions to featurize!")
                else:
                    st.markdown("### 🚀 开始特征生成")
                    
                    # Create progress display
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    try:
                        from matminer.featurizers.composition import (
                            ElementProperty,
                            Stoichiometry,
                            ValenceOrbital,
                            ElementFraction,
                            TMetalFraction
                        )
                        
                        # Define featurizers
                        featurizers = [
                            ("Magpie", ElementProperty.from_preset(preset_name="magpie")),
                            ("Stoichiometry", Stoichiometry()),
                            ("Valence Orbital", ValenceOrbital()),
                            ("Element Fraction", ElementFraction()),
                            ("Transition Metal Fraction", TMetalFraction())
                        ]
                        
                        total_steps = len(featurizers) * 2  # 硬质相 + 粘结相
                        current_step = 0
                        
                        # ========== 1. 硬质相特征化 ==========
                        st.markdown("#### 🔹 硬质相（Ceramic）特征化")
                        for name, feat in featurizers:
                            progress = current_step / total_steps
                            progress_bar.progress(progress)
                            status_text.text(f"⏳ 正在应用 Ceramic {name} featurizer... ({current_step + 1}/{total_steps})")
                            
                            try:
                                valid_df = feat.featurize_dataframe(
                                    valid_df, 
                                    'ceramic_comp', 
                                    ignore_errors=True
                                )
                                # 为硬质相特征添加前缀
                                new_cols = feat.feature_labels()
                                rename_dict = {col: f"Ceramic_{col}" for col in new_cols if col in valid_df.columns}
                                valid_df = valid_df.rename(columns=rename_dict)
                                
                                st.success(f"✓ Ceramic {name}: {len(new_cols)} features")
                            except Exception as e:
                                st.warning(f"✗ Ceramic {name} failed: {e}")
                            
                            current_step += 1
                        
                        # ========== 2. 粘结相特征化 ==========
                        st.markdown("#### 🔸 粘结相（Binder）特征化")
                        for name, feat in featurizers:
                            progress = current_step / total_steps
                            progress_bar.progress(progress)
                            status_text.text(f"⏳ 正在应用 Binder {name} featurizer... ({current_step + 1}/{total_steps})")
                            
                            try:
                                valid_df = feat.featurize_dataframe(
                                    valid_df, 
                                    'binder_comp', 
                                    ignore_errors=True
                                )
                                # 为粘结相特征添加前缀
                                new_cols = feat.feature_labels()
                                rename_dict = {col: f"Binder_{col}" for col in new_cols if col in valid_df.columns}
                                valid_df = valid_df.rename(columns=rename_dict)
                                
                                st.success(f"✓ Binder {name}: {len(new_cols)} features")
                            except Exception as e:
                                st.warning(f"✗ Binder {name} failed: {e}")
                            
                            current_step += 1
                        
                        # Complete progress
                        progress_bar.progress(1.0)
                        
                        ceramic_feat_count = len([c for c in valid_df.columns if c.startswith('Ceramic_')])
                        binder_feat_count = len([c for c in valid_df.columns if c.startswith('Binder_')])
                        total_feat_count = ceramic_feat_count + binder_feat_count
                        
                        status_text.text(f"✅ 完成！硬质相: {ceramic_feat_count} 特征, 粘结相: {binder_feat_count} 特征, 总计: {total_feat_count} 特征")
                        st.success(f"Successfully generated {total_feat_count} matminer features!")
                            
                    except ImportError as e:
                        st.error(f"Matminer not installed or missing dependencies: {e}")
                    except Exception as e:
                        st.error(f"Feature generation error: {e}")
                        import traceback
                        st.code(traceback.format_exc())
                    
                    # Add Process Parameters
                    with st.spinner("Adding process parameters..."):
                        # Identify Process Columns
                        col_map = {}
                        for c in df.columns:
                            c_low = c.lower()
                            if 'd,' in c_low or 'grain' in c_low: 
                                col_map['grain'] = c
                            if 't,' in c_low or ('sinter' in c_low and 'temp' in c_low): 
                                col_map['temp'] = c
                            if 'time' in c_low: 
                                col_map['time'] = c
                        
                        st.info(f"Mapped process columns: {col_map}")
                        
                        # Helper for safe conversion
                        def safe_float(val, default):
                            try:
                                s = str(val).strip()
                                if not s or s == '-' or s.lower() == 'nan':
                                    return default
                                return float(val)
                            except:
                                return default
                        
                        # Add process parameters as features
                        if 'temp' in col_map:
                            valid_df['Sinter_Temp_C'] = valid_df[col_map['temp']].apply(
                                lambda x: safe_float(x, 1400.0)
                            )
                        else:
                            valid_df['Sinter_Temp_C'] = 1400.0
                            
                        if 'time' in col_map:
                            valid_df['Sinter_Time_Min'] = valid_df[col_map['time']].apply(
                                lambda x: safe_float(x, 60.0)
                            )
                        else:
                            valid_df['Sinter_Time_Min'] = 60.0
                            
                        if 'grain' in col_map:
                            valid_df['Grain_Size_um'] = valid_df[col_map['grain']].apply(
                                lambda x: safe_float(x, 1.0)
                            )
                        else:
                            valid_df['Grain_Size_um'] = 1.0
                        
                        # Add ceramic info
                        valid_df['Ceramic_Type'] = parsed_df.loc[valid_df.index, 'Ceramic_Type']
                        valid_df['Ceramic_Wt_Pct'] = parsed_df.loc[valid_df.index, 'Ceramic_Wt_Pct']
                        
                        st.success("Added process parameters and ceramic info")
                    
                    # Cleanup - 移除临时的Composition对象列
                    cols_to_drop = ['ceramic_comp', 'binder_comp']
                    valid_df = valid_df.drop(columns=[c for c in cols_to_drop if c in valid_df.columns])
                    
                    # Remove duplicate columns
                    valid_df = valid_df.loc[:, ~valid_df.columns.duplicated()]
                    
                    
                    st.success("✅ Feature generation complete!")
                    st.write(f"**Total features generated**: {len(valid_df.columns)} columns")
                    
                    
                    # ========== 数据清洗步骤 ==========
                    st.divider()
                    st.subheader("🧹 Data Cleaning & Preprocessing")
                    
                    # 0. 量纲统一（Scale Normalization）
                    st.markdown("#### 📏 量纲统一")
                    with st.spinner("Normalizing scales..."):
                        # 将 Binder vol-% (0~100) 转换为 Binder_Vol_Frac (0~1)
                        # 以保持与 Ceramic_Vol_Frac 相同的量纲
                        if 'Binder_Vol_Pct' in valid_df.columns:
                            valid_df['Binder_Vol_Frac'] = valid_df['Binder_Vol_Pct'] / 100.0
                            st.success(f"✓ 创建 `Binder_Vol_Frac` 列（0~1量纲，与Ceramic_Vol_Frac一致）")
                            
                            # 标记原始百分比列（供用户参考）
                            st.info("💡 提示：`Binder_Vol_Pct` (0~100) 和 `Binder_Vol_Frac` (0~1) 包含相同信息。"
                                   "训练模型时，建议只保留一个（推荐使用0~1量纲的`_Frac`列）")
                        
                        # 同样处理 Ceramic_Wt_Pct
                        if 'Ceramic_Wt_Pct' in valid_df.columns:
                            valid_df['Ceramic_Wt_Frac'] = valid_df['Ceramic_Wt_Pct'] / 100.0
                            st.success(f"✓ 创建 `Ceramic_Wt_Frac` 列（0~1量纲）")
                        
                        st.write("**量纲统一后的关键列：**")
                        scale_cols = ['Binder_Vol_Frac', 'Ceramic_Vol_Frac', 'Ceramic_Wt_Frac']
                        existing_scale_cols = [c for c in scale_cols if c in valid_df.columns]
                        if existing_scale_cols:
                            st.dataframe(valid_df[existing_scale_cols].head())
                    
                    # 1. 移除常量特征（方差为0）
                    st.markdown("#### 🗑️ 移除常量特征")
                    with st.spinner("Removing constant features..."):
                        numeric_cols = valid_df.select_dtypes(include=['number']).columns
                        constant_cols = []
                        
                        for col in numeric_cols:
                            if valid_df[col].nunique() == 1:
                                constant_cols.append(col)
                        
                        if constant_cols:
                            st.warning(f"⚠️ 发现 {len(constant_cols)} 个常量特征（方差=0），已移除")
                            with st.expander("查看被移除的常量特征"):
                                st.write(constant_cols)
                            valid_df = valid_df.drop(columns=constant_cols)
                        else:
                            st.success("✓ 未发现常量特征")
                    
                    # 2. 缺失值报告
                    with st.expander("📊 缺失值统计"):
                        missing_counts = valid_df.isnull().sum()
                        missing_features = missing_counts[missing_counts > 0].sort_values(ascending=False)
                        
                        if len(missing_features) > 0:
                            st.write(f"**发现 {len(missing_features)} 个列存在缺失值:**")
                            st.dataframe(missing_features.to_frame(name='Missing Count'))
                            st.info("💡 建议：训练模型前，针对每个目标变量使用 `df.dropna(subset=['Target'])` 移除对应的缺失行")
                        else:
                            st.success("✓ 无缺失值")
                    
                    # 3. 数据质量报告
                    with st.expander("📋 数据质量报告"):
                        st.write(f"**最终数据维度**: {valid_df.shape[0]} 行 × {valid_df.shape[1]} 列")
                        
                        # 统计硬质相和粘结相特征数量
                        ceramic_feats = [c for c in valid_df.columns if c.startswith('Ceramic_')]
                        binder_feats = [c for c in valid_df.columns if c.startswith('Binder_')]
                        
                        st.write(f"- 硬质相特征: {len(ceramic_feats)}")
                        st.write(f"- 粘结相特征: {len(binder_feats)}")
                        st.write(f"- 其他特征: {valid_df.shape[1] - len(ceramic_feats) - len(binder_feats)}")
                        
                        # 验证体积分数和
                        if 'Binder_Vol_Pct' in valid_df.columns and 'Ceramic_Vol_Frac' in valid_df.columns:
                            vol_sum = valid_df['Binder_Vol_Pct'] + valid_df['Ceramic_Vol_Frac'] * 100
                            max_diff = abs(vol_sum - 100).max()
                            
                            if max_diff < 0.1:
                                st.success(f"✓ 体积分数验证通过：Binder Vol% + Ceramic Vol% ≈ 100% （最大误差: {max_diff:.2f}%）")
                            else:
                                st.error(f"✗ 体积分数验证失败：最大误差 {max_diff:.2f}%")
                    
                    st.write("Preview of cleaned data:", valid_df.head())
                    
                    # Save to CSV
                    valid_df.to_csv(output_path, index=False)
                    st.success(f"💾 Saved processed data to `{output_path}`")
                    
                    # Show feature summary
                    with st.expander("📊 Feature Summary"):
                        feature_cols = [c for c in valid_df.columns if c not in df.columns]
                        st.write(f"**Matminer-generated features ({len(feature_cols)}):**")
                        st.write(", ".join(feature_cols[:50]))  # Show first 50
                        if len(feature_cols) > 50:
                            st.write(f"... and {len(feature_cols) - 50} more")
                
            else:
                st.error("Could not find 'Composition' column.")

                    
        except Exception as e:
            st.error(f"An error occurred: {e}")
            import traceback
            st.code(traceback.format_exc())
elif file_path:
    st.error(f"文件不存在: {file_path}")
else:
    st.info("请选择一个文件或上传新文件以开始处理")
