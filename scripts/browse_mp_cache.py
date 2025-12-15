"""
Materials Project缓存浏览和管理工具

此脚本用于管理和查看MP API的缓存数据。

用法:
    # 查看缓存统计
    python scripts/browse_mp_cache.py --stats
    
    # 列出所有缓存
    python scripts/browse_mp_cache.py --list
    
    # 查看特定缓存内容
    python scripts/browse_mp_cache.py --view summary_TiO2.json
    
    # 清理过期缓存
    python scripts/browse_mp_cache.py --clean
"""

import argparse
import json
import sys
from pathlib import Path
from datetime import datetime, timedelta

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.config import config


def get_cache_files():
    """获取所有缓存文件"""
    cache_dir = config.get_cache_path()
    if not cache_dir.exists():
        return []
    return list(cache_dir.glob('*.json'))


def format_size(size_bytes):
    """格式化文件大小"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} TB"


def show_stats():
    """显示缓存统计信息"""
    cache_files = get_cache_files()
    
    if not cache_files:
        print("📂 缓存目录为空")
        return
    
    total_size = sum(f.stat().st_size for f in cache_files)
    
    # 统计过期文件
    expired_count = 0
    ttl_days = config.MP_CACHE_TTL_DAYS
    cutoff_date = datetime.now() - timedelta(days=ttl_days)
    
    for cache_file in cache_files:
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                cached_time = datetime.fromisoformat(data.get('_cached_at', '2000-01-01'))
                if cached_time < cutoff_date:
                    expired_count += 1
        except:
            pass
    
    print(f"\n{'='*60}")
    print(f"Materials Project 缓存统计")
    print(f"{'='*60}")
    print(f"缓存目录: {config.get_cache_path()}")
    print(f"缓存文件数: {len(cache_files)}")
    print(f"总大小: {format_size(total_size)}")
    print(f"缓存TTL: {ttl_days} 天")
    print(f"过期文件数: {expired_count}")
    print(f"{'='*60}\n")


def list_cache():
    """列出所有缓存文件"""
    cache_files = get_cache_files()
    
    if not cache_files:
        print("📂 缓存目录为空")
        return
    
    print(f"\n{'='*60}")
    print(f"缓存文件列表 (共 {len(cache_files)} 个)")
    print(f"{'='*60}\n")
    
    # 按修改时间排序
    cache_files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
    
    for i, cache_file in enumerate(cache_files, 1):
        stat = cache_file.stat()
        mod_time = datetime.fromtimestamp(stat.st_mtime)
        size = format_size(stat.st_size)
        
        # 读取缓存时间
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                cached_at = data.get('_cached_at', 'N/A')
                if cached_at != 'N/A':
                    cached_time = datetime.fromisoformat(cached_at)
                    age = datetime.now() - cached_time
                    age_str = f"{age.days}天前" if age.days > 0 else f"{age.seconds//3600}小时前"
                else:
                    age_str = 'N/A'
        except:
            age_str = 'Error'
        
        print(f"{i:3d}. {cache_file.name}")
        print(f"     大小: {size:>10s} | 缓存时间: {age_str}")
        
        if i % 10 == 0 and i < len(cache_files):
            print()


def view_cache(filename: str):
    """查看特定缓存文件内容"""
    cache_dir = config.get_cache_path()
    cache_file = cache_dir / filename
    
    if not cache_file.exists():
        print(f"❌ 缓存文件不存在: {filename}")
        return
    
    try:
        with open(cache_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print(f"\n{'='*60}")
        print(f"缓存文件: {filename}")
        print(f"{'='*60}")
        print(f"缓存时间: {data.get('_cached_at', 'N/A')}")
        print(f"\n内容:")
        print(json.dumps(data.get('content'), ensure_ascii=False, indent=2))
        print(f"{'='*60}\n")
        
    except Exception as e:
        print(f"❌ 读取缓存文件失败: {e}")


def clean_cache(dry_run: bool = False):
    """清理过期缓存"""
    cache_files = get_cache_files()
    
    if not cache_files:
        print("📂 缓存目录为空")
        return
    
    ttl_days = config.MP_CACHE_TTL_DAYS
    cutoff_date = datetime.now() - timedelta(days=ttl_days)
    
    print(f"\n{'='*60}")
    print(f"清理过期缓存 (TTL: {ttl_days} 天)")
    if dry_run:
        print("(模拟运行 - 不会实际删除)")
    print(f"{'='*60}\n")
    
    deleted_count = 0
    deleted_size = 0
    
    for cache_file in cache_files:
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                cached_time = datetime.fromisoformat(data.get('_cached_at', '2000-01-01'))
                
                if cached_time < cutoff_date:
                    size = cache_file.stat().st_size
                    age = datetime.now() - cached_time
                    
                    print(f"{'[模拟] ' if dry_run else ''}删除: {cache_file.name}")
                    print(f"  缓存时间: {cached_time.strftime('%Y-%m-%d %H:%M:%S')}")
                    print(f"  已过期: {age.days} 天")
                    print(f"  大小: {format_size(size)}")
                    print()
                    
                    if not dry_run:
                        cache_file.unlink()
                    
                    deleted_count += 1
                    deleted_size += size
        except Exception as e:
            print(f"❌ 处理 {cache_file.name} 时出错: {e}")
    
    print(f"{'='*60}")
    if deleted_count > 0:
        print(f"{'模拟' if dry_run else ''}删除了 {deleted_count} 个文件")
        print(f"释放空间: {format_size(deleted_size)}")
    else:
        print("没有过期的缓存文件")
    print(f"{'='*60}\n")


def main():
    parser = argparse.ArgumentParser(
        description='Materials Project缓存管理工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 查看统计信息
  python browse_mp_cache.py --stats
  
  # 列出所有缓存
  python browse_mp_cache.py --list
  
  # 查看特定缓存
  python browse_mp_cache.py --view summary_TiO2.json
  
  # 清理过期缓存（模拟运行）
  python browse_mp_cache.py --clean --dry-run
  
  # 清理过期缓存（实际删除）
  python browse_mp_cache.py --clean
        """
    )
    
    parser.add_argument('--stats', action='store_true', 
                        help='显示缓存统计信息')
    parser.add_argument('--list', '-l', action='store_true', 
                        help='列出所有缓存文件')
    parser.add_argument('--view', '-v', type=str, metavar='FILENAME',
                        help='查看特定缓存文件内容')
    parser.add_argument('--clean', '-c', action='store_true', 
                        help='清理过期缓存')
    parser.add_argument('--dry-run', action='store_true', 
                        help='模拟运行（不实际删除文件）')
    
    args = parser.parse_args()
    
    # 根据参数执行相应操作
    if args.stats:
        show_stats()
    elif args.list:
        list_cache()
    elif args.view:
        view_cache(args.view)
    elif args.clean:
        clean_cache(dry_run=args.dry_run)
    else:
        # 默认显示统计信息
        show_stats()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
