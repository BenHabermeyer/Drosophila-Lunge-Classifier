%Ben Habermeyer
%Function calls behavior classifier given path to .jab file and a directory
%folder containing the video of interest
function classify_behavior(jaaba_path, classifier, directoryname)
    %first must add all the JAABA stuff to path
    %1. add JAABA/perframe to path
    %2. call JAABA's function for adding all its necessary files to path
    %3. call JAABA Detect to classify behavior
    
    %1.
    addpath(jaaba_path);
    %2.
    SetUpJAABAPath;
    %3.
    JAABADetect(directoryname, 'jabfiles', classifier);
end