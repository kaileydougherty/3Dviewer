# Create a plotter to include wells in visualized model.
# Author: Kailey Dougherty
# Date created: 24-FEB-2025
# Date last modified: 07-APRIL-2025

# Import needed libraries
import pandas as pd
import plotly.graph_objects as go
import pyproj

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
        
        # Translate data to be in the same coordinate system as the microseismic data
        reference_point = [31.97706, -103.70791]
        proj_wgs84 = pyproj.CRS('EPSG:4326')
        proj_spcs = pyproj.CRS('EPSG:32039')
        transformer = pyproj.Transformer.from_crs(proj_wgs84, proj_spcs, always_xy=True)
        reference_easting, reference_northing = transformer.transform(reference_point[1], reference_point[0])

        # Add each trace to the well plot
        for i, (well, df) in enumerate(self.data.items()):

            # Ensure columns are numeric
            df.loc[:, 'Easting'] = pd.to_numeric(df['Easting'], errors='coerce')
            df.loc[:, 'Northing'] = pd.to_numeric(df['Northing'], errors='coerce')
            df.loc[:, 'True Vertical Depth'] = pd.to_numeric(df['True Vertical Depth'], errors='coerce')

            # Invert depth for plotting
            df.loc[:, 'Depth'] = -1 * df['True Vertical Depth']

            # Update spatial coordinates
            df.loc[:, 'Referenced Easting (ft)'] = reference_easting + df['Easting']
            df.loc[:, 'Referenced Northing (ft)'] = reference_northing + df['Northing']

            # Cycle through colors for each well
            nxtcolor = colors[i % len(colors)]
            
            # Create a 3D scatter trace for the current well
            well_trace = go.Scatter3d(
                x=df['Referenced Easting (ft)'],
                y=df['Referenced Northing (ft)'],
                z=df['Depth'],
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
