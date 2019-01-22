import numpy as np
import pandas as pd
import tkinter as tk
from tkinter import Tk, filedialog, messagebox
from tkinter import*
import os, subprocess
import cv2
import pickle
from multiprocessing import Pool
import moviepy.editor as mpy
from moviepy.config import get_setting
import time
import moviepy
import matlab.engine
import shutil
import math


class VideoPipelineNew(object):

	#Create instance of class with 12 videos to crop
	def __init__(self):
		#path to where the code is kept
		self.code_path = r'C:\Users\Ben\Documents\JAABA\PythonForJaaba'
		#classifier filename
		self.classifier = 'LungeV1.jab'
		#FlyTracker path on computer
		self.flytracker_path = r'C:\Users\Ben\Documents\FlyTracker-1.0.5'
		#JAABA path on computer
		self.jaaba_path = r'C:\Users\Ben\Documents\JAABA\JAABA-master\perframe'

		#background variables
		self.num_wells = 12
		self.n_cpus = 2

		#select the video file
		self.load_single()
		#ask if you want to crop the first x seconds
		self.ask_crop()

		
		#MATLAB stuff
		#calibrate the tracker
		self.calibrate_tracker()
		#track the video
		self.run_tracker()
		#reorganize the folders for JAABA
		self.prepare_JAABA()
		

		#JAABA stuff
		#run the JAABA program
		#self.classify_behavior()
		#get the output
		#self.get_lunge_data()

		

		#other important varialbes
		#self.filename = full path to and ending with video name
		#self.root is root of folder containing video, filename without the file extension
		#self.name is video name without extension
		#self.fullname is the video name with extension
		#self.calib is the path to the calibration .mat file


		#stuff only needed for cropping the videos into 12 separate ones (ew)
		'''
		#self.well_roots = [] # This will contain the paths of all wells
		#make its folders
		#self.make_wellfolders()
		#detect the wells
		self.detect()
		self.select_background_pixel()
		self.mask_background()
		#crop the videos
		#self.crop_vid()
		'''
		
		


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


	def ask_crop(self):
		"""
		asks if you would like to crop the start of a video to fix the aparature settings. if no does nothing.
		if yes then calls next dialog
		"""
		MsgBox = tk.messagebox.askquestion('Crop Video',"Would you like to crop the video's beginning?", icon = 'warning')
		if MsgBox == 'yes':
			self.how_long_crop()

	def how_long_crop(self):
		"""
		asks another dialog of how many seconds you would like to crop off the start of the video
		"""
		def get_time():
			self.crop_time = int(Entry.get(entry_1))
			my_window.quit()
			self.crop_start()

		my_window = Tk()

		label_1 = Label(my_window, text = 'How many seconds would you like to crop from the start:')
		entry_1 = Entry(my_window)

		label_1.grid(row = 0, column = 0)
		entry_1.grid(row = 0, column = 1)


		button_1 = Button(my_window, text = "Done", command = get_time)
		button_1.grid(row = 1, column = 0)

		my_window.mainloop()

	def crop_start(self):
		"""
		crops the beginning of a video based on the self.crop_time defined in the how_long_crop function.
		updates the filename, name, and fullname to be that of the newly cropped video
		"""
		print('Starting video crop')
		p = Pool(self.n_cpus)
		os.chdir(self.root)
		path = self.filename
		start_time = self.crop_time
		#arbitrary end time is really big like 300 minutes
		end_time = 18000

		#rename the cropped file
		filetype = self.fullname.split('.')[-1]
		outputname = self.name + '_cropped.' + filetype

		from moviepy.video.io.ffmpeg_tools import ffmpeg_extract_subclip
		ffmpeg_extract_subclip(self.fullname, start_time, end_time, targetname = outputname)

		#rename the originial file and path to be the new cropped file
		self.fullname = outputname
		self.name = self.name + '_cropped'
		self.filename = self.root + '/' + self.fullname

	def calibrate_tracker(self):
		"""
		launches MATLAB code for automatic calibration of the video
		"""
		os.chdir(self.code_path)
		print('Launching FlyTracker Calibration')
		try:  # try quiting out of any lingering matlab engines
			eng.quit()
		except:  # if not just keep going with the code
			print('could not find any engines to quit')
			pass
		eng = matlab.engine.start_matlab() 

		# for each of the videos, launch AutoCalibrate.m matlab script
		# takes as input the path to the video and the path to the calibration file
		video = self.filename # this is the file to the trimmed video per well
		self.calib = video.split('.')[0] + '_calibration.mat' 
		# Launch FlyTracker Calibration - takes as input the path name to the video and the
		eng.auto_calibrate(self.flytracker_path, video, self.calib, nargout = 0) 

		
		try:  # try quiting out of any lingering matlab engines
			eng.quit()
		except:  # if not just keep going with the code
			print('could not find any engines to quit')
			pass
		

	def run_tracker(self):
		"""
		launches MATLAB code for automatic tracking of the video after calibration
		"""
		print('Launching FlyTracker Tracking')
		os.chdir(self.code_path)
		try:  # try quiting out of any lingering matlab engines
			eng.quit()
		except:  # if not just keep going with the code
			print('could not find any engines to quit')
			pass

		#or eng = matlab.engine.connect_matlab()
		eng = matlab.engine.start_matlab()
		#videoname and calibration file needed for tracking
		foldername = self.root
		extension = '*.' + self.fullname.split('.')[-1]
		#calibration = self.calib
		calibration = self.filename.split('.')[0] + '_calibration.mat'
		eng.auto_track(self.flytracker_path, foldername, extension, calibration, nargout = 0)

		try:  # try quiting out of any lingering matlab engines
			eng.quit()
		except:  # if not just keep going with the code
			print('could not find any engines to quit')
			pass

	def prepare_JAABA(self):
		"""
		function prepares the data for JAABA by making the correct directory structure JAABA wants
		need to grab the perframe folder and the tracking file and move to directory
		"""
		print('Preparing files for JAABA')
		destination = self.root
		filename = self.name
		trx_path = destination + '/' + filename + '/' + filename + '_JAABA' + '/trx.mat'
		perframe_path = destination + '/' + filename + '/' + filename + '_JAABA/perframe'
		shutil.move(trx_path, destination)
		shutil.move(perframe_path, destination)

	def classify_behavior(self):
		"""
		calls JAABA classifier from MATLAB
		.jab file name is stored at the start, should be stored in the same spot as all the code
		"""
		print('Classifying behavior using JAABA')
		os.chdir(self.code_path)
		try:  # try quiting out of any lingering matlab engines
			eng.quit()
		except:  # if not just keep going with the code
			print('could not find any engines to quit')
			pass
		eng = matlab.engine.start_matlab() 
		classifier_path = self.code_path + '/' + self.classifier
		eng.classify_behavior(self.jaaba_path, classifier_path, self.root, nargout = 0)

		try:  # try quiting out of any lingering matlab engines
			eng.quit()
		except:  # if not just keep going with the code
			print('could not find any engines to quit')
			pass	

	def get_lunge_data(self):
		"""
		calls MATLAB function to grab the data from the JAABA output
		"""
		print('Writing lunge data')
		os.chdir(self.code_path)
		try:  # try quiting out of any lingering matlab engines
			eng.quit()
		except:  # if not just keep going with the code
			print('could not find any engines to quit')
			pass
		eng = matlab.engine.start_matlab() 
		directory = self.root
		videoname = self.name
		classifiername = self.classifier.split('.')[0]
		#call whichever classifier you want
		eng.get_lunges(directory, videoname, classifiername, nargout = 0)
		try:  # try quiting out of any lingering matlab engines
			eng.quit()
		except:  # if not just keep going with the code
			print('could not find any engines to quit')
			pass



	#code below here is for slicing videos by individual wells, if necessary


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
		print('Starting detect')
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
						
					
					if cv2.waitKey(10) & 0xFF == ord('q'):
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
							dirname = os.path.dirname(videofile) + '/'
							self.dictpath = dirname + 'well_dictionary'
							self.circlespath = dirname + 'well_circles'
							self.save_obj(d, self.dictpath)
							self.save_obj(circles, self.circlespath)
							#self.circ_vid_root.append(dirname + 'allwells')
							self.fname = dirname + "crop_test.jpg"
							# write image
							cv2.imwrite(self.fname, frame)
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

	def select_background_pixel(self):
		#aiting = True
		#efPT = []
		'''
		def click(event, x, y, flags, param):
			global refPT, waiting

			if event ==cv2.EVENT_LBUTTONDOWN:
				refPT = [(x, y)]
				waiting = False
		'''
		image = cv2.imread(self.fname)
		'''
		cv2.namedWindow("image")
		cv2.setMouseCallback("image", click)
		while waiting:
			cv2.imshow("image", image)
			key = cv2.waitKey(1) & 0xFF

			if key == ord('q'):
				break

		cv2.destroyAllWindows()
		'''
		self.rgb_point = image[360][640]
		print(self.rgb_point)


	def mask_background(self):
		"""
		TO DO
		function takes the result of detecting the wells to apply a mask to the 
		background of the video, thereby constructing
		a new masked video
		"""		
		path = self.filename
		dirname = os.path.dirname(path) + '/'
		#circles is a list of lists of length 3 given by [height, width, radius]
		circles = self.load_obj(dirname + 'well_circles')

		#checks if a given pixel location is inside one of the 12 circles
		def incircle(xinput, yinput, circleslist):
			for circle in circleslist:
				x = circle[1]
				y = circle[0]
				radius = circle[2]
				ans = math.sqrt((x - xinput)**2 + (y - yinput)**2)
				if ans < radius:
					return True
			return False

		#construct the 2 masks
		mask1 = np.zeros((720, 1280, 3)).astype('uint8')
		mask2 = np.zeros((720, 1280, 3)).astype('uint8')
		for x in range(720):
			for y in range(1280):
				if incircle(x, y, circles):
					mask1[x][y][:] = 1
				else:
					mask2[x][y][0] = self.rgb_point[0]
					mask2[x][y][1] = self.rgb_point[1]
					mask2[x][y][2] = self.rgb_point[2]

		#write the new maked video to a new video
		videofile = self.filename
		capture = cv2.VideoCapture(videofile)

		#output file type and codec
		fourcc = cv2.VideoWriter_fourcc(*'mp4v')
		outputname = self.root + '/' + self.name + '_masked.mp4'
		out = cv2.VideoWriter(outputname, fourcc, 30, (1280, 720))
			
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

		#rename the current file and name to be the cropped one
	

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
		p = Pool(self.n_cpus)
		s1 = time.time()
		#get the video path
		path = self.filename
		name = self.name
		#get the video pathname

		#be careful of \\ vs /

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
		print('cropping individual wells time' + str(s2 - s1))


#create instance of class and run
if __name__ == '__main__':
	import time
	s = time.time()
	self = VideoPipelineNew()
	print('Program took this long to run: ' + str(time.time() - s) + ' seconds')
	self.show_attributes()
