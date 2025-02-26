# Create a plotter to include wells in visualized model.
# Author: Kailey Dougherty
# Date created: 24-FEB-2025
# Date last modified: 26-FEB-2025

# Import needed libraries
import pandas as pd
import numpy as np
import os
import plotly.graph_objects as go

class WellPlot():

    def __init__(self, well1, well2, well3, well4):
        # NOTE: Eventually make this a list entry of file paths for well catalogs. Needs to be updated.

        self.well1 = well1
        self.well2 = well2
        self.well3 = well3
        self.well4 = well4

    def load_catalogs(self):
        # NOTE: This is hardcoded using example files. Needs to be updated.

        self.well1 = pd.read_csv(self.well1, skiprows=27, skipfooter=5, usecols=['Azimuth','TVD', 'NS', 'EW'], encoding='ISO-8859-1')
        self.well2= pd.read_csv(self.well2, skiprows=22, usecols=['Azimuth','TVD', 'NS', 'EW'],
                        names=['Azimuth','TVD', 'NS', 'EW'], encoding='ISO-8859-1')
        self.well3 = pd.read_csv(self.well3, skiprows=22, usecols=['Azimuth','TVD', 'NS', 'EW'],
                        names=['Azimuth','TVD', 'NS', 'EW'], encoding='ISO-8859-1')
        self.well4 = pd.read_csv(self.well4, skiprows=22, usecols=['Azimuth','TVD', 'NS', 'EW'],
                        names=['Azimuth','TVD', 'NS', 'EW'], encoding='ISO-8859-1')
        
        print('Success!')

        return True


    def create_plot(self):

        colors = ['red', 'blue', 'green', 'orange']
        dataframes = [self.well1, self.well2, self.well3, self.well4] 

        fig = go.Figure()

        for i, df in enumerate(dataframes):
            nxtcolor = colors[i % len(colors)]  #Cycle through colors
            fig.add_trace(go.Scatter3d(
                x=df['EW'],
                y=df['NS'],
                z=df['TVD'],
                mode='lines',
                line=dict(
                    color=nxtcolor,
                    width=3
                ),
                name=f'{i+1}H')) #Title each well
                
            fig.update_layout(
                title="Well Paths",
                scene=dict(
                    xaxis_title="Easting (ft)",
                    yaxis_title="Northing (ft)",
                    zaxis_title="True Vertical Depth (ft)"
                ),
                margin=dict(l=0, r=0, b=0, t=40),
            )

        fig.show()            