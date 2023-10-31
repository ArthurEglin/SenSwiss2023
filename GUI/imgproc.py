import numpy as np
import cv2
from scipy.optimize import curve_fit

class ROIparams:
    def __init__(self, radius: float, height: float, width: float, shape_type: str):
        self.radius = radius
        self.height = height
        self.width = width
        self.shape_type = shape_type


def get_avg_intensity(img: np.ndarray, thr: float, params: ROIparams, kernel_size: int, dilation_number: int, ROIblocked: bool, center) -> float:
    """
    Get the average intensity of the image in the region of interest.

    :param img: The image to be processed.
    :param thr: The threshold to be used for the mask. Pixels with 
        intensity above this threshold will be included in the mask.
    :param radius: The radius of the circular mask.
    :param kernel_size: The size of the kernel used for dilation.
    :param dilation_number: The number of times the mask is dilated.
    :type img: np.ndarray
    :type thr: float
    :type radius: float
    :type kernel_size: int
    :type dilation_number: int

    :return: The average intensity of the image in the region of interest.
    """
    if not ROIblocked:
        smoothed = cv2.GaussianBlur(img, (15, 15), 0)
        #I would change the Kernel size to 15, 15 from 201, 201 => and then try 
        mask = cv2.threshold(smoothed, thr, 255, cv2.THRESH_BINARY)[1]
        dilated = cv2.dilate(mask, np.ones((kernel_size,kernel_size),np.uint8), iterations=dilation_number)
        M = cv2.moments(dilated)
        #I added binaryImage=True to the moments function
        if M["m00"] == 0:
            cX, cY = center
        else:
            cX = int(M["m10"] / M["m00"])
            cY = int(M["m01"] / M["m00"])
    else:
        cX, cY = center
        
    mask = np.zeros_like(img, dtype=np.uint8)

    if params.shape_type == "circle":
        cv2.circle(mask, (cX, cY), params.radius, 255, -1)
    elif params.shape_type == "rectangle":
        cv2.rectangle(mask, (cX - int(params.width/2), cY - int(params.height/2)), (cX + int(params.width/2), cY + int(params.height/2)), 255, -1)
    else:
        raise ValueError("Invalid ROI shape type.")

    ave = np.mean(img[mask == 255])

    return ave, (cX, cY)


def exponential(x, a, b, c):
    """
    Exponential function. Will compute a * exp(-b * (x - x0)) + c.

    :param x: The independent variable.
    :param a: The amplitude.
    :param b: The decay constant.
    :param c: The offset.
    :type x: np.array(float)
    :type a: float
    :type b: float
    :type c: float

    :return: The value of the exponential function.
    """
    return a * np.exp(-b * (x - x[0])) + c

def linear_function(x, a, b):
    return a * x + b
    
def fit_segment(time_segment, segment):
    """
    Fit a segment with the exponential function.
    It will enforce the curve to pass through the first point of the segment.

    :param time_segment: The time segment of the data.
    :param segment: The segment of the data.

    :type time_segment: list
    :type segment: list

    :return: The parameters of the exponential function.
    """
    sigma = np.ones(len(segment))
    sigma[0] = 0.0001

    try:
        params, _ = curve_fit(exponential, time_segment, segment, sigma=sigma)

    except RuntimeError:
        params = curve_fit(linear_function, time_segment, segment, sigma=sigma)
        expo = False
        params.append(expo)
    return params

def fit_all_segments(time_segments, segments):

    """
    Fit all the segments with the exponential function.

    :param time_segments: The time segments of the data.
    :param segments: The segments of the data.

    :type time_segments: list
    :type segments: list

    :return: The parameters of the exponential function for each segment.
    """
    params = []
    params_clean = []
    
    # Fit the first segment
    params.append(fit_segment(time_segments[0], segments[0]))

    # Fit the rest of the segments
    for i in range(1, len(time_segments)):
        # The first point of the segment is the last point of the previous fit
        if params[i-1][-1] == False: #if the last fit was linear
            #take only the linear function parameters
            params4 = params[i-1][0:2]
            params_clean.append(params4)
            last_fit = linear_function(time_segments[i-1], *params4)
        else: #if the last fit was exponential
            last_fit = exponential(time_segments[i-1], *params[i-1])

        # last_fit = exponential(time_segments[i-1], *params[i-1])
        time_segment = np.concatenate(([time_segments[i-1][-1]], time_segments[i]))
        segment = np.concatenate(([last_fit[-1]], segments[i]))

        params.append(fit_segment(time_segment, segment))
    
    if params[-1][-1] == False:
        params4 = params[-1][0:2]
        params_clean.append(params4)
    
    return params, params_clean
