import streamlit as st
import pandas as pd
import os
import sys

# 确保core可被导入
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# 统一导入core模块
from core import MaterialProcessor

st.set_page_config(page_title="Data Processing Agent", layout="wide")

import ui.style_manager as style_manager
style_manager.apply_theme()

style_manager.ui_header("🛠️ HEA Data Preprocessing Agent")

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
    
    # 数据处理配置选项
    st.divider()
    st.subheader("⚙️ 数据处理配置")
    
    col1, col2 = st.columns(2)
    
    with col1:
        duplicate_col_handling = st.radio(
            "重复列处理策略",
            options=["自动合并", "保留新值", "保留原值", "保留全部（添加后缀）"],
            index=1,  # 默认"保留新值"
            help="当原始数据和解析结果存在同名列时的处理方式"
        )
    
    with col2:
        st.markdown("""\n**策略说明：**
        - **自动合并**: 智能合并同名列的数据
        - **保留新值**: 删除原始列，使用解析后的新值
        - **保留原值**: 保留原始数据，忽略解析的新值
        - **保留全部**: 为新列添加后缀 `_new`
        """)
    
    st.divider()
    
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
            
            # ========== 智能列名识别 ==========
            cols = df.columns.tolist()
            
            # 识别成分列
            comp_col = next((c for c in cols if 'composition' in c.lower() or 'formula' in c.lower()), None)
            
            # 识别专有列（优先使用这些列）
            def find_column(variants):
                """查找匹配的列名（不区分大小写）"""
                for col in cols:
                    col_lower = col.lower().strip()
                    for variant in variants:
                        if variant.lower() in col_lower or col_lower in variant.lower():
                            return col
                return None
            
            # 粘结相成分列
            binder_comp_col = find_column(['binder_composition', 'binder_comp', 'binder composition', 'binder', 'Binder_Atomic_Formula'])
            
            # 粘结相质量分数列
            binder_wt_col = find_column(['binder_wt_pct', 'binder wt%', 'binder, wt-%', 'binder weight'])
            
            # 硬质相类型列
            ceramic_type_col = find_column(['ceramic_type', 'ceramic type', 'hard phase', 'ceramic'])
            
            # 硬质相质量分数列
            ceramic_wt_col = find_column(['ceramic_wt_pct', 'ceramic wt%', 'ceramic, wt-%', 'ceramic weight'])
            
            # 显示识别到的列
            st.info(f"""📋 **识别到的列**:
            - 成分字符串: `{comp_col}`
            - 粘结相成分: `{binder_comp_col}`
            - 粘结相质量%: `{binder_wt_col}`
            - 硬质相类型: `{ceramic_type_col}`
            - 硬质相质量%: `{ceramic_wt_col}`
            """)
            
            if comp_col or ceramic_type_col:
                # 导入HEADataProcessor（可能用于解析）
                from core import HEADataProcessor
                processor_hea = HEADataProcessor()
                
                # 辅助函数：安全转换为浮点数
                def safe_float(val, default=None):
                    """安全转换为浮点数"""
                    if pd.isna(val):
                        return default
                    try:
                        s = str(val).strip()
                        if not s or s == '-' or s.lower() == 'nan':
                            return default
                        return float(s)
                    except:
                        return default
                
                # 辅助函数：解析粘结相成分字符串为字典
                def parse_binder_comp_string(comp_str):
                    """解析粘结相成分字符串为原子分数字典"""
                    if pd.isna(comp_str) or not comp_str:
                        return None
                    
                    try:
                        # 尝试使用CompositionParser
                        from core.data_standardizer import CompositionParser
                        parser = CompositionParser()
                        result = parser.parse(str(comp_str), extract_binder_only=False)
                        return result
                    except:
                        # 如果解析失败，尝试使用pymatgen直接解析
                        try:
                            from pymatgen.core import Composition
                            comp = Composition(str(comp_str))
                            total = sum(comp.get_el_amt_dict().values())
                            if total > 0:
                                return {str(el): amt/total for el, amt in comp.get_el_amt_dict().items()}
                        except:
                            pass
                    return None
                
                # ========== 新的解析逻辑：优先使用原始列 ==========
                def parse_cermet_row(row):
                    """
                    优先从原始数据列读取，仅在必要时解析成分字符串
                    
                    优先级：
                    1. 直接从专有列读取（Ceramic_Type, Binder_Composition等）
                    2. 解析成分字符串（使用HEADataProcessor）
                    3. 如果都失败，返回None（不使用默认值）
                    """
                    # ========== 优先级1：直接读取原始列 ==========
                    ceramic_from_col = row.get(ceramic_type_col) if ceramic_type_col else None
                    ceramic_wt_from_col = safe_float(row.get(ceramic_wt_col)) if ceramic_wt_col else None
                    binder_comp_from_col = row.get(binder_comp_col) if binder_comp_col else None
                    binder_wt_from_col = safe_float(row.get(binder_wt_col)) if binder_wt_col else None
                    
                    # 检查是否有足够的原始列数据
                    has_ceramic_data = ceramic_from_col and pd.notna(ceramic_from_col) and str(ceramic_from_col).strip()
                    has_binder_comp = binder_comp_from_col and pd.notna(binder_comp_from_col) and str(binder_comp_from_col).strip()
                    
                    if has_ceramic_data and has_binder_comp:
                        # 所有关键列都存在，直接使用（最可靠）
                        ceramic_type_str = str(ceramic_from_col).strip()
                        
                        # 解析粘结相成分字符串
                        binder_dict = parse_binder_comp_string(binder_comp_from_col)
                        if not binder_dict:
                            # 如果解析失败，尝试回退到HEADataProcessor
                            pass  # 继续到优先级2
                        else:
                            # 成功从原始列读取
                            return {
                                'Ceramic_Type': ceramic_type_str,
                                'Ceramic_Wt_Pct': ceramic_wt_from_col if ceramic_wt_from_col is not None else 90.0,
                                'Binder_Composition': binder_dict,
                                'Binder_Wt_Pct': binder_wt_from_col if binder_wt_from_col is not None else 10.0
                            }
                    
                    # ========== 优先级2：解析成分字符串 ==========
                    if comp_col and row.get(comp_col):
                        # 获取粘结相体积分数（如果有）
                        binder_vol_pct = None
                        for c in df.columns:
                            if 'binder' in c.lower() and 'vol' in c.lower():
                                try:
                                    val = row[c]
                                    if pd.notna(val) and str(val).strip() != '-':
                                        binder_vol_pct = float(val)
                                        break
                                except:
                                    pass
                        
                        # 使用HEADataProcessor解析
                        result = processor_hea.parse_composition_advanced(
                            row[comp_col],
                            binder_vol_pct=binder_vol_pct
                        )
                        
                        if result and result.get('binder_wt_pct') is not None:
                            # 提取硬质相类型
                            ceramic_elements = result.get('ceramic_elements', {})
                            
                            if ceramic_elements and len(ceramic_elements) > 0:
                                # 过滤掉空键
                                valid_ceramics = {k: v for k, v in ceramic_elements.items() if k and k.strip()}
                                if valid_ceramics:
                                    ceramic_type = ', '.join(valid_ceramics.keys())
                                else:
                                    ceramic_type = None  # 不使用默认值
                            else:
                                ceramic_type = None  # 不使用默认值
                            
                            # 如果ceramic_type仍然无效，尝试从原始列读取
                            if not ceramic_type and has_ceramic_data:
                                ceramic_type = str(ceramic_from_col).strip()
                            
                            # 使用原子分数作为Binder_Composition
                            binder_atomic_comp = result.get('binder_atomic_comp', {})
                            if not binder_atomic_comp and result.get('binder_elements'):
                                total = sum(result['binder_elements'].values())
                                if total > 0:
                                    binder_atomic_comp = {k: v/total for k, v in result['binder_elements'].items()}
                            
                            if ceramic_type and binder_atomic_comp:
                                return {
                                    'Ceramic_Type': ceramic_type,
                                    'Ceramic_Wt_Pct': max(0, min(100, 100 - result.get('binder_wt_pct', 10.0))),
                                    'Binder_Composition': binder_atomic_comp,
                                    'Binder_Wt_Pct': max(0, min(100, result.get('binder_wt_pct', 10.0)))
                                }
                    
                    # ========== 优先级3：都失败，返回None ==========
                    # 不使用默认值，让后续处理决定如何处理无效行
                    return None

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
                    
                    # 处理重复列（根据用户选择）
                    duplicate_cols = set(df.columns) & set(parsed_df.columns)
                    
                    if duplicate_cols:
                        st.info(f"📋 发现 {len(duplicate_cols)} 个重复列: {list(duplicate_cols)}")
                        st.info(f"📌 使用策略: **{duplicate_col_handling}**")
                        
                        if duplicate_col_handling == "自动合并":
                            # 使用data_standardizer的合并功能
                            from core.data_standardizer import data_standardizer
                            # 先合并，然后添加parsed_df中的新列
                            for col in duplicate_cols:
                                # 合并逻辑：优先使用非空值
                                df[col] = df[col].fillna(parsed_df[col])
                                # 从parsed_df中移除已处理的列
                                parsed_df = parsed_df.drop(columns=[col])
                            st.success(f"✓ 已合并 {len(duplicate_cols)} 个重复列")
                        
                        elif duplicate_col_handling == "保留新值":
                            # 删除原始列，保留解析后的新值
                            df = df.drop(columns=list(duplicate_cols))
                            st.success(f"✓ 已删除原始列，将使用解析后的新值")
                        
                        elif duplicate_col_handling == "保留原值":
                            # 保留原始数据，从parsed_df中移除重复列
                            parsed_df = parsed_df.drop(columns=list(duplicate_cols))
                            st.success(f"✓ 已保留原始列，忽略解析的新值")
                        
                        else:  # "保留全部（添加后缀）"
                            # 为parsed_df中的重复列添加"_new"后缀
                            rename_dict = {col: f"{col}_new" for col in duplicate_cols}
                            parsed_df = parsed_df.rename(columns=rename_dict)
                            st.success(f"✓ 已为新列添加 '_new' 后缀")
                    
                    # 合并数据
                    df = pd.concat([df, parsed_df], axis=1)
                    
                    # 最终安全检查：如果仍有重复列名，保留第一个
                    if df.columns.duplicated().any():
                        duplicated_list = df.columns[df.columns.duplicated()].tolist()
                        st.warning(f"⚠️ 仍发现重复列名: {duplicated_list}，保留第一个出现的列")
                        df = df.loc[:, ~df.columns.duplicated(keep='first')]
                
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
                        # 获取硬质相类型（注意：合并后从df中读取）
                        ceramic_type = df.loc[idx, 'Ceramic_Type']
                        
                        # 获取粘结相成分（dict 对象）
                        binder_comp_dict = df.loc[idx, 'Binder_Composition']
                        
                        # 创建硬质相 Composition
                        try:
                            # 验证ceramic_type是否有效（非空且包含字母）
                            if pd.notna(ceramic_type) and isinstance(ceramic_type, str):
                                ceramic_type_clean = str(ceramic_type).strip()
                                
                                # 处理多硬质相情况（如"WC, NbC"）
                                if ',' in ceramic_type_clean:
                                    # 取第一个硬质相（主要硬质相）
                                    main_ceramic = ceramic_type_clean.split(',')[0].strip()
                                    ceramic_type_clean = main_ceramic
                                
                                # 确保至少包含一个字母（有效的化学式）
                                if ceramic_type_clean and any(c.isalpha() for c in ceramic_type_clean):
                                    ceramic_compositions.append(Composition(ceramic_type_clean))
                                else:
                                    # 无效的ceramic_type，标记为None
                                    st.warning(f"Row {idx}: Invalid ceramic type '{ceramic_type}', 将跳过此行")
                                    ceramic_compositions.append(None)
                            else:
                                # ceramic_type为空或非字符串，标记为None
                                st.warning(f"Row {idx}: Ceramic_Type 缺失或无效，将跳过此行")
                                ceramic_compositions.append(None)
                        except Exception as e:
                            st.warning(f"Row {idx}: Failed to create ceramic composition - {e}")
                            ceramic_compositions.append(None)
                        
                        # 创建粘结相 Composition
                        try:
                            # 详细的数据有效性检查
                            if binder_comp_dict is None:
                                binder_compositions.append(None)
                            elif not isinstance(binder_comp_dict, dict):
                                binder_compositions.append(None)
                            elif not binder_comp_dict:  # 空字典
                                binder_compositions.append(None)
                            else:
                                # 检查字典值是否有效
                                valid_dict = {}
                                for elem, frac in binder_comp_dict.items():
                                    if elem and str(elem).strip() and pd.notna(frac):
                                        try:
                                            valid_dict[str(elem).strip()] = float(frac)
                                        except:
                                            pass
                                
                                if valid_dict:
                                    binder_compositions.append(Composition(valid_dict))
                                else:
                                    binder_compositions.append(None)
                        except Exception as e:
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
                        
                        # Add ceramic info（从df中读取，因为parsed_df可能已被修改）
                        valid_df['Ceramic_Type'] = df.loc[valid_df.index, 'Ceramic_Type']
                        valid_df['Ceramic_Wt_Pct'] = df.loc[valid_df.index, 'Ceramic_Wt_Pct']
                        
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
