import matplotlib.pyplot as plt
import scipy
import numpy as np
import nidaqmx
import time
from nidaqmx.stream_readers import AnalogSingleChannelReader

start_time = time.time()                                   ## start stopwatch

## INPUTS

membrane1 = 'SB1'                                          ## name of membrane 1
membrane2 = 'SB2'                                          ## name of membrane 2
freq = np.arange(150.0, 610.0, 10.0)                       ## frequency of waveform (Hz) from 150 to 600 with a step size of 10
#freq = np.arange(500.0, 510.0, 10.0)
freq = np.insert(freq, 0, 0.0)                             ## insert 0 in front of freq array
#freq = [450]

output_sampling_rate = 5000.0                              ## output sampling rate
t = 2.0                                                    ## output waveform time (sec)
output_samples = output_sampling_rate * t                  ## output samples
output_time = np.arange(output_samples)                    ## output time array
max_amp = [0.1472, 0.2930, 0.4383, 0.5835, 0.7281, 0.8735]                                 ## maximum amplitude array (60V, 80V)


amplitude = np.empty([len(max_amp), int(output_samples)])  ## initalize amplitude array

## fill amplitude array
for i in range(len(max_amp)):
    dummy_amp = np.empty(int(output_sampling_rate/2))        ## initalize dummy amplitude array
    dummy_amp = np.arange(0.0, max_amp[i], max_amp[i]/(output_sampling_rate/2))     ## ramp up amplitude
    dummy_amp = np.append(dummy_amp, np.full(int(output_samples - output_sampling_rate/2 * 2.0), max_amp[i], dtype = np.float64))  ## steady max amplitude
    dummy_amp = np.append(dummy_amp, np.arange(max_amp[i], 0.0, -max_amp[i]/(output_sampling_rate/2)))  ## ramp down amplitude
    amplitude[i] = dummy_amp   ## put dummy amplitude into amplitude array

laser_input_sampling_rate = 10000.0                                               ## laser input sampling rate
laser_input_samples = laser_input_sampling_rate/2        #(t - 2) / 2                    ## laser input samples

pressure_input_sampling_rate = 10000.0                                            ## pressure input sampling rate
pressure_input_samples = pressure_input_sampling_rate/2     #(t - 2) / 2                ## pressure input samples

data_cycles = 100                                                                  ## number of cycles to take min/max from
laser_data = np.empty([len(max_amp), len(freq), int(laser_input_samples)])        ## initalize laser data array
min_laser_data = np.empty([len(max_amp), len(freq), int(data_cycles/2)])          ## initalize min laser data array
max_laser_data = np.empty([len(max_amp), len(freq), int(data_cycles/2)])          ## initalize max laser data array
min_laser = np.empty([len(freq), len(max_amp)])                                   ## initalize avg min laser data array
max_laser = np.empty([len(freq), len(max_amp)])                                   ## initalize avg max laser data array
displacement = np.empty([len(freq), len(max_amp)])                                ## initalize displacement laser data array

pressure_data = np.empty([len(max_amp), len(freq), int(pressure_input_samples)])  ## initalize pressure data array
max_pressure_data = np.empty([len(max_amp), len(freq), int(data_cycles/2)])       ## initalize max pressure data array
max_pressure = np.empty([len(freq), len(max_amp)])                                ## initalize avg max pressure data array

## create output sine wave function
signal_data = np.empty([len(max_amp), len(freq), int(output_samples)])            ## initalize signal data array
for k in range(len(max_amp)):                                                     ## loop for amplitude
    for i in range(len(freq)):                                                    ## loop for frequency
        for j in range(len(output_time)):                                         ## loop for output time
            signal_data[k, i, j] = amplitude[k, j] * np.sin( 2.0 * np.pi * freq[i] * (output_time[j] / output_sampling_rate))   ## input signal data (amplitude)

