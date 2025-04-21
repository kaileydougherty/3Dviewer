# Create a 3D visualization for distributed fiber optic sensing data for microseismic events.
# Author: Kailey Dougherty
# Date created: 24-FEB-2025
# Date last modified: 20-APRIL-2025

# Import needed libraries
import plotly.graph_objects as go
import ipywidgets as widgets
import pandas as pd
from IPython.display import display, clear_output


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
    _last_fig : go.Figure or None
        Stores the most recently generated Plotly figure.
    start_slider : ipywidgets.SelectionSlider
        Widget for selecting the start time of the seismic event window.
    end_slider : ipywidgets.SelectionSlider
        Widget for selecting the end time of the seismic event window.
    out : ipywidgets.Output
        Output area used for rendering the updated Plotly figure.
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

    def draw(self):
        """
        Render the 3D visualization in a Jupyter notebook.

        If a microseismic object is present, interactive sliders allow filtering seismic events
        by origin time. If not, only the well trajectories are displayed.
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
        """
        Update the 3D plot based on the selected time window from the sliders.

        This method filters the microseismic events to those occurring within the selected
        time range and re-renders the plot with both well and filtered MS data.

        Parameters
        ----------
        change : dict, optional
            Optional change dictionary passed automatically by the widget observer.
        """
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
