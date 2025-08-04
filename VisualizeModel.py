# Create a 3D visualization to show distributed acoustic sensing data and microseismic events with well trajectories.
# Author: Kailey Dougherty
# Date created: 24-FEB-2025
# Date last modified: 04-AUG-2025

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

    DASobj : object, optional
        A Plotly Scatter3d trace object for DAS data visualization.

    DAS_image : str, optional
        Base64 encoded image string for DAS waterfall plot.

    DAS_viewer : object, optional
        The DAS plotting object containing the loaded DAS data for time slicing.

    well_trajectory_path : str, optional
        Path to the well trajectory CSV file for DAS 3D plotting.

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
    def __init__(self, MS_obj=None, well_objs=None, DAS_obj=None, DAS_image=None,
                 DAS_viewer=None, well_trajectory_path=None):
        """
        Initialize the DataViewer with optional well and microseismic data sources.

        Parameters
        ----------
        MS_obj : object, optional
            A microseismic plotting object with a pandas 'data' attribute and methods:
            'set_start_time', 'set_end_time', and 'create_plot.'

        well_objs : list, optional
            A list of Plotly 3D trace objects providing well trajectories.

        DAS_obj : object, optional
            A Plotly Scatter3d trace object for DAS data visualization.

        DAS_image : str, optional
            Base64 encoded image string for DAS waterfall plot.

        DAS_viewer : object, optional
            The DAS plotting object containing the loaded DAS data for time slicing.

        well_trajectory_path : str, optional
            Path to the well trajectory CSV file for DAS 3D plotting.
        """
        self.MSobj = MS_obj
        self.well_objs = well_objs if well_objs is not None else []
        self.DASobj = DAS_obj
        self.DASimage = DAS_image
        self.DASviewer = DAS_viewer
        self.well_trajectory_path = well_trajectory_path
        self.plot_objects = []
        self._last_fig = None
        self.title = '3DViewer'

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
        has_das = self.DASviewer is not None

        # For TROUBLESHOOTING
        print("Data availability check:")
        print(f"  - Microseismic: {has_ms}")
        print(f"  - Wells: {has_well}")
        print(f"  - DAS viewer: {has_das}")
        print(f"  - DAS viewer type: {type(self.DASviewer)}")

        # Get DAS time information if available
        das_times = []
        if has_das and self.DASviewer is not None and hasattr(self.DASviewer, 'data'):
            try:
                das_times = self.DASviewer.data.taxis  # Get time axis from DAS data
                print(f"DAS time range: {das_times[0]} to {das_times[-1]} ({len(das_times)} time steps)")
            except AttributeError as e:
                print(f"Warning: Could not access DAS time axis: {e}")
                has_das = False
        else:
            print("DAS viewer not available or doesn't have data attribute")

        # If microseismic was added, prepare graph
        if self.MSobj is not None:

            # Prepare ms range slider
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

            # Prepare axes based on data
            # Grab the starting axes range by using the min. and max. of microseismic data
            x_range = [self.MSobj.data['Easting (ft)'].min(), self.MSobj.data['Easting (ft)'].max()]
            y_range = [self.MSobj.data['Northing (ft)'].min(), self.MSobj.data['Northing (ft)'].max()]
            z_range = [self.MSobj.data['TVDSS (ft)'].min(), self.MSobj.data['TVDSS (ft)'].max()]

            # Prepare dropdowns based on data
            # Find all numeric columns for imaging attributes that are not coordinate-related
            numeric_cols = [col for col in self.MSobj.data.select_dtypes(include='number').columns
                            if col not in ['Easting (ft)', 'Northing (ft)', 'TVDSS (ft)']]
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

        else:
            print("Error: No data provided for visualization.")
            return

        app = dash.Dash(__name__, suppress_callback_exceptions=True)

        layout_children = [
            html.H1(self.title, style={'textAlign': 'center', 'marginBottom': '30px'}),
        ]

        # Add informational message if only wells are available
        if has_well and not has_ms and not has_das:
            layout_children.append(
                html.Div([
                    html.P("Displaying well trajectories only. No microseismic or DAS data available.",
                           style={'textAlign': 'center', 'fontStyle': 'italic', 'color': '#666'})
                ], style={'marginBottom': '20px'})
            )

        # Only add microseismic controls if MS data is available
        if has_ms:
            layout_children.extend([
                html.Div(
                    children="Microseismic Events",
                    style={'fontWeight': 'normal', 'whiteSpace': 'nowrap', 'marginBottom': '16px'}
                ),
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
                html.Div(
                    dcc.RangeSlider(
                        id='ms-time-slider',
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
            ])

        # Conditionally add DAS slider if DAS data is available
        if has_das and len(das_times) > 0:
            # If microseismic data is available, sync DAS slider range with MS time range
            if has_ms and len(times_filtered) > 0:
                # Map DAS times to match microseismic time indices
                das_time_min = 0
                das_time_max = len(times_filtered) - 1
                das_time_step = 1

                # Create marks that correspond to microseismic time indices
                das_marks = {}
                step_size = max(1, len(times_filtered) // 10)  # Show max 10 marks
                for i in range(0, len(times_filtered), step_size):
                    try:
                        # Use the same datetime formatting as microseismic
                        time_str = times_filtered.iloc[i].strftime("%m-%d %H:%M")
                        das_marks[i] = time_str
                    except (ValueError, OSError, AttributeError):
                        das_marks[i] = f"Index {i}"

                # Ensure first and last marks are included
                if 0 not in das_marks:
                    das_marks[0] = times_filtered.iloc[0].strftime("%m-%d %H:%M")
                if (len(times_filtered) - 1) not in das_marks:
                    das_marks[len(times_filtered) - 1] = times_filtered.iloc[-1].strftime("%m-%d %H:%M")
            else:
                # Fall back to original DAS time range if no microseismic data
                das_time_min = float(das_times[0])
                das_time_max = float(das_times[-1])
                das_time_step = float(das_times[1] - das_times[0]) if len(das_times) > 1 else 1.0

                # Create marks with actual DAS time values
                das_marks = {}
                max_marks = 10  # Maximum number of marks to display
                step_size = max(1, len(das_times) // max_marks)

                for i in range(0, len(das_times), step_size):
                    try:
                        from datetime import timedelta
                        # Convert time offset to actual datetime
                        actual_datetime = self.DASviewer.data.start_time + timedelta(seconds=das_times[i])
                        das_marks[float(das_times[i])] = actual_datetime.strftime("%m-%d %H:%M")
                    except (ValueError, OSError, AttributeError):
                        das_marks[float(das_times[i])] = f"{das_times[i]:.2f}s"

            if has_das:
                layout_children.extend([
                    html.Div(
                        children="Distributed Acoustic Sensing (DAS) Data",
                        style={'fontWeight': 'normal', 'whiteSpace': 'nowrap', 'marginBottom': '16px'}
                    ),
                    # DAS colorscale and colorbar range controls
                    html.Div([
                        html.Label("Colorscale:", style={'marginRight': '8px'}),
                        dcc.Dropdown(
                            id='das-colorscale-dropdown',
                            options=[
                                {'label': 'RdBu', 'value': 'RdBu'},
                                {'label': 'Spectral', 'value': 'Spectral'},
                                {'label': 'Coolwarm', 'value': 'Coolwarm'},
                                {'label': 'Seismic', 'value': 'Seismic'},
                                {'label': 'Berlin', 'value': 'Berlin'},
                            ],
                            value=(self.DASviewer.color_scale
                                   if self.DASviewer and hasattr(self.DASviewer, 'color_scale')
                                   else 'RdBu'),
                            clearable=False,
                            style={'width': '200px', 'marginRight': '20px'}
                        ),
                        html.Label("Colorbar Range:", style={'marginRight': '8px'}),
                        dcc.Input(
                            id='das-colorbar-min', type='number',
                            placeholder="Auto min",
                            style={'width': '100px', 'marginRight': '4px'},
                            debounce=True
                        ),
                        dcc.Input(
                            id='das-colorbar-max', type='number',
                            placeholder="Auto max",
                            style={'width': '100px', 'marginRight': '20px'},
                            debounce=True
                        ),
                    ], style={'display': 'flex', 'alignItems': 'center', 'marginBottom': '16px'}),
                    html.Div(
                        id='das-time-output',
                        style={'fontWeight': 'normal', 'whiteSpace': 'nowrap', 'marginBottom': '8px'}
                    ),
                    html.Div(
                        dcc.Slider(
                            id='das-time-slider',
                            min=das_time_min,
                            max=das_time_max,
                            value=das_time_min,
                            marks=das_marks,
                            step=das_time_step,
                            tooltip={"placement": "bottom", "always_visible": True}
                        ),
                        style={
                            'width': '92%',
                            'margin': '20px auto',
                            'padding': '20px',
                            'fontSize': '16px',
                            'whiteSpace': 'nowrap'
                        }
                    ),
                ])

        # Continue with the rest of the layout
        layout_children.extend([
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
        ])

        # Add DAS image layout based on data availability
        if has_das and self.DASimage:
            # Main row for 3D plot and DAS image using grid layout
            layout_children.append(
                html.Div(
                    [
                        dcc.Graph(
                            id='combined-3d-plot',
                            figure=go.Figure(),
                            style={'height': '600px', 'width': '100%'}
                        ),
                        html.Div([
                            html.H2("DAS", style={'textAlign': 'center'}),
                            html.Img(src=self.DASimage, id='das-image', style={
                                'width': '500px', 'height': '400px', 'display': 'block', 'margin': 'auto'
                            })
                        ], style={'width': '85%', 'display': 'flex', 'flexDirection': 'column', 'alignItems': 'center'})
                    ],
                    style={
                        'display': 'grid',
                        'gridTemplateColumns': '3fr 2fr',  # 3:2 width ratio for plot:image
                        'gap': '20px',
                        'alignItems': 'start',
                        'marginTop': '20px'
                    }
                )
            )
        else:
            # Simple layout with just the 3D plot when no DAS image
            layout_children.append(
                html.Div([
                    dcc.Graph(
                        id='combined-3d-plot',
                        figure=go.Figure(),
                        style={'height': '600px', 'width': '100%'}
                    )
                ], style={'marginTop': '20px'})
            )

        app.layout = html.Div(layout_children)

        # Single callback for the 3D plot
        @app.callback(
            Output('combined-3d-plot', 'figure'),
            Input('color-by-dropdown', 'value') if has_ms else Input('combined-3d-plot', 'relayoutData'),
            Input('size-by-dropdown', 'value') if has_ms else Input('combined-3d-plot', 'relayoutData'),
            Input('ms-time-slider', 'value') if has_ms else Input('combined-3d-plot', 'relayoutData'),
            Input('combined-3d-plot', 'relayoutData'),
            Input('x-min', 'value') if has_ms else Input('combined-3d-plot', 'relayoutData'),
            Input('x-max', 'value') if has_ms else Input('combined-3d-plot', 'relayoutData'),
            Input('y-min', 'value') if has_ms else Input('combined-3d-plot', 'relayoutData'),
            Input('y-max', 'value') if has_ms else Input('combined-3d-plot', 'relayoutData'),
            Input('z-min', 'value') if has_ms else Input('combined-3d-plot', 'relayoutData'),
            Input('z-max', 'value') if has_ms else Input('combined-3d-plot', 'relayoutData'),
            Input('colorscale-dropdown', 'value') if has_ms else Input('combined-3d-plot', 'relayoutData'),
            Input('colorbar-min', 'value') if has_ms else Input('combined-3d-plot', 'relayoutData'),
            Input('colorbar-max', 'value') if has_ms else Input('combined-3d-plot', 'relayoutData'),
            Input('aspectmode-dropdown', 'value') if has_ms else Input('combined-3d-plot', 'relayoutData'),
            Input('das-time-slider', 'value') if has_das else Input('combined-3d-plot', 'relayoutData'),
            Input('das-colorscale-dropdown', 'value') if has_das else Input('combined-3d-plot', 'relayoutData'),
            Input('das-colorbar-min', 'value') if has_das else Input('combined-3d-plot', 'relayoutData'),
            Input('das-colorbar-max', 'value') if has_das else Input('combined-3d-plot', 'relayoutData'),
            allow_duplicate=True
        )
        def update_combined_plot(*args):
            if has_ms:
                # Unpack arguments for MS case, including DAS slider if available
                if has_das:
                    (color_by, size_by, time_range, relayout_data, x_min, x_max,
                     y_min, y_max, z_min, z_max, colorscale, colorbar_min, colorbar_max,
                     aspect_mode, das_time_value, das_colorscale, das_colorbar_min, das_colorbar_max) = args
                    print(f"DAS SLIDER CALLBACK TRIGGERED - DAS time value: {das_time_value}")
                else:
                    (color_by, size_by, time_range, relayout_data, x_min, x_max,
                     y_min, y_max, z_min, z_max, colorscale, colorbar_min, colorbar_max,
                     aspect_mode) = args
                    das_time_value = None
                    das_colorscale = None
                    das_colorbar_min = None
                    das_colorbar_max = None

                # NOTE: CHECKPOINT for callback - troubleshooting
                print("Dash callback triggered")

                # Consistently sort and reset index for times in the callback
                sorted_times = pd.to_datetime(self.MSobj.data['Origin DateTime']).sort_values().reset_index(drop=True)
                x_range = [self.MSobj.data['Easting (ft)'].min(), self.MSobj.data['Easting (ft)'].max()]
                y_range = [self.MSobj.data['Northing (ft)'].min(), self.MSobj.data['Northing (ft)'].max()]
                z_range = [self.MSobj.data['TVDSS (ft)'].min(), self.MSobj.data['TVDSS (ft)'].max()]
                has_well = self.well_objs is not None and len(self.well_objs) > 0

                if not (sorted_times != pd.Timestamp(0)).any() or len(sorted_times) == 0:
                    well_traces = self.well_objs if has_well else []
                    fig = go.Figure(data=well_traces)
                    # Set layout to be consistent
                    fig.update_layout(
                        height=700,
                        width=1000,  # Reverted back to original width
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
                            x=1.45,
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

                # Handle DAS traces - Update DAS 3D plot based on time slider
                das_traces = []
                if self.DASviewer is not None and has_das and das_time_value is not None:
                    try:
                        # Convert DAS slider value to actual DAS time
                        if has_ms and len(times_filtered) > 0:
                            # DAS slider is synced with MS indices - map to actual DAS time
                            das_slider_idx = int(das_time_value)
                            # Clamp to valid range
                            das_slider_idx = max(0, min(das_slider_idx, len(times_filtered) - 1))

                            # Get the corresponding MS time
                            ms_time = times_filtered.iloc[das_slider_idx]
                            print(f"DAS slider index: {das_slider_idx}, corresponding MS time: {ms_time}")

                            # Find closest DAS time to this MS time
                            # Convert MS datetime to seconds offset from DAS start time
                            try:
                                das_start_datetime = self.DASviewer.data.start_time
                                time_diff = (ms_time - das_start_datetime).total_seconds()

                                # Find closest DAS time index
                                current_das_times = self.DASviewer.data.taxis
                                das_time_idx = np.argmin(np.abs(current_das_times - time_diff))
                                das_center_time = time_diff

                                print(f"Mapped to DAS time: {das_center_time:.2f}s (index: {das_time_idx})")
                            except Exception as e:
                                print(f"Warning: Could not map MS time to DAS time: {e}")
                                # Fallback: use proportional mapping
                                das_range = len(self.DASviewer.data.taxis)
                                ms_range = len(times_filtered)
                                das_time_idx = int(das_slider_idx * das_range / ms_range)
                                das_center_time = self.DASviewer.data.taxis[das_time_idx]
                        else:
                            # DAS slider uses actual DAS time values
                            das_center_time = float(das_time_value)
                            current_das_times = self.DASviewer.data.taxis
                            das_time_idx = np.argmin(np.abs(current_das_times - das_center_time))
                            print(f"DAS time value: {das_center_time:.2f} (index: {das_time_idx})")

                        # Create updated DAS 3D plot for the selected time index
                        print(f"Updating DAS 3D plot for time value {das_center_time:.2f} (index: {das_time_idx})")

                        # Update DAS colorscale and colorbar range if provided
                        if das_colorscale is not None:
                            self.DASviewer.set_colorscale(das_colorscale)
                        if das_colorbar_min is not None and das_colorbar_max is not None:
                            self.DASviewer.set_colorbar_range([das_colorbar_min, das_colorbar_max])
                        elif das_colorbar_min is None and das_colorbar_max is None:
                            self.DASviewer.set_colorbar_range(None)  # Auto-range

                        # Check if well trajectory path is available
                        if self.well_trajectory_path is None:
                            print("Warning: No well trajectory path provided for DAS 3D plot")
                            das_plot = None
                        else:
                            # Pass the well trajectory path to create_plot
                            das_plot = self.DASviewer.create_plot(
                                well_traj=self.well_trajectory_path,
                                time_index=das_time_idx
                            )
                            if das_plot is not None:
                                das_traces = [das_plot]
                            else:
                                print("Warning: DAS create_plot returned None")
                    except Exception as e:
                        print(f"Error updating DAS 3D plot: {e}")
                        import traceback
                        traceback.print_exc()
                        # Fall back to original DAS object if available
                        if self.DASobj is not None:
                            das_traces = [self.DASobj]
                elif self.DASobj is not None:
                    # Use original DAS object if no slider or viewer available
                    das_traces = [self.DASobj]
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

                # Filter out None values and combine all traces
                all_traces = []
                all_traces.extend(ms_traces)
                all_traces.extend(well_traces)
                all_traces.extend(das_traces)
                # Remove any None values from the traces list
                all_traces = [trace for trace in all_traces if trace is not None]

                # Update figure with new traces
                fig = go.Figure(data=all_traces)

                # Adjust colorbar positions for DAS traces to prevent overlap
                for trace in fig.data:
                    if hasattr(trace, 'marker') and hasattr(trace.marker, 'colorbar') and trace.name == 'DAS Signal':
                        # Position DAS colorbar to match MS colorbar size and alignment
                        trace.marker.colorbar.update(
                            x=1.2,  # Positioned to the right of MS colorbar
                            xanchor='left',
                            y=0.40,  # Same y position as MS colorbar
                            yanchor='middle'
                        )

                fig.update_layout(
                    height=700,
                    width=1000,  # Reverted back to original width
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
                        x=1.45,
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

            else:
                # Handle case with no microseismic data - plot well traces and DAS
                if has_das:
                    if len(args) >= 5:  # Has DAS inputs
                        (relayout_data, das_time_value, das_colorscale,
                         das_colorbar_min, das_colorbar_max) = args[:5]
                    else:
                        relayout_data, das_time_value = args if len(args) >= 2 else (args[0] if args else None, None)
                        das_colorscale = None
                        das_colorbar_min = None
                        das_colorbar_max = None
                    print(f"DAS SLIDER CALLBACK TRIGGERED (No MS) - DAS time value: {das_time_value}")
                else:
                    relayout_data = args[0] if args else None
                    das_time_value = None
                    das_colorscale = None
                    das_colorbar_min = None
                    das_colorbar_max = None

                # Handle DAS traces if available
                das_traces = []
                if self.DASviewer is not None and has_das and das_time_value is not None:
                    try:
                        # Convert time range to center time for DAS plotting
                        if isinstance(das_time_value, list) and len(das_time_value) == 2:
                            # Use the center of the selected range
                            das_center_time = (das_time_value[0] + das_time_value[1]) / 2
                            print(f"DAS range selected: {das_time_value[0]:.2f} to {das_time_value[1]:.2f}, "
                                  f"using center: {das_center_time:.2f}")
                        else:
                            # Fallback for single value (backward compatibility)
                            das_center_time = (das_time_value if not isinstance(das_time_value, list)
                                               else das_time_value[0])
                            print(f"DAS single time value: {das_center_time:.2f}")

                        # Convert time value to index
                        current_das_times = self.DASviewer.data.taxis
                        das_time_idx = np.argmin(np.abs(current_das_times - das_center_time))

                        print(f"Updating DAS 3D plot for time value {das_center_time:.2f} (index: {das_time_idx})")

                        # Update DAS colorscale and colorbar range if provided
                        if das_colorscale is not None:
                            self.DASviewer.set_colorscale(das_colorscale)
                        if das_colorbar_min is not None and das_colorbar_max is not None:
                            self.DASviewer.set_colorbar_range([das_colorbar_min, das_colorbar_max])
                        elif das_colorbar_min is None and das_colorbar_max is None:
                            self.DASviewer.set_colorbar_range(None)  # Auto-range

                        # Check if well trajectory path is available
                        if self.well_trajectory_path is None:
                            print("Warning: No well trajectory path provided for DAS 3D plot")
                            das_plot = None
                        else:
                            # Pass the well trajectory path to create_plot
                            das_plot = self.DASviewer.create_plot(
                                well_traj=self.well_trajectory_path,
                                time_index=das_time_idx
                            )

                        if das_plot is not None:
                            das_traces = [das_plot]
                    except Exception as e:
                        print(f"Error updating DAS 3D plot: {e}")
                        if self.DASobj is not None:
                            das_traces = [self.DASobj]
                elif self.DASobj is not None:
                    das_traces = [self.DASobj]

                well_traces = self.well_objs if has_well else []

                # Combine all traces
                all_traces = []
                all_traces.extend(well_traces)
                all_traces.extend(das_traces)
                all_traces = [trace for trace in all_traces if trace is not None]

                fig = go.Figure(data=all_traces)

                # Adjust colorbar positions for DAS traces to prevent overlap
                for trace in fig.data:
                    if hasattr(trace, 'marker') and hasattr(trace.marker, 'colorbar') and trace.name == 'DAS Signal':
                        # Position DAS colorbar to match MS colorbar size and alignment
                        trace.marker.colorbar.update(
                            x=1.2,  # Positioned to the right of MS colorbar
                            xanchor='left',
                            y=0.40,  # Same y position as MS colorbar for alignment
                            yanchor='middle'
                        )

                # Set layout to be consistent
                fig.update_layout(
                    height=700,
                    width=1000,  # Reverted back to original width
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
                        x=1.45,  # Moved farther right
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

        # Register other callbacks only for microseismic data
        if has_ms:
            # Get reference to sorted times for callbacks
            sorted_times = pd.to_datetime(self.MSobj.data['Origin DateTime']).sort_values().reset_index(drop=True)

            # Update time range message based on slider movement
            @app.callback(
                Output('slider-range-output', 'children'),
                Input('ms-time-slider', 'value'),
                allow_duplicate=True
            )
            def update_slider_output(time_range):
                start_idx, end_idx = time_range
                start_time = sorted_times[min(start_idx, end_idx)]
                end_time = sorted_times[max(start_idx, end_idx)]
                return f"Selected time range: {start_time} to {end_time}"

            # Update colorbar range placeholders
            @app.callback(
                Output('colorbar-min', 'placeholder'),
                Output('colorbar-max', 'placeholder'),
                Input('color-by-dropdown', 'value'),  # Update when color_by changes
                Input('ms-time-slider', 'value')
            )
            def update_colorbar_placeholders(color_by, time_range):
                start_idx, end_idx = time_range
                start_time = sorted_times[min(start_idx, end_idx)]
                end_time = sorted_times[max(start_idx, end_idx)]
                df_filtered = self.MSobj.data[
                    (pd.to_datetime(self.MSobj.data['Origin DateTime']) >= start_time) &
                    (pd.to_datetime(self.MSobj.data['Origin DateTime']) <= end_time)
                ]
                if color_by in df_filtered.columns and not df_filtered.empty:
                    min_val = f"{df_filtered[color_by].min():.2f}"
                    max_val = f"{df_filtered[color_by].max():.2f}"
                else:
                    min_val = "Auto min"
                    max_val = "Auto max"
                return min_val, max_val

        if has_das:
            # DAS callback to update the waterfall image based on time slider and color settings
            @app.callback(
                Output('das-image', 'src'),
                Input('das-time-slider', 'value'),
                Input('das-colorscale-dropdown', 'value'),
                Input('das-colorbar-min', 'value'),
                Input('das-colorbar-max', 'value'),
                prevent_initial_call=False
            )
            def update_das_image(das_time_value, das_colorscale, das_colorbar_min, das_colorbar_max):
                print(f"DAS callback triggered with time value: {das_time_value}, colorscale: {das_colorscale}")

                if self.DASviewer is not None and hasattr(self.DASviewer, 'data'):
                    # Update DAS colorscale and colorbar range if provided
                    if das_colorscale is not None:
                        self.DASviewer.set_colorscale(das_colorscale)
                    if das_colorbar_min is not None and das_colorbar_max is not None:
                        self.DASviewer.set_colorbar_range([das_colorbar_min, das_colorbar_max])
                    elif das_colorbar_min is None and das_colorbar_max is None:
                        self.DASviewer.set_colorbar_range(None)  # Auto-range

                    # Get the time axis fresh from the DAS data
                    current_das_times = self.DASviewer.data.taxis
                    if das_time_value is not None:
                        # Handle single value slider
                        if has_ms and len(times_filtered) > 0:
                            # DAS slider is synced with MS indices - map to actual DAS time
                            das_slider_idx = int(das_time_value)
                            # Clamp to valid range
                            das_slider_idx = max(0, min(das_slider_idx, len(times_filtered) - 1))

                            # Get the corresponding MS time
                            ms_time = times_filtered.iloc[das_slider_idx]

                            # Convert MS datetime to seconds offset from DAS start time
                            try:
                                das_start_datetime = self.DASviewer.data.start_time
                                center_time = (ms_time - das_start_datetime).total_seconds()
                                print(f"DAS slider index: {das_slider_idx}, "
                                      f"MS time: {ms_time}, DAS time: {center_time:.2f}s")
                            except Exception as e:
                                print(f"Warning: Could not map MS time to DAS time: {e}")
                                # Fallback: use proportional mapping
                                das_range = current_das_times[-1] - current_das_times[0]
                                center_time = (das_slider_idx / len(times_filtered)) * das_range
                        else:
                            # DAS slider uses actual DAS time values
                            center_time = float(das_time_value)
                            print(f"DAS single time value: {center_time:.2f}")

                        # Create waterfall plot with entire dataset and selected time marker
                        new_image = self.DASviewer.create_waterfall(
                            selected_time=center_time
                        )
                        if new_image:
                            return new_image
                        else:
                            print("Warning: create_waterfall returned empty image")
                            return self.DASimage
                    else:
                        print("DAS time value is None")
                        return self.DASimage

            # Update DAS time display
            @app.callback(
                Output('das-time-output', 'children'),
                Input('das-time-slider', 'value')
            )
            def update_das_time_output(selected_time):
                print(f"DAS time output callback triggered with time: {selected_time}")

                if self.DASviewer is not None and hasattr(self.DASviewer, 'data'):
                    try:
                        current_das_times = self.DASviewer.data.taxis
                        if selected_time is not None:
                            # Handle single value slider
                            if has_ms and len(times_filtered) > 0:
                                # DAS slider is synced with MS indices - map to actual DAS time
                                das_slider_idx = int(selected_time)
                                # Clamp to valid range
                                das_slider_idx = max(0, min(das_slider_idx, len(times_filtered) - 1))

                                # Get the corresponding MS time
                                ms_time = times_filtered.iloc[das_slider_idx]

                                return (f"Selected time: {ms_time.strftime('%Y-%m-%d %H:%M:%S')} "
                                        f"(Index: {das_slider_idx}/{len(times_filtered)-1})")
                            else:
                                # DAS slider uses actual DAS time values
                                single_time = float(selected_time)
                                time_idx = np.argmin(np.abs(current_das_times - single_time))
                                actual_time_offset = current_das_times[time_idx]

                                # Convert time offset to actual datetime using start_time
                                from datetime import timedelta
                                actual_datetime = (self.DASviewer.data.start_time +
                                                   timedelta(seconds=actual_time_offset))
                                formatted_time = actual_datetime.strftime('%Y-%m-%d %H:%M:%S')

                                total_steps = len(current_das_times)
                                return f"Selected time: {formatted_time} (Index: {time_idx}/{total_steps-1})"
                        else:
                            return "No time selected"
                    except Exception as e:
                        print(f"Error in DAS time output callback: {e}")
                        return f"Error: {str(e)}"
                else:
                    return "DAS time: No data available"

            # Update DAS colorbar range placeholders based on data
            @app.callback(
                Output('das-colorbar-min', 'placeholder'),
                Output('das-colorbar-max', 'placeholder'),
                Input('das-time-slider', 'value')
            )
            def update_das_colorbar_placeholders(das_time_value):
                if self.DASviewer is not None and hasattr(self.DASviewer, 'data'):
                    try:
                        # Get data range for placeholder values
                        data_min = float(self.DASviewer.data.data.min())
                        data_max = float(self.DASviewer.data.data.max())
                        return f"{data_min:.2f}", f"{data_max:.2f}"
                    except Exception as e:
                        print(f"Error getting DAS data range: {e}")
                        return "Auto min", "Auto max"
                else:
                    return "Auto min", "Auto max"

        # Always register DAS callbacks if DAS components exist in layout
        # This needs to be outside the has_das condition to avoid callback registration issues
        if has_das and len(das_times) > 0:
            print(f"Registering DAS callbacks for {len(das_times)} time steps")

        # Register DAS callbacks only if DAS slider was added to layout
        try:
            # This will only work if the DAS slider components were added to the layout
            if has_das and len(das_times) > 0:
                # These callbacks are already defined above
                pass
        except Exception as e:
            print(f"Note: DAS callbacks not registered: {e}")

        # NOTE: Checkpoint for sliders - troubleshooting
        if has_ms:
            print(f"Data min time: {self.MSobj.data['Origin DateTime'].min()}")
            print(f"Data max time: {self.MSobj.data['Origin DateTime'].max()}")
        else:
            print("No microseismic data available for time range display")

        # Define host and port
        host = "127.0.0.1"
        port = 8050
        print(f"Dash app running at http://{host}:{port}")

        # Run the app with specified host and port
        app.run(debug=True, host=host, port=port)
