from __future__ import absolute_import

import subprocess
import tempfile


def convert_to_wav(ext, filename):
    tmp_file = tempfile.NamedTemporaryFile(suffix = ".wav").name
    print subprocess.call(
        'ffmpeg -i %s -ac 1 -ar 16000 %s' % (filename, tmp_file),
        shell=True)
    return tmp_file
