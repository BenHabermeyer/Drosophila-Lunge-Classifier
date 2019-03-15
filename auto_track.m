function auto_track(flytracker_path, folder, f_vid, f_calib)
    %Ben Habermeyer
    %Function for calling flytracker given a video and calibration file
    %folders represents the folders containing videos to track
    %f_vid represents the file extension .mp4
    %f_calib represents the calibration file
    
    %add flytracker directory to path
    addpath(genpath(flytracker_path))
    
    % set options (omit any or all to use default options)
    %options.granularity  = 10000;
    options.num_chunks   = 4;       %set either granularity or num_chunks
    options.num_cores    = 2;       %2 on Ben's Computer
    options.max_minutes  = Inf;
    options.save_JAABA   = 1;
    options.save_seg     = 0;       %don't need segmentation

    % set up tracker using inputted file and f_calib
    % loop through all folders
        % set parameters for specific folder
    videos.dir_in  = folder;
    videos.dir_out = folder; % save results into video folder
    videos.filter = f_vid;     % extension of the videos to process
        % track all videos within folder
    tracker(videos, options, f_calib);
end