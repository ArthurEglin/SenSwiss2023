import PySimpleGUI as sg
import typing
import microflu
import gui

def create_layout(logo_size: typing.Tuple[int, int], camera_img_size: typing.Tuple[int, int], reducing_factor: float, device_connected: int) -> list:
    """
    Create the layout of the GUI for SenSwiss 2023 sensor interface.

    :param logo_size: The size of the logo.
    :param camera_img_size: The size of the camera image.
    :param reducing_factor: The factor by which the camera image is reduced.
    :param device_connected: The device connected to the computer, 0 for none, 1 for camera, 2 for spectrometer.
    :type logo_size: tuple
    :type camera_img_size: tuple
    :type reducing_factor: float

    :return: The layout of the GUI.
    """
    sens_us_logo = [[sg.Image(size=logo_size, key="logoImage")]]
    explanations = [
        [
            sg.Column(
                [
                    [sg.Text("Welcome to the SenSwiss 2023 sensor interface!", pad=(0, 0))],
                    [
                        sg.Text(
                            "From here you will be able to control our microfluidics pump Matilda and adjust the settings of our camera Gerald",
                            pad=(0, 0),
                        ),
                    ],
                ],
                pad=(0, 0),
            )
        ]
    ]

    tab_man_micro_flu = [
        [
            sg.Text("Basic Pump Controls", key="basicPumpControls"),
        ],
        [
            sg.Button("Go to zero", key="goToZero"),
            sg.Button("Reinitialize", key="reinit"),
        ],
        [
            sg.Input("", key='inputChosenValve', size=(6, 1)),
            sg.Button("Switch to Valve", key="switchValve"),
        ],
        [
            sg.Input("", key='inputChosenSpeed', size=(6, 1)),
            sg.Button("Set speed", key="setSpeed"),
        ],
        [
            sg.Input("", key='inputChosenPickUpVolume', size=(6, 1)),
            sg.Button("Pickup uL", key="pickupVolume"),
        ],
        [
            sg.Input("", key='inputChosenDispenseVolume', size=(6, 1)),
            sg.Button("Dispense uL", key="dispenseVolume"),
        ],
        [
            sg.Input("", key='inputTemperature', size=(6, 1)),
            sg.Button("Heat ON", key="heatON"),
            sg.Button("Heat OFF", key="heatOFF"),
        ],
    ]

    tab_semi_auto_micro_flu = [
        [
            sg.Text("Enter the commands to send to the pump"),
            sg.Button("+", key="addCommand"),
            sg.Button("Copy commands", key="copyCommands"),
        ],
        [sg.Frame("", [[sg.Text("                       Port         Action         Volume   Speed    Title    Wait   copy"),]], key="commandFrame")],
        [
            sg.Button("Send", key="sendCommands"),
            sg.Button("Delete all", key="deleteCommands"),
            sg.Button("Save commands", key="saveCommands"),
            sg.Text("Protocol name:"),
            sg.Input("", key="protocolName", size=(10, 1)),

        ],
    ]

    tab_auto_micro_flu = [
        [
            sg.Text("Coded sequences for the pump"),
        ],
        [
            sg.Button("Fill tubes", key="fillTubes"),
        ],
        [
            sg.Button("Send protocol", key="sendProtocol"),
            sg.Combo(gui.protocol_list, default_value="", key="protocolAuto", size=(100, 1)),
        ],
        [
            sg.Button("Load protocol", key="loadProtocol"),
            sg.Combo(gui.protocol_list, default_value="", key="protocolLoad", size=(100, 1)),
        ],
    ]

    tab_camera = [
        [
            sg.Text("Exposure time:"),
            sg.Spin(
                [100 * i for i in range(80, 200)],
                initial_value=10332,
                key="exposureTime",
                font=("Helvetica 12"),
                enable_events=True,
            ),
            sg.Text("Gain:"),
            sg.Spin(
                [i / 10 for i in range(50, 280)],
                initial_value=13.8,
                key="gainValue",
                font=("Helvetica 12"),
                enable_events=True,
            ),
        ],
        [
            sg.Button("Save image", key="saveImage"),
            sg.Text("Add to name of file (optional):"),
            sg.Input("", key="imageName", size=(10, 1)),
        ],
        [
            sg.Button("Show ROI", key="displayROI"),
            sg.Button("Block ROI center", key="ROIcenter"),
            sg.Combo(['circle', 'rectangle'], default_value="circle", key='ROIshapeType', enable_events=True, size=(10, 1)),
        ],
        [
            sg.Text("Radius:"),
            sg.Input("500", key="ROIradiusInput", size=(6, 1)),
            sg.Text("Height:"),
            sg.Input("1000", key="ROIheightInput", size=(6, 1), background_color="#424242"),
            sg.Text("Width:"),
            sg.Input("1000", key="ROIwidthInput", size=(6, 1), background_color="#424242"),
            sg.Button("Set ROI params", key="ROIparams"),
        ],
        [
            sg.Button("Set", key="IPparameters"),
            sg.Text("Kernel size:"),
            sg.Input("3", key="IPparamKernelSize", size=(3, 1)),
            sg.Text("Number of dilations:"),
            sg.Input("2", key="IPparamDilationNumber", size=(3, 1)),
            sg.Text("Threshold value:"),
            sg.Input("90", key="IPparamThreshold", size=(5, 1)),
        ],
        [
            sg.Button("Save plot", key="saveCameraPlot"),
            sg.Text("Add to name of file (optional):"),
            sg.Input("", key="plotName", size=(10, 1)),
            sg.Button("Clear plot", key="clearPlot"),
        ],
        [
            sg.Text("Y Axis limits :"),
            sg.Checkbox("Auto", key="autoYAxis", enable_events=True),
            sg.Input("0", key="yAxisMin", size=(6, 1), use_readonly_for_disable=True),
            sg.Input("300", key="yAxisMax", size=(6, 1), use_readonly_for_disable=True),
            sg.Button("Apply", key="applyYAxis")
        ],
    ]

    tab_spectrometer = [
        [
            sg.Button("Acquisition period", key="acquisitionPeriod"),
            sg.Input("0.5", key="acquistionPeriodInput", size=(6, 1)),
            sg.Button("Reconnect spectrometer", key="reconnectSpectrometer"),
        ],
        [
            sg.Text("To plot: "),
            sg.Checkbox("Raw", key="plotRaw", default=True),
            sg.Checkbox("Normalized", key="plotNormalized"),
        ],
        [
            sg.Button("Save dark field", key="saveDarkField"),
            sg.Button("Save flat field", key="saveFlatField"),
            sg.Text("No dark field", key="darkFieldStatus"),
            sg.Text("No flat field", key="flatFieldStatus"),
        ],
        [
            sg.Text("Wavelength range:"),
            sg.Input("500", key="wavelengthMin", size=(6, 1)),
            sg.Input("900", key="wavelengthMax", size=(6, 1)),
            sg.Button("Apply", key="applyWavelength"),
        ],
        [
            sg.Input("20", key="movingAverage", size=(6, 1)),
            sg.Button("Set moving average", key="setMovingAverage"),
        ],
        [
            sg.Input("100", key="SavGol", size=(8, 1)),
            sg.Button("Set SG window", key="setSGwindow"),
        ],
        [
            sg.Text("Window width for centroid:"),
            sg.Input("50", key="centroidWidth", size=(6, 1)),
            sg.Button("Reset min peak", key="resetMinPeak"),
            sg.Text("Not set", key="minPeakStatus")
        ],
        [
            sg.Button("Save Spectrograph", key="saveSpec"),
            sg.Text("Add to name of file (optional):"),
            sg.Input("", key="specName", size=(10, 1)),
        ],
        [
            sg.Text("------------------------------------------------------------------------------------------------------------------------"),
        ],
        [
            sg.Input("", key="plotComment", size=(10, 1)),
            sg.Button("Add comment", key="addComment"),
        ],
        [
            sg.Input("GFAP", key="gfapShiftKey", size=(6, 1)),
            sg.Input("STOP", key="stopShiftKey", size=(6, 1)),
            sg.Button("Compute shift", key="computeShift"),
            sg.Text("No computation", key="shiftTxt"),
        ],
        [
            sg.Text("Y Axis limits :"),            
            sg.Checkbox("Auto", key="autoYAxis", enable_events=True),
            sg.Input("500", key="yAxisMin", size=(6, 1), use_readonly_for_disable=True),
            sg.Input("900", key="yAxisMax", size=(6, 1), use_readonly_for_disable=True),
            sg.Button("Apply", key="applyYAxis")
        ],
        [
            sg.Button("Save plot", key="saveSpecPlot"),
            sg.Text("Add to name of file (optional):"),
            sg.Input("", key="specPlotName", size=(10, 1)),
            sg.Button("Clear plot", key="clearSpecPlot"),
        ],
    ]

    if device_connected == 0:
        tab_displayed = []
        name_of_tab = "No device connected"
    elif device_connected == 1:
        tab_displayed = tab_camera
        name_of_tab = "Camera settings:"
    elif device_connected == 2:
        tab_displayed = tab_spectrometer
        name_of_tab = "Spectrometer settings:"    
        
    tab_motor = [
        [
            sg.Button("Reconnect arduino", key="reconnectArduino"),
            sg.Button("Open chamber", key="openChamber"),
            sg.Button("Close chamber", key="closeChamber"),
            sg.Button("Stop DC motor", key="stopDCmotor"),
        ],
    ]
    
    print_metric = [
        [
            sg.Button("Reconnect pump", key="reconnectPump"),
            sg.Button("Stop and trash", key="goToZero"),
            sg.Button("Reinitialize", key="reinit"),
        ],
        [
            sg.Button("Kick out bubble", key="kickOutBubble"),
            sg.Text("Pick from: "),
            sg.Input("", key='inputPickupValve', size=(6, 1)),
            sg.Text("Dispense to: "),
            sg.Input("", key='inputDispenseValve', size=(6, 1)),
        ],
        [
            sg.TabGroup(
                [
                    [
                        sg.Tab("Manual Microfluidics", tab_man_micro_flu),
                        sg.Tab("Semi-Auto Microfluidics", tab_semi_auto_micro_flu),
                        sg.Tab("Auto Microfluidics", tab_auto_micro_flu),
                    ]
                ],
                expand_x=True,
            )
        ],
        [
            sg.TabGroup(
                [
                    [
                        sg.Tab(name_of_tab, tab_displayed),
                    ]
                ],
                expand_x=True,
            )
        ],    
        [
            sg.TabGroup(
                [
                    [
                        sg.Tab("Motor", tab_motor),
                    ]
                ],
                expand_x=True,
            )
        ],
    ]

    img_to_print = [
        [
            sg.Graph(
                (
                    int(camera_img_size[1] * reducing_factor),
                    int(camera_img_size[0] * reducing_factor),
                ),
                (0, camera_img_size[0]),
                (camera_img_size[1], 0),
                key="cameraGraph",
                enable_events=True,
            )
        ],
        [
            sg.Graph(
                (
                    int(camera_img_size[1] * reducing_factor),
                    int(camera_img_size[0] * reducing_factor),
                ),
                (0, 50),
                (camera_img_size[1], 0),
                key="plotGraph",
            )
        ],
    ]
    
    # ----- Full layout -----
    # Main layout
    layout = [
        [
            sg.Column(sens_us_logo),
            sg.VSeperator(),
            sg.Column(
                explanations,
                element_justification="left",
                expand_x=True,
                size=(100, 50),
            ),
        ],
        [
            sg.Column(img_to_print),
            sg.VSeperator(),
            sg.Column(
                print_metric,
                element_justification="left",
                expand_x=True,
                size=(100, 800),
                scrollable=True,
                key="scrollableCollumn"
            ),
        ],
    ]
    return layout

