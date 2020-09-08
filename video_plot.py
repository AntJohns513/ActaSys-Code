import sys
import time
from datetime import datetime
import math
import random
import serial
import cv2
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

src1 = cv2.imread('Base_Image.jpg')
base_image = cv2.cvtColor(src1, cv2.COLOR_BGR2GRAY)

#Use Manually select the points for the mask
'''
bound_list = np.array([], np.int32)

drawing_image = base_image.copy()

drawing_disabled = False

def draw_circle(event,x,y,flags,param):
    global drawing_disabled
    global bound_list
    if event == cv2.EVENT_LBUTTONDBLCLK:
        cv2.circle(drawing_image,(x,y),5,(255,0,0),-1)
        if(x < 10 and y < 10):
            drawing_disabled = True
            print("DRAWING DISABLED")
            print("Disable Point: ", x, y)
        else:
            print("Point:",x,y)
            bound_list = np.append(bound_list, [x,y])

# Create a black image, a window and bind the function to window
cv2.namedWindow('Marked Image')
cv2.moveWindow('Marked Image', 0, 0)
cv2.setMouseCallback('Marked Image',draw_circle)

while(1):
    cv2.imshow('Marked Image',drawing_image)
    cv2.waitKey(1)
    if drawing_disabled:
        break
cv2.destroyAllWindows()

bound_list = np.reshape(bound_list, (-1, 2))
'''

#Hardcoded bounds for The mask
bound_list = np.array([[767, 324], [1210, 187], [1166, 35], [675, 61], [25, 103], [5, 131], [64, 401], [101, 421]], np.int32)

bound_list = bound_list.reshape((-1, 1, 2))

print ("Points Used For Mask:\n", bound_list)


simple_mask = base_image.copy()
#Shades in the testing area from points specified above for mask
simple_mask = cv2.fillPoly(simple_mask, [bound_list], 0)

#Creates the mask to be added to images
ret, simple_mask = cv2.threshold(simple_mask,1,255,cv2.THRESH_BINARY);


cv2.namedWindow('Simple Mask')
cv2.moveWindow('Simple Mask', 0, 0)
cv2.imshow('Simple Mask', simple_mask)
cv2.waitKey(0)
cv2.destroyAllWindows()


mask_white_pixels = cv2.countNonZero(simple_mask)
lidar_area = simple_mask.size - cv2.countNonZero(simple_mask)


#Adds Mask to the base image (not needed)
#base_image = cv2.add(base_image, simple_mask)

data = pd.DataFrame({'Time':[], 'Water Percentage':[]} )

start_time = time.time()

src_vid = cv2.VideoCapture('Live_Video.mp4')

success, current_image = src_vid.read()

while(success):
    #Converts current image into gray scale
    current_image = cv2.cvtColor(current_image, cv2.COLOR_BGR2GRAY)

    #Creates the subtracted image between base and current then re-applies mask
    grayscale_difference = cv2.absdiff(base_image, current_image)
    grayscale_difference = cv2.add(grayscale_difference, simple_mask)

    #Converts the subtracted image into a purely binary black/white image
    ret, binary_difference = cv2.threshold(grayscale_difference,15,255,cv2.THRESH_BINARY); 

    #binary_difference = cv2.add(binary_difference, simple_mask)

    #print("Frame:", binary_difference.shape)

    #Number of White Pixels
    #print(cv2.countNonZero(binary_difference))

    num_white_pixels = cv2.countNonZero(binary_difference)

    new_row = {'Time': time.time()-start_time, 'Water Percentage': (num_white_pixels - mask_white_pixels)/lidar_area * 100}

    data = data.append(new_row, ignore_index = True)

    success, current_image = src_vid.read()

src_vid.release()

plt.plot(data["Time"], data["Water Percentage"], linewidth = 2)
plt.show()









