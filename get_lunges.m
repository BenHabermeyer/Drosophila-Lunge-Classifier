%Ben Habermeyer

%function get_lunges(input) 
input = 'C:\Users\Ben\Documents\JAABA\tracking_b6_1000\testvid\testvid_JAABA';

%function takes as input a string containing the name of the directory
%finds the initial a and b locations using x.mat and y.mat in the perframe
%features for each well
%outputs an excel file containing the number of bouts and their frame
%start/end frames for each fly

%add the input folder to path
addpath(input);

%laod the scored data
load scores_lungeV1.mat
scores = allScores.scores;

%load in the x and y data
load x.mat
xdata = data;
load y.mat
ydata = data;
clear data

%figure out which index corresponds to which fly position
%use a cell arary to store wells 1-12 flies A-B and their corresponding #
ids = cell(24, 2);
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
}

%find start frames - make sure start

%find ends frames - make sure end

%convert frames to seconds (assume 30fps)

%count the number of lunge bouts
    

%write the data to an excel file - has directory name_classifier name
splitinput = strsplit(input, '\'); 
filename = strcat(char(splitinput{end}), '_', behaviorName, '_Data');
%xlswrite(filename, alldata);
%disp('Finished writing to excel file')


%end