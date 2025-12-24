"""
批量设计引擎

支持一次性运行多组设计任务。
"""

from typing import List, Dict
import pandas as pd
from .inverse_designer import InverseDesigner, DesignSolution


class BatchDesignTask:
    """单个批量设计任务"""
    
    def __init__(self, 
                 task_id: int,
                 name: str,
                 hv_range: tuple,
                 kic_range: tuple,
                 **kwargs):
        self.task_id = task_id
        self.name = name
        self.hv_range = hv_range
        self.kic_range = kic_range
        self.kwargs = kwargs
        self.solutions = []
        self.status = 'Pending'
        self.error = None
    
    def to_dict(self) -> Dict:
        return {
            'task_id': self.task_id,
            'name': self.name,
            'hv_min': self.hv_range[0],
            'hv_max': self.hv_range[1],
            'kic_min': self.kic_range[0],
            'kic_max': self.kic_range[1],
            'num_solutions': len(self.solutions),
            'status': self.status
        }


class BatchDesigner:
    """批量设计引擎"""
    
    def __init__(self, designer: InverseDesigner):
        """
        初始化批量设计器
        
        Args:
            designer: InverseDesigner实例
        """
        self.designer = designer
        self.tasks = []
    
    def add_task_from_csv(self, csv_path: str) -> int:
        """
        从CSV文件添加任务
        
        CSV格式:
        Name,HV_Min,HV_Max,KIC_Min,KIC_Max
        Task1,1500,2000,8,12
        Task2,1700,1900,10,15
        
        Args:
            csv_path: CSV文件路径
            
        Returns:
            添加的任务数
        """
        df = pd.read_csv(csv_path)
        
        for idx, row in df.iterrows():
            task = BatchDesignTask(
                task_id=len(self.tasks) + 1,
                name=row.get('Name', f'Task_{idx+1}'),
                hv_range=(row['HV_Min'], row['HV_Max']),
                kic_range=(row['KIC_Min'], row['KIC_Max'])
            )
            self.tasks.append(task)
        
        return len(df)
    
    def add_task_from_dataframe(self, df: pd.DataFrame) -> int:
        """
        从DataFrame添加任务
        
        Args:
            df: 包含任务定义的DataFrame
            
        Returns:
            添加的任务数
        """
        for idx, row in df.iterrows():
            task = BatchDesignTask(
                task_id=len(self.tasks) + 1,
                name=row.get('Name', f'Task_{idx+1}'),
                hv_range=(row['HV_Min'], row['HV_Max']),
                kic_range=(row['KIC_Min'], row['KIC_Max'])
            )
            self.tasks.append(task)
        
        return len(df)
    
    def run_all(self, 
                allowed_elements: List[str],
                **common_params) -> pd.DataFrame:
        """
        运行所有任务
        
        Args:
            allowed_elements: 允许的元素列表
            **common_params: 公共参数（陶瓷类型、工艺范围等）
            
        Returns:
            汇总结果DataFrame
        """
        results = []
        
        for task in self.tasks:
            print(f"Running {task.name}...")
            task.status = 'Running'
            
            try:
                solutions = self.designer.design(
                    target_hv_range=task.hv_range,
                    target_kic_range=task.kic_range,
                    allowed_elements=allowed_elements,
                    **common_params
                )
                
                task.solutions = solutions
                task.status = 'Completed'
                
                # 提取最佳解
                if solutions:
                    best_sol = solutions[0]
                    results.append({
                        'Task': task.name,
                        'Target_HV': f"{task.hv_range[0]}-{task.hv_range[1]}",
                        'Target_KIC': f"{task.kic_range[0]}-{task.kic_range[1]}",
                        'Best_HV': best_sol.predicted_hv,
                        'Best_KIC': best_sol.predicted_kic,
                        'Num_Solutions': len(solutions),
                        'Status': 'OK'
                    })
                else:
                    results.append({
                        'Task': task.name,
                        'Target_HV': f"{task.hv_range[0]}-{task.hv_range[1]}",
                        'Target_KIC': f"{task.kic_range[0]}-{task.kic_range[1]}",
                        'Best_HV': None,
                        'Best_KIC': None,
                        'Num_Solutions': 0,
                        'Status': 'No solutions found'
                    })
                    
            except Exception as e:
                task.status = 'Failed'
                task.error = str(e)
                results.append({
                    'Task': task.name,
                    'Target_HV': f"{task.hv_range[0]}-{task.hv_range[1]}",
                    'Target_KIC': f"{task.kic_range[0]}-{task.kic_range[1]}",
                    'Best_HV': None,
                    'Best_KIC': None,
                    'Num_Solutions': 0,
                    'Status': f'Error: {str(e)}'
                })
        
        return pd.DataFrame(results)
    
    def get_all_solutions(self) -> List[DesignSolution]:
        """获取所有任务的所有解"""
        all_solutions = []
        for task in self.tasks:
            all_solutions.extend(task.solutions)
        return all_solutions
    
    def export_all_solutions(self, filename: str):
        """
        导出所有解到CSV
        
        Args:
            filename: 输出文件名
        """
        from ..ui.visualizations import export_solutions_to_csv
        
        all_sols = self.get_all_solutions()
        csv_data = export_solutions_to_csv(all_sols)
        
        with open(filename, 'w') as f:
            f.write(csv_data)
