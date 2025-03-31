# Create a plotter to include wells in visualized model.
# Author: Kailey Dougherty
# Date created: 24-FEB-2025
# Date last modified: 31-MAR-2025

# Import needed libraries
import pandas as pd
import plotly.graph_objects as go
from geopy.distance import geodesic
import pyproj

# NEXT TASKS: SITUATE DATA IN REF. TO MAIN WELL, CONVERT TO COMMON SPACE

class WellPlot():
    def __init__(self):
        self.data = None

    def load_csv(self, welltraj_file):
        # Load the well trajectory file
        file = pd.ExcelFile(welltraj_file)

        # Load each sheet within the excel file for each individual well
        well_data = {sheet: file.parse(sheet) for sheet in file.sheet_names}
        self.data = well_data
        
        print('Success!')
        return True

    def create_plot(self):
        colors = ['red', 'blue', 'green', 'orange'] 
        well_traces = []
            
        # Add each trace to the well plot
        for i, (well, df) in enumerate(self.data.items()):

            # Make sure the data is numeric
            df['Easting'] = pd.to_numeric(df['Easting'], errors='coerce')
            df['Northing'] = pd.to_numeric(df['Northing'], errors='coerce')

            # Drop NaNs corresponding to non-numeric characters
            df = df.dropna(subset=['Easting', 'Northing'])

             # Invert depth for plotting
            df['Depth'] = -df['True Vertical Depth']

            # Cycle through colors for each well
            nxtcolor = colors[i % len(colors)]  # Cycle through colors
            
            # Create a 3D scatter trace for the current well
            well_trace = go.Scatter3d(
                x=df['Easting'],
                y=df['Northing'],
                z=df['Depth'],
                mode='lines',
                line=dict(
                    color=nxtcolor,
                    width=3
                ),
                name=f'{well} Well'  # Title each well
            )

            # Append the trace to the well_traces list
            well_traces.append(well_trace)

        # Return the well log plot object (list of traces)
        return well_traces