def new_line(i: int) -> list:
    """
    Create a new line for the semi-auto microfluidics tab.

    :param i: the number of the line
    :type i: int

    :return: the new line elements
    """
    return [
        [
            sg.Text(f'Command {i+1}', key=f'command_{i}'),
            sg.Input(key=f'port_{i}', size=(5, 1)),
            sg.Combo(['Pick', 'Dispense'], default_value="Pick", key=f'action_{i}', size=(10, 1)),
            sg.Input(key=f'volume_{i}', size=(5, 1)),
            sg.Input(key=f'speed_{i}', size=(5, 1)),
            sg.Input(key=f'title_{i}', size=(5, 1)),
            sg.Input(key=f'wait_{i}', size=(5, 1)),
            sg.Checkbox("", key=f'copy_{i}', enable_events=True),
            sg.Button('Delete', key=f'delete_{i}')
        ]
    ]
    
def update_line(i: int, win, port: str, action: str, volume: str, speed: str, title: str, wait: str, copy: bool = False) -> None:
    '''
    Update a line from the semi-auto microfluidics tab.
    '''
    win[f'port_{i}'].update(port)
    win[f'action_{i}'].update(action)
    win[f'volume_{i}'].update(volume)
    win[f'speed_{i}'].update(speed)
    win[f'title_{i}'].update(title)
    win[f'wait_{i}'].update(wait)
    win[f'copy_{i}'].update(copy)

