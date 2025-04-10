# Create a plotter to include wells in visualized model.
# Author: Kailey Dougherty
# Date created: 24-FEB-2025
# Date last modified: 10-APRIL-2025

# Import needed libraries
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

class WellPlot():
    def __init__(self):
        self.data = None

    def load_csv(self, welltraj_files):
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
        well_traces = []

        # Generate a color palette with as many colors as wells
        color_scale = px.colors.qualitative.Plotly  # 10-color palette
        if len(self.data) > len(color_scale):
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
