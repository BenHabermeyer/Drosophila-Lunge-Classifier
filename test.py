from multiprocessing import Pool
from time import time
from moviepy.config import get_setting
import numpy as np
from Tkinter import Tk
from tkFileDialog import askopenfilename
import os, subprocess
import moviepy.editor as mpy
import matlab.engine
from glob import glob
import cv2
import pickle
from scipy.io import loadmat
import pandas as pd
from openpyxl import load_workbook

class VideoPipelineNew(object):
    """
    Here we will organize functions required to automate behavioral detection in drosophilla, specifically
    we will build one for lunge behavior, however, parameters in the code can be modified slightly (and
    documented where this can occur) to include other behavioral classifiers.
    For technical support please contact Logan Fickling: loganf@mail.med.upenn.edu, 480-529-1839

    IMPORTANT
    ---------
        The following methods (e.g. functions) assume that the video entered will contain 12 wells:
                -make_wellfolders
                -detect
                -get_well_labels
            - To solve* this issue, if you don't have 12 wells change the argument in the def __init__ num_wells
              from 12 to whatever number you have
                *this solution was untested so if for some reason it breaks when changed, let Logan know

        The method five_minute_subclip, doesn't have to create five minute subclips, it can be
        modified as detailed in the code to create whatever arbitary minute subclip you want. While making this
        I tried 1 minute, 5 minutes and 10 minutes. I'd recommend at least five minutes. But there are trade offs
        being that the shorter you subclip (e.g. 2 mins vs 10 mins) means you'll have to calibrate more video files,
        however contamination in video through zooming in/out while recording, variance in the lighting, and errors
        due to FlyTracker is limited
        with smaller clips.
            - This can be adjusted in by changing the variable subclip_length from 5 to whatever number you want
              in the __init__ method

        In Future videos where it is known that videos aren't zoomed in, then the code can be adjusted such that
        the user could would only need to calibrate regardless of subclip length, the issue is primarily a
        necesscity because of the uncertainity in the zooming***
    """

    def __init__(self, num_wells=12, subclip_length=5):
        """
        What the code does each time an 'instance' of the class is created, these steps are what the
        code uses to do all the differenet things, you can reference each function below to follow how
        the code flows
        """
        self.num_wells = num_wells
        self.subclip_length = subclip_length
        # self.jab_path = []
        self.short_vids = []  # This will hold the paths of all trimmed videos with ALL wells
        self.circ_vid_root = []  # This will include the paths of all trimmed video with one well
        self.well_roots = []  # This will contain the paths of all wells
        self.load_single()  # Launch Gui to click on the video file
        self.draw_rectangles()

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

    def load_single(self):
        """
        Launch a GUI so people can click on the videofile that they want to track
        """
        print 'Please select the file corresponding to the video you would like to process'
        Tk().withdraw()  # we don't want a full GUI, so keep the root window from appearing
        self.filename = askopenfilename()  # Set the filename of the video
        self.root = self.parent(self.filename)  # Set the video's folder
        self.name, self.fullname = self.get_fname(self.filename)

        # This is only required because I'm a tired and rewrite these variables -_-
        self.true_root = self.root
        self.true_name = self.name

    def pkill(self, process_name='ffmpeg.win32.exe'):
        """
        Windows LOVES to keep processes open, and sometimes when you try to close them or move files associated
        with this code windows will tell you that "like I can't even right now".

        Actual Explaination
        -------------------
        This Code force closes ffmpeg by default, else any passed process name
        e.g. self.pkill(process_name='yolo.exe')

        ffmpeg is used to crop the videos, it is great software that is built upon C++ a much faster language
        so we can capitalize upon orders of magnitude of speed increases relative to python. The downside is that
        in windows it doesn't automatically terminate after so you'll need to be able to force it to terminate or
        the files won't be able to be open (because they're already opened by something else) leading to the code
        breaking.
        """
        # import subprocess
        try:  # Try to kill the damn thing
            task = 'taskkill /im ' + process_name + ' /f'
            # subprocess allows direct interaction with the 'terminal'
            # or whatever it is that window uses in lack of its terminal
            killed = subprocess.check_call(task, shell=True)
        except:
            killed = 0

    def detect(self, i):
        """
        Function uses vision based machine learning to guess where circles are,
        then uses these circles to draw a rectangle around them. Saves information on both rectangle and circle
        Per five minutes of video, the code will create two things, one called well_dictionaries which
        contains a way of labeling the X1,X2, Y1, Y2 coordinates of the rectangle and circles which contains x,y,r of
        each circle
        :param i: corresponds to the i of the video, e.g. first five minutes is 0, second five minutes is 1

        IMPORTANT
        ---------
        Code Assumes that the number of wells is 12, if not this parameter needs to be changed below
        """
        print 'hello detect'
        num_wells = self.num_wells
        # import numpy as np
        # import cv2, time
        # import moviepy.editor as mpy
        # import os
        videofile = self.filename #self.short_vids[i]
        print videofile
        # clip = (mpy.VideoFileClip(videofile, audio=False))
        capture = cv2.VideoCapture(videofile)


        while capture.isOpened():

            # grab the current frame and initialize the status text
            grabbed, frame = capture.read()
            if frame is not None:
                # convert the frame to grayscale, blur it, and detect circles
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                blur = cv2.medianBlur(gray, 5)
                circles = cv2.HoughCircles(blur, cv2.HOUGH_GRADIENT, 1, 20, \
                                           param1=60, param2=30, minRadius=85, maxRadius=100)
                if circles is not None:
                    # convert the (x, y) coordinates and radius of the circles to integers
                    circles = np.round(circles[0, :]).astype("int")

                    # loop over the (x, y) coordinates and radius of the circle
                    for index, (x, y, r) in enumerate(circles):
                        # draw the circle in the output image, then draw a rectangle
                        # corresponding to the center of the circle
                        cv2.circle(frame, (x, y), r, (255, 0, 255), 2)
                        # Use the circle to math a rectangle around it
                        X1, Y1 = x - r - 20, y - r - 20  # Top left rect coords
                        X2, Y2 = x + r + 20, y + r + 20  # Bottom right rect coords
                        side = X2 - X1
                        # draw the frame of rectangle on the screen
                        (cv2.rectangle(frame, (X1, Y2), (X2, Y1), (0, 255, 0), 3))

                    if len(circles) == num_wells:
                        # only show image if it predicts there to be 12 circles
                        cv2.imshow("Frame", frame)

                    # if the 'q' key is pressed twice, stop the loop else next frame
                    if cv2.waitKey(0) & 0xFF != ord('q'):  # == ord('n'):
                        capture.read()

                    if cv2.waitKey(0) & 0xFF == ord('q'):
                        if len(circles) == 12:
                            d = self.get_well_labels(circles)
                            dirname = os.path.dirname(videofile) + '\\'
                            self.save_obj(d, dirname + 'well%d\\well_dictionary_%d' % (i, i))
                            self.save_obj(circles, dirname + 'well%d\\circles_%d' % (i, i))
                            self.circ_vid_root.append(dirname + 'well{}'.format(i))
                            fname = dirname + 'crop_test_%d.jpg' % i
                            # write image
                            cv2.imwrite(fname, frame)
                            capture.release()
                            cv2.destroyAllWindows()
                            # self.circ_vid_root=dirname

    def draw_rectangles(self):
        """
        Function uses vision based machine learning to guess where circles are,
        then uses these circles to draw a rectangle around them. Saves information on both rectangle and circle
        Per five minutes of video, the code will create two things, one called well_dictionaries which
        contains a way of labeling the X1,X2, Y1, Y2 coordinates of the rectangle and circles which contains x,y,r of
        each circle
        :param i: corresponds to the i of the video, e.g. first five minutes is 0, second five minutes is 1

        IMPORTANT
        ---------
        Code Assumes that the number of wells is 12, if not this parameter needs to be changed below
        Rectangle
        x1,y1-------------------------
        |                            |
        |                            |
        |                            |
        -------------------------x2,y2


        """
        print 'hello detect'
        num_wells = self.num_wells

        import argparse
        videofile = self.filename
        dirname = os.path.dirname(videofile) + '\\'

        # clip = (mpy.VideoFileClip(videofile, audio=False))q
        capture = cv2.VideoCapture(videofile)

        while capture.isOpened():
            # grab the current frame and initialize the status text
            grabbed, frame = capture.read() # Step every 60 seconds
            if frame is not None:

                image = dirname + 'crop_test.jpg'
                # write image
                cv2.imwrite(image, frame)

                refPt = []
                cropping = False
                my_rectangles = []
                def backup():
                    clone = image.copy()


                def click_and_crop(event, x, y, flags, param):
                    # grab references to the global variables
                    global refPt, cropping#, my_rectangles

                    # if the left mouse button was clicked, record the starting
                    # (x, y) coordinates and indicate that cropping is being
                    # performed
                    if event == cv2.EVENT_LBUTTONDOWN:
                        refPt = [(x, y)]
                        cropping = True
                    # check to see if the left mouse button was released
                    elif event == cv2.EVENT_LBUTTONUP:
                        # record the ending (x, y) coordinates and indicate that
                        # the cropping operation is finished
                        refPt.append((x, y))
                        cropping = False
                        #print refPt[0], refPt[1]  # draw a rectangle around the region of interest
                        cv2.rectangle(image, refPt[0], refPt[1], (0, 255, 0), 2)
                        cv2.imshow("image", image)
                        # construct the argument parser and parse the arguments
                        my_rectangles.append([refPt[0], refPt[1]])
                        print(my_rectangles)
                        print()


                # Skip to the 15th second of the video (30fps)
                capture.read(30*15)

                # Call the argument parser
                ap = argparse.ArgumentParser()
                cv2.imshow("Frame", frame)
                ap.add_argument("-i", '--image', required=True, help="Path to the image")
                args = vars(ap.parse_args(['--image', image]))
                print(image)
                # load the image, clone it, and setup the mouse callback function
                image = cv2.imread(args["image"])
                clone = image.copy()
                cv2.namedWindow("image")
                cv2.setMouseCallback("image", click_and_crop)

                # keep looping until the 'q' key is pressed
                while True:
                    # display the image and wait for a keypress
                    cv2.imshow("image", image)
                    user_input = cv2.waitKey(0) & 0xFF

                    # if the 'r' key is pressed, reset the cropping region
                    if user_input == ord("r"):
                        image = clone.copy()
                        my_rectangles = []

                    # if the 'c' key is pressed, break from the loop
                    elif user_input == ord("c"):
                        # print len(refPt)
                        cv2.destroyAllWindows()
                        break
                    elif user_input == ord("q"):
                        #capture.release()
                        capture.read(30*60)

                # if there are two reference points, then crop the region of interest
                # from teh image and display it
                """ccccccccc
                if len(refPt) == 2:
                    roi = clone[refPt[0][1]:refPt[1][1], refPt[0][0]:refPt[1][0]]
                    print roi
                    cv2.imshow("ROI", roi)
                    cv2.waitKey(20)
                """
                # close all open windows
                cv2.destroyAllWindows()
if __name__ == '__main__':
    self = VideoPipelineNew()