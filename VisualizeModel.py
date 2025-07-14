# Create a 3D visualization for distributed fiber optic sensing data for microseismic events.
# Author: Kailey Dougherty
# Date created: 24-FEB-2025
# Date last modified: 14-JUL-2025

# Import needed libraries
import dash
from dash import html, dcc, Input, Output
import plotly.graph_objects as go
import pandas as pd
import numpy as np


class DataViewer:
    """
    A class to visualize well trajectories and microseismic event data using interactive 3D Plotly figures.

    This class integrates well data and time-filtered seismic data into a single visualization through Plotly Dash.

    Attributes
    ----------
    MSobj : object, optional
        An object representing microseismic data, expected to have 'data',
        'set_start_time', 'set_end_time', and 'create_plot' attributes/methods.

    well_objs : list, optional
        A list of Plotly-compatible 3D trace objects representing well trajectories.

    plot_objects : list
        A combined list of all Plotly trace objects to be displayed, including well and seismic traces.

    _last_fig : object
        Stores the last generated Plotly figure for reference to preserve user settings in dynamic updates.

    title : str, optional
        The title of the visualization, default is 'Seismic and Well Trajectory Viewer'.

    Methods
    -------
    __init__(self, MS_obj=None, well_objs=None)
        Initialize the DataViewer with optional well and microseismic data sources.

    set_title(title)
        Set the title for the visualization. Default is 'Seismic and Well Trajectory Viewer.'

    run_dash_app()
        Runs the Dash web application for visualizing microseismic and well data.
        Provides interactive controls for filtering by time, color, size, axis ranges, and aspect ratio.
        Preserves user camera/zoom settings between updates.
    """
    def __init__(self, MS_obj=None, well_objs=None):
        """
        Initialize the DataViewer with optional well and microseismic data sources.

        Parameters
        ----------
        MS_obj : object, optional
            A microseismic plotting object with a pandas 'data' attribute and methods:
            'set_start_time', 'set_end_time', and 'create_plot.'

        well_objs : list, optional
            A list of Plotly 3D trace objects providing well trajectories.
        """
        self.MSobj = MS_obj
        self.well_objs = well_objs if well_objs is not None else []
        self.plot_objects = []
        self._last_fig = None
        self.title = 'Seismic and Well Trajectory Viewer'

        if well_objs is not None:
            for obj in well_objs:
                self.plot_objects.append(obj)

    def set_title(self, title):
        self.title = title

    def run_dash_app(self):
        """
        Run the Dash web application for visualizing microseismic and well data.

        The app provides:
        - Interactive dropdowns for color and size attributes.
        - A time range slider to filter events by timestamp.
        - Dynamic display of the selected time range.
        - Inputs for axis ranges and aspect ratio.
        - A 3D Plotly graph showing microseismic events and well trajectories.
        - Preservation of user camera/zoom settings between updates.

        Returns
        -------
        None
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
                start_time = pd.to_datetime(self.MSobj.plot_start_time)  # Make start user defined
            else:
                start_time = sorted_times.min() if len(sorted_times) > 0 else None  # Use all data otherwise

            if self.MSobj.plot_end_time is not None:
                end_time = pd.to_datetime(self.MSobj.plot_end_time)  # Make end user defined
            else:
                end_time = sorted_times.max() if len(sorted_times) > 0 else None  # Use all data otherwise

            # Find indices for the selected range
            start_idx = int(np.searchsorted(sorted_times, start_time, side='left'))
            end_idx = int(np.searchsorted(sorted_times, end_time, side='right') - 1)

            # Clamp indices to valid range
            start_idx = max(0, min(start_idx, len(sorted_times) - 1))
            end_idx = max(0, min(end_idx, len(sorted_times) - 1))

            # Filter the dataframe based on found range
            df_filtered = df[(sorted_times >= sorted_times[start_idx]) & (sorted_times <= sorted_times[end_idx])]

            # Convert to datetime
            times_filtered = pd.to_datetime(df_filtered['Origin DateTime'])

            # Create the time range slider labels
            if len(times_filtered) > 0:
                step = max(1, (len(times_filtered) - 1) // (num_labels - 1))
                marks = {i: times_filtered.iloc[i].strftime("%Y-%m-%d %H:%M:%S")
                         for i in range(0, len(times_filtered), step)}
                # Ensure first and last always included
                marks[0] = times_filtered.iloc[0].strftime("%Y-%m-%d %H:%M:%S")
            else:
                marks = {}

            # Grab the starting axes range by using the min. and max. of microseismic data
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

            # Define placeholders for the colorbar input field
            colorbar_min_placeholder = None
            colorbar_max_placeholder = None
            if color_by_default in df.columns:
                colorbar_min_placeholder = float(df_filtered[color_by_default].min())
                colorbar_max_placeholder = float(df_filtered[color_by_default].max())

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
            html.H1(self.title, style={'textAlign': 'center', 'marginBottom': '30px'}),

            # Group color-by, colorscale, and colorbar range dropdowns in a flex row
            html.Div([
                html.Label("Color points by:", style={'marginRight': '8px'}),
                dcc.Dropdown(
                    id='color-by-dropdown',
                    options=color_options,
                    value=color_by_default,
                    clearable=False,
                    style={'width': '200px', 'marginRight': '20px'}
                ),
                html.Label("Colorscale:", style={'marginRight': '8px'}),
                dcc.Dropdown(
                    id='colorscale-dropdown',
                    options=[
                        {'label': 'Viridis', 'value': 'Viridis'},
                        {'label': 'Cividis', 'value': 'Cividis'},
                        {'label': 'Plasma', 'value': 'Plasma'},
                        {'label': 'Inferno', 'value': 'Inferno'},
                        {'label': 'Magma', 'value': 'Magma'},
                        {'label': 'Rainbow', 'value': 'Rainbow'}
                    ],
                    value=self.MSobj.color_scale,
                    clearable=False,
                    style={'width': '200px', 'marginRight': '20px'}
                ),
                html.Label("Colorbar Range:", style={'marginRight': '8px'}),
                dcc.Input(
                    id='colorbar-min', type='number',
                    placeholder=f"{colorbar_min_placeholder:.2f}" if colorbar_min_placeholder is not None else
                    "Auto min",
                    style={'width': '100px', 'marginRight': '4px'},
                    debounce=True
                ),
                dcc.Input(
                    id='colorbar-max', type='number',
                    placeholder=f"{colorbar_max_placeholder:.2f}" if colorbar_max_placeholder is not None else
                    "Auto max",
                    style={'width': '100px', 'marginRight': '20px'},
                    debounce=True
                ),
            ], style={'display': 'flex', 'alignItems': 'center', 'marginBottom': '16px'}),

            html.Div([
                html.Label("Size points by:", style={'marginRight': '8px'}),
                dcc.Dropdown(
                    id='size-by-dropdown',
                    options=size_options,
                    value=size_by_default,
                    clearable=False,
                    style={'width': '200px', 'marginRight': '20px'}
                )
            ], style={'display': 'flex', 'alignItems': 'center', 'marginBottom': '16px'}),

            # Insert slider range output message
            html.Div(
                id='slider-range-output',
                style={'fontWeight': 'normal', 'whiteSpace': 'nowrap', 'marginBottom': '16px'}
            ),

            # Show time range slider
            html.Label("Time Range:"),
            html.Div(
                dcc.RangeSlider(
                    id='time-range-slider',
                    min=0,
                    max=len(times_filtered) - 1,
                    value=[0, len(times_filtered) - 1],
                    marks=marks,
                    step=1,
                    allowCross=False
                ),
                style={
                    'width': '92%',
                    'margin': '20px auto',
                    'padding': '20px',
                    'fontSize': '16px',
                    'whiteSpace': 'nowrap'
                }
            ),

            # Group input fields for x-, y-, z- ranges and dropdown for aspect ratio mode in a flex row
            html.Div([
                html.Label("X Range: "),
                dcc.Input(id='x-min', type='number', placeholder=f"{x_range[0]:.2f}",
                          style={'width': '100px'}, debounce=True),
                dcc.Input(id='x-max', type='number', placeholder=f"{x_range[1]:.2f}",
                          style={'width': '100px'}, debounce=True),
                html.Label("Y Range: ", style={'marginLeft': '20px'}),
                dcc.Input(id='y-min', type='number', placeholder=f"{y_range[0]:.2f}",
                          style={'width': '100px'}, debounce=True),
                dcc.Input(id='y-max', type='number', placeholder=f"{y_range[1]:.2f}",
                          style={'width': '100px'}, debounce=True),
                html.Label("Z Range: ", style={'marginLeft': '20px'}),
                dcc.Input(id='z-min', type='number', placeholder=f"{z_range[1]:.2f}",
                          style={'width': '100px'}, debounce=True),
                dcc.Input(id='z-max', type='number', placeholder=f"{z_range[0]:.2f}",
                          style={'width': '100px'}, debounce=True),
                html.Label("Aspect Ratio Mode:", style={'marginLeft': '20px', 'marginRight': '8px'}),
                dcc.Dropdown(
                    id='aspectmode-dropdown',
                    options=[
                        {'label': 'Manual', 'value': 'manual'},
                        {'label': 'Cube', 'value': 'cube'},
                        {'label': 'Data', 'value': 'data'},
                        {'label': 'Auto', 'value': 'auto'}
                    ],
                    value='manual',
                    clearable=False,
                    style={'width': '150px', 'marginRight': '20px'}
                ),
            ], style={'margin': '10px 0', 'display': 'flex', 'alignItems': 'center'}),

            dcc.Graph(
                id='combined-3d-plot',
                figure=go.Figure(),
                style={'height': '600px', 'width': '90%'}
            )
        ]

        app.layout = html.Div(layout_children)

        # Callback only for microseismic data to update the plot dynamically
        if has_ms:
            @app.callback(
                Output('combined-3d-plot', 'figure'),
                Input('color-by-dropdown', 'value'),
                Input('size-by-dropdown', 'value'),
                Input('time-range-slider', 'value'),
                Input('combined-3d-plot', 'relayoutData'),
                Input('x-min', 'value'),
                Input('x-max', 'value'),
                Input('y-min', 'value'),
                Input('y-max', 'value'),
                Input('z-min', 'value'),
                Input('z-max', 'value'),
                Input('colorscale-dropdown', 'value'),
                Input('colorbar-min', 'value'),
                Input('colorbar-max', 'value'),
                Input('aspectmode-dropdown', 'value'),
            )
            def update_combined_plot(
                color_by, size_by, time_range, relayout_data, x_min, x_max,
                y_min, y_max, z_min, z_max, colorscale, colorbar_min, colorbar_max,
                aspect_mode
            ):

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

                # Set new start and end based on slider movement
                start_idx, end_idx = time_range  # Unpack the slider values
                # Clamp indices to valid range
                start_idx = max(0, min(start_idx, len(sorted_times) - 1))
                end_idx = max(0, min(end_idx, len(sorted_times) - 1))
                # Extract times from sorted list
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
                self.MSobj.set_colorscale(colorscale)
                # Set colorbar range if both min. and max. are provided, otherwise set as auto
                if colorbar_min is not None and colorbar_max is not None:
                    self.MSobj.set_colorbar_range([colorbar_min, colorbar_max])
                else:
                    self.MSobj.set_colorbar_range(None)
                ms_traces = [self.MSobj.create_plot()]
                well_traces = self.well_objs if has_well else []

                # Update the x-, y-, z- ranges based on user input or defaults
                # Use user input if provided, otherwise use auto-calculated defaults
                x_range_plot = [x_min if x_min is not None else x_range[0],
                                x_max if x_max is not None else x_range[1]]
                y_range_plot = [y_min if y_min is not None else y_range[0],
                                y_max if y_max is not None else y_range[1]]
                z_range_plot = [z_min if z_min is not None else z_range[0],
                                z_max if z_max is not None else z_range[1]]

                # Reverse z-axis to align with TVDSS convention
                z_range_plot = sorted(z_range_plot, reverse=True)  # allows user input in dash app

                # Update figure with new traces
                fig = go.Figure(data=ms_traces + well_traces)
                fig.update_layout(
                    height=700,
                    width=1000,
                    scene=dict(
                        xaxis_title="Easting (ft)",
                        yaxis_title="Northing (ft)",
                        zaxis_title="TVDSS (ft)",
                        xaxis=dict(range=x_range_plot, autorange=False),
                        yaxis=dict(range=y_range_plot, autorange=False),
                        zaxis=dict(range=z_range_plot, autorange=False),
                        aspectmode=aspect_mode,  # Use the selected aspect mode
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
                fig.layout.uirevision = None

                # Only update camera from relayout_data
                if relayout_data and 'scene.camera' in relayout_data:
                    fig.update_layout(scene_camera=relayout_data['scene.camera'])

                return fig

            # Update time range message based on slider movement
            @app.callback(
                Output('slider-range-output', 'children'),
                Input('time-range-slider', 'value')
            )
            def update_slider_output(time_range):
                start_idx, end_idx = time_range
                start_time = sorted_times[min(start_idx, end_idx)]
                end_time = sorted_times[max(start_idx, end_idx)]
                return f"Selected time range: {start_time} to {end_time}"

        else:
            # If no microseismic data, just plot well traces
            @app.callback(
                Output('combined-3d-plot', 'figure'),
                Input('combined-3d-plot', 'relayoutData')
            )
            # Update the layout based on user input
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

        # NOTE: Checkpoint for sliders - troubleshooting
        print(f"Data min time: {self.MSobj.data['Origin DateTime'].min()}")
        print(f"Data max time: {self.MSobj.data['Origin DateTime'].max()}")

        # Define host and port
        host = "127.0.0.1"
        port = 8050
        print(f"Dash app running at http://{host}:{port}")

        # Run the app with specified host and port
        app.run(debug=True, host=host, port=port)
