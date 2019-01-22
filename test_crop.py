#test cropping
import time
from PIL import Image, ImageDraw, ImageOps
import cv2
import numpy as np
import math

class Crop(object):

	def __init__(self):
		print("init")
		#self.cutit()
		self.usecv2()

	def cutit(self):
		size = (1280, 720)
		transparent_area = (50,80,400,400)

		im = Image.new('RGBA', size, (255, 255, 255, 0))

		mask=Image.new('L', im.size, color=255)
		draw=ImageDraw.Draw(mask) 
		draw.rectangle(transparent_area, fill=0)
		im.putalpha(mask)

		#draw = ImageDraw.Draw(img)
		#draw.ellipse((25, 25, 75, 75), fill=(0, 0, 0))

		im.save(r'C:\Users\Ben\Documents\JAABA\practice_mask\mask_with_alpha.png', 'PNG')

		#colorim = Image.new('L', size, color = 100)

		#mask=Image.new('L', size, color=255)
		#draw=ImageDraw.Draw(mask) 
		#draw.rectangle(transparent_area, fill=0)

		#output = ImageOps.fit(colorim, mask.size, centering=(0.5, 0.5))
		#output.putalpha(mask)
		#mask.save(r'C:\Users\Ben\Documents\JAABA\practice_mask\mask_with_alpha.png', 'PNG')
		#mask.save(r'C:\Users\Ben\Documents\JAABA\PythonForJaaba\test.png', 'PNG')

	def incircle(self, xinput, yinput):
		x = 150
		y = 150
		radius = 90
		ans = math.sqrt((x - xinput)**2 + (y - yinput)**2)
		return ans < radius

	def usecv2(self):
		mask1 = np.zeros((720, 1280, 3)).astype('uint8')
		mask2 = np.zeros((720, 1280, 3)).astype('uint8')
		for x in range(720):
			for y in range(1280):
				if self.incircle(x, y):
					mask1[x][y][:] = 1
				else:
					mask2[x][y][:] = 255

		videofile = r'C:\Users\Ben\Documents\JAABA\practice_mask\input.mp4'
		capture = cv2.VideoCapture(videofile)
		fourcc = cv2.VideoWriter_fourcc(*'mp4v')
		out = cv2.VideoWriter(r'C:\Users\Ben\Documents\JAABA\practice_mask\outputtry4.mp4', 
			fourcc, 30, (1280, 720))
			
		while(True):
			ret, frame = capture.read()

			if ret == True:
				#modify the current frame and write it to new video
				out.write(np.add(np.multiply(frame, mask1), mask2))
				#out.write(np.dstack([single] * 3))
			else:
				break

		capture.release()
		out.release()

		cv2.destroyAllWindows()


if __name__ == '__main__':
	s = time.time()
	self = Crop()
	print('Program took this long to run: ' + str(time.time() - s) + ' seconds')
