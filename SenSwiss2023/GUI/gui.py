# import librairies
import PySimpleGUI as sg
from PIL import Image, ImageTk, ImageGrab
import PySpin
import matplotlib.pyplot as plt
import matplotlib.figure
import os
import numpy as np
import cv2
import pandas as pd
import csv
import serial
import serial.tools.list_ports
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from io import BytesIO
import base64
import typing
from seabreeze.spectrometers import Spectrometer
from scipy import signal
import time
import sys

# import code files
import control_flir_camera
import microflu
import imgproc
import arduino_control
import layout

# Used to display plot on interface
class Canvas(FigureCanvasTkAgg):
    """
    Create a canvas for matplotlib pyplot under tkinter/PySimpleGUI canvas
    """
    def __init__(self, figure=None, master=None):
        super().__init__(figure=figure, master=master)
        self.canvas = self.get_tk_widget()
        self.canvas.pack(side="top", fill="both", expand=1)

def connect_spectrometer() -> (Spectrometer, bool):
    print("Connection with spectrometer")
    spec = None
    try:
        spec = Spectrometer.from_first_available()
        spec_connected = True
        if spec.model == "MAYA2000PRO":
            print("Spectrometer MAYA2000PRO connected")
        else:
            spec_connected = False
            print("Unrecognized spectrometer connected")

    except Exception as e:
        print("Connection with spectrometer failed")
        spec_connected = False
        print(e)

    return spec, spec_connected

def linkFigToWindow(winCan: Canvas, fig: matplotlib.figure.Figure) -> None:
    """ 
    Link a matplotlib figure to the canvas
    """
    canvas = Canvas(fig, winCan.Widget)
    plot_widget = canvas.get_tk_widget()
    plot_widget.pack(side='top', fill='both', expand=1)
    return
    
def updatePlot(fig: matplotlib.figure.Figure, ax: plt.Axes, data_y: list, data_x: list, autoYLim: bool, minY: float, maxY: float, title="Default Title", x_axis_title="Default axis", y_axis_title="Default axis", legends: list = [], data_y_2: list = [], comments: list = [], mov_avg_size: int = -1) -> None:
    """
    Update a plot if the fig is already linked to the window
    """
    ax.cla()
    ax.set_title(title) #"Real time measurement of average intensity"
    ax.set_xlabel(x_axis_title) #"Time [s]"
    ax.set_ylabel(y_axis_title) #"Intensity"
    if not autoYLim:
        ax.set_ylim(minY, maxY)
    ax.grid()

    ax.plot(data_x, data_y, color='blue')

    if mov_avg_size > 0 and len(data_y) > mov_avg_size:
        ax.plot(data_x[mov_avg_size-1:], np.convolve(data_y, np.ones(mov_avg_size)/mov_avg_size, mode='valid'), color='red')

   

    if len(data_y_2) > 0:
        ax.plot(data_x, data_y_2, color='green')

    if len(legends) > 0:
        ax.legend(legends)

    # Get min and max y lim of the ax
    min_y, max_y = ax.get_ylim()
    y_pos_text = min_y + (max_y - min_y)/50

    if len(comments) > 0:
        # Add vertical lines to show when the comments were made
        # and the text of the comment, there indices allows to find time
        for i in range(len(comments)):
            if comments[i] != '':
                ax.axvline(x=data_x[i], color='r', linestyle='--')
                ax.text(data_x[i], y_pos_text, comments[i], rotation=90)

    if len(data_x) > 0:
        ax.plot(data_x[-1], data_y[-1], 'rx')
        ax.text(data_x[-1], data_y[-1], str(data_y[-1]))

    fig.canvas.draw()

def save_element_as_file(element, filename: str):
    """
    Saves any element as an image file.  Element needs to have an underlyiong Widget available (almost if not all of them do)
    :param element: The element to save
    :param filename: The filename to save to. The extension of the filename determines the format (jpg, png, gif, ?)
    """
    widget = element.Widget
    box = (widget.winfo_rootx(), widget.winfo_rooty(), widget.winfo_rootx() + widget.winfo_width(), widget.winfo_rooty() + widget.winfo_height())
    grab = ImageGrab.grab(bbox=box)
    grab.save(filename)

def get_new_image(cam: PySpin.Camera, data_to_plot: list, drawROI: bool, threshold, params, kernel_size, dilation_number, ROIblocked, ROIcenter) -> bool:
    """
    Get a new image from the camera and display it
    If required can save the image and add its average intensity to the plot
    """

    try:
        image_result = cam.GetNextImage(100)

        if image_result.IsIncomplete():
            raise Exception("Image incomplete with image status {} ...".format(image_result.GetImageStatus()))

        else:
            image_data = image_result.GetNDArray()
            image_result.Release()
            # Get average intensity
            ave, center = imgproc.get_avg_intensity(image_data, threshold, params, kernel_size, dilation_number, ROIblocked, ROIcenter)
            data_to_plot.append(ave)
            if drawROI:
                cX, cY = center
                if params.shape_type == "circle":
                    cv2.circle(image_data, (cX, cY), params.radius, 255, 10)
                elif params.shape_type == "rectangle":
                    cv2.rectangle(image_data, (cX - int(params.width/2), cY - int(params.height/2)), (cX + int(params.width/2), cY + int(params.height/2)), 255, 10)
                else:
                    raise ValueError("Invalid ROI shape type.")

            # Reduce image to display
            resized_width, resized_height = [
                int(i * reducing_factor) for i in image_data.shape
            ]
            image_data = cv2.resize(image_data, (resized_height, resized_width))
            # To display img after
            buffered = BytesIO()
            Image.fromarray(image_data).save(buffered, format="PNG", compress_level=0) 
            img_str = base64.b64encode(buffered.getvalue())
            buffered.close()
            window["cameraGraph"].erase()
            window["cameraGraph"].DrawImage(data=img_str, location=(0,0))
            window.refresh()

            return True, center
    except:
        print("Error while getting image or processing it, nice weather today")
        pass
    return False, ROIcenter

