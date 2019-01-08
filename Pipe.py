from Automate import VideoPipelineNew
from Automate import parallel_video_cropping
from Automate import excel_writer
from Automate import fx_get_JAABA_output
from time import time

if __name__ == '__main__':

    s = time()
    # Select, pre-process Video
    self = VideoPipelineNew()
    print 'Program took this long to run: ' + str(time() - s)
    parallel_video_cropping(self)
    # Apply Matlab stuff up until JAABA
    self.matlab_stuff()
    # See if a function makes it happy...
    root = self.true_root
    name = self.true_name
    print root, name
    fx_get_JAABA_output(root, name)
    excel_writer(root,name, zoom=False)