with nidaqmx.Task() as signal_Task, nidaqmx.Task() as laser_Task, nidaqmx.Task() as pressure_Task:
    ## add analog output channel
    signal_Task.ao_channels.add_ao_voltage_chan("Dev1/ao0",                                           ## analog output channel pin AO0
                                                min_val = -2.0,                                       ## expected min value
                                                max_val = 2.0,                                        ## expected max value
                                                units = nidaqmx.constants.VoltageUnits.VOLTS)         ## units of output value

    ## set timing on analog output channel
    signal_Task.timing.cfg_samp_clk_timing(output_sampling_rate,                                      ## output sampling rate
                                           samps_per_chan = int(output_samples))                      ## total samples gathered
    
    ## add analog input channel
    laser_Task.ai_channels.add_ai_voltage_chan("Dev1/ai0",                                            ## analog input channel pin AI0
                                               min_val = -2.0,                                        ## expected min value
                                               max_val = 2.0,                                         ## expected max value
                                               units = nidaqmx.constants.VoltageUnits.VOLTS)          ## units of input value
    
    ## set timing on analog input channel
    laser_Task.timing.cfg_samp_clk_timing(laser_input_sampling_rate,                                  ## input sampling rate
                                          sample_mode = nidaqmx.constants.AcquisitionType.FINITE,     ## set sampling mode to finite
                                          samps_per_chan = int(laser_input_samples))                  ## samples collected
    
    ## add analog input channel
    pressure_Task.ai_channels.add_ai_voltage_chan("Dev1/ai4",                                         ## analog input channel pin AI4
                                               min_val = 0.0,                                         ## expected min value
                                               max_val = 5.0,                                         ## expected max value
                                               units = nidaqmx.constants.VoltageUnits.VOLTS)          ## units of input value
    
    ## set timing on analog input channel
    pressure_Task.timing.cfg_samp_clk_timing(pressure_input_sampling_rate,                            ## input sampling rate
                                          sample_mode = nidaqmx.constants.AcquisitionType.FINITE,     ## set sampling mode to finite
                                          samps_per_chan = int(pressure_input_samples))               ## samples collected

   # signal_Task.out_stream.output_buf_size = 20000
    for j in range(len(amplitude)):                                         ## loop through amplitude
        for i in range(len(freq)):                                          ## loop through frequency
            signal_Task.write(signal_data[j, i, :], auto_start = False)     ## prepare signal data, do not auto start

            signal_Task.start()                                             ## start sending signal data

            time.sleep(0.5)                                                   ## wait one second for ramp up

            laser_data[j, i, :] = laser_Task.read(int(laser_input_samples))                           ## read laser data into array by the amount in "laser_input_samples"
            min_laser_data[j, i, :] = np.partition(laser_data[j, i, :], data_cycles)[50:data_cycles]    ## get top 'data cycle' max laser data values
            max_laser_data[j, i, :] = np.partition(laser_data[j, i, :], -data_cycles)[-data_cycles:-50]  ## get top 'data cycle' min laser data values
            min_laser[i, j] = np.average(min_laser_data[j, i, :])                                     ## get avg of max laser data values
            max_laser[i, j] = np.average(max_laser_data[j, i, :])                                     ## get avg of min laser data values
            displacement[i, j] = (max_laser[i, j] - min_laser[i, j])/10                               ## get displacement laser data values

            pressure_data[j, i, :] = pressure_Task.read(int(pressure_input_samples))                        ## read pressure data into array
            #min_pressure_data[j, i, :] = np.partition(pressure_data[j, i, :], data_cycles)[:data_cycles]   ## get top 'data cycle' max pressure data values
            max_pressure_data[j, i, :] = np.partition(pressure_data[j, i, :], -data_cycles)[-data_cycles:-50]  ## get top 'data cycle' min pressure data values
            #min_pressure[i, j] = np.average(min_pressure_data[j, i, :])                                    ## get avg of max pressure data values
            max_pressure[i, j] = np.average(max_pressure_data[j, i, :])                                     ## get avg of min pressure data values
            #final_pressure[i, j] = max_pressure[i, j] - min_pressure[i, j]                                 ## get final pressure data values

            time.sleep(0.5)
            signal_Task.stop()        ## stop sending signal data
            time.sleep(0.5)             ## wait one second

## Writing to an excel sheet using Python 
import xlsxwriter as excel 
  
## Workbook is created 
workbook = excel.Workbook('D:/Actasys/Code/Membrane_Test.xlsx') 
  
## add_sheet is used to create sheet. 
sheet1 = workbook.add_worksheet('20V') 
sheet2 = workbook.add_worksheet('40V')
sheet3 = workbook.add_worksheet('60V') 
sheet4 = workbook.add_worksheet('80V')
sheet5 = workbook.add_worksheet('100V') 
sheet6 = workbook.add_worksheet('120V')  

## layout for sheet.write: (row, column, 'words')  
sheet1.write(0, 0, 'Frequency') 
sheet1.write(0, 1, 'Displacement') 
sheet1.write(0, 2, 'Voltage')
sheet1.write(0, 3, 'Offset')
sheet1.write(0, 4, 'V-P')
sheet1.write(0, 5, 'P-V')

sheet2.write(0, 0, 'Frequency') 
sheet2.write(0, 1, 'Displacement') 
sheet2.write(0, 2, 'Voltage')
sheet2.write(0, 3, 'Offset')
sheet2.write(0, 4, 'V-P')
sheet2.write(0, 5, 'P-V')

sheet3.write(0, 0, 'Frequency') 
sheet3.write(0, 1, 'Displacement') 
sheet3.write(0, 2, 'Voltage')
sheet3.write(0, 3, 'Offset')
sheet3.write(0, 4, 'V-P')
sheet3.write(0, 5, 'P-V')

