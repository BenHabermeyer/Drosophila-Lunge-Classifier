function auto_calibrate(flytracker_path, f_vid, f_info)
    %Ben Habermeyer
    %Add flytracker to path then launch calibrator
    %function takes as input the pathname to the video and the pathname to
    %the calibration file
    
    addpath(genpath(flytracker_path))
    success = calibrator(f_vid, f_info);
end
