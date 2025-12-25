"""
增强的查询模块内容

这是tab5的完整内容，用于替换简单查询
"""

# Tab 5: 数据查询（增强版）
content = '''
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
'''

print(content)
