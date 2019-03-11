import numpy as np
import tkinter as tk
from tkinter import Tk, filedialog, messagebox
from tkinter import*
import os, subprocess, cv2, pickle
from multiprocessing import Pool
import moviepy.editor as mpy
from moviepy.editor import*
from moviepy.config import get_setting
import time, moviepy, matlab.engine, shutil, math


class BehaviorClassifier(object):
	'''
	This is the main analysis file for tracking Drosophila videos and applying behavior classifiers created
	in JAABA. Execution of this code allows a user to select one video to analyze, and apply the classifier
	that they choose. Simply execute in a terminal BehaviorClassifier.py to use and follow the steps when
	prompted.

	Notes: Code assumes number of wells does not exceed 12.

	Author: Ben Habermeyer, some materials from Logan
	Contact: benhabe@seas.upenn.edu, 434-242-6984
	'''

	def __init__(self):
		'''
		Initializes path variables to the code, classifier, tracker, and jaaba, and executes the functions
		to select and classify a video
		'''
		#path to where the code is kept
		self.code_path = r'C:\Users\Ben\Documents\JAABA\PythonForJaaba'
		#classifier filename
		#self.classifier = 'LungeV1.jab'
		self.classifier = 'LungeV2.jab'
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
		self.checkbox_grid()
		self.find_centers()
		#track the video
		self.run_tracker()
		#reorganize the folders for JAABA
		self.prepare_JAABA()
		
		#JAABA stuff
		#run the JAABA program
		self.classify_behavior()
		#get the output
		self.get_lunge_data()

		#other important variables which will be created during this code run
		#self.filename = full path to and ending with video name
		#self.root is root of folder containing video, filename without the file extension
		#self.name is video name without extension
		#self.fullname is the video name with extension
		#self.calib is the path to the calibration .mat file
		#self.excluded_wells is a list of wells to remove from analysis
		#self.well_dictionary is a dictionary mapping well to x and y center coordinates
		#self.well_circles is a list containing lists of x,y, and radii coordinates of well circles
		#self.x_centers are the x pixel coordinates of well centers
		#self.y_centers are the y pixel coordinates of well centers

	def load_single(self):
		"""
		Launch a GUI so people can click on the videofile that they want to track
		"""
		print('Please select the file corresponding to the video you would like to process')
		root = tk.Tk()
		root.withdraw()
		self.filename = filedialog.askopenfilename()  # Set the filename of the video
		self.root = self.parent(self.filename)  # Set the video's folder
		self.name, self.fullname = self.get_fname(self.filename)
		root.destroy()

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
		Asks if you would like to crop the start of a video to fix the aparature settings. If no does nothing.
		if yes then calls next dialog asking how long
		"""
		root = tk.Tk()
		root.withdraw()
		MsgBox = tk.messagebox.askquestion('Crop Video',"Would you like to crop the video's beginning?", icon = 'warning')
		if MsgBox == 'yes':
			root.destroy()
			self.how_long_crop()
		else:
			root.destroy()

	def how_long_crop(self):
		"""
		Another dialog asking how many seconds you would like to crop off the start of the video. Enter the number of
		seconds cropped
		"""
		#callback function for the tkinter entries
		def get_time():
			#get the start and end times and save as variable
			self.crop_time1 = int(Entry.get(entry_1))
			self.crop_time2 = int(Entry.get(entry_2))
			my_window.withdraw()
			self.crop_start()
			my_window.destroy()

		#master window
		my_window = Tk()

		#create labels and entry space for text
		label_1 = Label(my_window, text = 'How many seconds would you like to crop from the start:')
		entry_1 = Entry(my_window)

		#create second label for length of video
		label_2 = Label(my_window, text = 'How long is the original video in seconds:')
		entry_2 = Entry(my_window)

		label_1.grid(row = 0, column = 0)
		entry_1.grid(row = 0, column = 1)

		label_2.grid(row = 1, column = 0)
		entry_2.grid(row = 1, column = 1)

		#add a "done" button to press when finished
		button_1 = Button(my_window, text = "Done", command = get_time)
		button_1.grid(row = 2, column = 0)

		#run indefinitely
		my_window.mainloop()

	def crop_start(self):
		"""
		Crops the beginning of a video based on the self.crop_time defined in the how_long_crop function.
		Updates the filename, name, and fullname to be that of the newly cropped video and moves the original
		video to a new folder so it does not also get tracked.
		"""
		print('Starting video crop')
		p = Pool(self.n_cpus)
		#need to set current directory for moviepy
		os.chdir(self.root)
		path = self.filename
		start_time = self.crop_time1
		end_time = self.crop_time2

		#rename the cropped file
		filetype = self.fullname.split('.')[-1]
		outputname = self.name + '_cropped.' + filetype

		#use moviepy to extract the desired subclip
		oldvideo = VideoFileClip(self.fullname)
		clipped = oldvideo.subclip(start_time, end_time)
		clipped.write_videofile(outputname, codec = 'libx264')
		oldvideo.close()

		#create a new subfolder to put the original video in - FlyTracker tracks all videos in folder
		newfolder = self.root + '/' + 'uncropped_video'
		os.mkdir(newfolder)
		shutil.move(self.fullname, newfolder)

		#rename the originial file and path to be the new cropped file
		self.fullname = outputname
		self.name = self.name + '_cropped'
		self.filename = self.root + '/' + self.fullname

	def calibrate_tracker(self):
		"""
		Launches MATLAB code for automatic calibration of the video. Follow steps outlined on FlyTracker
		website for tracking, manually-excluding wells you do not want to analyze
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

		#calls dialog to ask if calibration should be accepted
		self.good_calibration()
		
	def good_calibration(self):
		"""
		Dialog asks thse user if he/she was pleased with the calibration. If not, calibration files
		are deleted and the calibration is called again.
		"""
		#create a tkinter window
		root = tk.Tk()
		#hide the master window to prompt a question window
		root.withdraw()
		#ask the question in a messagebox
		MsgBox = tk.messagebox.askquestion('Accept Calibration',"Would you like to accept the calibration?", icon = 'warning')
		if MsgBox == 'yes':
			root.destroy()
		elif MsgBox == 'no':
			#deletes old calibration files and calls calibrator again
			calib_folder = self.root + '/' + self.name
			shutil.rmtree(calib_folder)
			calib_file = self.root + '/' + self.name + '_calibration.mat'
			os.unlink(calib_file)
			root.destroy()
			self.calibrate_tracker()

	def checkbox_grid(self):
		"""
		Dialog box with 12 checkboxes for the user to select which wells they would like to exclude, if any. 
		"""
		#list of excluded wells
		self.excluded_wells = []

		#callback for the "done" button appends to list wells whose buttons have been pressed
		def get_state():
			var_list = [var1.get(), var2.get(), var3.get(), var4.get(), var5.get(), var6.get(),
			var7.get(), var8.get(), var9.get(), var10.get(), var11.get(), var12.get()]
			self.excluded_wells = [v for v in var_list if v > 0]
			master.destroy()

		#master tkinter window
		master = Tk()

		#grid of checkbuttons corresponding to each well with a value equal to their well number
		#assumes grid of 12 wells
		Label(master, text="Check Wells to Exclude from Analysis (if any) and click 'Done'").grid(row=0, columnspan = 4,  pady = 4)
		var1 = IntVar()
		Checkbutton(master, text="Well 1", variable=var1, onvalue=1, offvalue=0, anchor='w').grid(row=1, column=0, pady = 4, padx = 8)
		var2 = IntVar()
		Checkbutton(master, text="Well 2", variable=var2, onvalue=2, offvalue=0, anchor='w').grid(row=1, column=1, pady = 4, padx = 8)
		var3 = IntVar()
		Checkbutton(master, text="Well 3", variable=var3, onvalue=3, offvalue=0, anchor='w').grid(row=1, column=2, pady = 4, padx = 8)
		var4 = IntVar()
		Checkbutton(master, text="Well 4", variable=var4, onvalue=4, offvalue=0, anchor='w').grid(row=1, column=3, pady = 4, padx = 8)
		var5 = IntVar()
		Checkbutton(master, text="Well 5", variable=var5, onvalue=5, offvalue=0, anchor='w').grid(row=2, column=0, pady = 4, padx = 8)
		var6 = IntVar()
		Checkbutton(master, text="Well 6", variable=var6, onvalue=6, offvalue=0, anchor='w').grid(row=2, column=1, pady = 4, padx = 8)
		var7 = IntVar()
		Checkbutton(master, text="Well 7", variable=var7, onvalue=7, offvalue=0, anchor='w').grid(row=2, column=2, pady = 4, padx = 8)
		var8 = IntVar()
		Checkbutton(master, text="Well 8", variable=var8, onvalue=8, offvalue=0, anchor='w').grid(row=2, column=3, pady = 4, padx = 8)
		var9 = IntVar()
		Checkbutton(master, text="Well 9", variable=var9, onvalue=9, offvalue=0, anchor='w').grid(row=3, column=0, pady = 4, padx = 8)
		var10 = IntVar()
		Checkbutton(master, text="Well 10", variable=var10, onvalue=10, offvalue=0, anchor='w').grid(row=3, column=1, pady = 4, padx = 8)
		var11 = IntVar()
		Checkbutton(master, text="Well 11", variable=var11, onvalue=11, offvalue=0, anchor='w').grid(row=3, column=2, pady = 4, padx = 8)
		var12 = IntVar()
		Checkbutton(master, text="Well 12", variable=var12, onvalue=12, offvalue=0, anchor='w').grid(row=3, column=3, pady = 4, padx = 8)
		Button(master, text='Done', command=get_state).grid(row=4, column = 1)

		#run loop indefinitely
		master.mainloop()

	def find_centers(self):
		"""
		Function finds the centers of circular wells for later analysis where flies will be identified by which well they are 
		closest to the center of.
		"""
		num_wells = self.num_wells
		videofile = self.filename

		#open the video
		capture = cv2.VideoCapture(videofile)
		
		#indefinitely read in frames, and when 12 circles are present grab their locations and sizes
		boolean = True
		while(boolean):
			ret, frame = capture.read()

			#convert frame to grayscale, blut it, and loop for circles using HoughCircles algorithm
			if frame is not None:
				gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
				blur = cv2.medianBlur(gray, 5)
				circles = cv2.HoughCircles(blur, cv2.HOUGH_GRADIENT, 1, 20, 
					param1=60, param2=30, minRadius=85, maxRadius=105)

				#convert circles to int type
				if circles is not None:
					circles = np.round(circles[0, :]).astype('int')

					#draw rectangles around the circles to specify each well
					for index, (x, y, r) in enumerate(circles):
						cv2.circle(frame, (x, y), r, (255, 0, 255), 2)
						X1, Y1 = x - r - 20, y - r - 20  # Top left rect coords
						X2, Y2 = x + r + 20, y + r + 20  # Bottom right rect coords
						side = X2 - X1
                    	# draw the frame of rectangle on the screen
						(cv2.rectangle(frame, (X1, Y2), (X2, Y1), (0, 255, 0), 3))
					
					#if you found 12 circles, save their locations and an image of the circles
					if len(circles) == num_wells:
						d = self.get_well_labels(circles)
						d.pop('well0', None)
						dirname = os.path.dirname(videofile) + '/'
						self.well_dictionary = d
						self.well_circles = circles
						self.fname = dirname + "well_centers.jpg"
						# write image
						cv2.imwrite(self.fname, frame)
						capture.release()
						cv2.destroyAllWindows()
						boolean = False

		#code to segment the well positions and send to python
		xvals = []
		yvals = []
		for i in range(1, 13):
			data = self.well_dictionary['well' + str(i)]
			datasplit = data.split('_')
			xvals.append(int(datasplit[0]))
			yvals.append(int(datasplit[1]))

		#retains the x and y pixel locations of the center of the circles
		self.x_centers = xvals
		self.y_centers = yvals

	def run_tracker(self):
		"""
		Launches MATLAB code for automatic tracking of the video after calibration using FlyTracker
		Note: FlyTracker will track every video in directory
		"""
		print('Launching FlyTracker Tracking')
		os.chdir(self.code_path)
		try:  # try quiting out of any lingering matlab engines
			eng.quit()
		except:  # if not just keep going with the code
			print('could not find any engines to quit')
			pass

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
		Function prepares the data for JAABA by making the correct directory structure JAABA wants.
		Needs to grab the perframe folder and the tracking file and move to directory for JAABA.
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
		Calls JAABA classifier from MATLAB
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
		calls MATLAB function to grab the data from the JAABA output and write to an excel file
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
		excluded = self.excluded_wells
		xvals = self.x_centers
		yvals = self.y_centers

		#call whichever classifier you want
		eng.get_lunges2(directory, videoname, classifiername, excluded, xvals, yvals, nargout = 0)
		try:  # try quiting out of any lingering matlab engines
			eng.quit()
		except:  # if not just keep going with the code
			print('could not find any engines to quit')
			pass

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
		c = 1  # counter for the well label
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
		return d

#create instance of class and run
if __name__ == '__main__':
	import time
	s = time.time()
	self = BehaviorClassifier()
	print('Program took this long to run: ' + str(time.time() - s) + ' seconds')

	#if you want to show all the function outputs, uncomment the line below
	self.show_attributes()