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


src1 = cv2.imread('Base_Image.png')
src2 = cv2.imread('Video_Image.png')


window_name = "Base_Image"
base_image = cv2.cvtColor(src1, cv2.COLOR_BGR2GRAY)

clean_image = cv2.cvtColor(src2, cv2.COLOR_BGR2GRAY)

subtracted_image = cv2.absdiff(base_image, clean_image)

ret, black_white_difference = cv2.threshold(subtracted_image,15,255,cv2.THRESH_BINARY); 

titles = ["Base Image", "Cleaned Image", "Gray Difference", "Binary Difference"]
images = [base_image, clean_image, subtracted_image, black_white_difference]

#for i in range(0, 4):
#    cv2.namedWindow(titles[i])
#    cv2.moveWindow(titles[i], 0, 0)
#    cv2.imshow(titles[i], images[i])
#    cv2.waitKey(0)
#cv2.destroyAllWindows()

bound_list = list()

'''
#Use This to find the points for the mask
def draw_circle(event,x,y,flags,param):
    if event == cv2.EVENT_LBUTTONDBLCLK:
        cv2.circle(base_image,(x,y),5,(255,0,0),-1)
        print("Point:",x,y)

# Create a black image, a window and bind the function to window
cv2.namedWindow('image')
cv2.setMouseCallback('image',draw_circle)

while(1):
    cv2.imshow('image',base_image)
    if cv2.waitKey(20) & 0xFF == 27:
        break
cv2.destroyAllWindows()
'''

black_white_mask = base_image.copy()

#Shades in the testing area from points found using above code
pts = np.array([[499, 585], [759, 532], [1076, 436], [1416, 294], [1545, 200], [1527, 143], [1065, 143], [381, 271]], np.int32)
pts = pts.reshape((-1, 1, 2))
black_white_mask = cv2.fillPoly(black_white_mask, [pts], 0)

#Creates the mask to be added to images
ret, black_white_mask = cv2.threshold(black_white_mask,1,255,cv2.THRESH_BINARY);

base_image = cv2.add(base_image, black_white_mask)

cv2.namedWindow('Masked Base')
cv2.moveWindow('Masked Base', 0, 0)
cv2.imshow('Masked Base', base_image)
cv2.waitKey(0)
cv2.destroyAllWindows()


















