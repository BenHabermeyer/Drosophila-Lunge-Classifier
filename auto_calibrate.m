function auto_calibrate(f_vid, f_info)
    %Ben Habermeyer
    %Add flytracker to path then launch calibrator
    %function takes as input the pathname to the video and the pathname to
    %the calibration file
    
    flytracker_path = 'C:\Users\Ben\Documents\FlyTracker-1.0.5';
    addpath(genpath(flytracker_path))
    success = calibrator(f_vid, f_info)
end
