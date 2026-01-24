# -*- coding: utf-8 -*-
"""
陶瓷材料属性管理测试脚本

测试新添加的 get_ceramic_properties() 方法
"""
import sys
import io
from core.material_database import db

# Windows 控制台编码修复
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

print("=" * 70)
print("陶瓷材料属性查询测试")
print("=" * 70)

# 测试1: 查询WC属性
print("\n测试1: 查询WC（碳化钨）属性")
print("-" * 70)
wc_props = db.get_ceramic_properties('WC')
if wc_props:
    print(f"✓ WC属性获取成功!")
    print(f"  密度: {wc_props.get('density')} g/cm³")
    print(f"  结构: {wc_props.get('structure')}")
    print(f"  空间群: {wc_props.get('space_group')}")
    print(f"  晶格参数 a: {wc_props.get('lattice_a')} Å")
    print(f"  晶格参数 c: {wc_props.get('lattice_c')} Å")
    print(f"  最近邻距离: {wc_props.get('neighbor_distance')} Å")
    print(f"  数据来源: {wc_props.get('source')}")
else:
    print("✗ WC属性获取失败!")

# 测试2: 查询TiC属性
print("\n测试2: 查询TiC（碳化钛）属性")
print("-" * 70)
tic_props = db.get_ceramic_properties('TiC')
if tic_props:
    print(f"✓ TiC属性获取成功!")
    print(f"  密度: {tic_props.get('density')} g/cm³")
    print(f"  结构: {tic_props.get('structure')}")
    print(f"  空间群: {tic_props.get('space_group')}")
    print(f"  晶格参数 a: {tic_props.get('lattice_a')} Å")
    print(f"  最近邻距离: {tic_props.get('neighbor_distance')} Å")
    print(f"  数据来源: {tic_props.get('source')}")
else:
    print("✗ TiC属性获取失败!")

# 测试3: 查询TiN属性
print("\n测试3: 查询TiN（氮化钛）属性")
print("-" * 70)
tin_props = db.get_ceramic_properties('TiN')
if tin_props:
    print(f"✓ TiN属性获取成功!")
    print(f"  密度: {tin_props.get('density')} g/cm³")
    print(f"  结构: {tin_props.get('structure')}")
    print(f"  空间群: {tin_props.get('space_group')}")
    print(f"  晶格参数 a: {tin_props.get('lattice_a')} Å")
    print(f"  最近邻距离: {tin_props.get('neighbor_distance')} Å")
    print(f"  数据来源: {tin_props.get('source')}")
else:
    print("✗ TiN属性获取失败!")

# 测试4: 查询所有硬质合金陶瓷
print("\n测试4: 批量查询常用硬质合金陶瓷")
print("-" * 70)
ceramics = ['WC', 'TiC', 'TaC', 'NbC', 'VC', 'TiN']
results = []
for formula in ceramics:
    props = db.get_ceramic_properties(formula)
    if props:
        results.append({
            'formula': formula,
            'density': props.get('density'),
            'structure': props.get('structure'),
            'lattice_a': props.get('lattice_a')
        })

print(f"成功获取 {len(results)}/{len(ceramics)} 种陶瓷的属性")
print("\n陶瓷材料对比表:")
print(f"{'材料':<8} {'密度(g/cm³)':<12} {'结构':<15} {'晶格a(Å)':<10}")
print("-" * 50)
for r in results:
    print(f"{r['formula']:<8} {r['density']:<12} {r['structure']:<15} {r['lattice_a']:<10.3f}")

# 测试5: 向后兼容性 - 原有密度查询方法仍可用
print("\n测试5: 向后兼容性测试")
print("-" * 70)
density_old = db.get_compound_density('WC')
density_new = db.get_ceramic_properties('WC').get('density')
if density_old == density_new:
    print(f"✓ 向后兼容性验证通过")
    print(f"  get_compound_density('WC'): {density_old}")
    print(f"  get_ceramic_properties('WC')['density']: {density_new}")
else:
    print(f"✗ 向后兼容性验证失败!")

print("\n" + "=" * 70)
print("测试完成！")
print("=" * 70)
