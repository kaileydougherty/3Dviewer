# Create a 3D visualization for distributed fiber optic sensing data for microseismic events.
# Author: Kailey Dougherty
# Date created: 24-FEB-2025
# Date last modified: 24-FEB-2025

# NOT A WORKING FILE YET

class DataViewer:
	attributes:
		plot_objects:  [obj]
		begin_time
		end_time
	
    def __init__(self, plot_objects):
	
	method:
		set_time_range(bgtime, edtime):
			for b in self.plot_objects:
				b.set_time_range(bgtime, edtime)
		draw()
			for b in self.plot_objects:
				b.plot()