sheet4.write(0, 0, 'Frequency') 
sheet4.write(0, 1, 'Displacement') 
sheet4.write(0, 2, 'Voltage')
sheet4.write(0, 3, 'Offset')
sheet4.write(0, 4, 'V-P')
sheet4.write(0, 5, 'P-V')

sheet5.write(0, 0, 'Frequency') 
sheet5.write(0, 1, 'Displacement') 
sheet5.write(0, 2, 'Voltage')
sheet5.write(0, 3, 'Offset')
sheet5.write(0, 4, 'V-P')
sheet5.write(0, 5, 'P-V')


sheet6.write(0, 0, 'Frequency') 
sheet6.write(0, 1, 'Displacement') 
sheet6.write(0, 2, 'Voltage')
sheet6.write(0, 3, 'Offset')
sheet6.write(0, 4, 'V-P')
sheet6.write(0, 5, 'P-V')


## write freq array into 1st column
row = 1
for data in freq:
    sheet1.write(row, 0, data)
    sheet2.write(row, 0, data)
    sheet3.write(row, 0, data)
    sheet4.write(row, 0, data)
    sheet5.write(row, 0, data)
    sheet6.write(row, 0, data)
    row += 1

## write displacement array into 2nd column
row = 1
for i in range(len(displacement)):
    sheet1.write(row, 1, displacement[i, 0]) # does this disp. data supposed to be in 2nd column?
    sheet2.write(row, 1, displacement[i, 1])
    sheet3.write(row, 1, displacement[i, 2])
    sheet4.write(row, 1, displacement[i, 3])
    sheet5.write(row, 1, displacement[i, 4])
    sheet6.write(row, 1, displacement[i, 5])
    row += 1

## write pressure (volts) array into 3rd column
#  start at sheet 6 - only in paired memebranes pressure sensor is setup
row = 1
for i in range(len(max_pressure)):
    sheet1.write(row, 2, max_pressure[i, 0])
    sheet2.write(row, 2, max_pressure[i, 1])
    sheet3.write(row, 2, max_pressure[i, 2])
    sheet4.write(row, 2, max_pressure[i, 3])
    sheet5.write(row, 2, max_pressure[i, 4])
    sheet6.write(row, 2, max_pressure[i, 5])
    row += 1

## write offset voltage into 4th column
# start at sheet 6 - only in paired memebranes pressure sensor is setup
sheet1.write_formula('D2', '=C2-2.5')
sheet2.write_formula('D2', '=C2-2.5')
sheet3.write_formula('D2', '=C2-2.5')
sheet4.write_formula('D2', '=C2-2.5')
sheet5.write_formula('D2', '=C2-2.5')
sheet6.write_formula('D2', '=C2-2.5')


## write pressure (volts) to pressure (kPa) formula into 5th column
for row_num in range(1, len(freq) + 1):
    sheet1.write_formula(row_num, 4, '=(((C%d-$D$2)/5)*55.56)-27.777' %(row_num + 1))
    sheet2.write_formula(row_num, 4, '=(((C%d-$D$2)/5)*55.56)-27.777' %(row_num + 1))
    sheet3.write_formula(row_num, 4, '=(((C%d-$D$2)/5)*55.56)-27.777' %(row_num + 1))
    sheet4.write_formula(row_num, 4, '=(((C%d-$D$2)/5)*55.56)-27.777' %(row_num + 1))
    sheet5.write_formula(row_num, 4, '=(((C%d-$D$2)/5)*55.56)-27.777' %(row_num + 1))
    sheet6.write_formula(row_num, 4, '=(((C%d-$D$2)/5)*55.56)-27.777' %(row_num + 1))

## write pressure (kPa) to velocity (m/s) formula into 6th column
for row_num in range(1, len(freq) + 1):
    sheet1.write_formula(row_num, 5, '=SQRT(2*E%d*1000/1.21)' %(row_num + 1))
    sheet2.write_formula(row_num, 5, '=SQRT(2*E%d*1000/1.21)' %(row_num + 1))
    sheet3.write_formula(row_num, 5, '=SQRT(2*E%d*1000/1.21)' %(row_num + 1))
    sheet4.write_formula(row_num, 5, '=SQRT(2*E%d*1000/1.21)' %(row_num + 1))
    sheet5.write_formula(row_num, 5, '=SQRT(2*E%d*1000/1.21)' %(row_num + 1))
    sheet6.write_formula(row_num, 5, '=SQRT(2*E%d*1000/1.21)' %(row_num + 1))

sheet7 = workbook.add_worksheet('Graphs')
chart_disp = workbook.add_chart({'type': 'scatter', 'subtype': 'smooth'}) # a scatter plot with smooth lines and markers
# adding the data to plotted: x-axis is categories, y-axis is values
chart_disp.add_series({
    'name': '20V',
    'categories': '=20V!$A$2:$A$%d' %(len(freq)+1), # x-axis data
    'values': '=20V!$B$2:$B$%d' %(len(displacement)+1), # y- axis data
    })
