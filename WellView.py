# Create a plotter to include wells in visualized model.
# Author: Kailey Dougherty
# Date created: 24-FEB-2025
# Date last modified: 09-MAY-2025

# Import needed libraries
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px


class WellPlot():
    """
    A class for loading and visualizing 3D well trajectory data using Plotly.

    This class provides functionality to read one or more well trajectory CSV files
    and generate interactive 3D line plots for each well.

    Attributes
    ----------
    data : dict
        A dictionary containing pandas DataFrames for each well, keyed by well name.

    Methods
    -------
    load_csv(welltraj_files)
        Loads multiple well trajectory CSV files into the data attribute. Each CSV file
        should contain columns for Referenced Easting (ft), Referenced Northing (ft),
        and True Vertical Depth (ft).

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
        Create a 3D line plot for each loaded well using Plotly.

        Returns
        -------
        list of plotly.graph_objects.Scatter3d
            A list of Plotly 3D scatter traces, each representing a well trajectory line.
            Each well is color-coded and plotted using its respective coordinates.
        """
        well_traces = []

        df = self.data

        # Generate a color palette with as many colors as wells
        color_scale = px.colors.qualitative.Plotly  # 10-color palette
        if len(df) > len(color_scale):
            # If more wells than colors, extend colors using repeat or other methods
            color_scale = px.colors.qualitative.Alphabet  # more unique colors
        # Add each trace to the well plot
        for i, (well, df) in enumerate(self.data.items()):
            # Generate a color for the current well
            nxtcolor = color_scale[i % len(color_scale)]
            # Create a 3D scatter trace for the current well
            well_trace = go.Scatter3d(
                x=df['Referenced Easting (ft)'],
                y=df['Referenced Northing (ft)'],
                z=df['TVDSS (ft)'],
                mode='lines',
                line=dict(
                    color=nxtcolor,
                    width=3
                ),
                name=f'{well} Well'
            )

            # Append the trace to the well_traces list
            well_traces.append(well_trace)

        # Return the well log plot object (list of traces)
        return well_traces