#params  parameters for the exponential function

def post_processing(time, data_to_fit, titles, mov_avg_size):
    """
    Perform post-processing on the data to fit. It assumes that the data to fit is exponential.
    The titles list should be same length as the data_to_fit list. Everytime it contains
    anything else than "", it considers that the data to fit is a new set of data.

    :param time: The time data.
    :param data_to_fit: The data to fit.
    :param titles: The titles of the data to fit.

    :type time: list
    :type data_to_fit: list
    :type titles: list

    :return: A vector being the concatenation of all fitted exponential functions.
    """

    try:
        mov_avg_size = int(mov_avg_size)
        if mov_avg_size < 1 or mov_avg_size > len(data_to_fit):
            mov_avg_size = 1
            print("Invalid moving average size. Using 1 instead.")
    except ValueError:
        mov_avg_size = 1
        print("Invalid moving average size. Using 1 instead.")

    # Aplly a smoothing filter to the data
    wavelength_moving_avg = np.convolve(data_to_fit, np.ones(mov_avg_size)/mov_avg_size, mode='valid')
    time_moving_avg = time[mov_avg_size-1:]

    # Create the different segments of data
    segments = []
    current_segment = []
    time_segments = []
    current_time_segment = []
    segment_titles = ["Start"]
    for i in range(len(time_moving_avg)):
        current_segment.append(wavelength_moving_avg[i])
        current_time_segment.append(time_moving_avg[i])
        if titles[i] != "":
            segment_titles.append(titles[i])
            segments.append(current_segment)
            time_segments.append(current_time_segment)
            current_segment = []
            current_time_segment = []

    segments.append(current_segment)
    time_segments.append(current_time_segment)

    # Fit the segments
    params, p_clean = fit_all_segments(time_segments, segments)

    # Create the fitted data

    # here correct the plot 
    fitted_data = []
    for i in range(len(segments)):
        fitted_data.append(exponential(time_segments[i], *params[i]))

    # Concatenate the fitted data
    fitted_data = np.concatenate(fitted_data)
    time_concat = np.concatenate(time_segments)

    # Return concatenated data for debugging
    return fitted_data, time_concat


### POST PROCESSING - SECOND METHOD

# Define the decaying exponential function
def decaying_exponential_func(x, a, b, c):
    return a * np.exp(-b * x) + c

# Define the segment for fitting
begin_instant = 2
end_instant = 7

def fit_exponential_segment(x_data, y_data, begin_instant, end_instant):
    """
    Fit a segment of data with the decaying exponential function.

    :param x_data: The x data.
    :param y_data: The y data.
    :param begin_instant: The beginning of the segment.
    :param end_instant: The end of the segment.

    :type x_data: np.array(float)
    :type y_data: np.array(float)
    :type begin_instant: float
    :type end_instant: float

    :return: The fitted parameters.
    """
    # Find the indices corresponding to the segment
    begin_index = np.argmin(np.abs(x_data - begin_instant))
    end_index = np.argmin(np.abs(x_data - end_instant))

    # Extract the segment data
    x_segment = x_data[begin_index:end_index+1]
    y_segment = y_data[begin_index:end_index+1]

    # Fit the decaying exponential function to the segment data
    params, covariance = curve_fit(decaying_exponential_func, x_segment, y_segment)

    # Extract the fitted parameters
    a_fit, b_fit, c_fit = params

    # Generate the fitted curve for the entire range
    y_fit = decaying_exponential_func(x_data, a_fit, b_fit, c_fit)

    return params, y_fit


def find_index_of_element(arr, target):
    for index, element in enumerate(arr):
        if element == target:
            return index
    return -1  # Element not found

def compute_shift(time, wavelenght, comments, window_size, gfap="GFAP", stop="STOP"):

    wavelength_avg = np.convolve(wavelenght, np.ones((window_size,))/window_size, mode='valid')

    # Find the indices corresponding to the beginning and end of the GFAP and STOP segments
    gfap_begin_index = find_index_of_element(comments, gfap)
    stop_begin_index = find_index_of_element(comments, stop)

    if gfap_begin_index == -1:
        print("Error searching for " + gfap + " in comments")
        return 0

    if stop_begin_index == -1:
        print("Error searching for " + stop + " in comments")
        return 0

    try:
        shift = wavelength_avg[stop_begin_index - window_size] - wavelength_avg[gfap_begin_index - window_size]
    except IndexError:
        print("Error computing shift, index too big, wait a bit")
        return 0
    
    return shift