# Init commands list
protocol_list = []
for file in os.listdir("protocols"):
    if file.endswith(".csv"):
        protocol_list.append(file)

wavelet = 1

################### MAIN ###################
if __name__ == "__main__":

    # Absolute path of this file folder
    path: str = os.path.dirname(os.path.abspath(__file__))
    
    # Creation of directories for image storage
    try:
        os.mkdir(path + "/images_saved")
    except:
        pass
    try:
        os.mkdir(path + "/plots_saved")
    except:
        pass
    
    # Init pump
    print("Connection with pump")
    pump_connected: bool = False
    lsp, pump_connected = microflu.connect_pump()
    
    # Init arduino
    print("Connection with arduino")
    arduino_connected: bool = False
    arduino, arduino_connected = arduino_control.connect_arduino()

    # Init camera / spectrometer, only one or the other
    print("Connection with camera")
    camera_connected: bool = True
    try:
        system = PySpin.System.GetInstance()
        cam_list = system.GetCameras()
        num_cameras = cam_list.GetSize()
        if num_cameras != 1:  # No camera or more than one camera
            cam_list.Clear()
            system.ReleaseInstance()
            # raise Exception("Single camera not detected")
            print("Single camera not detected")
            camera_connected = False
        else:
            print("Camera connected")
            cam = cam_list[0]

            # Init camera
            control_flir_camera.init_camera(cam)

    except Exception as e:
        print("Connection with camera failed")
        camera_connected = False
        print(e)

    spec_connected: bool = False
    if not camera_connected:
        # Init spectrometer
        spec, spec_connected = connect_spectrometer()
    
    # Logo
    logo_size: typing.Tuple[int, int] = (100, 40)
    logo_im: Image.Image = Image.open(path + "/layout_figures/SenSwissLogo.png")
    logo_im = logo_im.resize(logo_size, resample=Image.BICUBIC)

    # Size of image displayed
    camera_img_size = (3648, 5472)
    reducing_factor = 0.09
    max_num_command: int = 99

    # Create the layout of the window
    if camera_connected:
        device_connected = 1
    elif spec_connected:
        device_connected = 2
    else:
        device_connected = 0
    win_layout = layout.create_layout(logo_size, camera_img_size, reducing_factor, device_connected) #

    sg.theme("SystemDefault")
    AppFont = "Any 10"

    # Create the window
    window: sg.Window = sg.Window(
        "SenSwiss - User interface",
        win_layout,
        resizable=True,
        no_titlebar=False,
        auto_size_buttons=True,
        font=AppFont,
    ).Finalize()
    # The following values were found by trial, if it doesn't work for you, try some new ones using 
    #print(window.size) in the while loop to see the size of your window
    window.set_min_size((1070, 765))

    logo_image = ImageTk.PhotoImage(image=logo_im)
    window["logoImage"].update(data=logo_image)

    # acquire the exposure time and the gain value of the camera
    if camera_connected == True:
        control_flir_camera.configure_exposure(cam, float(window["exposureTime"].get()))
        control_flir_camera.configure_gain(cam, window["gainValue"].get())

    # Variables to control the saving of images
    save_img: bool = False
    drawROI: bool = False
    blockROI: bool = False
    
    # Variables for the ROI and image processing
    ROI_params: imgproc.ROIparams = imgproc.ROIparams(500, 1000, 1000, "circle")
    ROI_center = (0,0)
    kernel_size = 3
    dilation_number = 2
    filter_threshold = 90

    # Pandas dataframe to store the commands
    # Used to follow the protocol and be able able to automatically add comments
    commands_df = pd.DataFrame(columns=["port", "action", "volume", "speed", "title"])
    current_command = -1

    # Create the fig and ax and link them to the window for the intensity plot
    intensity_fig, intensity_ax = plt.subplots(figsize=(5,4))
    linkFigToWindow(window["plotGraph"], intensity_fig)
    if spec_connected == True and camera_connected == False:
        spectrometer_fig, spectrometer_ax = plt.subplots(figsize=(5,4))
        linkFigToWindow(window["cameraGraph"], spectrometer_fig)
    
    # Store the intensities to plot
    if camera_connected == True and spec_connected == False:
        intensities: typing.List[float] = []
        time_of_intensities: typing.List[float] = []
        clear_time: float = time.time()
        auto_scale: bool = False
        min_y: int = 0
        max_y: int = 260 # max value of the camera is 255 for an 8bit value, but we add a bit of margin
        updatePlot(intensity_fig, intensity_ax, intensities, time_of_intensities, auto_scale, min_y, max_y, "Real time measurement of average intensity", "Time [s]", "Intensity [a.u.]")

    if spec_connected == True and camera_connected == False:
        wavelengths: typing.List[float] = []
        intensities_spec: typing.List[float] = []
        comments: typing.List[str] = []
        comment_added: bool = False
        comment_to_add: str = ""

        title_delay: float = -1
        title_add_time: float = 0
        title_to_add: str = ""

        normalized_intensities_spec: typing.List[float] = []
        normalize_gain: float = 1

        min_peak_wavelength: typing.List[float] = []
        time_of_intensities_spec: typing.List[float] = []
        clear_time: float = time.time()
        auto_scale: bool = False
        min_y: int = 500
        max_y: int = 900

        flat_field: typing.List[float] = []
        flat_field_saving: bool = False
        flat_field_counter: int = 0
        dark_field: typing.List[float] = []
        dark_field_saving: bool = False
        dark_field_counter: int = 0
        num_frames_for_save: int = 50

        wavelength_min: int = 500
        wavelength_max: int = 900

        moving_average_size: int = 20
        SG_window: int = 100

        updatePlot(spectrometer_fig, spectrometer_ax, intensities_spec, wavelengths, True, min_y, max_y, "Real time measurement of average intensity", "Wavelength [nm]", "Intensity [a.u.]")
        updatePlot(intensity_fig, intensity_ax, min_peak_wavelength, time_of_intensities_spec, auto_scale, min_y, max_y, "Shift of the absorption peak over time", "Time [s]", "Wavelength [nm]")
        
    # Variables to find and save centroid of intensities around minimum peak
    centroid_window_size: int = 250
    window_fixed: bool = False
    index_min: int = 0
    centroids: typing.List[float] = []

    # Variables to control the acquisition period
    last_acquisition_time: float = 0
    acqPeriod: float = 0.5 # in seconds

    # Variable to control amount of commands
    command_number: int = 0

    # Run the Event Loop
    while True:

        if pump_connected:
            try:
                bytesToRead = lsp.inWaiting()
            except:
                print("Error while reading from pump")
                pump_connected = False
                print("Check pump connection and reboot")
            if pump_connected and bytesToRead > 0:
                try:
                    message = lsp.readline()
                except:
                    print("Error while reading from pump")
                    pump_connected = False
                    print("Check pump connection and reboot")
                #print(message)
                if (pump_connected and message == b'/0`12\x03\r\n'):
                    current_command += 1
                    # As a test, display the infos of the current command
                    # print(commands_df.iloc[current_command])
                    try:
                        if commands_df.iloc[current_command]["action"] == "Dispense" or commands_df.iloc[current_command]["action"] == "Pick":
                            title_delay = microflu.get_dispense_time(commands_df.iloc[current_command]["speed"])
                            title_add_time = time.time()
                            title_to_add = commands_df.iloc[current_command]["title"]
                    except:
                        print("Error while getting dispense time")

        if spec_connected and dark_field_saving:
            if len(dark_field) == 0:
                dark_field = intensities_spec
            else:
                dark_field = dark_field + intensities_spec
                
            dark_field_counter += 1

            if dark_field_counter == num_frames_for_save:
                dark_field = dark_field / num_frames_for_save
                dark_field_saving = False
                dark_field_counter = 0
                
                if window["darkFieldStatus"].get() == "Dark field saved":
                    window["darkFieldStatus"].update("Dark field updated")
                else:
                    window["darkFieldStatus"].update("Dark field saved")
                if len(flat_field) > 0:
                    normalize_gain = np.mean(flat_field - dark_field)

        if spec_connected and flat_field_saving:
            if len(flat_field) == 0:
                flat_field = intensities_spec

            else:
                flat_field = flat_field + intensities_spec
                
            flat_field_counter += 1

            if flat_field_counter == num_frames_for_save:
                flat_field = flat_field / num_frames_for_save
                flat_field_saving = False
                flat_field_counter = 0
                if window["flatFieldStatus"].get() == "Flat field saved":
                    window["flatFieldStatus"].update("Flat field updated")
                else:
                    window["flatFieldStatus"].update("Flat field saved")
                if len(dark_field) > 0:
                    normalize_gain = np.mean(flat_field - dark_field)

        # Acquisition of a new image
        if camera_connected == True and (time.time() - last_acquisition_time) > acqPeriod and spec_connected == False:
            success, ROI_center = get_new_image(cam, intensities, drawROI, filter_threshold, ROI_params, kernel_size, dilation_number, blockROI, ROI_center)
            if success:
                time_of_intensities.append(time.time() - clear_time)    
                updatePlot(intensity_fig, intensity_ax, intensities, time_of_intensities, auto_scale, min_y, max_y, "Real time measurement of average intensity", "Time [s]", "Intensity [a.u.]")
            
            last_acquisition_time = time.time()

        if spec_connected == True and (time.time() - last_acquisition_time) > acqPeriod and camera_connected == False:

            # Get the spectrum
            try:
                wavelengths = spec.wavelengths()
                wavelengths = wavelengths[100:-100] # Remove the first and last 100 values if the spectrum is too noisy at the extremities
                intensities_spec = spec.intensities()
                intensities_spec = intensities_spec[100:-100] # Remove the first and last 100 values if the spectrum is too noisy at the extremities
            except:
                spec_connected = False
                print("Error while getting spectrum")
                print("Check spectrometer connection and reboot")

            # Low pass filter to smooth the spectrum
            intensities_spec = signal.savgol_filter(intensities_spec, window_length=SG_window, polyorder=2, mode="nearest")
            
            if len(dark_field) > 0 and len(flat_field) > 0:
                normalized_intensities_spec = (intensities_spec - dark_field) / (flat_field - dark_field) * normalize_gain
            else:
                normalized_intensities_spec = intensities_spec

            # Remove all values if wavelength is not in the range
            ranged_intensities_spec = intensities_spec[np.logical_and(wavelengths > wavelength_min, wavelengths < wavelength_max)]
            ranged_wavelengths = wavelengths[np.logical_and(wavelengths > wavelength_min, wavelengths < wavelength_max)]
            ranged_normalized_intensities_spec = normalized_intensities_spec[np.logical_and(wavelengths > wavelength_min, wavelengths < wavelength_max)]
            
            index_min_normalized = np.argmin(ranged_normalized_intensities_spec)

            wavelength_min_peak = ranged_wavelengths[index_min_normalized]

            if len(dark_field) > 0 and len(flat_field) > 0 and (not window_fixed):
                print("Position of min peak: " + str(wavelength_min_peak) + " nm")

                # Get index at same wavelength in the original spectrum
                index_min = np.where(wavelengths == ranged_wavelengths[index_min_normalized])[0][0]

                window_limits = (index_min - centroid_window_size, index_min + centroid_window_size)
                if window_limits[0] < 0:
                    window_limits = (0, index_min + centroid_window_size)
                if window_limits[1] > len(wavelengths):
                    window_limits = (index_min - centroid_window_size, len(wavelengths)-1)

                print("Min and max wavelength: " + str(wavelengths[window_limits[0]]) + " nm, " + str(wavelengths[window_limits[1]]) + " nm")
                window["minPeakStatus"].update("Min : " + str(wavelengths[window_limits[0]]) + " nm, Max : " + str(wavelengths[window_limits[1]]) + " nm")
                window_fixed = True

            if window_fixed:
                # Get x centroid of intensities around minimum peak

                window_limits = (index_min - centroid_window_size, index_min + centroid_window_size)
                if window_limits[0] < 0:
                    window_limits = (0, index_min + centroid_window_size)
                if window_limits[1] > len(wavelengths):
                    window_limits = (index_min - centroid_window_size, len(wavelengths))
                
                reversed_intensities_spec = np.max(normalized_intensities_spec) - normalized_intensities_spec

                centroid = np.sum(wavelengths[window_limits[0]:window_limits[1]] * reversed_intensities_spec[window_limits[0]:window_limits[1]]) / np.sum(reversed_intensities_spec[window_limits[0]:window_limits[1]])
                centroids.append(centroid)
            else:
                centroids.append(wavelength_min_peak)

            min_peak_wavelength.append(wavelength_min_peak)
            time_of_intensities_spec.append(time.time() - clear_time)
            if title_delay > 0 and time.time() - title_add_time > title_delay:
                comments.append(title_to_add)
                title_delay = -1
                title_add_time = 0
                title_to_add = ""
            elif comment_added == True:
                comments.append(window["plotComment"].get())
                comment_added = False
                layout.activateButton(window["addComment"], True)
                layout.activateInput(window["plotComment"], True)
            else:
                comments.append("")

            if window["plotRaw"].get() == True:
                if window["plotNormalized"].get() == True:
                    updatePlot(spectrometer_fig, spectrometer_ax, ranged_intensities_spec, ranged_wavelengths, True, min_y, max_y, "Real time measurement of average intensity", "Wavelength [nm]", "Intensity [a.u.]", ["Spectrometer", "Normalized"], ranged_normalized_intensities_spec)
                else:
                    updatePlot(spectrometer_fig, spectrometer_ax, ranged_intensities_spec, ranged_wavelengths, True, min_y, max_y, "Real time measurement of average intensity", "Wavelength [nm]", "Intensity [a.u.]", ["Spectrometer"])
            elif window["plotNormalized"].get() == True:
                updatePlot(spectrometer_fig, spectrometer_ax, ranged_normalized_intensities_spec, ranged_wavelengths, True, min_y, max_y, "Real time measurement of average intensity", "Wavelength [nm]", "Intensity [a.u.]", ["Normalized"])
            
            updatePlot(intensity_fig, intensity_ax, min_peak_wavelength, time_of_intensities_spec, auto_scale, min_y, max_y, "Shift of the absorption peak over time", "Time [s]", "Wavelength [nm]", legends=["Raw", "Average", "Centroids"], data_y_2=centroids, comments=comments, mov_avg_size=moving_average_size)
            last_acquisition_time = time.time()
        
        # Read the Event Loop
        event, values = window.read(timeout=10)

        if event == "Exit" or event == sg.WIN_CLOSED:
            break
        
        elif event == "reconnectPump":
            if not pump_connected:
                lsp, pump_connected = microflu.connect_pump()
            else:
                print("Pump already connected!")
        
        elif event == "kickOutBubble":
            if pump_connected == True:
                seq = microflu.get_kick_bubble_seq(window["inputPickupValve"].get(), window["inputDispenseValve"].get())
                pump_connected = microflu.write_sequence_to_pump(lsp, seq)
            else:
                print("Check pump connection")

        elif event == "functionalizeChip":
            if pump_connected == True:
                channel_chosen = window["functionalizeChannel"].get()
                if channel_chosen == "Channel 1" or channel_chosen == "Channel 2":
                    channel_1_chosen = True if channel_chosen == "Channel 1" else False
                    seq = microflu.get_functionalize_seq(channel_1_chosen)
                    pump_connected = microflu.write_sequence_to_pump(lsp, seq)
                else:
                    print("Choose a channel")
            else:
                print("Check pump connection")

        elif event == "goToZero":
            if pump_connected == True:
                print("Going to zero")
                pump_connected = microflu.go_to_zero(lsp)
            else:
                print("Check pump connection")

        elif event == "reinit":
            if pump_connected == True:
                pump_connected = microflu.initialize_LSPOne(lsp)
            else:
                print("Check pump connection")

        elif event == "switchValve":
            if pump_connected == True:
                seq = microflu.change_to_valve_fastest(values['inputChosenValve'])
                pump_connected = microflu.write_sequence_to_pump(lsp, seq)
            else:
                print("Check pump connection")

        elif event == "setSpeed":
            if pump_connected == True:
                try:
                    seq = microflu.peak_speed_uL_min(window["inputChosenSpeed"].get())
                    pump_connected = microflu.write_sequence_to_pump(lsp, seq)
                except:
                    print("Issue setting speed")
                    pump_connected = False
            else:
                print("Check pump connection")

        elif event == "pickupVolume":
            if pump_connected == True:
                seq = microflu.pickup_uL(float(values['inputChosenPickUpVolume']))
                print(seq)
                pump_connected = microflu.write_sequence_to_pump(lsp, seq)
            else:
                print("Check pump connection")

        elif event == "dispenseVolume":
            if pump_connected == True:
                seq = microflu.dispense_uL(float(values['inputChosenDispenseVolume']))
                print(seq)
                pump_connected = microflu.write_sequence_to_pump(lsp, seq)
            else:
                print("Check pump connection")

        elif event == "heatON":
            if pump_connected == True:
                seq = microflu.get_heat_seq(values['inputTemperature'])
                pump_connected = microflu.write_sequence_to_pump(lsp, seq)
            else:
                print("Check pump connection")

        elif event == "heatOFF":
            if pump_connected == True:
                pump_connected = microflu.write_sequence_to_pump(lsp, "@INCUBOFFR")
            else:
                print("Check pump connection")
    
        elif event == "addCommand":
            if command_number < max_num_command:
                window.extend_layout(window['commandFrame'], layout.new_line(command_number))

                window.visibility_changed()
                window["scrollableCollumn"].contents_changed()
                command_number += 1

                # Deactivate the button
                if command_number == max_num_command:
                    layout.activateButton(window["addCommand"], False)
            else:
                print("Too many commands")

        elif event == "copyCommands":
            commands_seq = pd.DataFrame(columns=["port", "action", "volume", "speed", "title", "wait"])
            for k in range(command_number):
                if window[f'copy_{k}'].get():
                    port: str = window[f'port_{k}'].get()
                    action: str = window[f'action_{k}'].get()
                    volume: str = window[f'volume_{k}'].get()
                    speed: str = window[f'speed_{k}'].get()
                    title: str  = window[f'title_{k}'].get()
                    wait: str = window[f'wait_{k}'].get()
                    
                    # If all fields are valid, add the command to the commands dataframe
                    commands_seq = pd.concat([commands_seq, pd.DataFrame([[port, action, volume, speed, title, wait]], columns=["port", "action", "volume", "speed", "title", "wait"])], ignore_index=True)
            
            # write commands in the GUI using the commands stored in the dataframe
            for k in range(len(commands_seq)):
                window.extend_layout(window['commandFrame'], layout.new_line((command_number)))
                layout.update_line(k, window, commands_seq.iloc[k]["port"], commands_seq.iloc[k]["action"], commands_seq.iloc[k]["volume"], commands_seq.iloc[k]["speed"], commands_seq.iloc[k]["title"], commands_seq.iloc[k]["wait"])
                window.visibility_changed()
                window["scrollableCollumn"].contents_changed()
                command_number += 1

                # Deactivate the button
                if command_number == max_num_command:
                    layout.activateButton(window["addCommand"], False)
                    layout.activateButton(window["addWaitCommand"], False)
        
        elif event == "saveCommands":
            commands_seq = pd.DataFrame(columns=["port", "action", "volume", "speed", "title", "wait"])
            # load dataframe with commands
            for k in range(command_number):
                port: str = window[f'port_{k}'].get()
                action: str = window[f'action_{k}'].get()
                volume: str = window[f'volume_{k}'].get()
                speed: str = window[f'speed_{k}'].get()
                title: str  = window[f'title_{k}'].get()
                wait: str = window[f'wait_{k}'].get()
                
                # If all fields are valid, add the command to the commands dataframe
                commands_seq = pd.concat([commands_seq, pd.DataFrame([[port, action, volume, speed, title, wait]], columns=["port", "action", "volume", "speed", "title", "wait"])], ignore_index=True)
                
            # create a .csv file with commands from dataframe
            commands_seq.to_csv("protocols/" + window["protocolName"].get() + ".csv", index=False)

        elif event == "sendProtocol":
            protocol_name = window["protocolAuto"].get()
            if protocol_name != "":
                try:
                    if pump_connected == True:
                        commands_valid: bool = True
                        seq: str = ""
                        commands_seq = pd.read_csv("protocols/" + protocol_name)
                        # iterate through the commands_seq
                        for k in range(len(commands_seq)):
                            port: str = str(commands_seq.iloc[k]["port"])
                            action: str = commands_seq.iloc[k]["action"]
                            volume: str = str(commands_seq.iloc[k]["volume"])
                            speed: str = str(commands_seq.iloc[k]["speed"])
                            title: str  = commands_seq.iloc[k]["title"]
                            wait: str = commands_seq.iloc[k]["wait"]
                                                        
                            if port == "" and volume == "" and speed == "":
                                # Empty commands are ignored
                                continue
                            else:
                                # Check if all fields are filled correctly
                                try:
                                    # Port should be an int between 1 and 12
                                    if port in ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12"]:
                                        port = int(port)
                                    else:
                                        raise Exception
                                except:
                                    print("Invalid port, command " + str(k))
                                    window[f'port_{k}'].update("")
                                    commands_valid = False
                                    break

                                if action != "Pick" and action != "Dispense":
                                    print("Invalid action, command " + str(k))
                                    window[f'action_{k}'].update("Pick")
                                    commands_valid = False
                                    break

                                try:
                                    volume = float(volume)
                                    if volume < 3 or volume > 200:
                                        raise Exception
                                except:
                                    print("Invalid volume, command " + str(k))
                                    window[f'volume_{k}'].update("")
                                    commands_valid = False
                                    break

                                try:
                                    speed = float(speed)
                                    if (speed < 5) or (speed > 8000):
                                        raise Exception
                                except:
                                    print("Invalid speed, command " + str(k))
                                    window[f'speed_{k}'].update("")
                                    commands_valid = False
                                    break
                                
                                try:
                                    if wait != "":
                                        wait = int(wait)
                                        if wait < 0 or wait > 86400000:
                                            raise Exception
                                    else:
                                        wait = 0
                                except:
                                    print("Invalid wait, command " + str(k))
                                    window[f'wait_{k}'].update("")
                                    commands_valid = False
                                    break

                                # If all fields are valid, add the command to the sequence
                                seq += microflu.seq_from_command(port, action, volume, speed, title, wait)
                                   
                        if commands_valid:
                            if command_number > 0:
                                if layout.yesNoPopup("Send commands?", "Send commands"):
                                    # If all commands are valid, send the sequence to the pump
                                    pump_connected = microflu.write_sequence_to_pump(lsp, seq)
                                    current_command = -1

                        else:
                            print("At least one command is invalid")
                    else:
                        print("Check pump connection")
                    
                except:
                    print("Error while reading protocol")

        elif event == "loadProtocol":
            protocol_name = window["protocolLoad"].get()
            if protocol_name != "":
                try:
                    commands_seq = pd.read_csv("protocols/" + protocol_name, keep_default_na=False)
                    
                    # write commands in the GUI using the commands stored in the dataframe
                    for k in range(len(commands_seq)):
                        if k >= command_number:
                            window.extend_layout(window['commandFrame'], layout.new_line(k))
                            command_number += 1
                        layout.update_line(k, window, commands_seq.iloc[k]["port"], commands_seq.iloc[k]["action"], commands_seq.iloc[k]["volume"], commands_seq.iloc[k]["speed"], commands_seq.iloc[k]["title"], commands_seq.iloc[k]["wait"])
                    
                    # Clear following lines if needed
                    k += 1
                    while(k < command_number):
                        layout.delete_line(k, window)
                        k += 1
                            
                    # Deactivate the button
                    if command_number == max_num_command:
                        layout.activateButton(window["addCommand"], False)
                        layout.activateButton(window["addWaitCommand"], False)
                            
                    window.visibility_changed()
                    window["scrollableCollumn"].contents_changed()
                except:
                    print("Error while reading protocol")

        elif event == "exposureTime":  # Exposure time
            if camera_connected == True:
                control_flir_camera.configure_exposure(cam, window["exposureTime"].get())
            else:
                print("Check camera connection and reboot")

        elif event == "gainValue":  # Gain
            if camera_connected == True:
                control_flir_camera.configure_gain(cam, window["gainValue"].get())
            else:
                print("Check camera connection and reboot")

        elif event == "saveImage":
            if camera_connected == True:
                end_of_name = time.strftime("%Y%m%d_%H%M%S")  + "_" + window["imageName"].get()
                save_element_as_file(window["cameraGraph"], path + "/images_saved/camera_image_" + end_of_name + ".png")
            else:
                print("Check camera connection and reboot")

        elif event == "addComment":
            if spec_connected == True:
                comment = window["plotComment"].get()
                if comment != "":
                    comment_added = True
                    comment_to_add = comment
                    layout.activateButton(window["addComment"], False)
                    layout.activateInput(window["plotComment"], False)

        elif event == "saveSpec":
            try:
                end_of_name = time.strftime("%Y%m%d_%H%M%S")  + "_" + window["specName"].get()
                save_element_as_file(window["cameraGraph"], path + "/images_saved/spectrometer_spectrograph_" + end_of_name + ".png")
                tosave = np.array([wavelengths, intensities_spec.reshape(1,len(wavelengths))[0], normalized_intensities_spec.reshape(1,len(wavelengths))[0]]).astype(str).transpose()
                tosave = np.insert(tosave, 0, ["Wavelengths", "Intensities", "Normalized"], axis=0)
                np.savetxt(path + "/plots_saved/spectrograph_plot_" + end_of_name + ".csv", tosave, delimiter=",", fmt="%s")
            except:
                print("Check spectrometer connection and reboot")

        elif event == "saveDarkField":
            if spec_connected == True:
                dark_field_saving = True
                dark_field_counter = 0
                dark_field = []
                dark_field = intensities_spec
                if window["darkFieldStatus"].get() == "Dark field saved":
                    window["darkFieldStatus"].update("Dark field updated")
                else:
                    window["darkFieldStatus"].update("Dark field saved")
                if len(flat_field) > 0:
                    normalize_gain = np.mean(flat_field - dark_field)

        elif event == "saveFlatField":
            if spec_connected == True:
                flat_field_saving = True
                flat_field_counter = 0
                flat_field = []
                flat_field = intensities_spec
                if window["flatFieldStatus"].get() == "Flat field saved":
                    window["flatFieldStatus"].update("Flat field updated")
                else:
                    window["flatFieldStatus"].update("Flat field saved")
                if len(dark_field) > 0:
                    normalize_gain = np.mean(flat_field - dark_field)

        elif event == "setMovingAverage":
            if spec_connected == True:
                try:
                    moving_average_size = int(window["movingAverage"].get())
                except:
                    moving_average_size = 100
                    window["movingAverage"].update("100")
                    print("Error while getting moving average input, moving average set to 100")

        elif event == "setSGwindow":
            if spec_connected == True:
                try:
                    SG_window = int(window["SavGol"].get())
                    if SG_window < 3:
                        SG_window = 3
                        window["SavGol"].update("3")
                        print("Savitzky-Golay window set to 3")
                except:
                    SG_window = 100
                    window["SavGol"].update("100")
                    print("Savitzky-Golay window set to 100")

        elif event == "resetMinPeak":
            try:
                centroid_window_size = int(window["centroidWidth"].get())
                if centroid_window_size < 1:
                    centroid_window_size = 1
                    window["centroidWidth"].update("1")
                    print("Centroid width set to 1")
            except:
                centroid_window_size = 50
                window["centroidWidth"].update("50")
                print("Error while getting centroid width input, centroid width set to 50")
            
            # Convert between nanometers and pixels, with 2068 pixels for 498-941 nm
            centroid_window_size = int(centroid_window_size * 2068 / (941 - 498))

            window_fixed = False

        elif event == "saveCameraPlot":
            end_of_name = time.strftime("%Y%m%d_%H%M%S") + "_" + window["plotName"].get()
            to_save = np.array([time_of_intensities, intensities]).astype(str).transpose()
            to_save = np.insert(to_save, 0, ["Time", "Intensities"], axis=0)
            np.savetxt(path + "/plots_saved/camera_plot_" + end_of_name + ".csv", to_save, delimiter=",", fmt="%s")
            intensity_fig.savefig(path + "/plots_saved/camera_plot_" + end_of_name + ".png", dpi=300)

        elif event == "saveSpecPlot":
            end_of_name = time.strftime("%Y%m%d_%H%M%S") + "_" + window["specPlotName"].get()
            to_save = np.array([time_of_intensities_spec, min_peak_wavelength, comments, centroids]).astype(str).transpose()
            to_save = np.insert(to_save, 0, ["Time", "Wavelengths", "Comments", "Centroids"], axis=0)
            np.savetxt(path + "/plots_saved/spectrometer_plot_" + end_of_name + ".csv", to_save, delimiter=",", fmt="%s")
            intensity_fig.savefig(path + "/plots_saved/spectrometer_plot_" + end_of_name + ".png", dpi=300)

        elif event == "reconnectSpectrometer":
            if not spec_connected:
                spec, spec_connected = connect_spectrometer()

        elif event == "clearPlot":
            if layout.yesNoPopup("Clear the plot?", "Clearing plot"):
                intensities = []
                time_of_intensities = []
                clear_time = time.time()
                updatePlot(intensity_fig, intensity_ax, intensities, time_of_intensities, auto_scale, min_y, max_y, "Real time measurement of average intensity", "Time [s]", "Intensity [a.u.]")

        elif event == "clearSpecPlot":
            if layout.yesNoPopup("Clear the plot?", "Clearing plot"):
                time_of_intensities_spec = []
                min_peak_wavelength = []
                comments = []
                centroids = []
                clear_time = time.time()
                updatePlot(intensity_fig, intensity_ax, min_peak_wavelength, time_of_intensities_spec, auto_scale, min_y, max_y, "Shift of the absorption peak over time", "Time [s]", "Wavelength [nm]")

        elif event == "computeShift":
            if spec_connected:
                gfapKey = window["gfapShiftKey"].get()
                stopKey = window["stopShiftKey"].get()
                shift_min = imgproc.compute_shift(time_of_intensities_spec, min_peak_wavelength, comments, moving_average_size, gfapKey, stopKey)
                shift_cen = imgproc.compute_shift(time_of_intensities_spec, centroids, comments, moving_average_size, gfapKey, stopKey)
                window['shiftTxt'].update("Shifts computed: min = " + str(shift_min) + "; centroid = " + str(shift_cen))
                print("Shifts computed: min = " + str(shift_min) + "; centroid = " + str(shift_cen))

        elif event == "acquisitionPeriod":
            try:
                acqPeriod = float(window["acquistionPeriodInput"].get())
            except:
                print("Invalid acquisition period")
                window["acquistionPeriodInput"].update("0.5")
                acqPeriod = 0.5

        elif event == "displayROI":
            # inverts the boolean each time
            drawROI = not drawROI
            if drawROI:
                window["displayROI"].update("Hide ROI")
            else:
                window["displayROI"].update("Show ROI")
        
        elif event == "ROIparams":
            ROI_params.radius = int(window["ROIradiusInput"].get())
            ROI_params.width = int(window["ROIwidthInput"].get())
            ROI_params.height = int(window["ROIheightInput"].get())
        
        elif event == "ROIshapeType":
            shape_type = window["ROIshapeType"].get()
            if shape_type != "circle" and shape_type != "rectangle":
                print("Invalid shape type")
                window["ROIshapeType"].update("circle")
                shape_type = "circle"
            
            ROI_params.shape_type = shape_type
            layout.activateInput(window["ROIwidthInput"], shape_type == "rectangle")
            layout.activateInput(window["ROIheightInput"], shape_type == "rectangle")
            layout.activateInput(window["ROIradiusInput"], shape_type == "circle")

        elif event == "ROIcenter":
            blockROI = not blockROI
            if blockROI:
                window["ROIcenter"].update("Unblock ROI")
            else:
                window["ROIcenter"].update("Block ROI")

        elif event == "cameraGraph":
            if blockROI:
                ROI_center = values[event]

        elif event == "IPparameters":
            kernel_size = int(window["IPparamKernelSize"].get())
            dilation_number = int(window["IPparamDilationNumber"].get())
            filter_threshold = int(window["IPparamThreshold"].get())
        
        elif event == "autoYAxis":
            auto_scale = window["autoYAxis"].get()
            layout.activateButton(window["applyYAxis"], not window["autoYAxis"].get())
            layout.activateInput(window["yAxisMin"], not window["autoYAxis"].get())
            layout.activateInput(window["yAxisMax"], not window["autoYAxis"].get())
            if camera_connected:
                updatePlot(intensity_fig, intensity_ax, intensities, time_of_intensities, auto_scale, min_y, max_y)
                window.refresh()
            elif spec_connected:
                updatePlot(intensity_fig, intensity_ax, min_peak_wavelength, time_of_intensities_spec, auto_scale, min_y, max_y)
                window.refresh()

        elif event == "applyYAxis" or event == "applyYAxisSpec":

            if camera_connected:
                extrema = (0, 300)
            elif spec_connected:
                extrema = (500, 900)

            try:
                min_y = float(window["yAxisMin"].get())
                max_y = float(window["yAxisMax"].get())
            except:
                min_y = extrema[0]
                max_y = extrema[1]

            if max_y > extrema[1]:
                max_y = extrema[1]
                window["yAxisMax"].update(str(max_y))
            if min_y > max_y:
                min_y = max_y - 1
                window["yAxisMin"].update(str(min_y))
            if min_y < extrema[0]:
                min_y = extrema[0]
                window["yAxisMin"].update(str(min_y))

        elif event == "applyWavelength":
            try:
                wavelength_min = int(window["wavelengthMin"].get())
                wavelength_max = int(window["wavelengthMax"].get())

                if wavelength_min < 500:
                    wavelength_min = 500
                    window["wavelengthMin"].update("500")
                if wavelength_max > 900:
                    wavelength_max = 900
                    window["wavelengthMax"].update("900")
                if wavelength_min > wavelength_max:
                    wavelength_min = wavelength_max - 1
                    window["wavelengthMin"].update(str(wavelength_min))

            except:
                wavelength_min = 500
                wavelength_max = 900
                window["wavelengthMin"].update("500")
                window["wavelengthMax"].update("900")
                print("Invalid wavelength")

        elif event == "reconnectArduino":
            if not arduino_connected:
                arduino, arduino_connected = arduino_control.connect_arduino()
        
        elif event == "openChamber":
            if arduino_connected:
                arduino_connected = arduino_control.open_chamber(arduino)

        elif event == "closeChamber":
            if arduino_connected:
                arduino_connected = arduino_control.close_chamber(arduino)
                
        elif event == "stopDCmotor":
            if arduino_connected:
                arduino_connected = arduino_control.motor_powered(False, arduino)
        
        elif event == "sendCommands":
            if pump_connected == True:
                commands_valid: bool = True
                seq: str = ""
                commands_df = pd.DataFrame(columns=["port", "action", "volume", "speed", "title", "wait"])
                for k in range(command_number):
                    port: str = window[f'port_{k}'].get()
                    action: str = window[f'action_{k}'].get()
                    volume: str = window[f'volume_{k}'].get()
                    speed: str = window[f'speed_{k}'].get()
                    title: str  = window[f'title_{k}'].get()
                    wait: str = window[f'wait_{k}'].get()
                    
                    if port == "" and volume == "" and speed == "":
                        # Empty commands are ignored
                        continue
                    else:
                        # Check if all fields are filled correctly
                        try:
                            # Port should be an int between 1 and 12
                            if port in ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12"]:
                                port = int(port)
                            else:
                                raise Exception
                        except:
                            print("Invalid port, command " + str(k))
                            window[f'port_{k}'].update("")
                            commands_valid = False
                            break

                        if action != "Pick" and action != "Dispense":
                            print("Invalid action, command " + str(k))
                            window[f'action_{k}'].update("Pick")
                            commands_valid = False
                            break

                        try:
                            volume = float(volume)
                            if volume < 3 or volume > 200:
                                raise Exception
                        except:
                            print("Invalid volume, command " + str(k))
                            window[f'volume_{k}'].update("")
                            commands_valid = False
                            break

                        try:
                            speed = float(speed)
                            if (speed < 5) or (speed > 8000):
                                raise Exception
                        except:
                            print("Invalid speed, command " + str(k))
                            window[f'speed_{k}'].update("")
                            commands_valid = False
                            break
                        
                        try:
                            if wait != "":
                                wait = int(wait)
                                if wait < 0 or wait > 86400000:
                                    raise Exception
                            else:
                                wait = 0
                        except:
                            print("Invalid wait, command " + str(k))
                            window[f'wait_{k}'].update("")
                            commands_valid = False
                            break

                        # If all fields are valid, add the command to the sequence
                        seq += microflu.seq_from_command(port, action, volume, speed, title, wait)
                        # Append the command to the dataframe
                        commands_df = pd.concat([commands_df, pd.DataFrame([[port, action, volume, speed, title, wait]], columns=["port", "action", "volume", "speed", "title", "wait"])], ignore_index=True)
                if commands_valid:
                    if command_number > 0:
                        if layout.yesNoPopup("Send commands?", "Send commands"):
                            # If all commands are valid, send the sequence to the pump
                            pump_connected = microflu.write_sequence_to_pump(lsp, seq)
                            current_command = -1
                
                else:
                    print("At least one command is invalid")
            else:
                print("Check pump connection")

        elif event == "deleteCommands":
            if command_number > 0:
                if layout.yesNoPopup("Delete all commands?", "Delete commands"):
                    for k in range(command_number):
                        layout.delete_line(k, window)

        else:
            # Check for delete buttons
            for k in range(command_number):
                if event == f'delete_{k}':
                    layout.delete_line(k, window)
                    break

    # Stop the software
    # Pump go to zero
    if pump_connected == True:
        pump_connected = microflu.go_to_zero(lsp)

    # Turn off the camera
    if camera_connected == True:
        try:
            cam.EndAcquisition()
            cam.DeInit()
            del cam
            cam_list.Clear()
        except Exception as exc:
            print(exc)
    try:
        system.ReleaseInstance()
    except:
        pass
    
    if arduino_connected == True:
        arduino_control.motor_powered(False, arduino)
        arduino.close()

    # Close the window
    window.close()

    sys.exit()
