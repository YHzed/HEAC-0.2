"""
数据库管理器 UI - v2.0 增强版

新增功能：
- 支持新数据库架构切换
- 显示相分离信息
- 触发特征计算
- 高级成分解析预览
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.db_manager import CermetDB
from core import CermetDatabaseV2, FeatureEngine
from core.composition_parser_enhanced import EnhancedCompositionParser

# 页面配置
st.set_page_config(
    page_title="数据库管理 v2.0 - HEAC",
    page_icon="🗄️",
    layout="wide"
)

# 初始化会话状态
if 'use_v2_db' not in st.session_state:
    st.session_state.use_v2_db = False

# 标题
st.title("🗄️ 金属陶瓷数据库管理系统 v2.0")
st.markdown("---")

# 侧边栏 - 数据库选择
with st.sidebar:
    st.header("⚙️ 数据库设置")
    
    db_version = st.radio(
        "选择数据库版本",
        options=["v1.0 (旧架构)", "v2.0 (新架构)"],
        index=1 if st.session_state.use_v2_db else 0
    )
    
    st.session_state.use_v2_db = (db_version == "v2.0 (新架构)")
    
    if st.session_state.use_v2_db:
        st.success("✅ 使用新架构 v2.0")
        st.info("""
        **v2.0 特性**:
        - 🔍 智能成分解析
        - ⚛️ 自动特征计算
        - 📊 相分离存储
        - 🚀 高效多表查询
        """)
    else:
        st.warning("使用旧架构 v1.0")
    
    st.markdown("---")
    
    # 数据库统计
    st.header("📊 数据库统计")
    
    try:
        if st.session_state.use_v2_db:
            db_v2 = CermetDatabaseV2('cermet_master_v2.db')
            stats = db_v2.get_statistics()
        else:
            db_v1 = CermetDB('cermet_materials.db')
            stats = db_v1.get_statistics()
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("总记录数", stats.get('total_experiments', stats.get('total_records', 0)))
        with col2:
            st.metric("HEA 粘结相", stats.get('hea_count', stats.get('hea_records', 0)))
        
        st.metric("传统粘结相", stats.get('traditional_count', stats.get('traditional_records', 0)))
        
    except Exception as e:
        st.error(f"无法加载统计信息: {e}")

# 主界面 - 标签页
if st.session_state.use_v2_db:
    # v2.0 新界面
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📝 智能数据录入",
        "📂 批量导入",
        "🔬 成分解析预览",
        "⚡ 补充特征计算",
        "🔍 数据查询与分析"
    ])
    
    # Tab 1: 智能数据录入
    with tab1:
        st.header("📝 智能数据录入 (v2.0)")
        
        with st.form("smart_entry_form"):
            st.subheader("成分信息")
            
            col1, col2 = st.columns(2)
            with col1:
                composition = st.text_input(
                    "成分字符串 *",
                    placeholder="WC-10CoCrFeNi 或 b WC 69 CoCrFeNiMo 0.5 Cr3C2",
                    help="支持多种格式：短横线、空格、复杂格式"
                )
            
            with col2:
                source_id = st.text_input("数据来源", value="manual_entry")
            
            # 实时解析预览
            if composition:
                parser = EnhancedCompositionParser()
                result = parser.parse(composition)
                
                if result.get('success'):
                    st.success("✅ 成分解析成功")
                    col_a, col_b, col_c = st.columns(3)
                    with col_a:
                        st.info(f"**主硬质相**: {result['ceramic_formula']}")
                    with col_b:
                        st.info(f"**粘结相**: {result['binder_formula']}")
                    with col_c:
                        st.info(f"**粘结相 wt%**: {result.get('binder_wt_pct', 'N/A')}")
                else:
                    st.error(f"❌ 解析失败: {result.get('message')}")
            
            st.subheader("工艺参数")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                sinter_temp = st.number_input("烧结温度 (°C)", min_value=0.0, max_value=3000.0, value=1400.0)
            with col2:
                grain_size = st.number_input("晶粒尺寸 (μm)", min_value=0.0, value=1.0)
            with col3:
                load_kgf = st.number_input("测试载荷 (kgf)", min_value=0.0, value=30.0)
            
            st.subheader("性能指标")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                hv = st.number_input("维氏硬度 (HV)", min_value=0.0, value=1500.0)
            with col2:
                kic = st.number_input("断裂韧性 (MPa·m^1/2)", min_value=0.0, value=12.0)
            with col3:
                trs = st.number_input("抗弯强度 (MPa)", min_value=0.0, value=2000.0)
            
            # 高级选项
            with st.expander("⚙️ 高级选项"):
                auto_features = st.checkbox("自动计算物理特征", value=True)
                st.caption("启用后将自动计算 VEC、晶格失配等特征（可能需要几秒）")
            
            # 提交按钮
            submitted = st.form_submit_button("💾 提交数据", use_container_width=True)
            
            if submitted:
                if not composition:
                    st.error("请输入成分字符串")
                else:
                    try:
                        db_v2 = CermetDatabaseV2('cermet_master_v2.db')
                        db_v2.create_tables()  # 确保表存在
                        
                        with st.spinner("正在保存数据..."):
                            exp_id = db_v2.add_experiment(
                                raw_composition=composition,
                                source_id=source_id,
                                sinter_temp_c=sinter_temp,
                                grain_size_um=grain_size,
                                load_kgf=load_kgf,
                                hv=hv,
                                kic=kic,
                                trs=trs,
                                auto_calculate_features=auto_features
                            )
                        
                        st.success(f"✅ 数据保存成功！实验 ID: {exp_id}")
                        
                        # 显示详细信息
                        data = db_v2.get_experiment(exp_id)
                        if data:
                            with st.expander("🔍 查看保存的数据"):
                                st.json(data)
                        
                    except Exception as e:
                        st.error(f"❌ 保存失败: {e}")
    
    # Tab 2: 批量导入
    with tab2:
        st.header("📂 批量导入 (v2.0)")
        st.caption("支持 Excel (.xlsx) 和 CSV (.csv) 文件")
        
        uploaded_file = st.file_uploader(
            "选择文件",
            type=['xlsx', 'csv'],
            help="支持 Excel 和 CSV 格式"
        )
        
        if uploaded_file:
            try:
                # 读取文件
                if uploaded_file.name.endswith('.csv'):
                    df = pd.read_csv(uploaded_file)
                else:
                    df = pd.read_excel(uploaded_file)
                
                st.success(f"✅ 文件加载成功: {len(df)} 行")
                
                # 显示数据预览
                with st.expander("🔍 数据预览 (前 10 行)"):
                    st.dataframe(df.head(10), use_container_width=True)
                
                # 列映射
                st.subheader("⚡ 列映射设置")
                st.caption("请将 Excel 列名映射到数据库字段")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write("📄 **Excel 列名**")
                    available_cols = list(df.columns)
                    st.info(f"共 {len(available_cols)} 列")
                
                with col2:
                    st.write("🎯 **必须字段**")
                    st.markdown("""
                    - `composition` (成分) *
                    - `HV` (硬度)
                    - `KIC` (韧性)
                    - `Sinter_Temp` (烧结温度)
                    """)
                
                # 自动匹配列
                col_mapping = {}
                
                # 智能匹配逻辑
                composition_col = st.selectbox(
                    "🧪 成分列 (必须)",
                    options=[''] + available_cols,
                    index=0
                )
                
                col_a, col_b, col_c = st.columns(3)
                with col_a:
                    hv_col = st.selectbox(
                        "🔨 硬度列 (HV)",
                        options=[''] + available_cols
                    )
                with col_b:
                    kic_col = st.selectbox(
                        "🔪 韧性列 (KIC)",
                        options=[''] + available_cols
                    )
                with col_c:
                    temp_col = st.selectbox(
                        "🌡️ 温度列",
                        options=[''] + available_cols
                    )
                
                # 高级选项
                with st.expander("⚙️ 高级选项"):
                    auto_features = st.checkbox("自动计算物理特征", value=False)
                    st.caption("⚠️ 大量数据时可能较慢，建议关闭")
                    
                    source_id = st.text_input("数据来源标记", value="batch_import")
                
                # 导入按钮
                if st.button("🚀 开始批量导入", type="primary", use_container_width=True):
                    if not composition_col:
                        st.error("⚠️ 请选择成分列")
                    else:
                        # 辅助函数：清理数值字段
                        def clean_numeric(value):
                            """清理数值字段，将无效值转为None"""
                            if pd.isna(value):
                                return None
                            if isinstance(value, str):
                                value = value.strip()
                                if value in ['-', 'N/A', 'NA', '', 'nan', 'NaN', 'null', 'NULL']:
                                    return None
                                try:
                                    return float(value)
                                except (ValueError, TypeError):
                                    return None
                            try:
                                return float(value)
                            except (ValueError, TypeError):
                                return None
                        
                        db_v2 = CermetDatabaseV2('cermet_master_v2.db')
                        db_v2.create_tables()
                        
                        progress_bar = st.progress(0)
                        status_text = st.empty()
                        
                        success_count = 0
                        fail_count = 0
                        errors = []
                        
                        for idx, row in df.iterrows():
                            try:
                                # 准备数据
                                comp = row.get(composition_col) if composition_col else None
                                
                                if pd.isna(comp) or not comp:
                                    fail_count += 1
                                    errors.append(f"行 {idx+2}: 成分缺失")
                                    continue
                                
                                # 清理所有数值字段
                                hv_val = clean_numeric(row.get(hv_col)) if hv_col else None
                                kic_val = clean_numeric(row.get(kic_col)) if kic_col else None
                                temp_val = clean_numeric(row.get(temp_col)) if temp_col else None
                                
                                # 添加到数据库
                                exp_id = db_v2.add_experiment(
                                    raw_composition=str(comp).strip(),
                                    source_id=source_id,
                                    hv=hv_val,
                                    kic=kic_val,
                                    sinter_temp_c=temp_val,
                                    auto_calculate_features=auto_features
                                )
                                success_count += 1
                                
                            except Exception as e:
                                fail_count += 1
                                error_msg = str(e)
                                # 截取关键错误信息
                                if "Failed to parse" in error_msg:
                                    error_msg = "成分解析失败"
                                elif "could not convert" in error_msg:
                                    error_msg = "数值转换失败"
                                elif "ValueError" in error_msg:
                                    error_msg = "数据格式错误"
                                errors.append(f"行 {idx+2}: {error_msg}")
                            
                            # 更新进度
                            progress = (idx + 1) / len(df)
                            progress_bar.progress(progress)
                            status_text.text(f"处理中: {idx+1}/{len(df)} (成功: {success_count}, 失败: {fail_count})")
                        
                        # 完成总结
                        progress_bar.progress(1.0)
                        
                        if fail_count == 0:
                            st.success(f"🎉 导入完成！成功 {success_count} 条")
                        else:
                            st.warning(f"⚠️ 导入完成: 成功 {success_count} 条, 失败 {fail_count} 条")
                            
                            with st.expander("🔍 查看错误详情"):
                                for err in errors[:20]:  # 最多显示 20 个
                                    st.text(err)
            
            except Exception as e:
                st.error(f"❌ 文件读取失败: {e}")
        
        else:
            # 示例模板
            st.info("📝 提示: 上传文件前，请确保文件格式正确")
            
            with st.expander("📊 查看示例模板"):
                example_data = pd.DataFrame({
                    'Composition': ['WC-10CoCrFeNi', 'WC-10Co', 'TiC-20Ni'],
                    'HV': [1500, 1600, 1200],
                    'KIC': [12.0, 10.5, 15.0],
                    'Sinter_Temp': [1400, 1350, 1300]
                })
                st.dataframe(example_data, use_container_width=True)
                st.caption("⬆️ 按照此格式准备你的 Excel/CSV 文件")
    
    # Tab 3: 成分解析预览
    with tab3:
        st.header("🔬 成分解析预览工具")
        st.caption("测试成分字符串的解析结果，无需保存到数据库")
        
        test_comp = st.text_area(
            "输入成分字符串（每行一个）",
            placeholder="WC-10CoCrFeNi\nb WC 69 CoCrFeNiMo 0.5 Cr3C2 10 Mo\nWC 85 Co 10 Ni 5",
            height=150
        )
        
        if st.button("🔍 批量解析", use_container_width=True):
            if test_comp:
                parser = EnhancedCompositionParser()
                lines = [l.strip() for l in test_comp.split('\n') if l.strip()]
                
                results = []
                for comp_str in lines:
                    result = parser.parse(comp_str)
                    results.append({
                        '原始成分': comp_str,
                        '解析状态': '✅ 成功' if result.get('success') else '❌ 失败',
                        '主硬质相': result.get('ceramic_formula', '-'),
                        '第二硬质相': result.get('secondary_phase', '-'),
                        '粘结相化学式': result.get('binder_formula', '-'),
                        '粘结相 wt%': result.get('binder_wt_pct', '-'),
                        'HEA': '是' if result.get('is_hea') else '否'
                    })
                
                df_results = pd.DataFrame(results)
                st.dataframe(df_results, use_container_width=True)
                
                # 统计
                success_count = sum(1 for r in results if r['解析状态'] == '✅ 成功')
                st.metric("解析成功率", f"{success_count}/{len(results)} ({success_count/len(results)*100:.1f}%)")
    
    # Tab 4: 补充特征计算 (重新设计)
    with tab4:
                st.header("⚡ 补充特征计算")
                st.markdown("""
                基于**Proxy Models**和**Matminer**为数据库中缺失特征的记录批量计算深层物理特征。
    
                **支持特征**:
                - 🔬 Proxy Model: 形成能、晶格常数、磁矩、晶格失配
                - 🧪 Matminer: Magpie元素统计特征（可选）
                """)
    
                try:
                    db_v2 = CermetDatabaseV2('cermet_master_v2.db')
                    stats = db_v2.get_statistics()
        
                    if stats['total_experiments'] == 0:
                        st.info("📊 数据库为空，请先添加数据")
                    else:
                        # ===========================================
                        # 阶段1: 数据状态检测
                        # ===========================================
                        st.subheader("📊 数据状态检测")
            
                        session = db_v2.Session()
                        try:
                            from core.db_models_v2 import Experiment, Composition, Property, CalculatedFeature
                
                            # 查找缺失Proxy特征的记录
                            exps_missing_proxy = session.query(Experiment).filter(
                                ~Experiment.id.in_(
                                    session.query(CalculatedFeature.exp_id)
                                )
                            ).all()
                
                            # 查找缺失Matminer特征的记录
                            exps_missing_matminer = session.query(CalculatedFeature).filter(
                                (CalculatedFeature.has_matminer == False) | 
                                (CalculatedFeature.has_matminer == None)
                            ).count()
                
            # 显示统计
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric("总记录数", stats['total_experiments'])
                            with col2:
                                missing_proxy_pct = len(exps_missing_proxy)/stats['total_experiments']*100 if stats['total_experiments'] > 0 else 0
                                st.metric(
                                    "缺失Proxy特征", 
                                    len(exps_missing_proxy),
                                    delta=f"{missing_proxy_pct:.1f}%",
                                    delta_color="inverse"
                                )
                            with col3:
                                st.metric("缺失Matminer特征", exps_missing_matminer)
                
                            # 预览缺失记录
                            if len(exps_missing_proxy) > 0:
                                with st.expander("🔍 查看缺失Proxy特征的记录 (前10条)"):
                                    preview_data = []
                                    for exp in exps_missing_proxy[:10]:
                                        preview_data.append({
                                            'ID': exp.id,
                                            '成分': exp.raw_composition[:60] if len(exp.raw_composition) > 60 else exp.raw_composition,
                                            '来源': exp.source_id,
                                            '创建时间': exp.created_at.strftime('%Y-%m-%d %H:%M') if exp.created_at else 'N/A'
                                        })
                                    st.dataframe(pd.DataFrame(preview_data), use_container_width=True)
                
                            # ===========================================
                            # 阶段2: 特征计算配置
                            # ===========================================
                            st.markdown("---")
                            st.subheader("⚙️ 计算配置")
                
                            col_cfg1, col_cfg2, col_cfg3 = st.columns(3)
                
                            with col_cfg1:
                                use_proxy = st.checkbox(
                                    "启用Proxy Model特征",
                                    value=True,
                                    help="DFT预测: 形成能、晶格常数、磁矩等"
                                )
                
                            with col_cfg2:
                                use_matminer = st.checkbox(
                                    "启用Matminer特征",
                                    value=False,
                                    help="Magpie元素统计特征(会增加计算时间10-30秒)"
                                )
                
                            with col_cfg3:
                                force_recalc = st.checkbox(
                                    "重算已有特征",
                                    value=False,
                                    help="强制重新计算所有记录"
                                )
                
                            # 计算目标数量
                            target_count = stats['total_experiments'] if force_recalc else len(exps_missing_proxy)
                
                            if target_count == 0 and not use_matminer:
                                st.success("✅ 所有记录已有Proxy特征！")
                                if exps_missing_matminer > 0:
                                    st.info(f"💡 提示: 有 {exps_missing_matminer} 条记录可添加Matminer特征，请勾选'启用Matminer特征'并重算")
                            else:
                                st.info(f"🎯 将为 **{target_count}** 条记录计算特征")
                
                            #===========================================
                            # 阶段3: 批量计算
                            # ===========================================
                            st.markdown("---")
                            st.subheader("🚀 开始计算")
                
                            calc_disabled = (target_count == 0 and not (use_matminer and exps_missing_matminer > 0))
                
                            if st.button(
                                "⚡ 批量计算特征", 
                                type="primary", 
                                use_container_width=True,
                                disabled=calc_disabled
                            ):
                                # ===== 准备数据 =====
                                with st.spinner("准备数据..."):
                                    if force_recalc:
                                        target_exps = session.query(Experiment).all()
                                    else:
                                        target_exps = exps_missing_proxy
                        
                                    # 构建DataFrame
                                    data_for_injection = []
                                    for exp in target_exps:
                                        # 优先从Composition表读取已解析成分
                                        comp = session.query(Composition).filter_by(exp_id=exp.id).first()
                                        if comp and comp.binder_formula:
                                            binder_comp = comp.binder_formula
                                            ceramic_type = comp.ceramic_formula or 'WC'
                                        else:
                                            # 回退: 使用raw_composition
                                            binder_comp = exp.raw_composition
                                            ceramic_type = 'WC'
                            
                                        data_for_injection.append({
                                            'exp_id': exp.id,
                                            'binder_composition': binder_comp,
                                            'Ceramic_Type': ceramic_type,
                                            'raw_composition': exp.raw_composition
                                        })
                        
                                    df_to_inject = pd.DataFrame(data_for_injection)
                                    st.success(f"✅ 准备完成: {len(df_to_inject)} 条记录")
                    
                                # ===== Proxy Model特征注入 =====
                                progress_container = st.empty()
                                error_container = st.empty()
                    
                                try:
                                    from core.feature_injector import FeatureInjector
                        
                                    if use_proxy:
                                        with progress_container:
                                            st.info("🔬 正在加载Proxy Models...")
                            
                                        try:
                                            injector = FeatureInjector(model_dir='models/proxy_models')
                                
                                            with progress_container:
                                                st.info(f"💫 正在批量计算Proxy特征 ({len(df_to_inject)}条)...")
                                
                                            # 批量注入特征
                                            df_enhanced = injector.inject_features(
                                                df_to_inject,
                                                comp_col='binder_composition',
                                                ceramic_type_col='Ceramic_Type',
                                                verbose=False
                                            )
                                
                                            progress_container.success("✅ Proxy特征计算完成!")
                            
                                        except Exception as e:
                                            error_container.error(f"⚠️ Proxy Model加载/计算失败: {str(e)[:200]}")
                                            df_enhanced = df_to_inject  # 回退
                                    else:
                                        df_enhanced = df_to_inject
                        
                                    # ===== Matminer特征化（可选） =====
                                    if use_matminer:
                                        try:
                                            from matminer.featurizers.composition import ElementProperty
                                            from pymatgen.core import Composition
                                
                                            progress_container.info("🧪 正在计算Matminer特征... (预计10-30秒)")
                                
                                            # 创建Composition对象
                                            compositions = []
                                            for _, row in df_enhanced.iterrows():
                                                try:
                                                    comp_str = row['binder_composition']
                                                    comp_obj = Composition(comp_str)
                                                    compositions.append(comp_obj)
                                                except:
                                                    compositions.append(None)
                                
                                            df_enhanced['_temp_comp'] = compositions
                                
                                            # Magpie特征化
                                            featurizer = ElementProperty.from_preset("magpie")
                                            valid_df = df_enhanced[df_enhanced['_temp_comp'].notnull()].copy()
                                
                                            if len(valid_df) > 0:
                                                valid_df = featurizer.featurize_dataframe(
                                                    valid_df,
                                                    '_temp_comp',
                                                    ignore_errors=True
                                                )
                                    
                                                # 提取关键特征（节省数据库空间）
                                                feature_labels = featurizer.feature_labels()
                                                key_features = [
                                                    'MagpieData mean AtomicWeight',
                                                    'MagpieData std Electronegativity'
                                                ]
                                    
                                                for feat in key_features:
                                                    if feat in feature_labels and feat in valid_df.columns:
                                                        df_enhanced.loc[valid_df.index, feat] = valid_df[feat]
                                    
                                                df_enhanced.drop(columns=['_temp_comp'], inplace=True, errors='ignore')
                                                progress_container.success("✅ Matminer特征计算完成!")
                                            else:
                                                progress_container.warning("⚠️ Matminer: 所有成分解析失败")
                            
                                        except Exception as e:
                                            error_container.warning(f"⚠️ Matminer计算失败: {str(e)[:200]}")
                        
                                    # ===== 写入数据库 =====
                                    progress_container.info("💾 正在保存到数据库...")
                        
                                    success_count = 0
                                    fail_count = 0
                                    errors = []
                        
                                    for _, row in df_enhanced.iterrows():
                                        try:
                                            exp_id = row['exp_id']
                                
                                            # 检查是否已存在
                                            existing = session.query(CalculatedFeature).filter_by(exp_id=exp_id).first()
                                
                                            if existing:
                                                if force_recalc or use_matminer:
                                                    # 更新
                                                    existing.pred_formation_energy = row.get('pred_formation_energy')
                                                    existing.pred_lattice_param = row.get('pred_lattice_param')
                                                    existing.lattice_mismatch = row.get('lattice_mismatch_wc')
                                                    existing.pred_magnetic_moment = row.get('pred_magnetic_moment')
                                        
                                                    if use_matminer:
                                                        existing.magpie_mean_atomic_mass = row.get('MagpieData mean AtomicWeight')
                                                        existing.magpie_std_electronegativity = row.get('MagpieData std Electronegativity')
                                                        existing.has_matminer = True
                                            else:
                                                # 新建
                                                feature = CalculatedFeature(
                                                    exp_id=exp_id,
                                                    pred_formation_energy=row.get('pred_formation_energy'),
                                                    pred_lattice_param=row.get('pred_lattice_param'),
                                                    lattice_mismatch=row.get('lattice_mismatch_wc'),
                                                    pred_magnetic_moment=row.get('pred_magnetic_moment'),
                                                    magpie_mean_atomic_mass=row.get('MagpieData mean AtomicWeight'),
                                                    magpie_std_electronegativity=row.get('MagpieData std Electronegativity'),
                                                    has_matminer=use_matminer
                                                )
                                                session.add(feature)
                                
                                            session.commit()
                                            success_count += 1
                            
                                        except Exception as e:
                                            session.rollback()
                                            fail_count += 1
                                            errors.append(f"ID {row.get('exp_id')}: {str(e)[:50]}")
                        
                                    # ===== 结果展示 =====
                                    progress_container.empty()
                                    error_container.empty()
                        
                                    st.markdown("---")
                                    st.subheader("🎉 计算完成")
                        
                                    col_r1, col_r2, col_r3 = st.columns(3)
                                    with col_r1:
                                        st.metric("成功", success_count, delta="✅")
                                    with col_r2:
                                        st.metric("失败", fail_count, delta="❌" if fail_count > 0 else "")
                                    with col_r3:
                                        success_rate = (success_count / (success_count + fail_count) * 100) if (success_count + fail_count) > 0 else 0
                                        st.metric("成功率", f"{success_rate:.1f}%")
                        
                                    # 特征统计
                                    with st.expander("📊 特征统计"):
                                        feature_cols = ['pred_formation_energy', 'pred_lattice_param', 
                                                       'lattice_mismatch_wc', 'pred_magnetic_moment']
                            
                                        stats_data = []
                                        for col in feature_cols:
                                            if col in df_enhanced.columns:
                                                valid_count = df_enhanced[col].notna().sum()
                                                mean_val = df_enhanced[col].mean() if valid_count > 0 else 0
                                                std_val = df_enhanced[col].std() if valid_count > 0 else 0
                                    
                                                stats_data.append({
                                                    '特征': col,
                                                    '有效数': valid_count,
                                                    '均值': f"{mean_val:.4f}",
                                                    '标准差': f"{std_val:.4f}"
                                                })
                            
                                        if stats_data:
                                            st.dataframe(pd.DataFrame(stats_data), use_container_width=True)
                        
                                    # 错误日志
                                    if fail_count > 0:
                                        with st.expander(f"🔍 错误日志 ({fail_count} 条)"):
                                            for err in errors[:20]:
                                                st.text(err)
                                            if len(errors) > 20:
                                                st.info(f"...还有 {len(errors)-20} 条错误")
                        
                                    # 刷新按钮
                                    if st.button("🔄 刷新页面"):
                                        st.rerun()
                    
                                except ImportError as e:
                                    st.error(f"❗ 模块导入失败: {e}")
                                    st.info("💡 确认 `core/feature_injector.py` 存在且Proxy Models已训练")
                    
                                except Exception as e:
                                    st.error(f"❗ 计算失败: {e}")
                                    import traceback
                                    with st.expander("🔍 详细错误信息"):
                                        st.code(traceback.format_exc())
            
                        finally:
                            session.close()
    
                except Exception as e:
                    st.error(f"❗ 加载失败: {e}")

    # Tab 5: 数据查询
    with tab5:
        st.header("🔍 数据查询与分析")
        
        try:
            db_v2 = CermetDatabaseV2('cermet_master_v2.db')
            session = db_v2.Session()
            
            try:
                from core.db_models_v2 import Experiment, Composition, Property, CalculatedFeature
                
                stats = db_v2.get_statistics()
                
                if stats['total_experiments'] == 0:
                    st.info("📊 数据库为空，请先添加数据")
                else:
                    st.success(f"📊 数据库包含 {stats['total_experiments']} 条实验数据")
                    
                    # 数据筛选
                    st.subheader("🔍 数据筛选")
                    
                    col_f1, col_f2, col_f3 = st.columns(3)
                    with col_f1:
                        filter_hea = st.selectbox(
                            "粘结相类型",
                            options=["全部", "HEA", "传统"],
                            index=0
                        )
                    
                    with col_f2:
                        limit = st.number_input(
                            "显示记录数",
                            min_value=10,
                            max_value=5000,
                            value=100,
                            step=10
                        )
                    
                    with col_f3:
                        search_comp = st.text_input(
                            "成分搜索（关键词）",
                            placeholder="例如: WC, Co, CoCrFeNi"
                        )
                    
                    # 查询数据
                    query = session.query(
                        Experiment.id,
                        Experiment.raw_composition,
                        Experiment.source_id,
                        Experiment.sinter_temp_c,
                        Experiment.grain_size_um,
                        Composition.ceramic_formula,
                        Composition.binder_formula,
                        Composition.binder_wt_pct,
                        Composition.is_hea,
                        Property.hv,
                        Property.kic,
                        Property.trs,
                        CalculatedFeature.vec_binder,
                        CalculatedFeature.lattice_mismatch
                    ).join(
                        Composition, Experiment.id == Composition.exp_id, isouter=True
                    ).join(
                        Property, Experiment.id == Property.exp_id, isouter=True
                    ).join(
                        CalculatedFeature, Experiment.id == CalculatedFeature.exp_id, isouter=True
                    )
                    
                    # 应用筛选
                    if filter_hea == "HEA":
                        query = query.filter(Composition.is_hea == True)
                    elif filter_hea == "传统":
                        query = query.filter(Composition.is_hea == False)
                    
                    if search_comp:
                        query = query.filter(Experiment.raw_composition.like(f'%{search_comp}%'))
                    
                    results = query.limit(limit).all()
                    
                    if results:
                        # 转换为DataFrame
                        data = []
                        for r in results:
                            data.append({
                                'ID': r[0],
                                '成分': r[1],
                                '来源': r[2],
                                '烧结温度(°C)': r[3],
                                '晶粒尺寸(μm)': r[4],
                                '硬质相': r[5],
                                '粘结相': r[6],
                                '粘结wt%': r[7],
                                'HEA': '是' if r[8] else '否',
                                'HV': r[9],
                                'KIC': r[10],
                                'TRS': r[11],
                                'VEC': r[12],
                                '晶格失配': r[13]
                            })
                        
                        df = pd.DataFrame(data)
                        
                        st.subheader(f"📋 查询结果 ({len(df)} 条)")
                        
                        # 列选择
                        st.markdown("**选择显示列**")
                        col_sel1, col_sel2 = st.columns([4, 1])
                        
                        with col_sel1:
                            all_cols = list(df.columns)
                            default_cols = ['ID', '成分', '硬质相', '粘结相', 'HEA', 'HV', 'KIC']
                            selected_cols = st.multiselect(
                                "显示列（可多选）",
                                options=all_cols,
                                default=[c for c in default_cols if c in all_cols]
                            )
                        
                        with col_sel2:
                            if st.button("🔄 重置"):
                                st.rerun()
                        
                        # 显示表格
                        if selected_cols:
                            st.dataframe(
                                df[selected_cols],
                                use_container_width=True,
                                height=400
                            )
                        else:
                            st.warning("请至少选择一列")
                        
                        # 导出功能
                        st.markdown("---")
                        st.subheader("📥 导出数据")
                        
                        col_e1, col_e2 = st.columns(2)
                        with col_e1:
                            export_format = st.selectbox("格式", ["CSV", "Excel"])
                        with col_e2:
                            from datetime import datetime
                            export_name = st.text_input(
                                "文件名",
                                value=f"export_v2_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                            )
                        
                        if st.button("💾 导出", use_container_width=True):
                            try:
                                export_df = df[selected_cols] if selected_cols else df
                                
                                if export_format == "CSV":
                                    csv = export_df.to_csv(index=False, encoding='utf-8-sig')
                                    st.download_button(
                                        "⬇️ 下载 CSV",
                                        csv,
                                        file_name=f"{export_name}.csv",
                                        mime="text/csv"
                                    )
                                else:
                                    import io
                                    buffer = io.BytesIO()
                                    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                                        export_df.to_excel(writer, index=False)
                                    
                                    st.download_button(
                                        "⬇️ 下载 Excel",
                                        buffer.getvalue(),
                                        file_name=f"{export_name}.xlsx",
                                        mime="application/vnd.ms-excel"
                                    )
                                
                                st.success("✅ 导出成功！")
                            except Exception as e:
                                st.error(f"导出失败: {e}")
                        
                        # 简单统计
                        st.markdown("---")
                        st.subheader("📊 数据统计")
                        
                        col_s1, col_s2, col_s3, col_s4 = st.columns(4)
                        with col_s1:
                            st.metric("记录数", len(df))
                        with col_s2:
                            hea_count = df[df['HEA'] == '是'].shape[0]
                            st.metric("HEA", hea_count)
                        with col_s3:
                            avg_hv = df['HV'].mean() if 'HV' in df and df['HV'].notna().any() else 0
                            st.metric("平均HV", f"{avg_hv:.1f}" if avg_hv > 0 else "N/A")
                        with col_s4:
                            avg_kic = df['KIC'].mean() if 'KIC' in df and df['KIC'].notna().any() else 0
                            st.metric("平均KIC", f"{avg_kic:.2f}" if avg_kic > 0 else "N/A")
                    
                    else:
                        st.warning("未找到符合条件的数据")
            
            finally:
                session.close()
        
        except Exception as e:
            st.error(f"查询失败: {e}")
            import traceback
            st.code(traceback.format_exc())
