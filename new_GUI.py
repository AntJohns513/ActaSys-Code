from PyQt5.QtCore import QDir, Qt, QUrl, QSize
from PyQt5.QtMultimedia import QMediaContent, QMediaPlayer
from PyQt5.QtMultimediaWidgets import QVideoWidget
from PyQt5.QtWidgets import (QApplication, QFileDialog, QLabel,
		QPushButton, QSizePolicy, QSlider, QStyle, QWidget)
from PyQt5.QtWidgets import QMainWindow, QWidget, QPushButton, QAction, QInputDialog, QLineEdit
from PyQt5.QtWidgets import QVBoxLayout, QHBoxLayout, QGridLayout, QFormLayout, QGroupBox
from PyQt5.QtGui import QIcon, QPalette, QColor

from pyqtgraph import PlotWidget, PlotWidget
import pyqtgraph as pg
import cv2
import sys
import time
import serial

#PLOTS:
#Power Consumption
#Jet Velocity
#Sound in decibels

try:
    ser = serial.Serial(
        port='/dev/tty.usbserial-210244705470',
        baudrate = 9600,
        parity=serial.PARITY_ODD,
        stopbits=serial.STOPBITS_TWO,
        bytesize=serial.SEVENBITS
        )
    ser.flush()
    arduino_connected = True
except:
    print("Arduino Not Connected")
    arduino_connected = False

def createButton(label, isOn, tied_func):
	btn = QPushButton(label)
	btn.setCheckable(True)
	if (isOn):
		btn.toggle()

	btn.clicked.connect(tied_func)

	return btn

def createLabel(label, color = "darkCyan", alignment = 1):
	label = QLabel(label)

	label.setStyleSheet("background-color:" + color)

	if (alignment == 1):
		label.setAlignment(Qt.AlignCenter)
	elif (alignment == 2):
		label.setAlignment(Qt.AlignRight)

	return label

def createHorizontalSlider(min, max, start_value, tied_func):
	slider = QSlider(Qt.Horizontal)

	slider.setMinimum(min)
	slider.setMaximum(max)
	slider.setValue(start_value)

	slider.valueChanged.connect(tied_func)

	return slider


