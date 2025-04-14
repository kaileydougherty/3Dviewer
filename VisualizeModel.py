# Create a 3D visualization for distributed fiber optic sensing data for microseismic events.
# Author: Kailey Dougherty
# Date created: 24-FEB-2025
# Date last modified: 13-APRIL-2025

# Import needed libraries
import plotly.graph_objects as go

# UPDATE documentation after slider completetion.


class DataViewer:
    """
    A class to visualize well and seismic data in a 3D Plotly figure, including
    interactive sliders for adjusting the time window of the seismic data display.

    Attributes
    ----------
    plot_objects : list
        A list of Plotly trace objects (typically Scatter3d) representing wells and/or seismic events.
    """
    def __init__(self, plot_objects):
        """
        Initialize the DataViewer with a list of plot objects.

        Parameters
        ----------
        plot_objects : list
            A list containing Plotly trace objects or nested lists of such objects,
            typically generated from WellPlot and MSPlot classes.
        """
        self.plot_objects = plot_objects

    def draw(self):
        """
        UPDATE after slider completion.

        Draw the 3D visualization with time sliders using Plotly.

        This method creates a Plotly 3D figure and adds all provided Scatter3d traces.
        It also creates two interactive sliders — one for selecting the start time and
        one for the end time of the seismic data range.
        """
        fig = go.Figure()

        # Add traces to the figure
        for b in self.plot_objects:
            if isinstance(b, list):
                for c in b:
                    if isinstance(c, go.Scatter3d):  # If yes, add as trace
                        fig.add_trace(c)
                    else:  # Otherwise, print error message
                        print(f"Invalid object: {c}")
            else:
                if isinstance(b, go.Scatter3d):  # If yes, add as trace
                    fig.add_trace(b)
                else:  # Otherwise, print error message
                    print(f"Invalid object: {b}")

        # Create slider steps for start and end times
        start_steps, end_steps = self.create_slider_steps()

        # Add sliders to the layout
        fig.update_layout(
            scene=dict(
                xaxis_title='Easting (ft)',
                yaxis_title='Northing (ft)',
                zaxis_title='Depth (ft)'
            ),
            sliders=[
                {
                    'steps': start_steps,
                    'currentvalue': {
                        'visible': True,
                        'prefix': 'Start Time: ',
                        'xanchor': 'center',
                        'font': {'size': 20}
                    }
                },
                {
                    'steps': end_steps,
                    'currentvalue': {
                        'visible': True,
                        'prefix': 'End Time: ',
                        'xanchor': 'center',
                        'font': {'size': 20}
                    }
                }
            ],
            legend=dict(
                x=0.0,
                y=1.0,
                xanchor='left',
                yanchor='top',
            )
        )

        # Show the figure
        fig.show()

    def create_slider_steps(self):
        # Collect all unique times for the slider
        all_times = []

        for plot in self.plot_objects:
            if hasattr(plot, 'data') and 'Origin DateTime' in plot.data:
                plot_times = plot.data['Origin DateTime'].unique()
                all_times.extend(plot_times)

        all_times = sorted(set(all_times))  # Sort and remove duplicates
        print(all_times)
        start_steps = []
        end_steps = []

        # Create slider steps for start time
        for i, time in enumerate(all_times):
            step = {
                'args': [
                    {'start_time': time},  # Update start time dynamically
                    {'frame': {'duration': 300, 'redraw': True}}
                ],
                'label': str(time),
                'method': 'update'
            }
            start_steps.append(step)

        # Create slider steps for end time
        for i, time in enumerate(all_times):
            step = {
                'args': [
                    {'end_time': time},  # Update end time dynamically
                    {'frame': {'duration': 300, 'redraw': True}}
                ],
                'label': str(time),
                'method': 'update'
            }
            end_steps.append(step)

        return start_steps, end_steps
