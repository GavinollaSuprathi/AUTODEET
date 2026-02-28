import urllib.request
import os
import zipfile

# 1. Download ffprobe as well to ensure pydub works flawlessly
print('Downloading ffprobe...')
urllib.request.urlretrieve('https://evermeet.cx/ffmpeg/ffprobe-6.0.zip', 'ffprobe.zip')
with zipfile.ZipFile('ffprobe.zip', 'r') as zip_ref:
    zip_ref.extractall('.')
os.chmod('ffprobe', 0o755)
print('Done dumping ffprobe!')
