from __future__ import absolute_import

import subprocess
import tempfile


def convert_to_wav(ext, filename):
    supported_formats = ['mp4', 'mp3', 'm4a']
    supported = False
    for f in supported_formats:
        if ext.endswith(f):
            supported = True
    if supported:
        tmp_file = tempfile.NamedTemporaryFile(suffix = ".wav").name
        print subprocess.call(
            'ffmpeg -i %s -ac 1 -ar 16000 %s' % (filename, tmp_file),
            shell=True)
        return tmp_file
    else:
        return filename
