import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import plotly.figure_factory as ff

class Analyzer:
    def __init__(self, data_processor):
        self.dp = data_processor

    def plot_correlation_heatmap(self):
        """Generate a correlation heatmap."""
        if self.dp.data is None:
            return None
        
        # Select valid numeric columns for correlation
        df_numeric = self.dp.data.select_dtypes(include=['number'])
        
        if df_numeric.empty:
            return None
            
        corr = df_numeric.corr()
        
        fig = px.imshow(corr, text_auto=True, aspect="auto", color_continuous_scale='RdBu_r')
        fig.update_layout(title="Correlation Heatmap")
        return fig

    def plot_distribution(self, column):
        """Generate a distribution plot for a specific column."""
        if self.dp.data is None or column not in self.dp.data.columns:
            return None
        
        fig = px.histogram(self.dp.data, x=column, marginal="box", title=f"Distribution of {column}")
        return fig
    
    def plot_scatter(self, x_col, y_col, color_col=None):
        """Generate a scatter plot."""
        if self.dp.data is None:
            return None
        
        fig = px.scatter(self.dp.data, x=x_col, y=y_col, color=color_col, title=f"{x_col} vs {y_col}")
        return fig
    
    def plot_pairplot(self, columns=None, color_col=None):
        """Generate a pair plot (splom)."""
        if self.dp.data is None:
            return None
            
        if columns is None:
            columns = self.dp.data.select_dtypes(include=['number']).columns.tolist()
            # Limit to first 5 for performance if too many
            if len(columns) > 5:
                columns = columns[:5]
        
        fig = px.scatter_matrix(self.dp.data, dimensions=columns, color=color_col, title="Pair Plot")
        return fig
