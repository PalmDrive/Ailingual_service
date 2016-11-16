from __future__ import absolute_import

import subprocess
import tempfile
import os


def convert_to_wav(filename):
    tmp_file = tempfile.NamedTemporaryFile(suffix = ".wav").name
    null_dev = os.devnull
    null_file = open(null_dev,"w")
    print subprocess.call(
        'ffmpeg -i %s -ac 1 -ar 16000 %s' % (filename, tmp_file),
        stdout = null_file,
        stderr = null_file,
        shell=True)
    return tmp_file