def delete_line(i: int, win):
    '''
    Delete a line from the semi-auto microfluidics tab.
    :param i: the number of the line
    :type i: int
    :param win: the window of the GUI
    :type win: Window
    '''
    update_line(i, win, "", "Pick", "", "", "", "", False)

def activateButton(element, active: bool) -> None:
    """
    Activate or deactivate an element.

    :param element: the element to activate/deactivate
    :type element: Button
    :param active: True if the element should be activated, False otherwise
    :type active: bool
    """
    element.update(disabled=not active)
    element.update(button_color=sg.theme_button_color() if active else ("white", "grey"))

def activateInput(element, active: bool) -> None:
    """
    Activate or deactivate an element. It doesn't actually disable the element, but changes its background color.

    :param element: the element to activate/deactivate
    :type element: Input
    :param active: True if the element should be activated, False otherwise
    :type active: bool
    """
    if active:
        element.update(background_color="white")
    else:
        element.update(background_color="#424242")

def yesNoPopup(querry: str, title: str) -> bool:
    """
    Display a pop-up window with a Yes/No question.

    :param querry: the question to ask
    :type querry: str
    :param title: the title of the pop-up window
    :type title: str

    :return: True if the answer is yes, False otherwise
    """
    ch = sg.popup_yes_no(querry, title=title)
    if ch == "Yes":
        return True
    else:
        return False