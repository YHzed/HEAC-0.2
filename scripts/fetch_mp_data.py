"""
Materials Project数据获取工具

此脚本用于从Materials Project获取材料数据并更新到本地数据库。

用法:
    # 获取单个材料数据
    python scripts/fetch_mp_data.py --formula "TiO2"
    
    # 批量获取材料数据
    python scripts/fetch_mp_data.py --batch compounds_list.txt
    
    # 搜索化学系统
    python scripts/fetch_mp_data.py --search "Fe-C"
    
    # 显示详细信息
    python scripts/fetch_mp_data.py --formula "TiO2" --verbose
"""

import argparse
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.material_database import db
from core.config import config


def fetch_single_material(formula: str, verbose: bool = False, update_local: bool = False):
    """
    获取单个材料的数据
    
    Args:
        formula: 化学式
        verbose: 是否显示详细信息
        update_local: 是否更新到本地数据库
    """
    print(f"\n{'='*60}")
    print(f"正在获取材料: {formula}")
    print(f"{'='*60}")
    
    # 首先检查本地是否有数据
    local_density = db.get_compound_density(formula)
    local_enthalpy = db.get_formation_enthalpy(formula)
    
    if local_density or local_enthalpy:
        print(f"\n本地数据库中已有此材料:")
        if local_density:
            print(f"  密度: {local_density} g/cm³")
        if local_enthalpy:
            print(f"  生成焓: {local_enthalpy} kJ/mol")
    
    # 从Materials Project获取
    print(f"\n从Materials Project获取数据...")
    mp_data = db.get_mp_data(formula)
    
    if not mp_data:
        print(f"❌ 未找到 {formula} 的数据")
        return False
    
    # 显示获取的数据
    print(f"\n✅ 成功获取数据:")
    print(f"  Material ID: {mp_data.get('material_id', 'N/A')}")
    print(f"  化学式: {mp_data.get('formula_pretty', 'N/A')}")
    
    if mp_data.get('density'):
        print(f"  密度: {mp_data.get('density'):.3f} g/cm³")
    
    if mp_data.get('formation_energy_per_atom') is not None:
        print(f"  生成能: {mp_data.get('formation_energy_per_atom'):.4f} eV/atom")
    
    if mp_data.get('energy_above_hull') is not None:
        print(f"  能量高于凸包: {mp_data.get('energy_above_hull'):.4f} eV/atom")
        stable = "是" if mp_data.get('is_stable') else "否"
        print(f"  是否稳定: {stable}")
    
    if mp_data.get('band_gap') is not None:
        print(f"  能带隙: {mp_data.get('band_gap'):.3f} eV")
        metal = "是" if mp_data.get('is_metal') else "否"
        print(f"  是否金属: {metal}")
    
    if verbose and mp_data.get('symmetry'):
        symmetry = mp_data.get('symmetry', {})
        print(f"\n  对称性信息:")
        print(f"    晶系: {symmetry.get('crystal_system', 'N/A')}")
        print(f"    空间群: {symmetry.get('symbol', 'N/A')}")
        print(f"    点群: {symmetry.get('point_group', 'N/A')}")
    
    # 更新到本地数据库
    if update_local:
        print(f"\n正在更新到本地数据库...")
        if db.update_compound_from_mp(formula, save=True):
            print(f"✅ 成功更新到本地数据库")
        else:
            print(f"❌ 更新失败")
    
    return True


def search_materials(query: str, max_results: int = 10):
    """
    搜索材料
    
    Args:
        query: 搜索查询（化学系统、化学式或MP ID）
        max_results: 最大结果数
    """
    print(f"\n{'='*60}")
    print(f"搜索: {query}")
    print(f"{'='*60}")
    
    results = db.search_mp_materials(query)
    
    if not results:
        print(f"❌ 未找到匹配的材料")
        return
    
    print(f"\n✅ 找到 {len(results)} 个材料 (显示前 {min(max_results, len(results))} 个):\n")
    
    for i, material in enumerate(results[:max_results], 1):
        print(f"{i}. {material.get('formula_pretty', 'N/A')}")
        print(f"   Material ID: {material.get('material_id', 'N/A')}")
        if material.get('density'):
            print(f"   密度: {material.get('density'):.3f} g/cm³")
        if material.get('formation_energy_per_atom') is not None:
            print(f"   生成能: {material.get('formation_energy_per_atom'):.4f} eV/atom")
        if material.get('energy_above_hull') is not None:
            energy_hull = material.get('energy_above_hull')
            stable = "✓" if energy_hull == 0 else "✗"
            print(f"   稳定性: {stable} ({energy_hull:.4f} eV/atom above hull)")
        print()


def batch_fetch(batch_file: str, update_local: bool = False):
    """
    批量获取材料数据
    
    Args:
        batch_file: 包含化学式列表的文件（每行一个）
        update_local: 是否更新到本地数据库
    """
    try:
        with open(batch_file, 'r', encoding='utf-8') as f:
            formulas = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        print(f"❌ 文件未找到: {batch_file}")
        return
    
    print(f"\n{'='*60}")
    print(f"批量获取 {len(formulas)} 个材料")
    print(f"{'='*60}")
    
    success_count = 0
    fail_count = 0
    
    for i, formula in enumerate(formulas, 1):
        print(f"\n[{i}/{len(formulas)}] 处理: {formula}")
        try:
            if fetch_single_material(formula, verbose=False, update_local=update_local):
                success_count += 1
            else:
                fail_count += 1
        except Exception as e:
            print(f"❌ 错误: {e}")
            fail_count += 1
    
    print(f"\n{'='*60}")
    print(f"批量获取完成")
    print(f"成功: {success_count}, 失败: {fail_count}")
    print(f"{'='*60}")


def main():
    parser = argparse.ArgumentParser(
        description='从Materials Project获取材料数据',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 获取单个材料
  python fetch_mp_data.py --formula "TiO2"
  
  # 获取并更新到本地数据库
  python fetch_mp_data.py --formula "TiO2" --update
  
  # 批量获取
  python fetch_mp_data.py --batch compounds.txt --update
  
  # 搜索材料
  python fetch_mp_data.py --search "Fe-C" --max-results 20
        """
    )
    
    parser.add_argument('--formula', '-f', type=str, 
                        help='化学式 (例如: "TiO2")')
    parser.add_argument('--batch', '-b', type=str, 
                        help='包含化学式列表的文件路径')
    parser.add_argument('--search', '-s', type=str, 
                        help='搜索查询 (化学系统或化学式, 例如: "Fe-C")')
    parser.add_argument('--update', '-u', action='store_true', 
                        help='更新到本地数据库')
    parser.add_argument('--verbose', '-v', action='store_true', 
                        help='显示详细信息')
    parser.add_argument('--max-results', '-m', type=int, default=10,
                        help='搜索时显示的最大结果数 (默认: 10)')
    
    args = parser.parse_args()
    
    # 验证配置
    if not config.validate():
        print("\n❌ 配置错误: 未设置Materials Project API密钥")
        print("请在项目根目录的 .env 文件中设置 MP_API_KEY")
        print("获取API密钥: https://materialsproject.org/dashboard")
        return 1
    
    # 根据参数执行相应操作
    if args.formula:
        fetch_single_material(args.formula, verbose=args.verbose, update_local=args.update)
    elif args.batch:
        batch_fetch(args.batch, update_local=args.update)
    elif args.search:
        search_materials(args.search, max_results=args.max_results)
    else:
        parser.print_help()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
