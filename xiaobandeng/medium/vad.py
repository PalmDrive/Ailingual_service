from __future__ import absolute_import

import collections
import contextlib
import sys
import tempfile
import wave
import statistics

import webrtcvad


def read_wave(path):
    with contextlib.closing(wave.open(path, 'rb')) as wf:
        num_channels = wf.getnchannels()
        assert num_channels == 1
        sample_width = wf.getsampwidth()
        assert sample_width == 2
        sample_rate = wf.getframerate()
        assert sample_rate in (8000, 16000, 32000)
        pcm_data = wf.readframes(wf.getnframes())
        return pcm_data, sample_rate


def write_wave(path, audio, sample_rate):
    with contextlib.closing(wave.open(path, 'wb')) as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(audio)


class Frame(object):
    def __init__(self, bytes, timestamp, duration):
        self.bytes = bytes
        self.timestamp = timestamp
        self.duration = duration


def frame_generator(frame_duration_ms, audio, sample_rate):
    n = int(sample_rate * (frame_duration_ms / 1000.0) * 2)
    offset = 0
    timestamp = 0.0
    duration = (float(n) / sample_rate) / 2.0
    while offset + n < len(audio):
        yield Frame(audio[offset:offset + n], timestamp, duration)
        timestamp += duration
        offset += n


def vad_collector(sample_rate, frame_duration_ms,
                  padding_duration_ms, vad, frames):
    num_padding_frames = int(padding_duration_ms / frame_duration_ms)
    ring_buffer = collections.deque(maxlen=num_padding_frames)
    triggered = False
    voiced_frames = []
    clip_start = 0.0
    for frame in frames:
        sys.stdout.write(
            '1' if vad.is_speech(frame.bytes, sample_rate) else '0')
        voiced_frames.append(frame)
        ring_buffer.append(frame)
        if not triggered:
            num_voiced = len([f for f in ring_buffer
                              if vad.is_speech(f.bytes, sample_rate)])
            if num_voiced >= 0.5 * ring_buffer.maxlen:
                # end a non-voiced chunk
                new_voiced_frames = voiced_frames[-len(ring_buffer):]
                del voiced_frames[-len(ring_buffer):]
                if len(voiced_frames) > 0:
                    duration = float(len(voiced_frames)*frame_duration_ms)/1000
                    # print "clip start %s , duration %s" % (clip_start, duration)
                    yield b''.join([f.bytes for f in voiced_frames]), clip_start, triggered, duration

                # start a voiced chunk
                triggered = True
                voiced_frames = new_voiced_frames
                clip_start = ring_buffer[0].timestamp
                sys.stdout.write('+(%s)' % (clip_start,))
                ring_buffer.clear()
        else:
            num_unvoiced = len([f for f in ring_buffer
                                if not vad.is_speech(f.bytes, sample_rate)])
            if num_unvoiced >= 0.4 * ring_buffer.maxlen:
                # end a voiced chunk
                sys.stdout.write('-(%s)' % (frame.timestamp + frame.duration))
                duration = float(len(voiced_frames) * frame_duration_ms) / 1000
                # print "clip start %s , duration %s" % (clip_start, duration)
                yield b''.join([f.bytes for f in voiced_frames]), clip_start, triggered, duration

                # start a unvoiced chunk
                triggered = False
                voiced_frames = []
                clip_start = frame.timestamp + frame.duration
                ring_buffer.clear()

    sys.stdout.write('\n')
    if voiced_frames:
        duration = float(len(voiced_frames) * frame_duration_ms) / 1000
        # print "clip start %s , duration %s" % (clip_start, duration)
        yield b''.join([f.bytes for f in voiced_frames]), clip_start, triggered, duration


# aggressive is limited to 0..3. By experience, 3 is the most aggressive. 0 is the least aggressive.
def slice(aggressive, filename):
    audio, sample_rate = read_wave(filename)
    vad = webrtcvad.Vad(int(aggressive))
    frames = frame_generator(30, audio, sample_rate)
    frames = list(frames)
    segments = vad_collector(sample_rate, 30, 300, vad, frames)

    dirpath = tempfile.mkdtemp()
    starts = []
    is_voices = []

    pause_durations = []
    for i, (segment, start, is_voice, duration) in enumerate(segments):
        path = dirpath + '/chunk-%d.wav' % i
        # print(' Writing %s' % (path,))
        write_wave(path, segment, sample_rate)
        starts.append(start)
        is_voices.append(is_voice)
        if not is_voice:
            pause_durations.append(duration)


    pause_durations = sorted(pause_durations)
    break_pause = statistics.median(pause_durations)
    # print "calculated break pause %s" % break_pause

    if break_pause > 0.7:
        break_pause = 0.7
    elif break_pause < 0.3:
        break_pause = 0.3
    return dirpath, starts, is_voices, break_pause


def main(args):
    if len(args) != 2:
        sys.stderr.write(
            'Usage: vad.py <aggressiveness> <path to wav file>\n')
        sys.exit(1)

    slice(args[0], args[1])


if __name__ == '__main__':
    main(sys.argv[1:])
