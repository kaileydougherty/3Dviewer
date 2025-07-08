# Create a 3D visualization for distributed fiber optic sensing data for microseismic events.
# Author: Kailey Dougherty
# Date created: 24-FEB-2025
# Date last modified: 08-JUL-2025

# Import needed libraries
import dash
from dash import html, dcc, Input, Output
import plotly.graph_objects as go
import pandas as pd
import numpy as np


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
        # NOTE: checkpoint - troubleshooting
        print("Dash app started")

        # Check what data is available
        has_ms = self.MSobj is not None
        has_well = self.well_objs is not None and len(self.well_objs) > 0

        # If microseismic was added, prepare graph
        if self.MSobj is not None:

            # Set number of labels for the time range slider, always include first and last
            num_labels = 5  # NOTE: Could make this an attribute to allow user customization

            df = self.MSobj.data.copy()

            # Consistently sort and reset index for times
            sorted_times = pd.to_datetime(df['Origin DateTime']).sort_values().reset_index(drop=True)

            # Determine start and end times
            if self.MSobj.plot_start_time is not None:
                start_time = pd.to_datetime(self.MSobj.plot_start_time)
            else:
                start_time = sorted_times.min() if len(sorted_times) > 0 else None

            if self.MSobj.plot_end_time is not None:
                end_time = pd.to_datetime(self.MSobj.plot_end_time)
            else:
                end_time = sorted_times.max() if len(sorted_times) > 0 else None

            # Find indices for the selected range
            start_idx = int(np.searchsorted(sorted_times, start_time, side='left'))
            end_idx = int(np.searchsorted(sorted_times, end_time, side='right') - 1)

            # Clamp indices to valid range
            start_idx = max(0, min(start_idx, len(sorted_times) - 1))
            end_idx = max(0, min(end_idx, len(sorted_times) - 1))

            # Now do the filtering
            df_filtered = df[(sorted_times >= sorted_times[start_idx]) & (sorted_times <= sorted_times[end_idx])]

            times_filtered = pd.to_datetime(df_filtered['Origin DateTime'])

            if len(times_filtered) > 0:
                step = max(1, (len(times_filtered) - 1) // (num_labels - 1))
                marks = {i: times_filtered.iloc[i].strftime("%Y-%m-%d %H:%M:%S")
                         for i in range(0, len(times_filtered), step)}
                # Ensure first and last always included
                marks[0] = times_filtered.iloc[0].strftime("%Y-%m-%d %H:%M:%S")
                marks[len(times_filtered) - 1] = times_filtered.iloc[-1].strftime("%Y-%m-%d %H:%M:%S")
            else:
                marks = {}

            x_range = [self.MSobj.data['Easting (ft)'].min(), self.MSobj.data['Easting (ft)'].max()]
            y_range = [self.MSobj.data['Northing (ft)'].min(), self.MSobj.data['Northing (ft)'].max()]
            z_range = [self.MSobj.data['Depth TVDSS (ft)'].min(), self.MSobj.data['Depth TVDSS (ft)'].max()]

            # Find all numeric columns for imaging attributes that are not coordinate-related
            numeric_cols = [col for col in self.MSobj.data.select_dtypes(include='number').columns
                            if col not in ['Easting (ft)', 'Northing (ft)', 'Depth TVDSS (ft)']]
            # Ensure current color_by is first in dropdown
            color_by_default = self.MSobj.color_by
            color_options = [{'label': color_by_default, 'value': color_by_default}]
            color_options += [{'label': col, 'value': col} for col in numeric_cols if col != color_by_default]
            # Ensure current size_by is first in dropdown
            size_by_default = self.MSobj.size_by
            size_options = [{'label': size_by_default, 'value': size_by_default}]
            size_options += [{'label': col, 'value': col} for col in numeric_cols if col != size_by_default]

        elif has_well and not has_ms:
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
            color_options = []

        else:
            print("Error: No data provided for visualization.")
            return

        app = dash.Dash(__name__)
        layout_children = [
            html.H1("Microseismic and Well Trajectory Viewer"),
        ]

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
                    min=0,
                    max=len(times_filtered) - 1,
                    value=[0, len(times_filtered) - 1],
                    marks=marks,
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
                # NOTE: CHECKPOINT for callback - troubleshooting
                print("Dash callback triggered")
                # Consistently sort and reset index for times in the callback
                sorted_times = pd.to_datetime(self.MSobj.data['Origin DateTime']).sort_values().reset_index(drop=True)
                x_range = [self.MSobj.data['Easting (ft)'].min(), self.MSobj.data['Easting (ft)'].max()]
                y_range = [self.MSobj.data['Northing (ft)'].min(), self.MSobj.data['Northing (ft)'].max()]
                z_range = [self.MSobj.data['Depth TVDSS (ft)'].min(), self.MSobj.data['Depth TVDSS (ft)'].max()]
                has_well = self.well_objs is not None and len(self.well_objs) > 0

                if not sorted_times.any() or len(sorted_times) == 0:
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
                                                                  y_range[1] - y_range[0],
                                                                  abs(z_range[1] - z_range[0])),
                                y=(y_range[1] - y_range[0]) / max(x_range[1] - x_range[0],
                                                                  y_range[1] - y_range[0],
                                                                  abs(z_range[1] - z_range[0])),
                                z=abs(z_range[1] - z_range[0]) / max(x_range[1] - x_range[0],
                                                                     y_range[1] - y_range[0],
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
                    if relayout_data and 'scene.camera' in relayout_data:
                        fig.update_layout(scene_camera=relayout_data['scene.camera'])
                    return fig

                start_idx, end_idx = time_range
                start_idx = max(0, min(start_idx, len(sorted_times) - 1))
                end_idx = max(0, min(end_idx, len(sorted_times) - 1))
                start_time = sorted_times[min(start_idx, end_idx)]
                end_time = sorted_times[max(start_idx, end_idx)]

                # NOTE: CHECKPOINT for sliders - troubleshooting
                print(f"Slider start_time: {start_time}")
                print(f"Slider end_time: {end_time}")

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
                # NOTE: Checkpoint for traces - troubleshooting
                print("Microseismic trace:", ms_traces)
                print("Well traces:", well_traces)
                print("Figure data:", fig.data)
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

                # NOTE: Checkpoint for traces - troubleshooting
                print("Figure data:", fig.data)
                return fig

        # NOTE: Checkpoint for sliders - troubleshooting
        print(f"Data min time: {self.MSobj.data['Origin DateTime'].min()}")
        print(f"Data max time: {self.MSobj.data['Origin DateTime'].max()}")

        host = "127.0.0.1"
        port = 8050
        print(f"Dash app running at http://{host}:{port}")

        app.run(debug=True, host=host, port=port)
