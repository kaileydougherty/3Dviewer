# Create DAS data object for plotting in 3DViewer.
# Author: Kailey Dougherty
# Date created: 20-JUL-2025
# Date last modified: 22-JUL-2025

# Import needed libraries
import matplotlib.pyplot as plt
import numpy as np
import io
import base64


class DASPlot:

    def __init__(self):
        self.data = None

    def load_h5(self, pylib, filepath):
        import sys  # ASK: Where to put this import? Usually at top, but never used another's library
        sys.path.append(pylib)
        from JIN_pylib import Data2D_XT

        self.data = Data2D_XT.load_h5(filepath)
        print('Success!')
        return True

    def create_waterfall(self, starttime=None, endtime=None):
        plt.figure()
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

    def create_plot(self):
        pass
