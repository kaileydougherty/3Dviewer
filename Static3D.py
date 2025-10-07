# Create a static model for simpler visualization of data.
# Author: Kailey Dougherty
# Date created: 06-OCT-2025
# Date last modified: 06-OCT-2025

# Import needed libraries
import plotly.graph_objects as go


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

    def __init__(self, MS_obj=None, well_objs=None, DAS_obj=None):
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
        """
        self.MSobj = MS_obj
        self.well_objs = well_objs if well_objs is not None else []
        self.DASobj = DAS_obj
        self.title = 'Static 3D Viewer'
        self.plot_objects = []
        self.aspect_mode = 'data'  # Default aspect mode
        self.aspect_ratio = None   # Custom aspect ratio

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

    def create_static_plot(self):
        """
        Create a static 3D plot combining all data sources.

        Returns
        -------
        plotly.graph_objects.Figure
            The combined 3D figure
        """
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

        # Add DAS data
        if self.DASobj:
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

        return fig
