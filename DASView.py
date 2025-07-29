# Create DAS data object for plotting in 3DViewer.
# Author: Kailey Dougherty
# Date created: 20-JUL-2025
# Date last modified: 29-JUL-2025

# Import needed libraries
import matplotlib.pyplot as plt
import numpy as np
from scipy.interpolate import interp1d
import plotly.graph_objects as go
import pandas as pd
import io
import base64


class DASPlot:

    def __init__(self):
        self.data = None
        self.well = None
        self.color_scale = 'RdBu'  # Default color scale
        self.colorbar_range = None

    def set_colorscale(self, color_scale):
        """
        Set the color scale for the plot.

        Parameters
        ----------
        color_scale : str
            The name of the Plotly color scale to use.
        """
        self.color_scale = color_scale

    def set_colorbar_range(self, colorbar_range):
        """
        Set the colorbar range for DAS signal visualization.

        Parameters
        ----------
        colorbar_range : list or tuple of length 2, or None
            The min and max values for the colorbar. If None, auto-range will be used.
        """
        self.colorbar_range = colorbar_range

    def load_h5(self, pylib, filepath):
        import sys  # ASK: Where to put this import? Usually at top, but never used another's library
        sys.path.append(pylib)
        from JIN_pylib import Data2D_XT

        self.data = Data2D_XT.load_h5(filepath)
        print('Success!')
        return True

    def create_waterfall(self, starttime=None, endtime=None, time_index=None):
        plt.figure()

        if time_index is not None:
            # Create a time slice plot instead of full waterfall
            if hasattr(self.data, 'data') and hasattr(self.data, 'taxis'):
                time_slice_data = self.data.data[:, time_index]  # Get data at specific time index
                depths = self.data.daxis * 3.28084  # Convert to feet  # FIX THIS

                plt.figure(figsize=(8, 6))
                plt.plot(time_slice_data, depths, 'b-', linewidth=1)
                plt.title(f'DAS Time Slice at t = {self.data.taxis[time_index]:.4f}')
                plt.grid(True, alpha=0.3)
            else:
                # Fallback to regular waterfall if data structure is different
                self.data.plot_waterfall(downsample=[5, 5], use_timestamp=True)
        else:
            # Original waterfall plot
            self.data.plot_waterfall(downsample=[5, 5], use_timestamp=True)
            plt.colorbar()
            cx = np.array([-1, 1])
            plt.clim(cx * 3000)

        # Save the figure to a BytesIO buffer
        buf = io.BytesIO()
        plt.savefig(buf, format="png", bbox_inches="tight")
        plt.close()
        buf.seek(0)
        encoded = base64.b64encode(buf.read()).decode("ascii")

        image = f"data:image/png;base64,{encoded}"

        return image

    def create_plot(self, well_traj=None, time_index=None, depth_offset=None):
        # well_df: DataFrame with columns 'Referenced Northing (ft)', 'Referenced Easting (ft)', 'TVDSS (ft)'
        # time_index: specific time index for DAS data (if None, uses full data)

        # Read well trajectory as pandas dataframe to map
        self.well = pd.read_csv(well_traj) if well_traj else None
        well_df = self.well

        # Sort well trajectory by depth (important for interp1d)
        well_df = well_df.sort_values('TVDSS (ft)')

        # Calculate cumulative distance along well trajectory
        x_well = well_df['Referenced Easting (ft)'].values
        y_well = well_df['Referenced Northing (ft)'].values
        z_well = well_df['TVDSS (ft)'].values

        # Calculate 3D distances between consecutive points
        dx = np.diff(x_well)
        dy = np.diff(y_well)
        dz = np.diff(z_well)
        segment_distances = np.sqrt(dx**2 + dy**2 + dz**2)

        # Cumulative distance along wellbore (starting from 0)
        cumulative_distance = np.concatenate([[0], np.cumsum(segment_distances)])

        print(f"Well trajectory distance range: 0 to {cumulative_distance[-1]:.1f} ft")

        # DAS fiber positions - convert from daxis to distance along wellbore
        # Assuming DAS daxis represents distance along fiber (originally in meters)
        das_distances_ft = self.data.daxis * 3.28084  # Convert to feet

        # Clip DAS distances to well trajectory range
        max_well_distance = cumulative_distance[-1]
        das_distances_ft = np.clip(das_distances_ft, 0, max_well_distance)

        # Interpolate well trajectory coordinates based on distance along wellbore
        x_interp = interp1d(cumulative_distance, x_well, bounds_error=False, fill_value="extrapolate")
        y_interp = interp1d(cumulative_distance, y_well, bounds_error=False, fill_value="extrapolate")
        z_interp = interp1d(cumulative_distance, z_well, bounds_error=False, fill_value="extrapolate")

        # Map DAS positions to 3D coordinates based on distance along wellbore
        x_das = x_interp(das_distances_ft)
        y_das = y_interp(das_distances_ft)
        z_das = z_interp(das_distances_ft)

        # FOR TROUBLE-SHOOTING - Print DAS data ranges
        print(f"DAS x range: {x_das.min()} to {x_das.max()}")
        print(f"DAS y range: {y_das.min()} to {y_das.max()}")
        print(f"DAS z range: {z_das.min()} to {z_das.max()}")

        # Create DAS signal scatter trace
        if time_index is not None and hasattr(self.data.taxis, 'data'):
            # Use specific time slice
            if time_index < self.data.data.shape[1]:  # Check bounds
                signal = self.data.data[:, time_index]  # Get data at specific time index
                print(f"Using DAS time slice at index {time_index}")
            else:
                print(f"Warning: time_index {time_index} out of bounds, using flattened data")
                signal = self.data.data.flatten()
        else:
            # Use all data (flattened)
            signal = self.data.data.flatten()

        # Ensure signal array matches coordinate arrays
        if len(signal) != len(x_das):
            print(f"Warning: Signal length ({len(signal)}) doesn't match coordinate length ({len(x_das)})")
            # If using time slice, signal should match depth dimension
            if time_index is not None:
                signal = signal[:len(x_das)]  # Truncate if necessary
            else:
                # For flattened data, repeat or subsample as needed
                signal = np.tile(signal, len(x_das) // len(signal) + 1)[:len(x_das)]

        # Determine colorbar range
        # Check if the user inputted a tuple of length 2
        if self.colorbar_range and len(self.colorbar_range) == 2:
            cmin, cmax = self.colorbar_range
        # If not, use auto-settings based on entire dataset
        else:
            cmin = self.data.data.min()
            cmax = self.data.data.max()

        das_trace = go.Scatter3d(
            x=x_das,
            y=y_das,
            z=z_das,
            mode='markers',
            marker=dict(
                size=3,
                color=signal,
                colorscale=self.color_scale,
                colorbar=dict(title='DAS Signal'),
                opacity=1.0,
                cmin=cmin,
                cmax=cmax,
                line=dict(width=0)
            ),
            name='DAS Signal'
        )

        return das_trace
