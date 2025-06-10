import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from typing import Dict, List, Any, Optional

class ChartGenerator:
    """Generate various charts using Plotly"""

    def __init__(self):
        # Color schemes
        self.color_palette = [
            '#667eea', '#764ba2', '#f093fb', '#f5576c',
            '#4ecdc4', '#44a08d', '#ffecd2', '#fcb69f',
            '#a8edea', '#fed6e3', '#ffdcd9', '#c2e59c'
        ]

        # Chart styling
        self.chart_layout = {
            'plot_bgcolor': 'rgba(0,0,0,0)',
            'paper_bgcolor': 'rgba(0,0,0,0)',
            'font': {'color': '#2c3e50', 'size': 12},
            'margin': {'l': 40, 'r': 40, 't': 60, 'b': 40}
        }

    def create_pie_chart(self, data: Dict[str, int], title: str) -> go.Figure:
        """Create a pie chart"""
        fig = go.Figure(data=[
            go.Pie(
                labels=list(data.keys()),
                values=list(data.values()),
                hole=0.3,
                marker_colors=self.color_palette[:len(data)]
            )
        ])

        fig.update_layout(
            title={
                'text': title,
                'x': 0.5,
                'font': {'size': 16, 'color': '#2c3e50'}
            },
            **self.chart_layout
        )

        return fig

    def create_bar_chart(self,
                        x_data: List[str],
                        y_data: List[int],
                        title: str,
                        x_label: str = "",
                        y_label: str = "") -> go.Figure:
        """Create a bar chart"""
        fig = go.Figure(data=[
            go.Bar(
                x=x_data,
                y=y_data,
                marker_color=self.color_palette[0],
                hovertemplate='<b>%{x}</b><br>%{y}<extra></extra>'
            )
        ])

        fig.update_layout(
            title={
                'text': title,
                'x': 0.5,
                'font': {'size': 16, 'color': '#2c3e50'}
            },
            xaxis_title=x_label,
            yaxis_title=y_label,
            **self.chart_layout
        )

        return fig

    def create_horizontal_bar_chart(self,
                                   x_data: List[int],
                                   y_data: List[str],
                                   title: str,
                                   x_label: str = "",
                                   y_label: str = "") -> go.Figure:
        """Create a horizontal bar chart"""
        fig = go.Figure(data=[
            go.Bar(
                x=x_data,
                y=y_data,
                orientation='h',
                marker_color=self.color_palette[1],
                hovertemplate='<b>%{y}</b><br>%{x}<extra></extra>'
            )
        ])

        fig.update_layout(
            title={
                'text': title,
                'x': 0.5,
                'font': {'size': 16, 'color': '#2c3e50'}
            },
            xaxis_title=x_label,
            yaxis_title=y_label,
            **self.chart_layout
        )

        return fig

    def create_histogram(self,
                        data: List[float],
                        title: str,
                        x_label: str = "",
                        y_label: str = "") -> go.Figure:
        """Create a histogram"""
        fig = go.Figure(data=[
            go.Histogram(
                x=data,
                nbinsx=30,
                marker_color=self.color_palette[2],
                opacity=0.7,
                hovertemplate='Range: %{x}<br>Count: %{y}<extra></extra>'
            )
        ])

        fig.update_layout(
            title={
                'text': title,
                'x': 0.5,
                'font': {'size': 16, 'color': '#2c3e50'}
            },
            xaxis_title=x_label,
            yaxis_title=y_label,
            **self.chart_layout
        )

        return fig

    def create_scatter_plot(self,
                           x_data: List[float],
                           y_data: List[float],
                           title: str,
                           x_label: str = "",
                           y_label: str = "",
                           hover_text: Optional[List[str]] = None) -> go.Figure:
        """Create a scatter plot"""
        fig = go.Figure(data=[
            go.Scatter(
                x=x_data,
                y=y_data,
                mode='markers',
                marker={
                    'color': self.color_palette[3],
                    'size': 8,
                    'opacity': 0.7
                },
                text=hover_text,
                hovertemplate='%{x}<br>%{y}<br>%{text}<extra></extra>' if hover_text else '%{x}<br>%{y}<extra></extra>'
            )
        ])

        fig.update_layout(
            title={
                'text': title,
                'x': 0.5,
                'font': {'size': 16, 'color': '#2c3e50'}
            },
            xaxis_title=x_label,
            yaxis_title=y_label,
            **self.chart_layout
        )

        return fig

    def create_line_chart(self,
                         x_data: List[Any],
                         y_data: List[float],
                         title: str,
                         x_label: str = "",
                         y_label: str = "") -> go.Figure:
        """Create a line chart"""
        fig = go.Figure(data=[
            go.Scatter(
                x=x_data,
                y=y_data,
                mode='lines+markers',
                line={'color': self.color_palette[4], 'width': 3},
                marker={'size': 6},
                hovertemplate='%{x}<br>%{y}<extra></extra>'
            )
        ])

        fig.update_layout(
            title={
                'text': title,
                'x': 0.5,
                'font': {'size': 16, 'color': '#2c3e50'}
            },
            xaxis_title=x_label,
            yaxis_title=y_label,
            **self.chart_layout
        )

        return fig

    def create_time_series_chart(self,
                                data: List[Dict[str, Any]],
                                title: str,
                                x_label: str = "Date",
                                y_label: str = "Count") -> go.Figure:
        """Create a time series chart"""
        dates = [item['date'] for item in data]
        values = [item['count'] for item in data]

        fig = go.Figure(data=[
            go.Scatter(
                x=dates,
                y=values,
                mode='lines+markers',
                line={'color': self.color_palette[5], 'width': 3},
                marker={'size': 6},
                fill='tonexty',
                fillcolor=f'rgba(102, 126, 234, 0.1)',
                hovertemplate='%{x}<br>Count: %{y}<extra></extra>'
            )
        ])

        fig.update_layout(
            title={
                'text': title,
                'x': 0.5,
                'font': {'size': 16, 'color': '#2c3e50'}
            },
            xaxis_title=x_label,
            yaxis_title=y_label,
            **self.chart_layout
        )

        return fig

    def create_multi_series_chart(self,
                                 data: Dict[str, List[float]],
                                 x_data: List[Any],
                                 title: str,
                                 x_label: str = "",
                                 y_label: str = "") -> go.Figure:
        """Create a multi-series line chart"""
        fig = go.Figure()

        for i, (series_name, y_values) in enumerate(data.items()):
            fig.add_trace(go.Scatter(
                x=x_data,
                y=y_values,
                mode='lines+markers',
                name=series_name,
                line={'color': self.color_palette[i % len(self.color_palette)], 'width': 2},
                marker={'size': 5},
                hovertemplate=f'{series_name}<br>%{{x}}<br>%{{y}}<extra></extra>'
            ))

        fig.update_layout(
            title={
                'text': title,
                'x': 0.5,
                'font': {'size': 16, 'color': '#2c3e50'}
            },
            xaxis_title=x_label,
            yaxis_title=y_label,
            legend={'x': 0, 'y': 1},
            **self.chart_layout
        )

        return fig

    def create_box_plot(self,
                       data: Dict[str, List[float]],
                       title: str,
                       y_label: str = "") -> go.Figure:
        """Create a box plot"""
        fig = go.Figure()

        for i, (category, values) in enumerate(data.items()):
            fig.add_trace(go.Box(
                y=values,
                name=category,
                marker_color=self.color_palette[i % len(self.color_palette)],
                hovertemplate=f'{category}<br>Value: %{{y}}<extra></extra>'
            ))

        fig.update_layout(
            title={
                'text': title,
                'x': 0.5,
                'font': {'size': 16, 'color': '#2c3e50'}
            },
            yaxis_title=y_label,
            **self.chart_layout
        )

        return fig

    def create_heatmap(self,
                      data: List[List[float]],
                      x_labels: List[str],
                      y_labels: List[str],
                      title: str) -> go.Figure:
        """Create a heatmap"""
        fig = go.Figure(data=go.Heatmap(
            z=data,
            x=x_labels,
            y=y_labels,
            colorscale='Blues',
            hovertemplate='%{x}<br>%{y}<br>Value: %{z}<extra></extra>'
        ))

        fig.update_layout(
            title={
                'text': title,
                'x': 0.5,
                'font': {'size': 16, 'color': '#2c3e50'}
            },
            **self.chart_layout
        )

        return fig

    def create_donut_chart(self,
                          data: Dict[str, int],
                          title: str,
                          center_text: str = "") -> go.Figure:
        """Create a donut chart with center text"""
        fig = go.Figure(data=[
            go.Pie(
                labels=list(data.keys()),
                values=list(data.values()),
                hole=0.5,
                marker_colors=self.color_palette[:len(data)],
                textinfo='label+percent',
                textposition='outside'
            )
        ])

        # Add center text if provided
        if center_text:
            fig.add_annotation(
                text=center_text,
                x=0.5, y=0.5,
                font_size=20,
                showarrow=False
            )

        fig.update_layout(
            title={
                'text': title,
                'x': 0.5,
                'font': {'size': 16, 'color': '#2c3e50'}
            },
            **self.chart_layout
        )

        return fig

    def create_gauge_chart(self,
                          value: float,
                          max_value: float,
                          title: str,
                          ranges: Optional[List[Dict[str, Any]]] = None) -> go.Figure:
        """Create a gauge chart"""
        if ranges is None:
            ranges = [
                {'range': [0, max_value * 0.5], 'color': "lightgray"},
                {'range': [max_value * 0.5, max_value * 0.8], 'color': "yellow"},
                {'range': [max_value * 0.8, max_value], 'color': "green"}
            ]

        fig = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=value,
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': title},
            delta={'reference': max_value * 0.5},
            gauge={
                'axis': {'range': [None, max_value]},
                'bar': {'color': self.color_palette[0]},
                'steps': [{'range': [r['range'][0], r['range'][1]], 'color': r['color']} for r in ranges],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': max_value * 0.9
                }
            }
        ))

        fig.update_layout(**self.chart_layout)

        return fig