class MainWindow(QMainWindow):
	def __init__(self, *args, **kwargs):
		super(MainWindow, self).__init__(*args, **kwargs)

		self.setWindowTitle("Testing GUI")

		self.weighted_freq_jump_ranges = {}
		self.num_of_ranges = 0;

		self.times = []
		self.water_percent = []

		self.main_layout = QVBoxLayout()

		self.waveform_layout = QHBoxLayout()

		self.run_waveform = createButton("Run Waveform", False, self.enableWaveform)

		#Create all the widgets for wave type
		self.wave_type_layout = QVBoxLayout()
		self.wave_type_layout.setSpacing(5)
		self.wave_type_layout.setContentsMargins(0, 0, 0, 0)

		#Label for Wave Types
		self.wave_label = createLabel("Primary Wave Type")
		#Button for sinusoid
		self.sinusoid_wave = createButton("Sinusoid", True, self.enableSine)
		self.sinusoid_wave.clicked.connect(self.enableSine)
		#Button for square wave
		self.square_wave = createButton("Square Wave", False, self.enableSquare)
		

		#Adds all the wavetype widgets
		self.wave_type_layout.addWidget(self.wave_label)
		self.wave_type_layout.addWidget(self.sinusoid_wave)
		self.wave_type_layout.addWidget(self.square_wave)

		#Label specifying wave carrier
		self.wave_modulation_label = createLabel("Type of Wave Modulation")
		#Button for Trapezoid Modulation
		self.sinusoid_modulation = createButton("Sinusoidal Modulation", False, self.setSinsuoidMod)
		#Button for Sinusoid Modulation
		self.trapezoid_modulation = createButton("Trapezoidal Modulation", False, self.setTrapezoidMod)

		self.wave_type_layout.addWidget(self.wave_modulation_label)
		self.wave_type_layout.addWidget(self.sinusoid_modulation)
		self.wave_type_layout.addWidget(self.trapezoid_modulation)



		#Creates all the widgets for primary waveform measurements
		self.wave_measurement_layout = QVBoxLayout()
		self.wave_measurement_layout.setContentsMargins(0, 0, 0, 0)
		self.wave_measurement_layout.setSpacing(5)

		self.wave_measurement_label = createButton("Measurements for Primary Waveform", True, self.keepOn)

		#Used for setting Wave Amplitude
		self.wave_amplitude_label = createLabel("Wave Amplitude: 0.46")
		self.wave_amplitude_slider = createHorizontalSlider(0, 91, 46, self.setAmplitude)

		#Used for setting Wave Frequency
		self.wave_frequency_label = createLabel("Wave Frequency: 500")
		self.wave_frequency_slider = createHorizontalSlider(0, 999, 500, self.setFrequency)

		#Used for setting Wave Symmetry
		self.wave_symmetry_label = createLabel("Wave Symmetry (%): 50")
		self.wave_symmetry_slider = createHorizontalSlider(0, 99, 50, self.setSymmetry)

		self.wave_measurement_layout.addWidget(self.wave_measurement_label)
		self.wave_measurement_layout.addWidget(self.wave_amplitude_label)
		self.wave_measurement_layout.addWidget(self.wave_amplitude_slider)
		self.wave_measurement_layout.addWidget(self.wave_frequency_label)
		self.wave_measurement_layout.addWidget(self.wave_frequency_slider)		
		self.wave_measurement_layout.addWidget(self.wave_symmetry_label)
		self.wave_measurement_layout.addWidget(self.wave_symmetry_slider)

		##############################################################
		
		##############################################################

		#Creates all the widgets for carrier waveform measurements
		self.pulse_mod_layout = QVBoxLayout()
		self.pulse_mod_layout.setContentsMargins(0, 0, 0, 0)
		self.pulse_mod_layout.setSpacing(5)

		self.pulse_mod = createButton("Pulse Modulation", False, self.enablePulseModulation)

		self.pulse_mod_duty_cycle_label = createLabel("Duty Cycle (%): 50")
		self.pulse_mod_duty_cycle_slider = createHorizontalSlider(0, 99, 50, self.setModDutyCycle)


		#Used for setting Wave Frequency
		self.pulse_mod_frequency_label = createLabel("Frequency: 50")
		self.pulse_mod_frequency_slider = createHorizontalSlider(0, 99, 50, self.setModFrequency)

		#Used for setting Wave Symmetry
		self.pulse_mod_rise_time_label = createLabel("Rise Time (%): 50")
		self.pulse_mod_rise_time_slider = createHorizontalSlider(0, 99, 50, self.setModRiseTime)

		self.pulse_mod_layout.addWidget(self.pulse_mod)
		self.pulse_mod_layout.addWidget(self.pulse_mod_duty_cycle_label)
		self.pulse_mod_layout.addWidget(self.pulse_mod_duty_cycle_slider)
		self.pulse_mod_layout.addWidget(self.pulse_mod_frequency_label)
		self.pulse_mod_layout.addWidget(self.pulse_mod_frequency_slider)		
		self.pulse_mod_layout.addWidget(self.pulse_mod_rise_time_label)
		self.pulse_mod_layout.addWidget(self.pulse_mod_rise_time_slider)

		##############################################################
		
		##############################################################

		#Creates all the widgets for carrier waveform measurements
		self.sweep_layout = QVBoxLayout()
		self.sweep_layout.setContentsMargins(0, 0, 0, 0)
		self.sweep_layout.setSpacing(5)

		self.sweep = createButton("Sweep Frequency", False, self.enablePulseModulation)

		self.sweep_min_freq_label = createLabel("Minimum Frequency: 500")
		self.sweep_min_freq_slider = createHorizontalSlider(0, 999, 500, self.setMinSweepFreq)


		#Used for setting Wave Frequency
		self.sweep_max_freq_label = createLabel("Maximum Frequency: 500")
		self.sweep_max_freq_slider = createHorizontalSlider(0, 999, 500, self.setMaxSweepFreq)

		#Used for setting Wave Symmetry
		self.sweep_time_label = createLabel("Sweep Time (s): 50")
		self.sweep_time_slider = createHorizontalSlider(0, 99, 50, self.setSweepTime)

		self.sweep_layout.addWidget(self.sweep)
		self.sweep_layout.addWidget(self.sweep_min_freq_label)
		self.sweep_layout.addWidget(self.sweep_min_freq_slider)
		self.sweep_layout.addWidget(self.sweep_max_freq_label)
		self.sweep_layout.addWidget(self.sweep_max_freq_slider)		
		self.sweep_layout.addWidget(self.sweep_time_label)
		self.sweep_layout.addWidget(self.sweep_time_slider)

		##############################################################
		
		##############################################################

		#Make all the widgets for random jumping the waveforms
		self.wave_jumping_layout = QVBoxLayout()
		self.wave_jumping_layout.setContentsMargins(0, 0, 0, 0)
		self.wave_jumping_layout.setSpacing(5)

		self.freq_jumping = createButton("Random Frequency Jumping", False, self.enableFreqJumping)
		self.freq_jump_cycle_label = createLabel("Cycles Before Frequency Jump: 50", alignment = 0)
		self.freq_jump_cycle_slider = createHorizontalSlider(0, 99, 50, self.setFreqJumpCycles)
		self.freq_jump_diff_label = createLabel("Maximum Frequency Difference: 500", alignment = 0)
		self.freq_jump_difference = createHorizontalSlider(0, 999, 500, self.setMaxFreqJump)
		
		self.amp_jumping = createButton("Random Amplitude Jumping", False, self.enableAmpJumping)
		self.amp_jump_cycle_label = createLabel("Cycles Before Amplitude Jump: 50", alignment = 0)
		self.amp_jump_cycle_slider = createHorizontalSlider(0, 99, 50, self.setAmpJumpCycles)
		self.amp_jump_diff_label = createLabel("Maximum Amplitude Difference: 0.50", alignment =  0)
		self.amp_jump_difference = createHorizontalSlider(0, 99, 50, self.setMaxAmpJump)

		#Add all the waveform jumping widgets
		self.wave_jumping_layout.addWidget(self.freq_jumping)
		self.wave_jumping_layout.addWidget(self.freq_jump_cycle_label)
		self.wave_jumping_layout.addWidget(self.freq_jump_cycle_slider)
		self.wave_jumping_layout.addWidget(self.freq_jump_diff_label)
		self.wave_jumping_layout.addWidget(self.freq_jump_difference)
		self.wave_jumping_layout.addWidget(self.amp_jumping)
		self.wave_jumping_layout.addWidget(self.amp_jump_cycle_label)
		self.wave_jumping_layout.addWidget(self.amp_jump_cycle_slider)
		self.wave_jumping_layout.addWidget(self.amp_jump_diff_label)
		self.wave_jumping_layout.addWidget(self.amp_jump_difference)

		##############################################################
		
		##############################################################

		#Make all the widgets for weighted jumping of the waveforms
		self.weighted_freq_jump_layout = QVBoxLayout()
		self.weighted_freq_jump_layout.setContentsMargins(0, 0, 0, 0)
		self.weighted_freq_jump_layout.setSpacing(5)

		self.weighted_freq_jump_button = createButton("Weighted Frequency Jumping", False, self.enableWeightedFreq)
		self.weighted_freq_box = QGroupBox("Weighted Frequency Range")
		self.weighted_freq_form_layout = QFormLayout()
		self.weighted_freq_form_layout.addRow(QLabel("Lower Frequency Bound:"), QLineEdit())
		self.weighted_freq_form_layout.addRow(QLabel("Upper Frequency Bound:"), QLineEdit())
		self.weighted_freq_form_layout.addRow(QLabel("Weight (integer):"), QLineEdit())
		self.weighted_freq_box.setLayout(self.weighted_freq_form_layout)
		self.single_form = QFormLayout()
		self.single_form.addRow(QLabel("Cycles before Frequency Jump: "), QLineEdit())
		self.weighted_freq_range_button = createButton("Add Weighted Frequency Range", False, self.addWeightedFreqRange)
		
		#Add all the waveform jumping widgets
		self.weighted_freq_jump_layout.addWidget(self.weighted_freq_jump_button)
		self.weighted_freq_jump_layout.addWidget(self.weighted_freq_box)
		self.weighted_freq_jump_layout.addLayout(self.single_form)
		self.weighted_freq_jump_layout.addWidget(self.weighted_freq_range_button)


		##############################################################
		
		##############################################################

		#Add all the different layouts to the waveform layout
		self.waveform_layout.addLayout(self.wave_type_layout, 1)
		self.waveform_layout.addLayout(self.wave_measurement_layout, 2)
		self.waveform_layout.addLayout(self.pulse_mod_layout, 2)
		self.waveform_layout.addLayout(self.sweep_layout, 2)
		self.waveform_layout.addLayout(self.wave_jumping_layout, 2)
		self.waveform_layout.addLayout(self.weighted_freq_jump_layout, 2)

		##############################################################
		
		##############################################################
		#Video widget with pause and play buttons

		self.video_widget = QVideoWidget()

		self.open_video_button = QPushButton("Open Video")   
		self.open_video_button.setToolTip("Open Video File")
		self.open_video_button.setStatusTip("Open Video File")
		self.open_video_button.setFixedHeight(24)
		self.open_video_button.setIconSize(QSize(16, 16))
		self.open_video_button.setIcon(QIcon.fromTheme("document-open", QIcon("D:/_Qt/img/open.png")))
		self.open_video_button.clicked.connect(self.open_video)

		self.play_video = QPushButton()
		self.play_video.setEnabled(False)
		self.play_video.setFixedHeight(24)
		self.play_video.setIconSize(QSize(16, 16))
		self.play_video.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
		self.play_video.clicked.connect(self.play)

		self.video_slider = QSlider(Qt.Horizontal)
		self.video_slider.setRange(0, 15)
		self.video_slider.sliderMoved.connect(self.setPosition)

		self.video_control_layout = QHBoxLayout()
		self.video_control_layout.setContentsMargins(0, 0, 0, 0)
		self.video_control_layout.addWidget(self.open_video_button)
		self.video_control_layout.addWidget(self.play_video)
		self.video_control_layout.addWidget(self.video_slider)

		self.media_player = QMediaPlayer(None, QMediaPlayer.VideoSurface)
		self.media_player.setVideoOutput(self.video_widget)
		self.media_player.positionChanged.connect(self.positionChanged)
		self.media_player.durationChanged.connect(self.durationChanged)

		self.video_layout = QVBoxLayout()
		self.video_layout.addWidget(self.video_widget)
		self.video_layout.addLayout(self.video_control_layout)

		##############################################################
		
		##############################################################
		#Graph of water percent obscuration vs time

		self.graph = pg.PlotWidget(self)
		self.graph.plot(self.times, self.water_percent)
		self.graph.setLabel('bottom', text = 'Time', units = 's')
		self.graph.setLabel('left', text = 'Percent Obscuration', units = '%')
		self.graph.setYRange(0, 105, padding = 0)

		##############################################################
		
		##############################################################
		#Adds all the layouts to the main layout/screen

		self.upper_layout = QHBoxLayout()
		self.upper_layout.addLayout(self.video_layout)
		self.upper_layout.addWidget(self.graph)

		self.main_layout.addLayout(self.upper_layout)
		self.main_layout.addWidget(self.run_waveform)
		self.main_layout.addLayout(self.waveform_layout)

		main_screen = QWidget()
		main_screen.setLayout(self.main_layout)

		self.setCentralWidget(main_screen)
	

	def enableWaveform(self):
		if (self.run_waveform.isChecked()):
			out = "1"
		else:
			out = "0"

		#Append the carrier wave values
		out += 'c'
		if (self.square_wave.isChecked()):
			out += "1"
		else:
			out += "0"
		out += str(self.wave_frequency_slider.value()).zfill(3)
		out += "0." + str(self.wave_amplitude_slider.value()).zfill(2)
		out += "0." + str(self.wave_symmetry_slider.value()).zfill(2)

		#Append the Pulse Modulation Values
		out += 'p'
		if (self.pulse_mod.isChecked()):
			out += "1"
		else:
			out += "0"
		if (self.sinusoid_modulation.isChecked()):
			out += "2"
		else:
			out += "1"
		out += "0." + str(self.pulse_mod_duty_cycle_slider.value()).zfill(2)
		out += str(self.pulse_mod_frequency_slider.value()).zfill(2)
		out += str(self.pulse_mod_rise_time_slider.value()).zfill(2)

		#Append the Sweep Values
		out += 's'
		if (self.sweep.isChecked()):
			out += "1"
		else:
			out += "0"
		if (self.sweep_min_freq_slider.value() <= self.sweep_max_freq_slider.value()):
			out += str(self.sweep_min_freq_slider.value()).zfill(3)
			out += str(self.sweep_max_freq_slider.value()).zfill(3)
		else:
			out += str(self.sweep_min_freq_slider.value()).zfill(3)
			out += str(self.sweep_min_freq_slider.value()).zfill(3)
		out += str(self.sweep_time_slider.value()).zfill(2)

		#Append the Frequency Jumping Values
		out += 'f'
		if (self.freq_jumping.isChecked()):
			out += "1"
		else:
			out += "0"
		out += str(self.freq_jump_cycle_slider.value()).zfill(2)
		out += str(self.freq_jump_difference.value()).zfill(3)

		#Append the Amplitude Jumping Values
		out += 'a'
		if (self.amp_jumping.isChecked()):
			out += "1"
		else:
			out += "0"
		out += str(self.amp_jump_cycle_slider.value()).zfill(2)
		out += "0." + str(self.amp_jump_difference.value()).zfill(2)

		#Append the Weighted Frequency Jumping Values
		out += 'w'
		if (not self.weighted_freq_jump_button.isChecked()):
			out += "0"
		else:
			out += str(self.num_of_ranges)
		out += self.single_form.itemAt(0,1).widget().text().zfill(2)
		for key, value in self.weighted_freq_jump_ranges.items():
			out += str(key[0]).zfill(3) + str(key[1]).zfill(3) + str(value)
		
		print (out)

		#ser.write(out.encode())
		#ser.flush()

	def keepOn(self):
		if (not self.wave_measurement_label.isChecked()):
			self.wave_measurement_label.toggle()

	##############################################################
	#Carrier Wave Buttons#
	##############################################################

	def setAmplitude(self, value):
		if (value < 10):
			self.wave_amplitude_label.setText("Amplitude: 0.0" + str(value))
		else:
			self.wave_amplitude_label.setText("Amplitude: 0." + str(value))
	def setFrequency(self, value):
		self.wave_frequency_label.setText("Frequency: " + str(value))
	def setSymmetry(self, value):
		self.wave_symmetry_label.setText("Symmetry (%): " + str(value))

	def enableSine(self):
		if (not self.sinusoid_wave.isChecked()):
			self.sinusoid_wave.toggle()
		else:
			print("Waveform set to Sine Wave")

		if (self.square_wave.isChecked()):
			self.square_wave.toggle()

	def enableSquare(self):
		if (not self.square_wave.isChecked()):
			self.square_wave.toggle()
		else:
			print("Waveform set to Square Wave")
		
		if (self.sinusoid_wave.isChecked()):
			self.sinusoid_wave.toggle()
		
	##############################################################
	#Pulse Modulation Buttons#
	##############################################################
	def enablePulseModulation(self, value):
		if (self.pulse_mod.isChecked()):
			print("Pulse Modulation Enabled")
		else:
			print("Pulse Modulation Disabled")
		
	def setModDutyCycle(self, value):
		self.pulse_mod_duty_cycle_label.setText("Duty Cycle (%): "+ str(value))
	def setModFrequency(self, value):
		self.pulse_mod_frequency_label.setText("Frequency: " + str(value))
	def setModRiseTime(self, value):
		self.pulse_mod_rise_time_label.setText("Rise Time (%): "  + str(value))

	def setSinsuoidMod(self):
		if (not self.sinusoid_modulation.isChecked()):
			self.sinusoid_modulation.toggle()
		else:
			print("Carrier Wave set to Sinusoid")

		if(self.trapezoid_modulation.isChecked()):
			self.trapezoid_modulation.toggle()

	def setTrapezoidMod(self):
		if (not self.trapezoid_modulation.isChecked()):
			self.trapezoid_modulation.toggle()
		else:
			print("Carrier Wave set to Trapezoidal")
		if(self.sinusoid_modulation.isChecked()):
			self.sinusoid_modulation.toggle()

	##############################################################
	#Sweeping Frequency Buttons#
	##############################################################
	def enableSweeping(self, value):
		if (self.sweep.isChecked()):
			print("Sweeping Frequency Enabled")
		else:
			print("Sweeping Frequency Disabled")
	def setMinSweepFreq(self, value):
		self.sweep_min_freq_label.setText("Minimum Frequency: " + str(value))
	def setMaxSweepFreq(self, value):
		self.sweep_max_freq_label.setText("Maximum Frequency: " + str(value))
	def setSweepTime(self, value):
		self.sweep_time_label.setText("Sweep Time (s): " + str(value))


	##############################################################
	#Amplitude/Frequency Jumping Buttons#
	##############################################################
	def setFreqJumpCycles(self, value):
		self.freq_jump_cycle_label.setText("Cycles Before Frequency Jump: " + str(value))
	def setMaxFreqJump(self, value):
		self.freq_jump_diff_label.setText("Maximum Frequency Difference: " + str(value))
	def setAmpJumpCycles(self, value):
		self.amp_jump_cycle_label.setText("Cycles Before Amplitude Jump: " + str(value))
	def setMaxAmpJump(self, value):
		self.amp_jump_diff_label.setText("Maximum Amplitude Difference: 0." + str(value).zfill(2))
	def enableFreqJumping(self):
		if(self.freq_jumping.isChecked()):
			print ("Frequency Jumping Enabled")
		else:
			print ("Frequency Jumping Disabled")
		
	def enableAmpJumping(self):
		if(self.amp_jumping.isChecked()):
			print("Amplitude Jumping Enabled")
		else:
			print("Amplitude Jumping Disabled")
		

	def enableWeightedFreq(self):
		if(self.weighted_freq_jump_button.isChecked()):
			print("Weighted Frequency Jumping Enabled")
		else:
			print("Weighted Frequency Jumping Disabled")

	def addWeightedFreqRange(self):
		self.num_of_ranges += 1;
		self.weighted_freq_range_button.toggle()
		bounds = (self.weighted_freq_form_layout.itemAt(0,1).widget().text().zfill(3), self.weighted_freq_form_layout.itemAt(1,1).widget().text().zfill(3))
		self.weighted_freq_jump_ranges[bounds] = self.weighted_freq_form_layout.itemAt(2,1).widget().text()
		
		self.weighted_freq_form_layout.itemAt(0,1).widget().setText("")
		self.weighted_freq_form_layout.itemAt(1,1).widget().setText("")
		self.weighted_freq_form_layout.itemAt(2,1).widget().setText("")

		print("Weighted Frequency Range Added")
		print(self.weighted_freq_jump_ranges)
		print("Number of Ranges: " + str(self.num_of_ranges))
	def open_video(self):
		fileName, _ = QFileDialog.getOpenFileName(self, "Selecciona los mediose",
				".", "Video Files (*.mp4 *.flv *.ts *.mts *.avi)")

		if fileName != '':
			self.media_player.setMedia(
			        QMediaContent(QUrl.fromLocalFile(fileName)))
			self.play_video.setEnabled(True)
			self.start_time = time.time()
			self.play()

	def play(self):
		if self.media_player.state() == QMediaPlayer.PlayingState:
			self.media_player.pause()
			self.play_video.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
		else:
			self.media_player.play()
			self.play_video.setIcon(self.style().standardIcon(QStyle.SP_MediaPause))

	def positionChanged(self, position):
		self.video_slider.setValue(position)

	def durationChanged(self, duration):
		self.video_slider.setRange(0, duration)
		self.graph.setXRange(0, .00105*duration)

	def setPosition(self, position):
		self.media_player.setPosition(position)

	#def updateGraph(self)


if __name__ == '__main__':
	app = QApplication(sys.argv)
	player = MainWindow()
	player.resize(1920, 1080)
	player.show()
	sys.exit(app.exec_())

















