# Create a static model for simpler visualization of data.
# Author: Kailey Dougherty
# Date created: 06-OCT-2025
# Date last modified: 27-OCT-2025

# Import needed libraries
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import dash
from dash import Dash, html, dcc


class StaticDataViewer:
    """
    A simplified class to create static 3D visualizations of microseismic events, well trajectories, and DAS data.

    Attributes
    ----------
    MSobj : object, optional
        Microseismic plotting object with create_plot method
    well_objs : list, optional
        List of well trajectory trace objects
    DASobj : object, optional
        DAS trace object for 3D plotting
    title : str
        Title for the visualization
    aspect_mode : str
        Aspect ratio mode ('auto', 'cube', 'data', 'manual')
    aspect_ratio : dict, optional
        Custom aspect ratio dictionary with 'x', 'y', 'z' keys
    """

    def __init__(self, MS_obj=None, well_objs=None, DAS_obj=None, DAS_image=None,
                 DAS_viewer=None, well_trajectory_path=None, include_waterfall=None,
                 selected_time=None, start_time=None, end_time=None):
        """
        Initialize the StaticDataViewer with data sources.

        Parameters
        ----------
        MS_obj : object, optional
            Microseismic plotting object
        well_objs : list, optional
            List of well trajectory trace objects
        DAS_obj : object, optional
            DAS trace object
        DAS_image : str, optional
            Base64 encoded image string for DAS waterfall plot.
        DAS_viewer : object, optional
            The DAS plotting object containing the loaded DAS data for time slicing.
        well_trajectory_path : str, optional
            Path to well trajectory CSV file for DAS 3D plotting.
        include_waterfall : bool, optional
            If True, create_static_plot returns combined layout with waterfall image.
            If False, returns only 3D figure.
            If None (default), automatically determines based on available DAS data.
        selected_time : float, optional
            Time for red line indicator in waterfall plot and DAS 3D time slice (implies include_waterfall=True)
        start_time : float, optional
            Start time for waterfall window (implies include_waterfall=True)
        end_time : float, optional
            End time for waterfall window (implies include_waterfall=True)
        """
        self.MSobj = MS_obj
        self.well_objs = well_objs if well_objs is not None else []
        self.DASobj = DAS_obj
        self.DASimage = DAS_image
        self.DASviewer = DAS_viewer
        self.well_trajectory_path = well_trajectory_path
        self.title = 'Static 3D Viewer'
        self.plot_objects = []
        self.aspect_mode = 'data'  # Default aspect mode
        self.aspect_ratio = None   # Custom aspect ratio

        # Waterfall plot parameters - store as provided (datetime strings or numeric)
        self.include_waterfall = include_waterfall
        self.selected_time = selected_time
        self.start_time = start_time
        self.end_time = end_time

    def set_title(self, title):
        """Set the title for the visualization."""
        self.title = title

    def set_aspect_mode(self, mode):
        """
        Set the aspect ratio mode for the 3D plot.

        Parameters
        ----------
        mode : str
            Aspect ratio mode: 'auto', 'cube', 'data', or 'manual'
        """
        valid_modes = ['auto', 'cube', 'data', 'manual']
        if mode not in valid_modes:
            raise ValueError(f"Invalid aspect mode. Must be one of: {valid_modes}")
        self.aspect_mode = mode

    def set_aspect_ratio(self, x=1.0, y=1.0, z=1.0):
        """
        Set custom aspect ratio for manual mode.

        Parameters
        ----------
        x : float, optional
            X-axis aspect ratio, by default 1.0
        y : float, optional
            Y-axis aspect ratio, by default 1.0
        z : float, optional
            Z-axis aspect ratio, by default 1.0
        """
        self.aspect_ratio = dict(x=x, y=y, z=z)
        # Automatically set to manual mode when custom ratio is provided
        self.aspect_mode = 'manual'

    def run_dash_app(self, host="127.0.0.1", port=8050):
        """
        Create a static 3D plot combining all data sources.

        Returns
        -------
        plotly.graph_objects.Figure or dash.html.Div
            3D figure alone, or combined layout with waterfall image based on instance settings
        """
        app = dash.Dash(__name__, suppress_callback_exceptions=True)

        # Initialize plot objects list
        self.plot_objects = []

        # Add well trajectories
        if self.well_objs:
            if isinstance(self.well_objs, list):
                self.plot_objects.extend(self.well_objs)
            else:
                self.plot_objects.append(self.well_objs)

        # Add microseismic data
        if self.MSobj:
            ms_plot = self.MSobj.create_plot()
            if ms_plot:
                self.plot_objects.append(ms_plot)

        # Add DAS data - use DASviewer if available and selected_time is specified
        if self.DASviewer is not None and self.selected_time is not None:
            try:
                # Handle datetime string or numeric time for DAS time indexing
                if isinstance(self.selected_time, str):
                    # Convert datetime string to pandas datetime and find closest time
                    target_datetime = pd.to_datetime(self.selected_time)
                    das_datetimes = pd.to_datetime(self.DASviewer.data.datetime)
                    time_index = np.argmin(np.abs(das_datetimes - target_datetime))
                    
                elif isinstance(self.selected_time, (int, float)):
                    # Use numeric time as seconds offset (existing behavior)
                    current_das_times = self.DASviewer.data.taxis
                    time_index = np.argmin(np.abs(current_das_times - self.selected_time))

                else:
                    print(f"Warning: Unsupported selected_time format: {type(self.selected_time)}")
                    time_index = None
                
                # Create 3D DAS plot at selected time if well trajectory path is available
                if time_index is not None and hasattr(self, 'well_trajectory_path') and self.well_trajectory_path:
                    das_3d_plot = self.DASviewer.create_plot(
                        well_traj=self.well_trajectory_path,
                        time_index=time_index
                    )
                    if das_3d_plot:
                        self.plot_objects.append(das_3d_plot)
                        if hasattr(self.DASviewer.data, 'taxis'):
                            actual_time = self.DASviewer.data.taxis[time_index]
                            print(f"Added DAS 3D plot at time index {time_index} (actual time: {actual_time:.4f}s)")
                elif time_index is None:
                    print("Warning: Could not determine time index for DAS 3D plotting")
                else:
                    print("Warning: Well trajectory path needed for DAS 3D plotting")
                    
            except Exception as e:
                print(f"Warning: Could not create DAS 3D plot at selected time: {e}")
                # Fallback to original DAS object if available
                if self.DASobj:
                    self.plot_objects.append(self.DASobj)
        elif self.DASobj:
            # Use original DAS object if no viewer or selected time
            self.plot_objects.append(self.DASobj)

        # Create the figure
        fig = go.Figure(data=self.plot_objects)

        # Adjust colorbar positions
        for trace in fig.data:
            if hasattr(trace, 'marker') and hasattr(trace.marker, 'colorbar'):
                if trace.name == 'DAS Signal':
                    # Position DAS colorbar to the right of MS colorbar
                    trace.marker.colorbar.update(
                        x=1.2,  # Positioned to the right of MS colorbar
                        xanchor='left',
                        y=0.40,  # Same y position as MS colorbar
                        yanchor='middle'
                    )
                # MS colorbar keeps default positioning (x=1.02, y=0.5)

        # Prepare scene configuration
        scene_config = dict(
            xaxis_title='Easting (ft)',
            yaxis_title='Northing (ft)',
            zaxis_title='TVDSS (ft)',
            zaxis=dict(autorange='reversed'),  # Reverse z-axis so depth increases downward
            aspectmode=self.aspect_mode
        )

        # Add custom aspect ratio if in manual mode
        if self.aspect_mode == 'manual' and self.aspect_ratio is not None:
            scene_config['aspectratio'] = self.aspect_ratio

        # Update layout
        fig.update_layout(
            title=self.title,
            scene=scene_config,
            width=1200,  # Increased width to accommodate colorbars
            height=800,
            margin=dict(r=200),  # Add right margin for colorbars
            legend=dict(
                x=1.3,  # Position legend farther right to avoid colorbar overlap
                y=0.5,
                xanchor='left',
                yanchor='top',
                bordercolor="Black",
                borderwidth=1,
                bgcolor="white",
                font=dict(size=12)
            )
        )

        # Determine if we should include waterfall based on instance attributes
        should_include_waterfall = False

        if self.include_waterfall is True:
            # Explicitly requested waterfall
            should_include_waterfall = True
        elif self.include_waterfall is False:
            # Explicitly requested no waterfall
            should_include_waterfall = False
        elif self.include_waterfall is None:
            # Auto-determine based on instance attributes and available data
            time_args_provided = any([self.selected_time is not None,
                                     self.start_time is not None,
                                     self.end_time is not None])
            has_das_data = self.DASviewer is not None or self.DASimage is not None
            should_include_waterfall = time_args_provided and has_das_data

        # Always return a Dash layout for consistency, even without waterfall
        if not should_include_waterfall:
            # Create simple layout with just the 3D plot
            layout = html.Div([
                dcc.Graph(
                    id='static-3d-plot',
                    figure=fig,
                    style={'height': '800px', 'width': '100%'}
                )
            ], style={'marginTop': '20px'})
          
            # Set the app layout
            app.layout = layout
           
            # Use provided host and port parameters
            print(f"Dash app running at http://{host}:{port}")
            
            # Run the app with specified host and port
            app.run(debug=True, host=host, port=port)
            return

        # Generate/update waterfall image if needed
        waterfall_image = None
        if self.DASviewer is not None:
            try:
                # Create waterfall with any provided time parameters
                waterfall_image = self.DASviewer.create_waterfall(
                    selected_time=self.selected_time,
                    starttime=self.start_time,
                    endtime=self.end_time
                )
                # Update stored image
                self.DASimage = waterfall_image
            except Exception as e:
                print(f"Warning: Could not create waterfall plot: {e}")
                waterfall_image = self.DASimage  # Use existing image if available
        else:
            # Use existing DAS image
            waterfall_image = self.DASimage

        # Check if we have a waterfall image to display
        if waterfall_image is None:
            print("Warning: No waterfall image available, returning 3D plot only")
            # Return simple layout without waterfall
            layout = html.Div([
                dcc.Graph(
                    id='static-3d-plot',
                    figure=fig,
                    style={'height': '800px', 'width': '100%'}
                )
            ], style={'marginTop': '20px'})
            
            # Set the app layout
            app.layout = layout
            
            # Use provided host and port parameters
            print(f"Dash app running at http://{host}:{port}")
            
            # Run the app with specified host and port
            app.run(debug=True, host=host, port=port)
            return

        # Create combined layout with 3D plot and DAS waterfall image
        # Add DAS image layout based on data availability
        layout = html.Div(
            [
                dcc.Graph(
                    id='combined-3d-plot',
                    figure=fig,
                    style={'height': '600px', 'width': '100%'}
                ),
                html.Div([
                    html.H2("Distributed Acoustic Sensing (DAS)", style={'textAlign': 'center'}),
                    html.Img(src=waterfall_image, id='das-image', style={
                        'width': '450px', 'height': '400px', 'display': 'block', 'margin': 'auto'
                    })
                ], style={
                    'width': '85%',
                    'display': 'flex',
                    'flexDirection': 'column',
                    'alignItems': 'center',
                    'marginTop': '120px'
                })
            ],
            style={
                'display': 'grid',
                'gridTemplateColumns': '3fr 2fr',  # 3:2 width ratio for plot:image
                'gap': '20px',
                'alignItems': 'start',
                'marginTop': '20px'
            }
        )

        # Set the app layout
        app.layout = layout

        # Use provided host and port parameters
        print(f"Dash app running at http://{host}:{port}")

        # Run the app with specified host and port
        app.run(debug=True, host=host, port=port)