chart_disp.add_series({
    'name': '40V',
    'categories': '=40V!$A$2:$A$%d' %(len(freq)+1), # x-axis data
    'values': '=40V!$B$2:$B$%d' %(len(displacement)+1), # y- axis data
    })
chart_disp.add_series({
    'name': '60V',
    'categories': '=60V!$A$2:$A$%d' %(len(freq)+1), # x-axis data
    'values': '=60V!$B$2:$B$%d' %(len(displacement)+1), # y- axis data
    })
chart_disp.add_series({
    'name': '80V',
    'categories': '=80V!$A$2:$A$%d' %(len(freq)+1), # x-axis data
    'values': '=80V!$B$2:$B$%d' %(len(displacement)+1), # y- axis data
    })
chart_disp.add_series({
    'name': '100V',
    'categories': '=100V!$A$2:$A$%d' %(len(freq)+1), # x-axis data
    'values': '=100V!$B$2:$B$%d' %(len(displacement)+1), # y- axis data
    })
chart_disp.add_series({
    'name': '120V',
    'categories': '=120V!$A$2:$A$%d' %(len(freq)+1), # x-axis data
    'values': '=120V!$B$2:$B$%d' %(len(displacement)+1), # y- axis data
    })
chart_disp.set_title({'name': 'Displacement'}) # adds a title
chart_disp.set_x_axis({'name': 'Frequency (Hz)', 'max': max(freq), 'major_gridlines': {'visible': True}})
chart_disp.set_y_axis({'name': 'Amplitude (mm)'})
chart_disp.set_style(2)
sheet7.insert_chart('A1', chart_disp) # adds chart2 into cell d2 on sheet2

chart_vel = workbook.add_chart({'type': 'scatter', 'subtype': 'smooth'}) # a scatter plot with smooth lines and markers
# adding the data to plotted: x-axis is categories, y-axis is values
chart_vel.add_series({
    'name': '20V',
    'categories': '=20V!$A$2:$A$%d' %(len(freq)+1), # x-axis data
    'values': '=20V!$F$2:$F$%d' %(len(displacement)+1), # y- axis data
    })
chart_vel.add_series({
    'name': '40V',
    'categories': '=40V!$A$2:$A$%d' %(len(freq)+1), # x-axis data
    'values': '=40V!$F$2:$F$%d' %(len(displacement)+1), # y- axis data
    })
chart_vel.add_series({
    'name': '60V',
    'categories': '=60V!$A$2:$A$%d' %(len(freq)+1), # x-axis data
    'values': '=60V!$F$2:$F$%d' %(len(displacement)+1), # y- axis data
    })
chart_vel.add_series({
    'name': '80V',
    'categories': '=80V!$A$2:$A$%d' %(len(freq)+1), # x-axis data
    'values': '=80V!FB$2:$F$%d' %(len(displacement)+1), # y- axis data
    })
chart_vel.add_series({
    'name': '100V',
    'categories': '=100V!$A$2:$A$%d' %(len(freq)+1), # x-axis data
    'values': '=100V!$F$2:$F$%d' %(len(displacement)+1), # y- axis data
    })
chart_vel.add_series({
    'name': '120V',
    'categories': '=120V!$A$2:$A$%d' %(len(freq)+1), # x-axis data
    'values': '=120V!$F$2:$F$%d' %(len(displacement)+1), # y- axis data
    })
chart_vel.set_title({'name': 'Jet Velocity'}) # adds a title
chart_vel.set_x_axis({'name': 'Frequency (Hz)', 'max': max(freq), 'major_gridlines': {'visible': True}})
chart_vel.set_y_axis({'name': 'Velocity (m/s)'})
chart_vel.set_style(2)
sheet7.insert_chart('I1', chart_vel) # adds chart2 into cell d2 on sheet2

# row = 1
# for i in range(len(laser_data[0][0])):
#     sheet3.write(row, 0, laser_data[0,0,i])
#     sheet3.write(row, 1, laser_data[0,1,i])
#     sheet3.write(row, 2, laser_data[0,2,i])
#     sheet3.write(row, 3, laser_data[0,3,i])
#     row += 1

# row = 1
# for i in range(len(laser_data[0][0])):
#     sheet4.write(row, 0, laser_data[1,0,i])
#     sheet4.write(row, 1, laser_data[1,1,i])
#     sheet4.write(row, 2, laser_data[1,2,i])
#     sheet4.write(row, 3, laser_data[1,3,i])
#     row += 1

workbook.close() ## close workbook

print("--- %s seconds ---" % (time.time() - start_time))  ## print time taken to run code