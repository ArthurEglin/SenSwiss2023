import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

# Importing the dataset
dataset = pd.read_csv('plots_saved/spectrometer_plot_20230829_102042_calibration1.csv')
#dataset = pd.read_csv('plots_saved/spectrometer_plot_20230825_094309_Olygo_83cc.csv')

time = dataset.iloc[:, 0].values
wavelength = dataset.iloc[:, 1].values
# Import comments as strings
comments = dataset.iloc[:, 2].values.astype(str)
centroids = dataset.iloc[:, 3].values

min_centroid = min(centroids)
max_centroid = max(centroids)

# Moving average
window_size = 20
centroids_avg = np.convolve(centroids, np.ones((window_size,))/window_size, mode='valid')
wavelength_avg = np.convolve(wavelength, np.ones((window_size,))/window_size, mode='valid')

plot_centroid = True

# Plotting centroids vs time and a vertical line at the time of the comment
if plot_centroid:
    plt.plot(time, centroids, color='b', label='Centroid', alpha=0.5)
    plt.plot(time[window_size-1:], centroids_avg, color='r', label='Centroid Moving Average')
else:
    plt.plot(time, wavelength, color="green", label="Raw", alpha=0.5)
    plt.plot(time[window_size-1:], wavelength_avg, color="green", label="Moving average")

for i in range(len(comments)):
    if comments[i] != "nan":
        plt.axvline(x=time[i], color='r', linestyle='--')
        plt.text(time[i], min_centroid + (max_centroid - min_centroid)/50, comments[i], rotation=90)

plt.xlabel('Time (s)')
plt.ylabel('Centroid (nm)')
plt.title('Centroid vs Time')
plt.legend()
plt.grid()
plt.show()