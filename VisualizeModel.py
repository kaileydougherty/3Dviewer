# Create a 3D visualization for distributed fiber optic sensing data for microseismic events.
# Author: Kailey Dougherty
# Date created: 24-FEB-2025
# Date last modified: 31-MAR-2025

# Import needed libraries
import pandas as pd
import numpy as np
import os
import plotly.graph_objects as go

# NEXT TASKS:
# (1) Take BEG and END times from all objects and combine
# (2) Define scroll bar (JUST APPEAR BETWEEN, NOT MOVIE) - take well log as just end snapshot
# (3) Depending on type of go., make IF branching in .draw()'''

class DataViewer:
	
	def __init__(self, plot_objects):
		self.plot_objects = plot_objects
	
	def	draw(self):
		fig = go.Figure()

		for b in self.plot_objects:	
			if isinstance(b, list):
				for c in b:
					if isinstance(c, go.Scatter3d):  #If yes, add as trace
						fig.add_trace(c)

					else:  #Otherwise, print error message
						print(f"Invalid object: {c}")
			else:	
				# Check if the object is valid
				if isinstance(b, go.Scatter3d):  #If yes, add as trace
					fig.add_trace(b)

				else:  #Otherwise, print error message
					print(f"Invalid object: {b}")

		# Update layout for the 3D plot
		fig.update_layout(
			scene=dict(
				xaxis=dict(
					title='Easting (ft)'
				),
				yaxis=dict(
					title='Northing (ft)'
				),
				zaxis=dict(
					title='Depth (ft)'
				)
			),
			legend=dict(
				x=0.8,
				y=0.9,
				xanchor='left',
				yanchor='top'
			)
		)

		return fig.show()
