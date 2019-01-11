function auto_track(folders, f_vid, f_calib)
    % list of all folders to be processed
    %Ben Habermeyer
    %Function for calling flytracker given a video and calibration file
    %folders represents the folders containing videos to track
    %f_vid represents the file extension .mp4
    %f_calib represents the calibration file
    
    %add flytracker directory to path
    flytracker_path = 'C:\Users\Ben\Documents\FlyTracker-1.0.5';
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
    for f=1:numel(folders)
        % set parameters for specific folder
        videos.dir_in  = folders{f};
        videos.dir_out = folders{f}; % save results into video folder
        videos.filter = f_vid;     % extension of the videos to process
        % track all videos within folder
        tracker(videos, options, f_calib);
    end