# Create a plotter to include wells in visualized model.
# Author: Kailey Dougherty
# Date created: 24-FEB-2025
# Date last modified: 16-MAR-2025

# Import needed libraries
import pandas as pd
import numpy as np
import os
import plotly.graph_objects as go


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

        for i, (well, df) in enumerate(self.data.items()):
            nxtcolor = colors[i % len(colors)]  #Cycle through colors
            well = (go.Scatter3d(
                x=df['Easting'],
                y=df['Northing'],
                z=df['True Vertical Depth'],
                mode='lines',
                line=dict(
                    color=nxtcolor,
                    width=3
                ),
                name=f'{i+1}H')) #Title each well
            
            well_traces.append(well)

        # Return the well log plot object
        return well_traces