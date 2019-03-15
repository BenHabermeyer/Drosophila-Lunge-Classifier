function get_lunges2(directory, videoname, classifiername, excluded, xvals, yvals)
  %Ben Habermeyer
    %function takes as input a string containing the name of the directory,
    %a string containing the video name, and a string containing the
    %clasifier name, and a list of wells to be excluded
    %finds the initial a and b locations using x.mat and y.mat in the perframe
    %features for each well
    %outputs an excel file containing the number of bouts and their frame
    %start/end frames for each fly
    %NOTE: pretty hard coded to 12 wells with 24 flies total so will change
    %file if anything different is run

    %add the input folder to path
    addpath(directory);
    addpath(strcat(directory, '\perframe'));

    %laod the scored data
    classifier_scores = strcat('scores_', classifiername);
    load(classifier_scores, 'allScores');
    scores = allScores.scores;

    %load in the x and y data
    load x.mat
    xdata = data;
    load y.mat
    ydata = data;
    clear data
    
    %boolean matrix for wells 1-12 whether they are excluded 1 or not 0
    is_excluded = zeros(1,12);
    for i = 1:length(excluded)
        is_excluded(double(excluded{i})) = 1;
    end

    %use a cell arary to store wells 1-12 flies A-B and their corresponding
    %information
    ids = cell(24, 7);
    %instantiate positions
    counter = 1;
    for i = 1:12
        for j = 1:2
            if j == 1
                letter = 'A';
            else
                letter = 'B';
            end
            ids{counter, 1} = strcat(num2str(i), letter);
            counter = counter + 1;
        end
    end
    %write to the excluded column
    for i = 1:12
        if is_excluded(i) == 1
            ids{2*i,3} = 'Excluded';
            ids{2*i-1,3} = 'Excluded';
        else
            ids{2*i,3} = '';
            ids{2*i-1,3} = '';
        end
    end
    
    %data of x and y positions, NaN for excluded wells
    %column 1 is x, 2 is y, 3 is JAABA fly #
    positions = NaN(length(scores),3);
    
    for i = 1:length(scores)
        positions(i, 1) = xdata{1, i}(1);
        positions(i, 2) = ydata{1, i}(1);
        positions(i, 3) = i;
    end
    
    %iterate through the positions, assigning which is closest to each well
    %center. X is column 1, Y is column 2
    circle_centers = NaN(12,2);
    for i = 1:12
       circle_centers(i,1) = xvals{i};
       circle_centers(i,2) = yvals{i};
    end
    
    %find which fly is closest to which circle center and classify
    wells = NaN(1,length(scores));
    for i = 1:length(scores)
        %check if the fly was not excluded
        %use the distance formula to calculate the closest well
        xdiff = (circle_centers(:,1) - positions(i,1)).^2;
        ydiff = (circle_centers(:,2) - positions(i,2)).^2;
        distances = sqrt(xdiff + ydiff);
        [~, ind] = min(distances);
        wells(i) = ind;
    end
    
    %for each well, classify which fly should be A and which should be B
    %use which fly was HIGHER is A - the lower y value of the pair and
    %assign to column 2 of the ids
    for i = 1:12
        if is_excluded(i) == 0
            [~, inds] = find(wells == i);
            if positions(inds(1),2) < positions(inds(2),2)
                ids{2*i-1,2} = num2str(inds(1));
                ids{2*i,2} = num2str(inds(2));
            else
                ids{2*i-1,2} = num2str(inds(2));
                ids{2*i,2} = num2str(inds(1));
            end
        else
            ids{2*i-1,2} = '';
            ids{2*i,2} = '';
        end
    end

    %load in the postprocessed scores, start time and end time for bouts
    postprocessed = allScores.postprocessed;
    %note: since it is 0 or 1 you really don't need this at all, just start
    %and end times
    
    tstart = allScores.t0s;
    tend = allScores.t1s;
    
    %I  made ids a cell so make a matrix for easy indexing
    ids_mat = NaN(24,1);
    for i = 1:24
        ids_mat(i) = str2double(ids{i, 2});
    end
    
    %loop through all of the wells - ignore if was excluded, otherwise
    %match id to fly and update accordingly
    i = 1;
    for j = 1:24
        if ~isnan(ids_mat(j))
            %just use the information we have from start and end frames
            startframes = tstart{i};
            endframes = tend{i};
            
            %add startframes and endframes to cell array of ids
            ids_ind = find(ids_mat == i);
            starttostring = sprintf('%d, ', startframes);
            ids{ids_ind, 5} = starttostring(1:end-2);
            endtostring = sprintf('%d, ', endframes);
            ids{ids_ind, 6} = endtostring(1:end-2);
            %count the number of lunge bouts
            ids{ids_ind, 4} = length(startframes);
            %convert start time frames to seconds (assume 30fps)
            starttimetostring = sprintf('%d, ', round(startframes ./ 30));
            ids{ids_ind, 7} = starttimetostring(1:end-2);
            i = i + 1;
        end
    end

    %write the data to an excel file - has directory name_classifier name
    filename = strcat(directory, '\', videoname, '_', classifiername, '_Data.xlsx');
    titles = {'Well Position', 'Fly ID', 'Excluded', 'Number of Lunges', 'Start Frames', ...
        'End Frames', 'Start Times (s)'};
    output = [titles; ids];
    xlswrite(filename, output);
    
end

