# Create plotting objects to include wells in visualized model.
# Author: Kailey Dougherty
# Date created: 24-FEB-2025
# Date last modified: 15-JUL-2025

# Import needed libraries
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import random


class WellPlot():
    """
    A class for loading well trajectory CSV files and creating Plotly plotting objects to visualize
    these wells in a 3D Dash space.

    This class provides functionality to read one or more well trajectory CSV files
    and generate interactive 3D line plots for each well.

    Attributes
    ----------
    data : dict
        A dictionary containing pandas DataFrames for each well, keyed by well name.

    colors : list
        A list of color strings to be used for plotting the well trajectories.

    Methods
    -------
    __init__()
        Initializes the WellPlot class with an empty data dictionary and optional colors.

    set_colors(colors)
    Sets the colors for the well trajectories. Expects a list of color strings.

    load_csv(welltraj_files)
        Loads multiple well trajectory CSV files into the data attribute. Each CSV file
        should contain columns for 'Easting (ft)', 'Northing (ft)', and 'TVDSS (ft).'

    create_plot()
        Generates a list of Plotly Scatter3d traces for visualizing the well trajectories
        in a 3D space. Each well is rendered as a separate colored trace.
    """
    def __init__(self):
        """
        Initialize the WellPlot class.

        Initializes the internal data dictionary, which will hold well trajectory
        data loaded from CSV files.
        """
        self.data = {}
        self.colors = None  # Store user-defined colors

    def set_colors(self, colors):
        """
        Set colors for wells. Expects a list of color strings.

        Parameters
        ----------
        colors : list of str
            List of color strings to assign to wells.
        """
        self.colors = colors

    def load_csv(self, welltraj_files):
        """
        Load multiple well trajectory CSV files into the internal data dictionary.

        Parameters
        ----------
        welltraj_files : list of str
            A list of file paths to well trajectory CSV files.
            Each file must contain at least the following columns to be compatible:
            - 'Referenced Easting (ft)'
            - 'Referenced Northing (ft)'
            - 'TVDSS (ft)'

        Returns
        -------
        bool
            True if all files are successfully loaded, False otherwise.
        """
        # Load each CSV file and store in a dictionary with well name
        for path in welltraj_files:
            well_name = path.split('\\')[-1].replace('.csv', '')
            try:
                df = pd.read_csv(path)
                self.data[well_name] = df
            except Exception as e:
                print(f"Error loading {path}: {e}")
                return False
        print('Success!')
        return True

    def create_plot(self):
        """
        Create a 3D line plot object for each loaded well using Plotly.

        Returns
        -------
        list of plotly.graph_objects.Scatter3d
            A list of Plotly 3D scatter traces, each representing a well trajectory line.
            Each well is color-coded and plotted using its respective coordinates.
        """
        well_traces = []
        df = self.data

        # Use user colors if entered, or default to palette from Plotly
        user_colors = self.colors if self.colors is not None else []
        palette = px.colors.qualitative.Plotly
        if len(df) > len(palette):
            palette = px.colors.qualitative.Alphabet

        # Build a color list for all wells
        color_list = []
        used_colors = set(user_colors)
        palette_unused = [c for c in palette if c not in used_colors]

        for i, well in enumerate(self.data.keys()):
            if i < len(user_colors):
                color_list.append(user_colors[i])
            else:
                # Pick a random unused color or fallback to palette cycling
                if palette_unused:
                    color = palette_unused.pop(random.randrange(len(palette_unused)))
                else:
                    color = palette[i % len(palette)]
                color_list.append(color)

        # Add each trace to the well plot
        for i, (well, df) in enumerate(self.data.items()):
            well_trace = go.Scatter3d(
                x=df['Referenced Easting (ft)'],
                y=df['Referenced Northing (ft)'],
                z=df['TVDSS (ft)'],
                mode='lines',
                line=dict(
                    color=color_list[i],
                    width=3
                ),
                name=f'{well} Well'
            )
            well_traces.append(well_trace)

        # Return list of plotting objects
        return well_traces
