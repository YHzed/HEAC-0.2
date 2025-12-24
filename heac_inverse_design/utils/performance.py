"""
性能优化工具

提供性能监控和优化建议。
"""

import time
from functools import wraps
from typing import Callable, Dict
import numpy as np


class PerformanceMonitor:
    """性能监控器"""
    
    def __init__(self):
        self.timings = {}
        self.call_counts = {}
    
    def time_function(self, func_name: str):
        """装饰器：测量函数执行时间"""
        def decorator(func: Callable):
            @wraps(func)
            def wrapper(*args, **kwargs):
                start = time.time()
                result = func(*args, **kwargs)
                elapsed = time.time() - start
                
                if func_name not in self.timings:
                    self.timings[func_name] = []
                    self.call_counts[func_name] = 0
                
                self.timings[func_name].append(elapsed)
                self.call_counts[func_name] += 1
                
                return result
            return wrapper
        return decorator
    
    def get_stats(self) -> Dict:
        """获取性能统计"""
        stats = {}
        for name, times in self.timings.items():
            stats[name] = {
                'calls': self.call_counts[name],
                'total_time': sum(times),
                'avg_time': np.mean(times),
                'min_time': min(times),
                'max_time': max(times),
            }
        return stats
    
    def print_report(self):
        """打印性能报告"""
        print("\n" + "=" * 60)
        print("Performance Report")
        print("=" * 60)
        
        stats = self.get_stats()
        for name, data in sorted(stats.items(), key=lambda x: x[1]['total_time'], reverse=True):
            print(f"\n{name}:")
            print(f"  Calls: {data['calls']}")
            print(f"  Total: {data['total_time']:.3f}s")
            print(f"  Avg: {data['avg_time']*1000:.1f}ms")
            print(f"  Min/Max: {data['min_time']*1000:.1f}/{data['max_time']*1000:.1f}ms")
        
        print("\n" + "=" * 60)
    
    def reset(self):
        """重置统计"""
        self.timings = {}
        self.call_counts = {}


# 全局监控器
_monitor = PerformanceMonitor()

def get_performance_monitor() -> PerformanceMonitor:
    """获取全局性能监控器"""
    return _monitor
