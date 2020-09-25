import numpy as np
import cv2
import time

SCREEN_HEIGHT = 110
HEIGHT_OFFSET = 50

def captureBaseImage(vid_stream):
	
	start_time = time.time()
	
	while (time.time() - start_time < 0.1):
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
	
	#Fill in above the mask with pure white
	'''bound_list = np.array([[0, 0], [0, ht_offset],
						   [img.shape[1], ht_offset],
						   [img.shape[1], 0]],  np.int32)
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

if __name__ == '__main__':
	vid_stream = cv2.VideoCapture(0)

	#Capture the base image with droplets and create a mask
	base_image = captureBaseImage(vid_stream)
	mask = createMask(base_image, HEIGHT_OFFSET, SCREEN_HEIGHT)

	mask_white_pixels = cv2.countNonZero(mask)
	lidar_area = mask.size - mask_white_pixels

	num_regions = 5
	region_width = int(base_image.shape[1] / num_regions)
	region_area = lidar_area/num_regions

	column_names = []
	for i in range(num_regions):
		column_names.append("Region " + str(i))
	
	while (True):
		ret, current_image = vid_stream.read()
	
		if (not ret):
			print ("Video Stream Failed")
			exit()


		cv2.imshow("Live Feed", mask)

		if cv2.waitKey(1) & 0xFF == ord('q'):
			break
	# When everything done, release the vid_streamture
	vid_stream.release()
	cv2.destroyAllWindows()
