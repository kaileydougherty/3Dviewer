# Create a 3D visualization for distributed fiber optic sensing data for microseismic events.
# Author: Kailey Dougherty
# Date created: 24-FEB-2025
# Date last modified: 03-JUL-2025

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
        # Check what data is available
        has_ms = self.MSobj is not None and hasattr(self.MSobj, "data") and self.MSobj.data is not None
        has_well = self.well_objs is not None and len(self.well_objs) > 0

        # If microseismic was added, prepare graph
        if has_ms:
            sorted_times = pd.to_datetime(self.MSobj.data['Origin DateTime']).sort_values().unique()
            min_idx = 0
            max_idx = len(sorted_times) - 1
            color_options = [
                {'label': 'Stage', 'value': 'Stage'},
                {'label': 'Brune Magnitude', 'value': 'Brune Magnitude'},
            ]
            x_range = [self.MSobj.data['Easting (ft)'].min(), self.MSobj.data['Easting (ft)'].max()]
            y_range = [self.MSobj.data['Northing (ft)'].min(), self.MSobj.data['Northing (ft)'].max()]
            z_range = [self.MSobj.data['Depth TVDSS (ft)'].min(), self.MSobj.data['Depth TVDSS (ft)'].max()]
        elif has_well:
            # If no microseismic object, use well data for axes ranges
            # Assume well_objs is a list of traces with x/y/z attributes
            all_x = []
            all_y = []
            all_z = []
            for trace in self.well_objs:
                all_x.extend(trace.x)
                all_y.extend(trace.y)
                all_z.extend(trace.z)
            x_range = [min(all_x), max(all_x)]
            y_range = [min(all_y), max(all_y)]
            z_range = [min(all_z), max(all_z)]
            sorted_times = []
            min_idx = 0
            max_idx = 0
            color_options = []
        else:
            print("Error: No data provided for visualization.")
            return

        app = dash.Dash(__name__)
        layout_children = [
            html.H1("Microseismic and Well Trajectory Viewer"),
        ]

        if has_ms:
            # Find all numeric columns for imaging attributes that are not coordinate-related
            numeric_cols = [col for col in self.MSobj.data.select_dtypes(include='number').columns
                            if col not in ['Easting (ft)', 'Northing (ft)', 'Depth TVDSS (ft)']]
            # Ensure current color_by is first in drop down
            color_by_default = self.MSobj.color_by
            color_options = [{'label': color_by_default, 'value': color_by_default}]
            color_options += [{'label': col, 'value': col} for col in numeric_cols if col != color_by_default]
            # Ensure current size_by is first in drop down
            size_by_default = self.MSobj.size_by
            size_options = [{'label': size_by_default, 'value': size_by_default}]
            size_options += [{'label': col, 'value': col} for col in numeric_cols if col != size_by_default]

            layout_children += [
                html.Label("Color points by:"),
                dcc.Dropdown(
                    id='color-by-dropdown',
                    options=color_options,
                    value=color_by_default,  # Default to current attribute
                    clearable=False,
                    style={'width': '300px'}
                ),
                html.Label("Size points by:"),
                dcc.Dropdown(
                    id='size-by-dropdown',
                    options=size_options,
                    value=size_by_default,  # Default to current attribute
                    clearable=False,
                    style={'width': '300px'}
                ),
                html.Label("Time Range:"),
                dcc.RangeSlider(
                    id='time-range-slider',
                    min=min_idx,
                    max=max_idx,
                    value=[min_idx, max_idx],
                    marks={i: str(sorted_times[i].date()) for i in
                           range(0, len(sorted_times), max(1, len(sorted_times)//5))} if len(sorted_times) > 0 else {},
                    step=1,
                    allowCross=False
                ),
            ]

        layout_children.append(
            dcc.Graph(
                id='combined-3d-plot',
                figure=go.Figure(),
                style={'height': '600px', 'width': '90%'}
            )
        )

        app.layout = html.Div(layout_children)

        # Callback only for microseismic data - range slider and color-by, size-by dropdowns
        if has_ms:
            @app.callback(
                Output('combined-3d-plot', 'figure'),
                Input('color-by-dropdown', 'value'),
                Input('size-by-dropdown', 'value'),
                Input('time-range-slider', 'value'),
                Input('combined-3d-plot', 'relayoutData')
            )
            def update_combined_plot(color_by, size_by, time_range, relayout_data):
                start_idx, end_idx = time_range
                start_time = sorted_times[min(start_idx, end_idx)]
                end_time = sorted_times[max(start_idx, end_idx)]

                # Update microseismic data
                self.MSobj.set_colorby(color_by)
                self.MSobj.set_sizeby(size_by)
                self.MSobj.set_start_time(str(start_time))
                self.MSobj.set_end_time(str(end_time))
                ms_traces = [self.MSobj.create_plot()]
                well_traces = self.well_objs if has_well else []

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
                        aspectmode="manual",
                        aspectratio=dict(
                            x=(x_range[1] - x_range[0]) / max(x_range[1] - x_range[0],
                                                              y_range[1] - y_range[0], abs(z_range[1] - z_range[0])),
                            y=(y_range[1] - y_range[0]) / max(x_range[1] - x_range[0],
                                                              y_range[1] - y_range[0], abs(z_range[1] - z_range[0])),
                            z=abs(z_range[1] - z_range[0]) / max(x_range[1] - x_range[0],
                                                                 y_range[1] - y_range[0], abs(z_range[1] - z_range[0]))
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
                if relayout_data and 'scene.camera' in relayout_data:
                    fig.update_layout(scene_camera=relayout_data['scene.camera'])
                return fig
        else:
            @app.callback(
                Output('combined-3d-plot', 'figure'),
                Input('combined-3d-plot', 'relayoutData')
            )
            def update_combined_plot(relayout_data):
                well_traces = self.well_objs if has_well else []
                fig = go.Figure(data=well_traces)
                # Set layout to be consistent
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
                        aspectmode="manual",
                        aspectratio=dict(
                            x=(x_range[1] - x_range[0]) / max(x_range[1] - x_range[0],
                                                              y_range[1] - y_range[0], abs(z_range[1] - z_range[0])),
                            y=(y_range[1] - y_range[0]) / max(x_range[1] - x_range[0],
                                                              y_range[1] - y_range[0], abs(z_range[1] - z_range[0])),
                            z=abs(z_range[1] - z_range[0]) / max(x_range[1] - x_range[0],
                                                                 y_range[1] - y_range[0], abs(z_range[1] - z_range[0]))
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
                # Preserve camera settings
                if relayout_data and 'scene.camera' in relayout_data:
                    fig.update_layout(scene_camera=relayout_data['scene.camera'])
                return fig

        host = "127.0.0.1"
        port = 8050
        print(f"Dash app running at http://{host}:{port}")

        app.run(debug=True, host=host, port=port)
