#Vineeth Vooppala
#Update 4-9-2019 by Anthony Mickalauskas
#Updated by Sumit Das (sumit.das.f@gmail.com)

import sys
import time
import datetime
import math
import random
import serial
import cv2
import numpy as np #np is a shorter name for numpy

from PyQt4.QtCore import *
from PyQt4.QtGui import *
import PyQt4
from PyQt4.uic import loadUi

import pyqtgraph as pg

import multiprocessing
from threading import Timer

appStyle="""QMainWindow{background-color: darkgray;}"""

actuator_on = 1

output_file = "output.dat"
output_file1 = "Interior.avi"
output_file2 = "Exterior.avi"

try:
    ser = serial.Serial(
        port='/dev/ttyACM1',
        baudrate = 9600,
        parity=serial.PARITY_ODD,
        stopbits=serial.STOPBITS_TWO,
        bytesize=serial.SEVENBITS
        )
    ser.flush()
    ard = True
except:
    print("Arduino Not Connected")
    ard = False

class wind(QMainWindow):
    def __init__(self):
        super(wind, self).__init__()

        loadUi('gui.ui',self)                   #Load GUI Layout

        ################################################################################################
        #Initialize Variables
        self.image = None
        self.t = []
        
        self.pob = []
        
        # These store the percentage data for each grid:        
        self.pob1 = []
        self.pob2 = []
        self.pob3 = []
        self.pob4 = []
        self.pob5 = []
        self.pob6 = []
        self.pob7 = []
        self.pob8 = []
        self.pob9 = []
            
        self.q = 1
        self.a = 1
        self.data_out = []
        ################################################################################################

        ################################################################################################
        #Setup Button Functionallity
        self.startButton.clicked.connect(self.startwebcam)
        #me self.startButton.clicked.connect(self.write_start)
        self.stopButton.clicked.connect(self.stopwebcam)
        ################################################################################################

        ################################################################################################
        #Setup Radio Buttons
        self.radioRGB.setChecked(True)
        self.radioThres.setChecked(False) 

        self.Pump_radio_off.setChecked(True)
        self.Pump_radio_on.setChecked(False)

        self.Act_radio_off.setChecked(True)
        self.Act_radio_on.setChecked(False)

        self.Heatcool_off.setChecked(True)
        self.Heatcool_on.setChecked(False)
        ################################################################################################

        ################################################################################################
        #Setup Doublespinbox
        self.doubleSpinBox.setRange(-25, 45)
        ################################################################################################

        ################################################################################################
        #Setup cameras
        self.webcam_num = 0
        # Start Video Camera (Internal)
        self.capture = cv2.VideoCapture('W-Static.mp4')
        self.webcam2_num = 1
        # Start Video Camera (External)
        self.capture2 = cv2.VideoCapture('W-Static.mp4')

        i = 1
        while i <= 30:
            self.capture.read()
            self.capture2.read()
            i = i + 1
        self.capture.set(cv2.CAP_PROP_FOCUS,.25)
        self.capture.set(cv2.CAP_PROP_AUTOFOCUS, 0)            # Disable AutoFocus
        self.capture2.set(cv2.CAP_PROP_FOCUS,.27)
        self.capture2.set(cv2.CAP_PROP_AUTOFOCUS, 0)           # Disable AutoFocus
        ################################################################################################

        ################################################################################################
        #Setup Graph
        self.graph = pg.PlotWidget(self)
        self.graph.plot(self.t,self.pob,pen='w',symbol=None)
        self.graph.setLabel('bottom', text='Time', units='s')
        self.graph.setLabel('left', text='Percent Obscuration', units='%')
        self.graph.move(990,40)
        self.graph.resize(900,540)
        self.graph.setYRange(0,110, padding=0)
        ################################################################################################

        manager = multiprocessing.Manager()
        self.T = manager.Value('d',0.4)
        self.Press = manager.Value('d',200.0)
        self.Hum = manager.Value('d',3.0)
        self.a = manager.Value('i',1)
        self.b = manager.Value('i',1)
        self.c = manager.Value('i',1)
        self.d = manager.Value('i',1)

        self.timer2 = QTimer(self)
        self.timer2.timeout.connect(self.spool)
        self.timer2.start(500)

        #################################################################################################
        #Video Writers
        self.frame_width = int(self.capture.get(cv2.CAP_PROP_FRAME_WIDTH)) #gets the frame width of the video
        self.frame_height = int(self.capture.get(cv2.CAP_PROP_FRAME_HEIGHT)) #gets the frame height of the video
        self.writer = cv2.VideoWriter(output_file1,cv2.VideoWriter_fourcc('M','J','P','G'), 13.0, (int(self.capture.get(cv2.CAP_PROP_FRAME_WIDTH)),int(self.capture.get(cv2.CAP_PROP_FRAME_HEIGHT))))
        self.writer2 = cv2.VideoWriter(output_file2,cv2.VideoWriter_fourcc('M','J','P','G'), 13.0, (int(self.capture.get(cv2.CAP_PROP_FRAME_WIDTH)),int(self.capture.get(cv2.CAP_PROP_FRAME_HEIGHT))))
        #################################################################################################

    def spool(self):
        if ard == True: #if Arduino is connected
            p = multiprocessing.Process(target=self.getenvirostat, args=(self.T,self.Press,self.Hum,self.a,self.b,self.c,self.d))
            p.start()

            if self.Act_radio_on.isChecked():
                self.d.value = 2

            if self.Act_radio_off.isChecked():
                self.d.value = 1

            if self.Heatcool_on.isChecked():
                if self.Heating.isChecked():
                    if self.T.value <= (self.doubleSpinBox.value()-.2):
                        self.a.value = 2
                        self.b.value = 2

                    if self.T.value > (self.doubleSpinBox.value()+.1):
                        self.a.value = 2
                        self.b.value = 1

                    if self.T.value > (self.doubleSpinBox.value()+.3):
                        self.a.value = 1
                        self.b.value = 1

                if self.Cooling.isChecked():
                    self.a.value = 1
                    self.b.value = 1

            if self.Heatcool_off.isChecked():
                self.a.value = 1
                self.b.value = 1

            if self.Pump_radio_off.isChecked():
                self.c.value = 1

            if self.Pump_radio_on.isChecked():
                self.c.value = 2

    def start_pump(self):
        self.Pump_radio_on.setChecked(True)
        self.Pump_radio_off.setChecked(False)
        self.c.value = 2

    def stop_pump(self):
        self.Pump_radio_off.setChecked(True)
        self.Pump_radio_on.setChecked(False)
        self.c.value = 1

    def Act_on(self):
        self.Act_radio_on.setChecked(True)
        self.Act_radio_off.setChecked(False)
        self.d.value = 2

    def Act_off(self):
        self.Act_radio_on.setChecked(False)
        self.Act_radio_off.setChecked(True)
        self.d.value = 1

    def getenvirostat(self,Tem, Pres, Humid,av,bv,cv,dv):
        achar = str(self.a.value)
        bchar = str(self.b.value)
        cchar = str(self.c.value)
        dchar = str(self.d.value)

        out = achar+bchar+cchar+dchar
        print(out)
        ser.write(out.encode())
        ser.flush()

        time.sleep(10)

        # Tem.value = 20
        # Pres.value = 40
        # Humid.value = 60

    def startwebcam(self):

        ret1,self.base = self.capture.read() #gets a frame from the webcam/video and used that as the base. ret1 is not used but is there to store a value returned from read()
        self.base_gray = cv2.cvtColor(self.base,cv2.COLOR_BGR2GRAY) #base_gray is a graystyle img
        rtl, self.thres = cv2.threshold(self.base_gray,0,255,cv2.THRESH_BINARY ); #thres is now an img where each pixel is either black or white

        width_number = 3
        height_number = 3
        width_step = int(self.frame_width/width_number)
        height_step = int(self.frame_height/height_number)
        
        #cropping thres into 9 parts:
        self.img1 = self.thres[0:height_step,0:width_step]
        self.img2 = self.thres[0:height_step,width_step:2*width_step]
        self.img3 = self.thres[0:height_step,2*width_step:3*width_step]
        self.img4 = self.thres[height_step:2*height_step,0:width_step]
        self.img5 = self.thres[height_step:2*height_step,width_step:2*width_step]
        self.img6 = self.thres[height_step:2*height_step,2*width_step:3*width_step]
        self.img7 = self.thres[2*height_step:3*height_step,0:width_step]
        self.img8 = self.thres[2*height_step:3*height_step,width_step:2*width_step]
        self.img9 = self.thres[2*height_step:3*height_step,2*width_step:3*width_step]        

        if self.Auto.isChecked():
            if actuator_on:
                Timer(4, self.start_pump, ()).start()
                Timer(20, self.stop_pump, ()).start()

