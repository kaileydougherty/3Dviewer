# Create DAS data object for plotting in 3DViewer.
# Author: Kailey Dougherty
# Date created: 20-JUL-2025
# Date last modified: 24-FEB-2026

# Import needed libraries
import matplotlib.pyplot as plt
import numpy as np
import sys
import plotly.graph_objects as go
import pandas as pd
import io
import base64


class DASPlot:

    def __init__(self):
        self.data = []               # Placeholder for DAS data object, written in list for multiple entries
        self.labels = []             # Labels for each DAS dataset
        self.well = None
        self.color_scale = 'RdBu_r'  # Default color scale
        self.colorbar_range = None
        self.downsample = [5, 5]     # Default downsampling for waterfall plot [time, depth]

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

    def get_colorbar_range(self):
        """
        Get the colorbar range for consistent use across waterfall and 3D plots.

        Returns
        -------
        tuple
            (cmin, cmax) values for the colorbar range
        """
        if self.colorbar_range and len(self.colorbar_range) == 2:
            return float(self.colorbar_range[0]), float(self.colorbar_range[1])
        else:
            # Use auto-settings based on entire dataset for consistency
            return float(self.data.data.min()), float(self.data.data.max())

    def set_downsample(self, downsample):
        """
        Set the downsampling factors for the waterfall plot.

        Parameters
        ----------
        downsample : list or tuple of length 2
            The downsampling factors [time_factor, depth_factor] for the waterfall plot.
            Higher values mean more downsampling (faster but lower resolution).
        """
        self.downsample = downsample

    def add_data(self, data):
        self.data.append(data)

    def load_h5(self, pylib, filepaths, bgtime=None, edtime=None, labels=None):
        sys.path.append(pylib)
        from JIN_pylib import Data2D_XT

        for i, fpath in enumerate(filepaths):
            data_obj = Data2D_XT.load_h5(fpath)

        # Apply time windowing if time range is provided
            if bgtime is not None and edtime is not None:
                data_obj.select_time(bgtime, edtime, makecopy=False, reset_starttime=True)
                print(f"Windowed data {i+1} from {bgtime} to {edtime}")

            self.data.append(data_obj)

        # Store labels (use provided labels or generate default ones)
        if labels:
            self.labels = labels
        else:
            self.labels = [f'DAS {i+1}' for i in range(len(filepaths))]

        print('Success!')
        print(self.data)
        return True

    def create_waterfall(self, das_index=0, starttime=None, endtime=None, time_index=None, selected_time=None):
        # UPDATE THIS TO USE WATERFALL PLOT FUNCTION RATHER THAN IMAGE

        # Select which DAS dataset to plot
        if len(self.data) == 0:
            print("Error: No DAS data loaded")
            return None
        
        # Get the specific data object and its label
        data_obj = self.data[das_index] if das_index < len(self.data) else self.data[0]
        label = self.labels[das_index] if das_index < len(self.labels) else f'DAS {das_index}'

        plt.figure()

        # Dropdown for colorscale selection
        colorscale_mapping = {
            'RdBu_r': 'RdBu_r',
            'RdBu': 'RdBu',
            'Spectral': 'Spectral',
            'Coolwarm': 'coolwarm',
            'Seismic': 'seismic',
            'Berlin': 'berlin'
        }

        # Get the corresponding matplotlib colormap
        matplotlib_cmap_name = colorscale_mapping.get(self.color_scale, 'RdBu_r')
        matplotlib_cmap = plt.get_cmap(matplotlib_cmap_name)

        if time_index is not None:
            # Create a time slice plot instead of full waterfall
            if hasattr(data_obj, 'data') and hasattr(data_obj, 'taxis'):
                time_slice_data = data_obj.data[:, time_index]  # Get data at specific time index
                depths = data_obj.daxis * 3.28084  # Convert to feet  # FIX THIS

                plt.figure(figsize=(8, 6))
                plt.plot(time_slice_data, depths, 'b-', linewidth=1)
                plt.title(f'DAS Time Slice at t = {data_obj.taxis[time_index]:.4f}')
                plt.grid(True, alpha=0.3)
            else:
                # Fallback to regular waterfall if data structure is different
                data_obj.plot_waterfall(downsample=self.downsample, use_timestamp=True, cmap=matplotlib_cmap)
                # Apply consistent colorbar range for fallback waterfall
                plt.colorbar()
                cmin, cmax = self.get_colorbar_range()
                plt.clim([cmin, cmax])
        else:
            # Full waterfall plot with specified colormap
            data_obj.plot_waterfall(downsample=self.downsample, use_timestamp=True, cmap=matplotlib_cmap)
            plt.colorbar()

            # Apply the same colorbar range as the 3D plotting object
            cmin, cmax = self.get_colorbar_range()
            plt.clim([cmin, cmax])

        # Add vertical red line at selected time position
        if selected_time is not None:
            try:
                from datetime import timedelta
                import matplotlib.dates as mdates
                import pandas as pd

                # Handle both datetime strings and numeric values
                if isinstance(selected_time, str):
                    # Parse datetime string directly
                    selected_datetime = pd.to_datetime(selected_time)
                elif isinstance(selected_time, (int, float)):
                    # Convert selected time offset to actual datetime
                    selected_datetime = data_obj.start_time + timedelta(seconds=selected_time)
                else:
                    print(f"Warning: Unsupported selected_time format: {type(selected_time)}")
                    selected_datetime = None

                if selected_datetime is not None:
                    # Convert datetime to matplotlib date number (required for axvline with datetime axis)
                    selected_datenum = mdates.date2num(selected_datetime)

                    # Add vertical line at the selected time
                    plt.axvline(x=selected_datenum, color='red', linewidth=3, linestyle='-',
                                alpha=0.9, label='Selected Time')
                    plt.legend(loc='upper right')
                    print(f"Added red line at datetime: {selected_datetime} (datenum: {selected_datenum})")
                    
            except Exception as e:
                print(f"Warning: Could not add time marker line: {e}")
                import traceback
                traceback.print_exc()

        # Save the figure to a BytesIO buffer
        buf = io.BytesIO()
        plt.savefig(buf, format="png", bbox_inches="tight")
        plt.close()
        buf.seek(0)
        encoded = base64.b64encode(buf.read()).decode("ascii")

        image = f"data:image/png;base64,{encoded}"

        return image

    def _create_single_trace(self, data_obj, label, time_index=None, selected_time=None):
        """
        Create a single DAS trace from one data object.
       
        Parameters
        ----------
        data_obj : Data2D object
            Single DAS data object to visualize
        label : str
            Name/label for this trace
        time_index : int, optional
            Specific time index to plot
        selected_time : str, optional
            Datetime string to find time index
            
        Returns
        -------
        go.Scatter3d
            Plotly 3D scatter trace
        """

        # If selected_time is provided, find the corresponding time index
        if selected_time is not None and time_index is None:
            time_index = self.find_nearest_das_time_index(selected_time, verbose=True)
            if time_index is not None:
                print(f"Using time index {time_index} for selected time '{selected_time}'")

        # Map DAS positions using existing coordinates
        x_das = data_obj.x
        y_das = data_obj.y
        z_das = data_obj.z

        # Get signal data
        if time_index is not None and hasattr(data_obj, 'data'):
            if time_index < data_obj.data.shape[1]:
                signal = data_obj.data[:, time_index]
                actual_time = data_obj.taxis[time_index] if hasattr(data_obj, 'taxis') else time_index
                trace_name = f'{label} (t={actual_time:.3f}s)'
            else:
                signal = data_obj.data.flatten()
                trace_name = label
        else:
            signal = data_obj.data.flatten()
            trace_name = label
        
        # Ensure signal length matches coordinates
        if len(signal) != len(x_das):
            if time_index is not None:
                signal = signal[:len(x_das)]
            else:
                signal = np.tile(signal, len(x_das) // len(signal) + 1)[:len(x_das)]
        
        # Get colorbar range
        cmin, cmax = self.get_colorbar_range()

        # Create trace
        das_trace = go.Scatter3d(
            x=x_das,
            y=y_das,
            z=z_das,
            mode='markers',
            marker=dict(
                size=3,
                color=signal,
                colorscale=self.color_scale,
                colorbar=dict(title=f'{label} Signal'),
                opacity=1.0,
                cmin=cmin,
                cmax=cmax,
                line=dict(width=0)
            ),
            name=trace_name
        )
        
        return das_trace

    def create_plot(self, well_traj=None, time_index=None, depth_offset=None, selected_time=None):
        """
        Create DAS plot trace(s). Returns single trace or list of traces.
        """
        
        # Handle multiple DAS datasets
        if len(self.data) > 1:
            print(f"Creating {len(self.data)} DAS traces")
            traces = []
            for i, data_obj in enumerate(self.data):
                label = self.labels[i] if i < len(self.labels) else f'DAS {i+1}'
                trace = self._create_single_trace(data_obj, label, time_index, selected_time)
                traces.append(trace)
            return traces
        
        # Handle single DAS dataset (backward compatibility)
        elif len(self.data) == 1:
            label = self.labels[0] if self.labels else 'DAS Signal'
            return self._create_single_trace(self.data[0], label, time_index, selected_time)
        
        else:
            print("Error: No DAS data loaded")
            return None

    def find_nearest_das_time_index(self, target_time, verbose=True):
        """
        Find the nearest DAS time index for a given datetime string or numeric time.
       
        Parameters:
        -----------
        target_time : str, float, or int
            Target time as datetime string or numeric seconds
        verbose : bool
            Whether to print matching information

        Returns:
        --------
        int or None
            Nearest time index, or None if matching fails
        """
        if self.data is None:
            if verbose:
                print("Warning: No DAS data available for time matching")
            return None
            
        try:            
            if isinstance(target_time, str):
                # Handle datetime string
                target_datetime = pd.to_datetime(target_time)
                
                # Check which datetime attribute exists in the data
                if hasattr(self.data, 'datetime'):
                    das_datetimes = pd.to_datetime(self.data.datetime)
                elif hasattr(self.data, 'start_time') and hasattr(self.data, 'taxis'):
                    # Convert from start_time + taxis seconds offset
                    das_start_time = pd.to_datetime(self.data.start_time)
                    time_offsets = pd.to_timedelta(self.data.taxis, unit='s')
                    das_datetimes = pd.DatetimeIndex(das_start_time + time_offsets)
                else:
                    if verbose:
                        available_attrs = dir(self.data)
                        print("Warning: Cannot find datetime information in DAS data.")
                        print(f"Available attributes: {available_attrs}")
                    return None
                
                # Find nearest time index with validation
                time_diffs = np.abs(das_datetimes - target_datetime)
                time_index = np.argmin(time_diffs)
                
                if verbose:
                    closest_datetime = das_datetimes[time_index]
                    time_diff_seconds = time_diffs[time_index].total_seconds()
                    
                    print(f"Datetime '{target_time}' -> nearest DAS time '{closest_datetime}'")
                    print(f"Index: {time_index}")
                    print(f"Time difference: {time_diff_seconds:.3f} seconds")
                    
                    # Warn if the match is far from requested time
                    if time_diff_seconds > 60:  # More than 1 minute difference
                        print(f"Warning: Nearest DAS time is {time_diff_seconds:.1f}s away from requested time")
                
                return time_index
                
            elif isinstance(target_time, (int, float)):
                # Handle numeric time (seconds offset)
                current_das_times = self.data.taxis
                time_index = np.argmin(np.abs(current_das_times - target_time))
                
                if verbose:
                    actual_time = current_das_times[time_index]
                    time_diff = abs(actual_time - target_time)
                    print(f"Numeric time {target_time:.2f}s -> nearest DAS time {actual_time:.2f}s")
                    print(f"Index: {time_index}")
                    if time_diff > 1.0:  # More than 1 second difference
                        print(f"Time difference: {time_diff:.3f} seconds")
                
                return time_index
                
            else:
                if verbose:
                    print(f"Warning: Unsupported time format: {type(target_time)}")
                return None
                
        except Exception as e:
            if verbose:
                print(f"Warning: Could not match time '{target_time}': {e}")
            return None

    def get_das_time_range(self):
        """
        Get the available time range in the loaded DAS data.
        
        Returns:
        --------
        dict or None
            Dictionary with 'start', 'end', 'duration_hours' keys, or None if no DAS data
        """
        if self.data is None:
            print("No DAS data available")
            return None
            
        try:
            # Check which datetime attribute exists in the data
            if hasattr(self.data, 'datetime'):
                das_datetimes = pd.to_datetime(self.data.datetime)
            elif hasattr(self.data, 'start_time') and hasattr(self.data, 'taxis'):
                # Convert from start_time + taxis seconds offset
                das_start_time = pd.to_datetime(self.data.start_time)
                time_offsets = pd.to_timedelta(self.data.taxis, unit='s')
                das_datetimes = pd.DatetimeIndex(das_start_time + time_offsets)
            else:
                print("Warning: Cannot find datetime information in DAS data for time range calculation")
                return None
            
            start_time = das_datetimes.min()
            end_time = das_datetimes.max()
            duration = end_time - start_time
            
            time_range = {
                'start': start_time,
                'end': end_time,
                'duration_hours': duration.total_seconds() / 3600,
                'total_samples': len(das_datetimes)
            }
            
            print("DAS Data Time Range:")
            print(f"  Start: {start_time}")
            print(f"  End: {end_time}")
            print(f"  Duration: {duration.total_seconds():.1f} seconds")
            print(f"  ({time_range['duration_hours']:.2f} hours)")
            print(f"  Total samples: {time_range['total_samples']:,}")
            
            return time_range
            
        except Exception as e:
            print(f"Error getting DAS time range: {e}")
            return None

