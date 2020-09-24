import numpy as np
import cv2
import time

SCREEN_HEIGHT = 200
HEIGHT_OFFSET = 200

def captureBaseImage(vid_stream):
	
	start_time = time.time()
	
	while (time.time() - start_time < 0.5):
		global base_image
		# vid_stream frame-by-frame
		ret, frame = vid_stream.read()
	
		if (not ret):
			print ("No Video Stream Detected")
			exit()
	
		# Our operations on the frame come here
		base_image = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
	
	print ("Base Image Captured")
	
	return base_image
	
def createMask(base, ht_offset, screen_ht):
	img = base.copy()

	bound_list = np.array([], np.int32)

	#Creates the masked area
	bound_list = np.array([[0, ht_offset], [0, ht_offset+screen_ht], 
	                       [img.shape[1], ht_offset+screen_ht], [img.shape[1], ht_offset]], np.int32)
	
	bound_list = bound_list.reshape((-1, 1, 2))
	#Fills the testing area with black
	img = cv2.fillPoly(img, [bound_list], 0)
	'''
	#Fill in above the mask with pure white
	bound_list = np.array([[0, 0], 
	                       [img.shape[1], ht_offset+screen_ht],
	                       [img.shape[1], img.shape[0]], 
	                       [0, img.shape[0]]], np.int32)
	bound_list = bound_list.reshape((-1, 1, 2))
	
	img = cv2.fillPoly(img, [bound_list], 255)
	
	#Fill in below the mask with pure white
	bound_list = np.array([[0, ht_offset+screen_ht], 
	                       [img.shape[1], ht_offset+screen_ht],
	                       [img.shape[1], img.shape[0]], 
	                       [0, img.shape[0]]], np.int32)
	bound_list = bound_list.reshape((-1, 1, 2))
	
	img = cv2.fillPoly(img, [bound_list], 255)'''

	return img
	
'''
while (True):
	cv2.imshow('frame',base_image)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break
'''

if __name__ == '__main__':
	vid_stream = cv2.VideoCapture(0)
	base_image = captureBaseImage(vid_stream)
	mask = createMask(base_image, HEIGHT_OFFSET, SCREEN_HEIGHT)

	while (True):
		cv2.imshow('Base Image',base_image)
		if cv2.waitKey(1) & 0xFF == ord('q'):
			break
	cv2.destroyAllWindows()

	while (True):
		cv2.imshow('Mask',mask)
		if cv2.waitKey(1) & 0xFF == ord('q'):
			break
	cv2.destroyAllWindows()

	mask_white_pixels = cv2.countNonZero(mask)
	lidar_area = mask.size - cv2.countNonZero(mask)

	num_regions = 5
	region_width = base_image.shape[1]

	# When everything done, release the vid_streamture
	vid_stream.release()
	cv2.destroyAllWindows()