##################################################################################################################################################################################################
            Timer(25, self.stopwebcam, ()).start()
####################################################################################################################################################################################################

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(5)
        self.baset = time.time() #baset is the time in seconds when the webcam starts

    def update_frame(self):
        ################################################################################################
        #Image Capture
        ret, self.image = self.capture.read() #gets a new frame
        ret2, self.image2 = self.capture2.read()

        self.writer.write(self.image)
        self.writer2.write(self.image2)
        ################################################################################################

        test = time.time() #test is the current time in seconds
        self.time = time.time() - self.baset #self.time is the time elapsed since startwebcam
        self.t.append(self.time) #adds elapsed time into self.t

        self.water_gray = cv2.cvtColor(self.image, cv2.COLOR_BGR2GRAY) #creates a graystyle of the grabbed frame
        self.sub = cv2.absdiff(self.water_gray,self.base_gray) #difference in the grabbed frame and the base frame
        rtl, self.sub_thres = cv2.threshold(self.sub,15,255,cv2.THRESH_BINARY); #takes the difference and turns it into binary pixels
        
        # Section to split the image into 9 sub grids
        width_number = 3
        height_number = 3
        width_step = int(self.frame_width/width_number)
        height_step = int(self.frame_height/height_number)
        
        img1 = self.sub_thres[0:height_step,0:width_step]
        img2 = self.sub_thres[0:height_step,width_step:2*width_step]
        img3 = self.sub_thres[0:height_step,2*width_step:3*width_step]
        img4 = self.sub_thres[height_step:2*height_step,0:width_step]
        img5 = self.sub_thres[height_step:2*height_step,width_step:2*width_step]
        img6 = self.sub_thres[height_step:2*height_step,2*width_step:3*width_step]
        img7 = self.sub_thres[2*height_step:3*height_step,0:width_step]
        img8 = self.sub_thres[2*height_step:3*height_step,width_step:2*width_step]
        img9 = self.sub_thres[2*height_step:3*height_step,2*width_step:3*width_step]
        
        # np.mean() is the average of the image
        # these 9 values are the ratio of the change to the origial as a percentage for each grid:
        self.po1 = (np.mean(img1)/np.mean(self.img1))*100
        self.po2 = (np.mean(img2)/np.mean(self.img2))*100
        self.po3 = (np.mean(img3)/np.mean(self.img3))*100
        self.po4 = (np.mean(img4)/np.mean(self.img4))*100
        self.po5 = (np.mean(img5)/np.mean(self.img5))*100
        self.po6 = (np.mean(img6)/np.mean(self.img6))*100
        self.po7 = (np.mean(img7)/np.mean(self.img7))*100
        self.po8 = (np.mean(img8)/np.mean(self.img8))*100
        self.po9 = (np.mean(img9)/np.mean(self.img9))*100
        
        #stores the percentages
        self.pob1.append(self.po1)
        self.pob2.append(self.po2)
        self.pob3.append(self.po3)
        self.pob4.append(self.po4)
        self.pob5.append(self.po5)
        self.pob6.append(self.po6)
        self.pob7.append(self.po7)
        self.pob8.append(self.po8)
        self.pob9.append(self.po9)
        
        #percentage for entire image:
        self.po = (np.mean(self.sub_thres)/np.mean(self.thres))*100  ## Add image weight here
        self.pob.append(self.po)
        
        self.displayImage(self.image,self.image2)
        
        plot_x = self.t[np.size(self.t)-100:np.size(self.t)]            #plots x without the first 100 datapoints in t
        plot_y = self.pob[np.size(self.pob)-100:np.size(self.pob)]      #plots y without the first 100 datapoints in pob
        self.graph.clear()
        self.graph.plot(plot_x,plot_y,pen='w',symbol=None)
        now = time.time()

    def displayImage(self,img,img2):
        if self.radioRGB.isChecked():
            ############################################################################################
            #LIDAR Image
            outImage = QImage(img,img.shape[1],img.shape[0],img.strides[0],QImage.Format_RGB888)
            outImage = outImage.rgbSwapped()
            self.camview.setPixmap(QPixmap.fromImage(outImage))
            self.camview.setScaledContents(True)
            ############################################################################################

            ############################################################################################
            #LIDAR External Image
            outImage2 = QImage(img2,img2.shape[1],img2.shape[0],img2.strides[0],QImage.Format_RGB888)
            outImage2 = outImage2.rgbSwapped()
            self.camview2.setPixmap(QPixmap.fromImage(outImage2))
            self.camview2.setScaledContents(True)
            ############################################################################################

        if self.radioThres.isChecked():
            ############################################################################################
            #LIDAR Image
            outImage = QImage(self.sub_thres,img.shape[1],img.shape[0],img.strides[0],QImage.Format_MonoLSB)
            outImage = outImage.rgbSwapped()
            self.camview.setPixmap(QPixmap.fromImage(outImage))
            self.camview.setScaledContents(True)
            ############################################################################################

            ############################################################################################
            #LIDAR External Image
            outImage2 = QImage(img2,img2.shape[1],img2.shape[0],img2.strides[0],QImage.Format_RGB888)
            outImage2 = outImage2.rgbSwapped()
            self.camview2.setPixmap(QPixmap.fromImage(outImage2))
            self.camview2.setScaledContents(True)
            ############################################################################################

    def stopwebcam(self):
        self.timer.stop()
        self.graph.clear()
        self.graph.plot(self.t,self.pob,pen='w',symbol=None)
        data = self.t,self.pob,self.pob1,self.pob2,self.pob3,self.pob4,self.pob5,self.pob6,self.pob7,self.pob8,self.pob9
        data = np.transpose(data)
        np.savetxt(output_file, data, delimiter = '\t')
        self.t = [];
        self.pob = [];
        self.capture.release() #closes video file

if __name__ == '__main__':
    app = QApplication(sys.argv)
    win = wind()
    win.setStyleSheet(appStyle)
    win.show()
    sys.exit(app.exec_())
