function get_lunges(directory, classifiername)
  %Ben Habermeyer
    %function takes as input a string containing the name of the directory
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

    %figure out which index corresponds to which fly position
    %use a cell arary to store wells 1-12 flies A-B and their corresponding #
    ids = cell(24, 6);
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
    positions = NaN(24,3);
    for i = 1:24
        positions(i, 1) = xdata{1, i}(1);
        positions(i, 2) = ydata{1, i}(1);
        positions(i, 3) = i;
    end
    %fill positions using x and y data
    %note increasing x is right increasing y is down
    %sort based on the y coordinate, then by the x coordinate
    [~,idx] = sort(positions(:,2)); % sort just the first column
    sortedpositions = positions(idx,:);   % sort the whole matrix using the sort indices

    %now iterate through 8 flies at a time for each of the 3 rows and sort
    %by y to assign A/B
    for row = 1:3
        %sort group of 8 flies
        submat = sortedpositions((row-1)*8 + 1 : row*8, :);
        [~,idx] = sort(submat(:,1)); % sort just the first column
        sortedx = submat(idx,:);   % sort the whole matrix using the sort indices
        for col = 1:4
            %select A and B based on which has the smaller y value (is higher)
            if sortedx((2*col)-1, 2) < sortedx(2*col, 2)
                ids{8*row - 8 + (2*col) - 1, 2} = sortedx((2*col)-1, 3);
                ids{8*row - 8 + (2*col), 2} = sortedx(2*col, 3);
            else
                ids{8*row - 8 + (2*col) - 1, 2} = sortedx(2*col, 3);
                ids{8*row - 8 + (2*col), 2} = sortedx((2*col)-1, 3);
            end
        end
    end

    %threshold for JAABA classifying a behavior
    threshold = 10;

    %create big matrix with all 24 wells and their scores per frame
    oldscores = NaN(24, length(scores{1}));
    for i = 1:24
        oldscores(i, :) = scores{i};
    end
    %I  made ids a cell so make a matrix for easy indexing
    ids_mat = NaN(24,1);
    for i = 1:24
        ids_mat(i) = ids{i, 2};
    end

    %apply the threshold to get a logical index
    scores_thresh = oldscores > 10;

    %find start frames - check if index is 1
    %find end frames - check if index is end
    for i = 1:24
        startframes = [];
        endframes = [];
        ind = find(scores_thresh(i, :) == 1);
        for j = 1:length(ind)
            %if value - 1 is not contained in ind it must be a starting index
            if all(ind(:) ~= ind(j) - 1)
                startframes = horzcat(startframes, ind(j));
            end
            %if value + 1 is not containined in ind it must be an ending index
            if all(ind(:) ~= ind(j) + 1)
                endframes = horzcat(endframes, ind(j));
            end
        end
        %add startframes and endframes to cell array of ids
        ids_ind = find(ids_mat == i);
        starttostring = sprintf('%d, ', startframes);
        ids{ids_ind, 4} = starttostring(1:end-2);
        endtostring = sprintf('%d, ', endframes);
        ids{ids_ind, 5} = endtostring(1:end-2);
        %count the number of lunge bouts
        ids{ids_ind, 3} = length(startframes);
        %convert start time frames to seconds (assume 30fps)
        starttimetostring = sprintf('%d, ', round(startframes ./ 30));
        ids{ids_ind, 6} = starttimetostring(1:end-2);
    end

    %write the data to an excel file - has directory name_classifier name
    filename = strcat(directory, '_', classifiername, '_Data');
    titles = {'Well Position', 'Fly ID', 'Number of Lunges', 'Start Frames', ...
        'End Frames', 'Start Times (s)'};
    output = [titles; ids];
    xlswrite(filename, output);
    disp('Finished writing to excel file')

    %plotting helper
    %{
    %dots
    figure;
    for i = 1:24
        hold on
        txt = num2str(i);
        plot(xdata{1,i}(1), -ydata{1,i}(1), '.r');
        text(xdata{1,i}(1), -ydata{1,i}(1), txt);
    end
    %lunge bouts
    for i = 1:24
        figure;
        plot(1:1811, scores{1, ids{i, 2}});
        title(ids{i, 1});
    end
    %}
end

