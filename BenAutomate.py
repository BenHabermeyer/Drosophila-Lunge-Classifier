import numpy as np
import pandas as pd
from tkinter import Tk, filedialog
import os, subprocess
import cv2
import pickle
from multiprocessing import Pool
import moviepy.editor as mpy
from moviepy.config import get_setting
import time
import moviepy


class VideoPipelineNew(object):

	#Create instance of class with 12 videos to crop
	def __init__(self, num_wells = 12):
		self.num_wells = num_wells
		self.well_roots = [] # This will contain the paths of all wells
		#self.circ_vid_root = []  # This will include the paths of all trimmed video with one well
		#select the video file
		self.load_single()
		#make its folders
		self.make_wellfolders()
		#detect the wells
		self.detect()
		#crop the videos
		#self.crop_vid()


	def load_single(self):
		"""
		Launch a GUI so people can click on the videofile that they want to track
		"""
		print('Please select the file corresponding to the video you would like to process')
		Tk().withdraw()  # we don't want a full GUI, so keep the root window from appearing
		self.filename = filedialog.askopenfilename()  # Set the filename of the video
		self.root = self.parent(self.filename)  # Set the video's folder
		self.name, self.fullname = self.get_fname(self.filename)

	def parent(self, path):
		"""Returns parent directory of a path"""
		return os.path.dirname(path)

	def get_fname(self, fullpath):
		"""Returns the base name of the path without filetype and with filetype
		e.x.
		input: '/Users/DrSwag/EverydayIm/Hustling.mp4'
		output: 'Hustling', 'Hustling.mp4'
		"""
		return os.path.basename(fullpath)[:-4], os.path.basename(fullpath)

	def show_attributes(self):
		"""
		Code serves to update attributes that are attached to the class, e.g. filetype/filename, and
		prints them all out to the user.
		"""
		self.attributes = '\n'.join("%s: %s" % item for item in vars(self).items())
		print('\nHere are the attributes you can access using .:')
		print(self.attributes)

	def make_wellfolders(self):
		"""
		Makes folders for each of the wells,

		 IMPORTANT
		---------
		Code Assumes that the number of wells is 12, if not this parameter needs to be changed below
		"""
		num_wells = self.num_wells
		# Check if there's a folder already for each well, if not make one
		for i in range(num_wells):  # number of wells, change if need be
			if not os.path.exists(
					os.path.normpath(os.path.join(self.root, self.name, 'well{}'.format(i)))):
				os.makedirs(os.path.join(self.root, self.name, 'well{}'.format(i)))
			self.well_roots.append(os.path.join(self.root, self.name, 'well{}'.format(i)))

	def detect(self):
		#to resolve later
		i = 0

		print('starting detect')
		num_wells = self.num_wells
		videofile = self.filename
		print('Videofile : ' + str(videofile))

		capture = cv2.VideoCapture(videofile)
		
		while(capture.isOpened()):
			ret, frame = capture.read()

			if frame is not None:
				gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
				blur = cv2.medianBlur(gray, 5)
				circles = cv2.HoughCircles(blur, cv2.HOUGH_GRADIENT, 1, 20, 
					param1=60, param2=30, minRadius=90, maxRadius=95)

				if circles is not None:
					circles = np.round(circles[0, :]).astype('int')

					for index, (x, y, r) in enumerate(circles):
						cv2.circle(frame, (x, y), r, (255, 0, 255), 2)
						X1, Y1 = x - r - 20, y - r - 20  # Top left rect coords
						X2, Y2 = x + r + 20, y + r + 20  # Bottom right rect coords
						side = X2 - X1
                    	# draw the frame of rectangle on the screen
						(cv2.rectangle(frame, (X1, Y2), (X2, Y1), (0, 255, 0), 3))

					if len(circles) == num_wells:
						cv2.imshow('frame', frame)

					#stop the loop if q is pressed
					#if cv2.waitKey(0) & 0xFF == ord('q'):
						#break

					 # if the 'q' key is pressed twice, stop the loop else next frame
					#if cv2.waitKey(0) & 0xFF != ord('q'):  # == ord('n'):
						#capture.read()
						
					
					if cv2.waitKey(2) & 0xFF == ord('q'):
						'''
						for index, (x, y, r) in enumerate(circles):
							print(index)
							print("({}, {}, {})".format(x, y, r))
						'''
						'''
						print(circles[:,0])
						print(circles[:,1])
						print(circles[:,2])
						array = np.array(list(zip(circles[:,0], circles[:,1])))
						print(array)
						'''

						if len(circles) == 12:
							d = self.get_well_labels(circles)
							dirname = os.path.dirname(videofile) + '\\'
							self.dictpath = dirname + 'well_dictionary'
							self.circlespath = dirname + 'well_circles'
							self.save_obj(d, self.dictpath)
							self.save_obj(circles, self.circlespath)
							#self.circ_vid_root.append(dirname + 'allwells')
							fname = dirname + 'crop_test.jpg'
							# write image
							cv2.imwrite(fname, frame)
							capture.release()
							cv2.destroyAllWindows()

					
	def save_obj(self, obj, name):
		"""saves passed obj as name.pickle"""
		with open(name + '.pickle', 'wb') as handle:
			pickle.dump(obj, handle, protocol=pickle.HIGHEST_PROTOCOL)

	def load_obj(self, name):
		"""loads name, which is a path to a pickle file without the .pickle at the end"""
		with open(name + '.pickle', 'rb') as handle:
			return pickle.load(handle)

	def get_well_labels(self, array):
		"""
		The purpose of this code is to use the circle generated from detect to generate a label (e.g. well0, well1,
		well2) that associates with it. Well number is left to right, top to the bottom
		:param array: an nx3 array(here 12x3), consisting of the (x,y) origin and radius of a circle.

		IMPORTANT
		---------
		Code Assumes that the number of wells is 12, if not this parameter needs to be changed below
		"""
		num_wells = self.num_wells  # Change this parameter as needed
		# Create dictionary for the 12 wells we'll edit later
		d = {'well' + str(i): i for i, j in enumerate(range(num_wells))}
		# inputted array is x,y,r of each circle, grab the x and y
		array = np.array(list(zip(array[:, 0], array[:, 1])))
		
		# let's organize y values first
		n1, n2 = 0, 4  # Slicing start, stop for the array we'll index
		c = 0  # counter for the well label
		while n2 <= num_wells:
			# Create an array of just y values to loop over
			y_arr = np.array([x for i, x in enumerate(array)
						if i in array[:, 1].argsort()[n1:n2]])
			# loop over the array we just made and inside the loop
			# organize each y by the x, then edit value into dict d
			for iterr, indx in enumerate(y_arr[:, 0].argsort()):
				vals = str(y_arr[indx][0]) + '_' + str(y_arr[indx][1])
				# add the values into the d, then increase the counter
				d['well' + str(c)] = vals
				c += 1
			n1 += 4
			n2 += 4
        # Oops I created dict d inside out, this fixes it for easier referencing
		my_d = {d[v]: v for k, v in enumerate(d)}  # oh wow dictionary comprehension so suave
		return my_d

	def crop_vid(self):
		"""
		Uses information saved from detect to crop rectangular videos around
		the circular wells.
		input: see below for code that generates the input, which is basically just the instance of the class attached to
		a number from 0 to n where n is the video duration/5.
		zip([self] * int(self.clip_duration / 5), xrange(int(self.clip_duration / 5)))
		"""

		#how long this is going to take
		n_cpus = 2
		p = Pool(n_cpus)
		s1 = time.time()
		#get the video path
		path = self.filename
		name = self.name
		#get the video pathname
		dirname = os.path.dirname(path) + '\\'
		dirname2 = os.path.dirname(path) + '\\' + str(name) + '\\'
		#folder name
		foldername = self.root
		#read in the dict of well names and their x and y positions FIX THE NAMES
		d = self.load_obj(dirname + 'well_dictionary')
		c = self.load_obj(dirname + 'well_circles')

		os.chdir(self.root)
		#iterate through the wells and parse the videos
		for index, (x, y, r) in enumerate(c):
			X1, Y1 = x - r - 20, y - r - 20  # Top left
			X2, Y2 = x + r + 20, y + r + 20  # Bottom right
			side = X2 - X1
			label = str(d[str(x) + '_' + str(y)])
			print('---')
			print(label)

			#ffmpeg_crop_out = foldername + '{}\\'.format(label) + os.path.basename(path)
			ffmpeg_crop_out = dirname2 + '{}\\'.format(label) + os.path.basename(path)
			print(ffmpeg_crop_out)
			'''
			subprocess.call(['ffmpeg', '-i', '{}'.format(path),  # input file
			       '-filter:v', 'crop={}:{}:{}:{}'.format(side, side, X1, Y1),
			       '-an', '{}'.format(ffmpeg_crop_out)])
			'''
			cmd = [get_setting(varname="FFMPEG_BINARY"), '-i', '{}'.format(path),  # input file
			       '-filter:v', 'crop={}:{}:{}:{}'.format(side, side, X1, Y1),
			       '-an', '{}'.format(ffmpeg_crop_out)]
			proc = subprocess.Popen(cmd, shell=False,
			                        stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
			output = proc.communicate()[0].decode()
			
			# self.jab_path.append(ffmpeg_crop_out)
			

		s2 = time.time()
		print('parallel time' + str(s2 - s1))


#create instance of class and run
if __name__ == '__main__':
	import time
	s = time.time()
	self = VideoPipelineNew()
	print('Program took this long to run: ' + str(time.time() - s) + ' seconds')
	self.show_attributes()
