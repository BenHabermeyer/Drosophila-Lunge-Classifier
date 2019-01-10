% list of all folders to be processed
function auto_track(folders,f_vid, f_calib)
    %folders = {'C:/Users/bmain/Desktop/machine_learning/videos/30_fps/vid2/test/6-16-16 D7 31 grouped splitp1 x Trpa1/'};

    % set options (omit any or all to use default options)
    %options.granularity  = 10000;
    options.num_chunks   = 4;       % set either granularity or num_chunks
    options.num_cores    = 2;
    options.max_minutes  = Inf;
    options.save_JAABA   = 1;
    options.save_seg     = 0;

    % set up tracker using inputted file and f_calib
    %videos.dir_in = f_vid;
    %videos.dir_out = f_vid;
    %videos.filter = 
    % loop through all folders
    for f=1:numel(folders)
        % set parameters for specific folder
        videos.dir_in  = folders{f};
        videos.dir_out = folders{f}; % save results into video folder
        videos.filter = f_vid;     % extension of the videos to process
        % track all videos within folder
        tracker(videos,options,f_calib);
    end