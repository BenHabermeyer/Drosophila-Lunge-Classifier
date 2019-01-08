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
import numpy as np
import argparse

class RectangleStore:

    def __init__(self):
        self.corners = []

    def draw_rectangles(self,event,x,y,flags,param):
        refPt = []
        if event == cv2.EVENT_LBUTTONDOWN:
            refPt = [(x, y)]


        elif event == cv2.EVENT_LBUTTONUP:
            # record the ending (x, y) coordinates and indicate that
            # the cropping operation is finished
            refPt.append((x, y))
            print refPt[0], refPt[1]  # draw a rectangle around the region of interest
            cv2.rectangle(image, refPt[0], refPt[1], (0, 255, 0), 2)
            #img = cv2.imshow("image", image)
            # construct the argument parser and parse the arguments
            self.corners.append(np.concatenate([refPt[0], refPt[1]]))
        return cv2.imshow("image", image)

if __name__ == '__main__':

    rects = RectangleStore()

    videofile = 'C:\\Users\\bmain\\Desktop\\videos_to_track\\debug.mp4'
    capture = cv2.VideoCapture(videofile)
    cv2.setMouseCallback("image", rects.draw_rectangles)
    count = 0

    while capture.isOpened():
        # grab the current frame and initialize the status text
        grabbed, frame = capture.read()
        if frame is not None:
            dirname = os.path.dirname(videofile) + '\\'
            image = dirname + 'crop_test__.jpg'
            # write image
            cv2.imwrite(image, frame)

        capture.read(30)
        # Call the argument parser
        ap = argparse.ArgumentParser()
        ap.add_argument("-i", '--image', required=True, help="Path to the image")
        args = vars(ap.parse_args(['--image', image]))

        # load the image, clone it, and setup the mouse callback function
        image = cv2.imread(args["image"])
        clone = image.copy()
        cv2.namedWindow("image")


        while True:
            cv2.imshow('image',image)
            user_input = cv2.waitKey(0) & 0xFF

            if user_input == ord("r"):
                image = clone.copy()

            # if the 'c' key is pressed, break from the loop
            elif user_input == ord("c"):
                # print len(refPt)
                cv2.destroyAllWindows()
                break
            #elif user_input == ord("q"):
                #capture.release()
                #capture.read(30 * 60)


    print "Selected Coordinates: "
    for i in rects.points:
        print i