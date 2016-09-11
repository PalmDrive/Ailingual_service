from __future__ import absolute_import

import tempfile
import subprocess


def convert_to_wav(ext, filename):
    if ext.endswith('mp4'):
        tmp_file = tempfile.NamedTemporaryFile().name + ".wav"
        print subprocess.call(
            'ffmpeg -i %s  -ac 1 -ar 16000 %s' % (filename, tmp_file),
            shell=True)
        return tmp_file
    else:
        return filename
