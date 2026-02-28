import os
import sys

# Force pydub to use our local ffmpeg
os.environ["PATH"] = "/Users/mac/Desktop/main:" + os.environ.get("PATH", "")

from pydub import AudioSegment
import pydub.utils

print("FFmpeg path being used:", pydub.utils.get_prober_name()) 
