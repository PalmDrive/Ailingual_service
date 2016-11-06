import contextlib
import math
import os
import wave


def preprocess_clip_length(audio_dir, starts, is_voices, break_pause, preferred_length=10,
                           force_preferred_length=False):
    print('break pause: %f' % break_pause)
    # length limit of audio for VOP api
    upper_length_limit = 30
    lower_length_limit = 1
    if upper_length_limit < preferred_length:
        preferred_length = upper_length_limit
    elif force_preferred_length:
        upper_length_limit = preferred_length
    # length we prefer using to avoid context-less transcription issue

    # initialization

    # count the order of output file
    output_count = 0

    # store total duration of current clip with the chunks collected
    clip_duration = 0

    # store the audio frames to be written into the current clip
    data = []

    # count how many chunks are ready to be written in current clip
    clip_count = 0

    # count how many voiced chunks are ready to be written in current clip
    voiced_clip_count = 0

    # store the start time of each clip
    clip_starts = []

    # store the duration of each clip
    clip_durations = []

    for subdir, dirs, files in os.walk(audio_dir):
        for i in range(0, len(files)):
            file_name = "chunk-%d.wav" % i
            file_path = os.path.join(subdir, file_name)
            with contextlib.closing(wave.open(file_path, 'rb')) as f:
                frames = f.getnframes()
                rate = f.getframerate()
                duration = frames / float(rate)
                print ('start processing clip %s duration %f, current total duration %f'
                       % (file_name, duration, clip_duration))

                if not is_voices[i]:
                    print('pause time: %f' % duration)
                # if the current clip is a breaking pause (long enough), then break it
                if (not is_voices[i]) \
                        and duration >= break_pause \
                        and clip_duration >= lower_length_limit \
                        and (not force_preferred_length):
                    if voiced_clip_count > 0:  # combine the remaining pieces
                        write_previous_clip(audio_dir, output_count, data)
                        clip_durations.append(clip_duration)
                        outfile = out_file_path(audio_dir, output_count)
                        print('break pause: combine %d clips into %s - clip_duration %f'
                              % (clip_count, outfile, clip_duration))
                        print('\nstart at %f end_at: %f\n' % (clip_starts[-1], clip_starts[-1] + clip_duration))
                        output_count += 1
                    clip_duration = 0
                    data = []
                    clip_count = 0
                    voiced_clip_count = 0

                # if concatenating next clip won't make the combined clip exceed the length limit, add the next clip
                elif clip_duration + duration <= preferred_length:
                    clip_duration += duration
                    data.append([f.getparams(), f.readframes(f.getnframes())])
                    f.close()

                    clip_count += 1
                    if is_voices[i]:
                        if voiced_clip_count == 0:
                            clip_starts.append(starts[i])
                            print('clip start 1: %f' % (clip_starts[-1]))
                        voiced_clip_count += 1
                    print (
                        'added to the previous clip %s duration %f - total duration %f' % (
                            file_name, duration, clip_duration))
                else:
                    if voiced_clip_count > 0:
                        write_previous_clip(audio_dir, output_count, data)
                        clip_durations.append(clip_duration)
                        outfile = out_file_path(audio_dir, output_count)
                        print('combine %d clips into %s - clip_duration %f' % (clip_count, outfile, clip_duration))
                        print('\nstart at %f end_at: %f\n' % (clip_starts[-1], clip_starts[-1] + clip_duration))
                        output_count += 1
                    clip_duration = 0
                    data = []
                    clip_count = 0
                    voiced_clip_count = 0

                    # if the current clip is too long, slice clip into smaller pieces with equal length
                    if duration > upper_length_limit:
                        n = int(math.ceil(duration / upper_length_limit))
                        for j in range(0, n):
                            outfile = out_file_path(audio_dir, output_count)
                            extract_slice(f, outfile,
                                          long(j * duration / n * 1000),
                                          long((j + 1) * duration / n * 1000))
                            print('slice audio %s into sub-audio %s' % (file_name, outfile))
                            clip_starts.append(starts[i] + j * duration / n)
                            clip_durations.append(duration / n)
                            print('clip start: %f' % (clip_starts[-1]))
                            output_count += 1
                        print('\nstart at %f end_at: %f\n' % (clip_starts[-1], clip_starts[-1] + duration / n))
                    else:
                        clip_duration += duration
                        data.append([f.getparams(), f.readframes(f.getnframes())])
                        f.close()

                        clip_count += 1
                        if is_voices[i]:
                            if voiced_clip_count == 0:
                                clip_starts.append(starts[i])
                                print('clip start 2: %f' % (clip_starts[-1]))
                            voiced_clip_count += 1
            os.remove(file_path)

    # combine the remaining pieces
    if voiced_clip_count > 0:
        write_previous_clip(audio_dir, output_count, data)
        clip_durations.append(clip_duration)
        outfile = out_file_path(audio_dir, output_count)
        print('combine %d clips into %s - clip_duration %f' % (clip_count, outfile, clip_duration))
        print('\nstart at %f end_at: %f\n' % (clip_starts[-1], clip_starts[-1] + clip_duration))

    return clip_starts, clip_durations


