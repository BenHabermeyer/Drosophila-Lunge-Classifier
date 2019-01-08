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
        print 'blessed ffmpeg errors we gonna ignore:\n'
        self.make_wellfolders()  # Makes folders for the wells
        self.five_minute_subclip(self.filename)  # Makes 5 minute long videos
        # For each 5min video, detect where the circles are
        for index in np.arange(0, self.clip_duration, 5):
            self.detect(i=int(index))
        # Matlab stuff
        self.video_list = []  # This will store a list of all cropped 5 minute videos
        self.calib_list = []  # This will hold calibration files from FlyTracker for each vid
        self.root_list = []  # This will store the folder name of each video
        self.output_list = []  # This will hold the output of where JAABA needs to start

    def get_matlab_vid_paths(self):
        """
        Creates an attribute matlab_vid_path, which contains a list of of all video paths needed for matlab
        """
        # concatenate because [[]] output, tolist because windows crashes with np.unicode formatting output
        self.matlab_vid_paths = np.concatenate([glob(y + '\\*.mp4') for y in self.well_roots]).tolist()

    def calibrate_tracker(self):
        """
        Launches the FlyTracker Calibration matlab code for each well, of each (trimmed in time) video

        IMPORTANT
        ---------
        this is kinda painful, so sorry whoever runs this. I've tried to automate  the process as much as
        possible, the "ruler" for calibration should be damn near close to what it needs to be, so the user
        will simply align it across the well and verify that the size and fps is correct in the GUI

        Additionally, if in future videos it's known that there is fixed lightning and no change in the
        camera's zoom, I could easily make code that would then reduce the number of times you need to calibrate
        to 12. If there's a standardization process in which the same lightning is used from a fixed height, with
        a fixed zoom, then you could skip the calibration step entirely by using a "default settings" calibration.
        """
        try:  # try quiting out of any lingering matlab engines
            eng.quit()
        except:  # if not just keep going with the code
            print 'could not find any engines to quit'
            pass
        eng = matlab.engine.start_matlab()  # import matlab engine
        # for each of the videos, launch Logans AutoCalibrate.m matlab script
        # which inputs these variables into the FlyTracker matlab script calibrator.m
        for f_vid in self.matlab_vid_paths:
            # Define matlab inputs
            self.f_vid = f_vid  # this is the file to the trimmed video per well
            self.f_calib = self.f_vid[:-4] + '_calibration.mat'  # arbitary but unique name for each calib
            # Launch FlyTracker Calibration
            eng.AutoCalibrate(self.f_vid,
                              self.f_calib,
                              nargout=0)  # no matlab argument outputs, else code weeps errors of sorrow

    def Automatic_Tracking(self):
        """
        function takes (the trimmed in time) videofiles and launches flytracker to track them.
        """
        from os.path import basename as base  # see function get_fname for clarification on base
        eng = matlab.engine.start_matlab()  # import matlab engine
        # for each of the videos, launch Logans auto_track.m matlab script which inputs these
        # variables into the Flytracker matlab script tracker.m
        for f_vid in self.matlab_vid_paths:
            # define matlab inputs
            self.f_vid = f_vid
            self.f_calib = self.f_vid[:-4] + '_calibration.mat'
            """
            THE LINE BELOW IS THE PROBLEM CHILD
            """
            self.root = os.path.dirname(self.f_vid) + '\\'
            # Launch Fly Tracker Tracking
            eng.auto_track({self.root},
                           base(self.f_vid),
                           self.f_calib,
                           nargout=0)  # no matlab argument outputs, else code drowns in a sea of errors
            """
            THIS IS WHAT LOGAN THINKS THE LINE SHOULD BE!!!!!
            # Launch Fly Tracker Tracking
            eng.auto_track({os.path.dirname(self.f_vid) + '\\'},
                           base(self.f_vid),
                           self.f_calib,
                           nargout=0)  # no matlab argument outputs, else code drowns in a sea of errors
            """


            # Move the video file once you're done tracking it into the folder JAABA needs it to be in
            os.rename(self.f_vid, self.root + base(self.f_vid)[:-4] + '\\' + base(self.f_vid))
            # Add the renamed path above to a list for later use by JAABA
            self.output_list.append(self.root + base(self.f_vid)[:-4] + '\\' + base(self.f_vid))
        try:  # exit matlab
            eng.quit()
        except:  # weak error exception = bad programming logan
            pass

    def matlab_stuff(self):
        """
        Function launches calibration process for each video, then upon completion will launch automatic tracking,
        finally it will launch the JAABA lunge classifier in the script auto_score_lunges.m

        IMPORTANT
        --------
        Once other behavioral classifiers are built, please contact Logan so he can add them into the code
        """
        self.get_matlab_vid_paths()  # Get video paths
        self.calibrate_tracker()  # Launch FlyTracker Calibration
        self.Automatic_Tracking()  # Launch Fly Tracker Tracking

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

    def load_extra_classifiers(self):
        """
        Launch a GUI so people can click extra classifiers if they want that they want to track
        TO DO: incorporate into code once more classifiers are built (Logan will happily do this if emailed)
        """
        print 'Please select the file corresponding to the video you would like to process'
        Tk().withdraw()  # we don't want a full GUI, so keep the root window from appearing
        self.classifier_extra = askopenfilename()

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

    def trim_vid(self, path_in, path_out, start, stop):
        """
        takes a video located at path_in, segments it between start and stop and saves the new video at path_out
        If the curious code-reader desires to know what the variables (e.g. -ss, -i) in cmd mean, refer to
        https://www.ffmpeg.org/ffmpeg.html#Advanced-options

        WARNING
        -------
        read https://www.ffmpeg.org/ffmpeg.html#Advanced-options before modifying cmd variable in the slightest.
        Seriously. Super srsly. Fucked up this function thrice now. Srsly don't change argument assignment order
        without INTENT, order of parsed arguments dictacte how the arguments behavior with this interface
        """
        # seriously don't modify the order
        cmd = [get_setting(varname="FFMPEG_BINARY"),
               '-ss', '00:{}:00'.format(start),
               '-t', '{}'.format(300),
               '-i', '{}'.format(path_in),
               '-c:v', 'copy', '-an',
               '{}'.format(path_out)]
        # Trim the video
        proc = subprocess.Popen(cmd, shell=False, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        output = proc.communicate()[0].decode()
        try:
            self.pkill()
        except:
            pass

    def five_minute_subclip(self, path_in, path_out=None):
        """
        Uses trim_vid method to trim the video into 5 minute segments

        IMPORTANT
        ---------
        Code assumes you want a five minute long subclip (who would have guessed)
        but if instead want a different length, just change the variable subclip_length
        below
        """
        # sub
        subclip_length = self.subclip_length
        # subclip_length =5 # change me if ya want
        root = self.parent(path_in)  # folder
        name, fullname = self.get_fname(path_in)
        # check if there isn't a path if so make it
        if not os.path.exists(os.path.normpath(os.path.join(root, name) + '\\')):
            os.makedirs(os.path.normpath(os.path.join(root, name) + '\\'))
        # set clip duration
        self.clip_duration = int(mpy.VideoFileClip(path_in, audio=False).duration / 60)
        # create a range of numbers from 0 to the end of the clip, with spacing of
        # subclip_length between them
        self.time_range = [i for i in np.arange(0, self.clip_duration, subclip_length)]
        self.time_range.append(self.clip_duration)
        # for every 5 minutes, segment the video, add it to a list we'll access later
        for i, j in enumerate(self.time_range):
            # Check if we should stop, if so stop
            if self.time_range[i] == self.clip_duration: break
            start, stop = int(self.time_range[i]), int(self.time_range[i + 1])
            # Launch function trim_vid to trim the video
            self.trim_vid(path_in, os.path.normpath(os.path.join(root, name, (name + '_' + str(i) + '.mp4')))
                          , start, stop)
            # Create attribute short_vids, which holds the path of the trimmed videos
            self.short_vids.append(os.path.normpath(os.path.join(root, name, (name + '_' + str(i) + '.mp4'))))

    def make_wellfolders(self):
        """
        Makes folders for each of the wells,

        IMPORTANT
        ---------
        Code Assumes that the number of wells is 12, if not this parameter needs to be changed below
        """
        num_wells = self.num_wells
        # Check if there's a folder already for each well, if not make one
        for i in xrange(num_wells):  # number of wells, change if need be
            if not os.path.exists(
                    os.path.normpath(os.path.join(self.root, self.name, 'well{}'.format(i)))):
                os.makedirs(os.path.join(self.root, self.name, 'well{}'.format(i)))
            self.well_roots.append(os.path.join(self.root, self.name, 'well{}'.format(i)))

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
        import argparse
        videofile = self.short_vids[i]
        print videofile
        # clip = (mpy.VideoFileClip(videofile, audio=False))
        capture = cv2.VideoCapture(videofile)
        count = 0

        while capture.isOpened():
            # grab the current frame and initialize the status text
            grabbed, frame = capture.read()
            if frame is not None:
                # convert the frame to grayscale, blur it, and detect circles
                #gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                #blur = cv2.medianBlur(gray, 5)
                #circles = cv2.HoughCircles(blur, cv2.HOUGH_GRADIENT, 1, 20, \
                                           #param1=60, param2=30, minRadius=85, maxRadius=100)


                dirname = os.path.dirname(videofile) + '\\'
                image = dirname + 'crop_test_%d.jpg' % i
                # write image
                cv2.imwrite(image, frame)

                refPt = []
                cropping = False
                my_zip = []

                def click_and_crop(event, x, y, flags, param):
                    # grab references to the global variables
                    global refPt, cropping

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
                        print refPt[0], refPt[1]  # draw a rectangle around the region of interest
                        cv2.rectangle(image, refPt[0], refPt[1], (0, 255, 0), 2)
                        cv2.imshow("image", image)
                        # construct the argument parser and parse the arguments
                if count < 50:
                    capture.read(15*30)
                if count > 50:
                    ap = argparse.ArgumentParser()
                    ap.add_argument("-i", '--image', required=True, help="Path to the image")
                    args = vars(ap.parse_args(['--image', image]))

                    # load the image, clone it, and setup the mouse callback function
                    image = cv2.imread(args["image"])
                    clone = image.copy()
                    cv2.namedWindow("image")
                    cv2.setMouseCallback("image", click_and_crop)

                    # keep looping until the 'q' key is pressed
                    while True:
                        # display the image and wait for a keypress
                        cv2.imshow("image", image)
                        key = cv2.waitKey(1) & 0xFF

                        # if the 'r' key is pressed, reset the cropping region
                        if key == ord("r"):
                            image = clone.copy()

                        # if the 'c' key is pressed, break from the loop
                        elif key == ord("c"):
                            # print len(refPt)
                            cv2.destroyAllWindows()
                            break

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
                #cv2.destroyAllWindows()

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
        d = {'well' + str(i): i for i, j in enumerate(xrange(num_wells))}
        # inputted array is x,y,r of each circle, grab the x and y
        array = np.array(zip(array[:, 0], array[:, 1]))
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

    def save_obj(self, obj, name):
        """saves passed obj as name.pickle"""
        # import pickle
        with open(name + '.pickle', 'wb') as handle:
            pickle.dump(obj, handle, protocol=pickle.HIGHEST_PROTOCOL)

    def load_obj(self, name):
        """loads name, which is a path to a pickle file without the .pickle at the end"""
        # import pickle
        with open(name + '.pickle', 'rb') as handle:
            return pickle.load(handle)

    def show_attributes(self):
        """
        Code serves to update attributes that are attached to the class, e.g. filetype/filename, and
        prints them all out to the user.
        """
        self.attributes = '\n'.join("%s: %s" % item for item in vars(self).items())
        print '\nHere are the attributes you can access using .:'
        print self.attributes


def crop_vid(input):  # , video_int):
    """
    Uses information saved from detect to crop rectangular videos around
    the circular wells.
    input: see below for code that generates the input, which is basically just the instance of the class attached to
    a number from 0 to n where n is the video duration/5.
    zip([self] * int(self.clip_duration / 5), xrange(int(self.clip_duration / 5)))
    """
    # from moviepy.config import get_setting
    self = input[0]
    video_int = input[1]
    path = self.short_vids[video_int]
    dirname = os.path.dirname(path) + '\\'
    d = self.load_obj(dirname + 'well%d\\well_dictionary_%d' % (video_int, video_int))
    c = self.load_obj(dirname + 'well%d\\circles_%d' % (video_int, video_int))
    for index, (x, y, r) in enumerate(c):
        X1, Y1 = x - r - 20, y - r - 20  # Top left
        X2, Y2 = x + r + 20, y + r + 20  # Bottom right
        side = X2 - X1
        label = str(d[str(x) + '_' + str(y)])
        ffmpeg_crop_out = dirname + '{}\\'.format(label) + os.path.basename(path)

        cmd = [get_setting(varname="FFMPEG_BINARY"), '-i', '{}'.format(path),  # input file
               '-filter:v', 'crop={}:{}:{}:{}'.format(side, side, X1, Y1),
               '-an', '{}'.format(ffmpeg_crop_out)]
        proc = subprocess.Popen(cmd, shell=False,
                                stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        output = proc.communicate()[0].decode()
        # self.jab_path.append(ffmpeg_crop_out)

#---------------> HELPER FUNCTIONS!!!!


def parallel_video_cropping(self):
    """
    Launches four cpus to paralizes the video cropping

    INPUTS
    ------
    self: an instance of the class VideoPipelineNew

    IMPORTANT
    ---------
    Code assumes you want a five minute long subclip but if instead want a different length,
    just change the variable subclip_length below to whatever one you used, make sure to change
    all subclip_length variables in other functions (see five_min_subclips)
    """
    from time import time as T
    subclip_length = self.subclip_length
    n_cpus = 4  # if computer has more than 4 cpus, change this
    p = Pool(n_cpus)
    func_in = zip([self] * int(self.clip_duration / subclip_length), xrange(int(self.clip_duration / subclip_length)))
    s1 = T()
    p.map(crop_vid, func_in)
    s2 = T()
    print 'parallel time', (s2 - s1)


def fx_get_JAABA_output(root, name):


    path = os.path.join(root, name) + '\\*\\*\\**JAABA**'
    paths = glob(path)

    # quit the matlab engine if it's running, then start it
    try:
        eng.quit()
    except:
        pass
    eng = matlab.engine.start_matlab()
    # pass in the paths generated above to matlab
    eng.auto_lunge_scores(paths, nargout=0)
    eng.quit()
    try:  # exit matlab
        eng.quit()
    except:  # weak error exception = bad programming logan
        pass


def get_lunge_bouts(path):
    """
    returns the number of lunges meeting the 2-4 criteria, and the number of lunges excluded, per fly.

    PARAMETERS:
                path: full path of the scored output; this must be a string
                e.g.: 'C:/Users/bmain/Desktop/machine_learning/videos/30_fps/vid2/test/scores_lunge.mat'
                savename: The name of the sheet you would like to save this as.
    """
    # Sanity check and Load data from matlab
    if not isinstance(path, type(str())):
        path = str(path)
    scores = loadmat(path)

    # Get start and end frames
    # index [0][0][0] to get out of all the stupid gobly goob that matlab auto generates in its conversion
    lunge_start = scores['allScores']['t0s'][0][0][0]
    lunge_stop = scores['allScores']['t1s'][0][0][0]
    lunge_bouts = lunge_stop - lunge_start

    # below is necessary becaure of the stupid nesting matlab loading does...
    flies = np.array([x[0] for x in lunge_bouts])
    lunge_bouts = []
    for i, j in enumerate(flies):
        lunge_bouts.append(np.array([x for x in j]))
    lunge_bouts = np.array(lunge_bouts)
    # Make sure the number you're using here reflects minimum ans maximum frame
    include = np.array([fly[np.where(fly >= 2) and np.where(fly <= 4)] for fly in lunge_bouts])

    # Generate dataframes using pandas in order to facilitate saving and organization
    lunge_count = pd.DataFrame(data=[len(x) for x in include],
                               columns=['Lunge Counts Included'],
                               index=[('fly' + str(i)) for i in xrange(len(include))])

    total = pd.DataFrame(data=[len(x) for x in lunge_bouts],
                         columns=['Lunge Counts Total'],
                         index=[('fly' + str(i)) for i in xrange(len(lunge_bouts))])

    df = pd.concat([lunge_count, total], axis=1)
    return df


def excel_writer(root, name):
    # Go through each of the 12 wells, get out all the data and combine it
    lunge_per_well = []
    for i in xrange(12):
        # Make sure we're collasping within well
        path = os.path.join(root, name) + '\\well{}\\*\\**JAABA**\\**lunge**'.format(i)
        scored_paths = glob(path)  # Get all wells
        well_level = []  # STORE FINAL PRODUCT HERE
        for path in scored_paths:
            df = get_lunge_bouts(path)
            well_level.append(df)
        df_in_well = pd.concat(well_level)  # This gets all split videos, for same well
        # Sum the dataframes, make sure we know which well is which!!!
        data = pd.DataFrame(df_in_well.sum(axis=0), columns=['well' + str(i)])
        lunge_per_well.append(data)
        # Make it into a dataframe
    df = pd.concat(lunge_per_well, axis=1)

    # Make a file if its not there
    excel_root = os.path.join(root, name) + '\\lunge_excel_output.xlsx'

    if not os.path.exists(excel_root):
        writer = pd.ExcelWriter(excel_root)  # +'output.xlsx')
        df.to_excel(writer, name)
        writer.save()
        writer.close()

    # DO NOT OVER WRITE DATA, CHECK IF FILE IS THERE ALREADY!!!
    elif os.path.exists(excel_root):
        book = load_workbook(excel_root)
        writer = pd.ExcelWriter(excel_root, engine='openpyxl')
        writer.book = book
        df.to_excel(writer, sheet_name=name)
        writer.save()
        writer.close()


# Basically means, run this if you're not import functions from this script e.g. you hit run
# instead of in another script typing from VideoPipelineFinal import parallel_video_cropping etc.
if __name__ == '__main__':
    from time import time as T
    s = T()
    self = VideoPipelineNew()
    print 'Program took this long to run: ' + str(time() - s)
    parallel_video_cropping(self)
    self.matlab_stuff()