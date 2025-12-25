# 新的Tab4实现 - 补充特征计算（基于FeatureInjector）
# 请复制此代码，替换 11_Database_Manager_V2.py 中第412-551行的内容

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
