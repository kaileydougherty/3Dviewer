# Create a 3D visualization for distributed fiber optic sensing data for microseismic events.
# Author: Kailey Dougherty
# Date created: 19-JAN-2025
# Date last modified: 15-JUL-2025

# Import needed libraries
import pandas as pd
import plotly.graph_objects as go
import numpy as np


class MSPlot():
    """
    A class for loading a microseismic event CSV file and creating a Plotly plotting object to visualize
    these events in a 3D Dash space.

    Attributes
    ----------
    MScatalog : str
        The relative path to the CSV file containing the microseismic data.
        This dataset must at least contain the following column names to be compatible:
        - File Name: The name of the event file.
        - Easting (ft): The Easting coordinate of the event in feet.
        - Northing (ft): The Northing coordinate of the event in feet.
        - TVDSS (ft): The true vertical depth subseaof the event in feet.
        - Origin DateTime: A combined datetime column of the origin time in UTC in 'YYYY-MM-DD HH:MM:ss.sss'
        format (str).
        - Brune Magnitude: The Brune magnitude of the event (float).
        - Stage: The stage identifier (int).

    color_by : str
        The attribute used to determine the color of each plot point. Default is 'Stage'.

    color_scale : str
        The color scale used for the visualization. Default is 'Viridis'.

    colorbar_range : list of int or None
        The range for the colorbar. If not set, the range will be determined automatically based on color_by.

    size_by : str
        The attribute used to determine the size of each plot point. Default is 'Brune Magnitude'.

    size_range : list of int
        The range for scaling the size of the points in the plot. Default is [10, 100].

    plot_start_time : str or None
        The start time for the plot's time range in 'YYYY-MM-DD HH:MM:SS' format. Default is None.

    plot_end_time : str or None
        The end time for the plot's time range in 'YYYY-MM-DD HH:MM:SS' format. Default is None.

    title : str
        The title of the plot. Default is '3D Bubble Chart of Cumulative Seismic Entries'.

    Methods
    -------
    __init__():
        Initializes the MSViewer with default parameters.

    set_colorby(color_by):
        Sets the attribute to be used for color encoding the plot points.

    set_colorscale(color_scale):
        Sets the color scale for the plot.

    set_sizeby(size_by):
        Sets the attribute to be used for determining the size of the plot points.

    set_sizerange(size_range):
        Sets the range for scaling the size of the plot points.

    set_start_time(plot_start_time):
        Sets the start time for the plot's time range.

    set_end_time(plot_end_time):
        Sets the end time for the plot's time range.

    set_title(title):
        Sets the title for the plot.

    load_csv(self, MScatalog):
        Loads and parses the data from the file specified by the MScatalog attribute,
        returning a Pandas DataFrame with structured data.

    create_plot(self):
        Creates an interactive 3D scatter plot object for seismic data.
    """

    def __init__(self):
        """
        Initialize the MSViewer with the given parameters.

        Parameters
        ----------
        MScatalog : str
            The relative path to the CSV file containing the microseismic data.
            This dataset must contain the following columns to be compatible:
            - File Name: The name of the event file.
            - Easting (ft): The Easting coordinate of the event in feet.
            - Northing (ft): The Northing coordinate of the event in feet.
            - TVDSS (ft): The true vertical depth subsea of the event in feet.
            - Origin DateTime: A combined datetime column of the origin time in UTC in YYYY-MM-DD HH:MM:ss.sss
            format (str).
            - Brune Magnitude: The Brune magnitude of the event (float).
            - Stage: The stage identifier (int).

        color_by : str, optional
            The attribute used for color encoding. Default is 'Stage'.

        color_scale : str, optional
            The color scale for the visualization. Default is 'Viridis'.

        colorbar_range : list of int or None, optional
            The range for the colorbar. If not set, the range will be determined automatically based on color_by.
            Default is None.

        size_by : str, optional
            The attribute used for determining the size of the plot points. Default is 'Brune Magnitude'.

        size_range : list of int, optional
            The size range for the plot points. Default is [10, 100].

        plot_start_time : str, optional
            The start time for the plot's time range. Default is None.

        plot_end_time : str, optional
            The end time for the plot's time range. Default is None.
        """
        self.MScatalog = None
        self.color_by = 'Stage'
        self.color_scale = 'Viridis'
        self.colorbar_range = None
        self.size_by = 'Brune Magnitude'
        self.size_range = [10, 100]
        self.plot_start_time = None
        self.plot_end_time = None

    def set_colorby(self, color_by):
        """
        Set the attribute to be used for color encoding the plot points.

        Parameters
        ----------
        color_by : str
            The column name in the data to use for coloring the plot points.
        """
        self.color_by = color_by

    def set_colorscale(self, color_scale):
        """
        Set the color scale for the plot.

        Parameters
        ----------
        color_scale : str
            The name of the Plotly color scale to use (e.g., 'Viridis', 'Cividis').
        """
        self.color_scale = color_scale

    def set_colorbar_range(self, color_range):
        """
        Set the range for the colorbar.

        Parameters
        ----------
        color_range : list of int or float
            A list or tuple of two values specifying the min and max for the colorbar.
        """
        self.colorbar_range = color_range

    def set_sizeby(self, size_by):
        """
        Set the attribute to be used for sizing the plot points.

        Parameters
        ----------
        size_by : str
            The column name in the data to use for sizing the plot points.
        """
        self.size_by = size_by

    def set_sizerange(self, size_range):
        """
        Set the range for scaling the size of the plot points.

        Parameters
        ----------
        size_range : list of int or float
            A list or tuple of two values specifying the min and max size for the plot points.
        """
        self.size_range = size_range

    def set_start_time(self, plot_start_time):
        """
        Set the start time for the plot's time range.

        Parameters
        ----------
        plot_start_time : str
            The start time in 'YYYY-MM-DD HH:MM:SS' format for filtering events.
        """
        self.plot_start_time = plot_start_time

    def set_end_time(self, plot_end_time):
        """
        Set the end time for the plot's time range.

        Parameters
        ----------
        plot_end_time : str
            The end time in 'YYYY-MM-DD HH:MM:SS' format for filtering events.
        """
        self.plot_end_time = plot_end_time

    def load_csv(self, MScatalog):
        """
        Load the dataset.
        Reads the data from the CSV file by its relative path and returns a Pandas DataFrame with the cleaned data.

        Parameters
        ----------
        MScatalog : str
            The relative path to the CSV file containing the microseismic data.
            This dataset must contain at least the following columns to be compatible:
            - File Name: The name of the event file.
            - Easting (ft): The Easting coordinate of the event in feet.
            - Northing (ft): The Northing coordinate of the event in feet.
            - TVDSS (ft): The true vertical depth subsea of the event in feet.
            - Origin DateTime: A combined datetime column of the origin time in UTC in YYYY-MM-DD HH:MM:ss.sss
            format (str).
            - Brune Magnitude: The Brune magnitude of the event (float).
            - Stage: The stage identifier (int).

        Returns
        -------
        bool
            True if the file is successfully loaded, False otherwise.
        """

        # Load the CSV file
        self.data = pd.read_csv(MScatalog)

        print('Success!')

        return True

    def create_plot(self):
        """
        Creates an interactive 3D scatter plot for the filtered seismic data.

        Filters the data by the specified time range and selected attributes, then generates a Plotly 3D scatter plot
        object. Points are colored and sized according to user-selected attributes, with hover text for event details.

        Returns
        -------
        plotly.graph_objects.Figure
            A Plotly figure object containing the interactive 3D scatter plot.
        """
        data = self.data

        df = data.copy()
        df['Origin DateTime'] = pd.to_datetime(df['Origin DateTime'])
        df = df.sort_values(by='Origin DateTime')
        sorted_times = df['Origin DateTime']

        # Filter data based on the start and stop times

        # Sort all microseismic data by time
        sorted_times = df['Origin DateTime']

        # Determine start and end times
        if self.plot_start_time is not None:
            start_time = pd.to_datetime(self.plot_start_time)
        else:
            start_time = sorted_times.min() if len(sorted_times) > 0 else None

        if self.plot_end_time is not None:
            end_time = pd.to_datetime(self.plot_end_time)
        else:
            end_time = sorted_times.max() if len(sorted_times) > 0 else None

        # Find indices for the selected range
        start_idx = int(np.searchsorted(sorted_times, start_time, side='left'))
        end_idx = int(np.searchsorted(sorted_times, end_time, side='right') - 1)

        # Clamp indices to valid range
        start_idx = max(0, min(start_idx, len(sorted_times) - 1))
        end_idx = max(0, min(end_idx, len(sorted_times) - 1))

        # Filter dataframe
        df_filtered = df[(sorted_times >= sorted_times[start_idx]) & (sorted_times <= sorted_times[end_idx])]

        # Determine colorbar range
        # Check if the user inputted a tuple of length 2
        if self.colorbar_range and len(self.colorbar_range) == 2:
            cmin, cmax = self.colorbar_range
        # If not, use auto-settings based on color_by feature
        else:
            cmin = df_filtered[self.color_by].min()
            cmax = df_filtered[self.color_by].max()

        # Create the 3D scatter plot
        MSplot = go.Scatter3d(
            x=df_filtered['Easting (ft)'],  # X-axis: Easting
            y=df_filtered['Northing (ft)'],  # Y-axis: Northing
            z=df_filtered['TVDSS (ft)'],  # Z-axis: Depth
            text=df_filtered.apply(
                lambda row: (
                    f"File: {row['File Name']}<br>"
                    f"Stage: {row['Stage']}<br>"
                    f"Magnitude: {row['Brune Magnitude']:.2f}"
                ),
                axis=1
            ),
            mode='markers',
            marker=dict(
                sizemode='diameter',  # Set the size mode to diameter
                sizeref=25,  # Adjust the size scaling factor
                size=abs(df_filtered[self.size_by]) * 100,  # Set size
                color=df_filtered[self.color_by],  # Set which column to color by
                colorscale=self.color_scale,  # Set color scale
                cmin=cmin,  # Set min.
                cmax=cmax,  # Set max.
                colorbar=dict(
                    title=f'{self.color_by}',
                    x=1.05,
                    xanchor='left',
                    y=0.40,
                    yanchor='middle'
                ),
                line=dict(width=0)
            ),
            name='Microseismic Events'
        )

        # Return plotting object
        return MSplot
