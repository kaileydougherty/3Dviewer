# Create a 3D visualization for distributed fiber optic sensing data for microseismic events.
# Author: Kailey Dougherty
# Date created: 24-FEB-2025
# Date last modified: 20-APRIL-2025

# Import needed libraries
import plotly.graph_objects as go
import ipywidgets as widgets
import pandas as pd
from IPython.display import display, clear_output

# UPDATE documentation after slider completetion.


class DataViewer:
    """
    UPDATE documentation.

    A class to visualize well and seismic data in a 3D Plotly figure, including
    interactive sliders for adjusting the time window of the seismic data display.

    Attributes
    ----------
    plot_objects : list
        A list of Plotly trace objects (typically Scatter3d) representing wells and/or seismic events.
    """
    def __init__(self, MS_obj=None, well_objs=None):
        """
        Initialize the DataViewer with a list of plot objects.

        Parameters
        ----------
        plot_objects : list
            A list containing Plotly trace objects or nested lists of such objects,
            typically generated from WellPlot and MSPlot classes.
        """
        self.MSobj = MS_obj
        self.well_objs = well_objs if well_objs is not None else []
        self.plot_objects = []
        self._last_fig = None

        if well_objs is not None:
            for obj in well_objs:
                self.plot_objects.append(obj)

    def draw(self):
        """
        Draw the 3D visualization using Plotly and ipywidgets sliders.
        """
        if self.MSobj is not None:
            # Extract and downsample unique timestamps
            unique_times = sorted(pd.to_datetime(self.MSobj.data['Origin DateTime'].unique()))
            unique_times_downsampled = unique_times[::10] if len(unique_times) > 10 else unique_times

            # Create sliders
            self.start_slider = widgets.SelectionSlider(
                options=unique_times_downsampled,
                description='Start Time:',
                layout=widgets.Layout(width='95%'),
                style={'description_width': 'initial'}
            )

            self.end_slider = widgets.SelectionSlider(
                options=unique_times_downsampled,
                description='End Time:',
                value=unique_times_downsampled[-1],
                layout=widgets.Layout(width='95%'),
                style={'description_width': 'initial'}
            )

            self.out = widgets.Output()

            # Attach update method and slider callbacks
            self.start_slider.observe(self.update_plot, names='value')
            self.end_slider.observe(self.update_plot, names='value')

            # Display the widgets
            display(widgets.VBox([self.start_slider, self.end_slider, self.out]))
            self.update_plot()

        else:
            # If no MSobj is passed, just show the wells
            fig = go.Figure(data=self.well_objs)
            fig.update_layout(
                scene=dict(
                    xaxis_title='Easting (ft)',
                    yaxis_title='Northing (ft)',
                    zaxis_title='Depth (ft)'
                ),
                title="Well Trajectories",
                height=700,
                legend=dict(
                    x=0.01, y=0.99,
                    bordercolor="black",
                    borderwidth=1,
                )
            )
            fig.show()
            self._last_fig = fig

    def update_plot(self, change=None):
        with self.out:
            clear_output(wait=True)

            start_time = self.start_slider.value
            end_time = self.end_slider.value

            if start_time > end_time:
                print("Warning: Start time must be before end time.")
                return

            # Update MSPlot time window
            self.MSobj.set_start_time(start_time.strftime("%Y-%m-%d %H:%M:%S"))
            self.MSobj.set_end_time(end_time.strftime("%Y-%m-%d %H:%M:%S"))

            # Generate new seismic trace
            ms_trace = self.MSobj.create_plot()

            # Build 3D figure
            fig = go.Figure(data=self.well_objs + [ms_trace])
            fig.update_layout(
                scene=dict(
                    xaxis_title='Easting (ft)',
                    yaxis_title='Northing (ft)',
                    zaxis_title='Depth (ft)'
                ),
                title="Filtered Microseismic Events",
                height=700,
                legend=dict(
                    x=0,
                    y=1,
                    xanchor='left',
                    yanchor='top',
                )
            )

            fig.show()
            self._last_fig = fig