def write_previous_clip(audio_dir, output_count, data):
    # combine the previous clips
    outfile = out_file_path(audio_dir, output_count)
    output = wave.open(outfile, 'wb')
    output.setparams(data[0][0])
    for params, frames in data:
        output.writeframes(frames)
    output.close()


def out_file_path(dir_path, output_count):
    return os.path.join(dir_path, "pchunk-%08d.wav" % output_count)


# improve transcription accuracy of the edges of clips by extending the clips with adjacent partial fragment
def smoothen_clips_edge(file_list):
    smoothen_length = 0.1  # in seconds
    for i, file_name in enumerate(file_list):
        if i > 0:
            prepend_last_clip(file_list[i - 1], file_name, smoothen_length, smoothen_length)
        if i < len(file_list) - 1:
            append_first_clip(file_list[i + 1], file_name, smoothen_length)


def prepend_last_clip(from_file_name, to_file_name, length, offset=0.0):
    from_file = wave.open(from_file_name, 'rb')
    from_rate = from_file.getframerate()
    from_frames = from_file.getnframes()
    last_clip_frames = length * float(from_rate)
    pos = from_frames - last_clip_frames - offset * from_rate
    from_file.setpos(pos)
    from_data = from_file.readframes(int(last_clip_frames))
    params = from_file.getparams()
    from_file.close()

    to_file = wave.open(to_file_name, 'rb')
    to_data = to_file.readframes(to_file.getnframes())
    to_file.close()

    output = wave.open(to_file_name, 'wb')
    output.setparams(params)
    output.writeframes(from_data)
    output.writeframes(to_data)
    output.close()


def append_first_clip(from_file_name, to_file_name, length, offset=0.0):
    from_file = wave.open(from_file_name, 'rb')
    from_rate = from_file.getframerate()
    first_clip_frames = length * float(from_rate)
    pos = offset * from_rate
    from_file.setpos(pos)
    from_data = from_file.readframes(int(first_clip_frames))
    params = from_file.getparams()
    from_file.close()

    to_file = wave.open(to_file_name, 'rb')
    to_data = to_file.readframes(to_file.getnframes())
    to_file.close()

    output = wave.open(to_file_name, 'wb')
    output.setparams(params)
    output.writeframes(to_data)
    output.writeframes(from_data)
    output.close()


def extract_slice(infile, outfilename, start_ms, end_ms):
    width = infile.getsampwidth()
    rate = infile.getframerate()
    fpms = rate / 1000  # frames per ms
    length = (end_ms - start_ms) * fpms
    start_index = start_ms * fpms

    out = wave.open(outfilename, "w")
    out.setparams((infile.getnchannels(), width, rate, length, infile.getcomptype(), infile.getcompname()))

    infile.rewind()
    anchor = infile.tell()
    infile.setpos(anchor + start_index)
    out.writeframes(infile.readframes(length))
