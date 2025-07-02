# Create a 3D visualization for distributed fiber optic sensing data for microseismic events.
# Author: Kailey Dougherty
# Date created: 24-FEB-2025
# Date last modified: 02-JUL-2025

# Import needed libraries
import dash
from dash import html, dcc, Input, Output
import plotly.graph_objects as go
import pandas as pd


class DataViewer:
    """
    A class to visualize well trajectories and microseismic event data using interactive 3D Plotly figures.

    This class integrates well data and time-filtered seismic data into a single visualization.
    If a microseismic data object is provided, interactive sliders allow users to filter and display events
    based on their origin timestamps.

    Attributes
    ----------
    MSobj : object, optional
        An object representing microseismic data, expected to have 'data',
        'set_start_time', 'set_end_time', and 'create_plot' attributes/methods.
    well_objs : list, optional
        A list of Plotly-compatible 3D trace objects representing well trajectories.
    plot_objects : list
        A combined list of all Plotly trace objects to be displayed, including well and seismic traces.
    """
    def __init__(self, MS_obj=None, well_objs=None):
        """
        Initialize the DataViewer with optional well and seismic data sources.

        Parameters
        ----------
        MS_obj : object, optional
            A microseismic plotting object with a pandas 'data' attribute and methods:
            'set_start_time', 'set_end_time', and 'create_plot'.
        well_objs : list, optional
            A list of Plotly 3D trace objects providing well trajectories.
        """
        self.MSobj = MS_obj
        self.well_objs = well_objs if well_objs is not None else []
        self.plot_objects = []
        self._last_fig = None

        if well_objs is not None:
            for obj in well_objs:
                self.plot_objects.append(obj)

    def run_dash_app(self):
        """
        Run the Dash web application for visualizing microseismic and well data.
        """
        if self.MSobj is None or self.well_objs is None:
            print("Error: MSobj and well_objs must be set before running the Dash app.")
            return

        sorted_times = pd.to_datetime(self.MSobj.data['Origin DateTime']).sort_values().unique()
        min_idx = 0
        max_idx = len(sorted_times) - 1

        color_options = [
            {'label': 'Stage', 'value': 'Stage'},
            {'label': 'Brune Magnitude', 'value': 'Brune Magnitude'},
        ]

        # Compute axis ranges from the full microseismic dataset
        x_range = [self.MSobj.data['Easting (ft)'].min(), self.MSobj.data['Easting (ft)'].max()]
        y_range = [self.MSobj.data['Northing (ft)'].min(), self.MSobj.data['Northing (ft)'].max()]
        z_range = [self.MSobj.data['Depth TVDSS (ft)'].min(), self.MSobj.data['Depth TVDSS (ft)'].max()]

        app = dash.Dash(__name__)
        app.layout = html.Div([
            html.H1("Microseismic and Well Trajectory Viewer"),

            html.Label("Color points by:"),
            dcc.Dropdown(
                id='color-by-dropdown',
                options=color_options,
                value='Stage',
                clearable=False,
                style={'width': '300px'}
            ),

            html.Label("Time Range:"),
            dcc.RangeSlider(
                id='time-range-slider',
                min=min_idx,
                max=max_idx,
                value=[min_idx, max_idx],
                marks={i: str(sorted_times[i].date()) for i in range(0, len(sorted_times), max(1, len(sorted_times)//5)
                                                                     )},
                step=1,
                allowCross=False
            ),

            dcc.Graph(
                id='combined-3d-plot',
                figure=go.Figure(),
                style={'height': '600px', 'width': '90%'}
            )
        ])

        @app.callback(
            Output('combined-3d-plot', 'figure'),
            Input('color-by-dropdown', 'value'),
            Input('time-range-slider', 'value'),
            Input('combined-3d-plot', 'relayoutData')
        )
        def update_combined_plot(color_by, time_range, relayout_data):
            start_idx, end_idx = time_range
            start_time = sorted_times[min(start_idx, end_idx)]
            end_time = sorted_times[max(start_idx, end_idx)]

            # Update microseismic data
            self.MSobj.set_colorby(color_by)
            self.MSobj.set_start_time(str(start_time))
            self.MSobj.set_end_time(str(end_time))
            ms_traces = [self.MSobj.create_plot()]
            well_traces = self.well_objs if isinstance(self.well_objs, list) else [self.well_objs]

            # Combine into one figure
            fig = go.Figure(data=ms_traces + well_traces)
            fig.update_layout(
                height=700,
                width=1000,
                scene=dict(
                    xaxis_title="Easting (ft)",
                    yaxis_title="Northing (ft)",
                    zaxis_title="TVDSS (ft)",
                    xaxis=dict(range=x_range, autorange=False),
                    yaxis=dict(range=y_range, autorange=False),
                    zaxis=dict(range=z_range, autorange='reversed'),
                    aspectmode="manual",  # Set aspect mode to manual for custom aspect ratio based on data
                    aspectratio=dict(
                        x=(x_range[1] - x_range[0]) / max(x_range[1] - x_range[0], y_range[1] - y_range[0],
                                                          abs(z_range[1] - z_range[0])),
                        y=(y_range[1] - y_range[0]) / max(x_range[1] - x_range[0], y_range[1] - y_range[0],
                                                          abs(z_range[1] - z_range[0])),
                        z=abs(z_range[1] - z_range[0]) / max(x_range[1] - x_range[0], y_range[1] - y_range[0],
                                                             abs(z_range[1] - z_range[0]))
                    )
                ),
                legend=dict(
                    x=1.18,
                    y=0.5,
                    xanchor='left',
                    yanchor='top',
                    bordercolor="Black",
                    borderwidth=1,
                    bgcolor="white",
                    font=dict(size=12)
                )
            )

            # Preserve user camera
            if relayout_data and 'scene.camera' in relayout_data:
                fig.update_layout(scene_camera=relayout_data['scene.camera'])

            return fig

        host = "127.0.0.1"
        port = 8050
        print(f"Dash app running at http://{host}:{port}")

        app.run(debug=True, host=host, port=port)
