# -*- coding: utf-8 -*-
# Copyright (c) 2016-2017, The Regents of the University of California (Regents).
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice, this
#    list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
# ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
#  OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
# The views and conclusions contained in the software and documentation are those
# of the authors and should not be interpreted as representing official policies,
# either expressed or implied, of the FreeBSD Project.
#
# REGENTS SPECIFICALLY DISCLAIMS ANY WARRANTIES, INCLUDING, BUT NOT LIMITED TO,
# THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE.
# THE SOFTWARE AND ACCOMPANYING DOCUMENTATION, IF ANY, PROVIDED HEREUNDER IS
# PROVIDED "AS IS". REGENTS HAS NO OBLIGATION TO PROVIDE MAINTENANCE, SUPPORT,
# UPDATES, ENHANCEMENTS, OR MODIFICATIONS.

#
# Contributors:
# Justin Bonus


#
# This script reads HydroUQ MPM output from sensors and then plots the data
# Plots are saved to a specified directory.
#

"""
Entry point to read the simulation results from MPM case and post-processes it.

"""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import os 
import sys
import argparse
# import json
# from pathlib import Path
# import plotly.graph_objects as go
# from plotly.subplots import make_subplots


if __name__ == '__main__':    

    #CLI parser
    input_args = sys.argv[1:]
    print("post_process_sensors.py - Backend-script post_process_sensors.py reached main. Starting...")
    print("post_process_sensors.py - Backend-script post_process_sensors.py running: " + str(sys.argv[0]))
    print("post_process_sensors.py - Backend-script post_process_sensors.py recieved input args: " + str(input_args))

    # parser = argparse.ArgumentParser(description="Get sensor measurements from output, process them, plot them, and then save the figures.")
    # parser.add_argument('-i', '--input_directory', help="Sensor Measurement Input Directory", required=True)
    # parser.add_argument('-o', '--output_directory', help="Sensor Plot Output Directory", required=True)
    # parser.add_argument('-f', '--files', help="Sensor Measurement Files", required=True)
    # arguments, unknowns = parser.parse_known_args()
    # print("post_process_sensors.py - Backend-script post_process_sensors.py recieved: " + str(arguments))
    # print("post_process_sensors.py - Backend-script post_process_sensors.py recieved: " + str(unknowns))
    

    # Get the directory of the sensor data
    # Get the directory to save the plots
    # Get the list of sensor filenames to plot, designated by comma separation
    sensor_data_dir = sys.argv[1]
    output_dir = sys.argv[2]
    sensor_files = sys.argv[3].split(',')

    # sensor_data_dir = arguments.input_directory
    # output_dir = arguments.output_directory
    # sensor_files = (arguments.files).split(',')  
    print("Sensor data directory: ", sensor_data_dir)
    print("Output directory: ", output_dir)
    print("Sensor files: ", sensor_files)
    # json_path =  os.path.join(case_path, "constant", "simCenter", "input", "MPM.json")
    # with open(json_path) as json_file:
    #     json_data =  json.load(json_file)
    # print("Backend-script post_process_sensors.py recieved: " + sys.argv[1] + " " + sys.argv[2] + " " + sys.argv[3] "")
        
    # Get the list of sensor names
    sensor_names = [(sensor_file.split('.')[0]).lstrip('/').strip() for sensor_file in sensor_files]

    # Load the sensor data
    sensor_data = {}
    for sensor_file in sensor_files:
        # Remove any leading '/' from the sensor file
        sensor_file = sensor_file.lstrip('/')
        sensor_file = sensor_file.strip() # Remove whitespace from the sensor file 
        sensor_file = sensor_file.split('.') # Split the sensor file by the '.' character
        if (sensor_file[-1] != 'csv'):
            print("Error: Sensor file is not a csv file. Please provide a csv file. Will skip this file: " + sensor_file[0] + '.' + sensor_file[-1])
            continue
        sensor_file = sensor_file[0] # Get the first part of the sensor file, which is the sensor name
        sensor_data[sensor_file] = pd.read_csv(os.path.join(sensor_data_dir, sensor_file + '.csv'), header=None, skiprows=1, delimiter=',', usecols=[0, 1])

        # Assume that the header is row 0, and that the time is in the first column, and the value is in the second column
        sensor_data[sensor_file].columns = ['time', 'value']
        
        please_convert_to_date_time = False # May want to use this later, as wave-flumes tend to report time in date-time formats
        if (please_convert_to_date_time == True and sensor_data[sensor_file]['time'].dtype != 'datetime64[ns]'):
            sensor_data[sensor_file]['time'] = pd.to_datetime(sensor_data[sensor_file]['time'])
        
    # Make sure the output directory exists, and save the sensor raw data to the output directory if they aren't already there 
    if not os.path.exists(output_dir):
        print("Output directory not found... Creating output directory: " + output_dir + "...")
        os.makedirs(output_dir)
    if (output_dir != sensor_data_dir):
        for sensor_name in sensor_names:
            print("Save " + os.path.join(output_dir, sensor_name) + '.csv' + "...")
            sensor_data[sensor_name].to_csv(os.path.join(output_dir, sensor_name + '.csv'), index=False)
            
    # Plot the sensor data, and save the plots to the output directory (html and png files)
    for sensor_name in sensor_names:
        print("Plotting " + sensor_name + "...")
        fig, axes = plt.subplots(1, 1)
        sensor_name_png = sensor_name + '.png'
        sensor_name_html = sensor_name + '.webp'

        # axes.set_title(sensor_name)
        axes.plot(sensor_data[sensor_name]['time'], sensor_data[sensor_name]['value'])
        axes.set_xlabel('Time [s]')
        axes.set_ylabel('Sensor Measurement')
        print("Save " + os.path.join(output_dir, sensor_name_png) + "...")
        plt.savefig(os.path.join(output_dir, sensor_name_png), dpi=300, bbox_inches='tight') # save the plot as a png file
        print("Save " + os.path.join(output_dir, sensor_name_html) + "...")
        plt.savefig(os.path.join(output_dir, sensor_name_html), dpi=300, bbox_inches='tight') # save the plot as an html file
        plt.show() 
        plt.close() 
        
    print("post_process_sensors.py - Backend-script post_process_sensors.py reached end of main. Finished.")
    

        