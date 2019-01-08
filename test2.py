import os
import subprocess

os.chdir('C:/Users/Ben/Documents/JAABA/tracking')

subprocess.call(['ffmpeg' '-i', 'C:/Users/Ben/Documents/JAABA/tracking/testvid.mp4', '-filter:v', 'crop=200:200:200:100', 
	'C:/Users/Ben/Documents/JAABA/tracking/output.mp4'])