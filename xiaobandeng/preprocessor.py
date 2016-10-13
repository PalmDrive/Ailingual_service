import wave
import contextlib
import math
import os


def preprocess_clip_length(audio_dir, starts, preferred_length=10, force_preferred_length=False):
    # length limit of audio for VOP api
    length_limit = 60
    if length_limit < preferred_length:
        preferred_length = length_limit
    elif force_preferred_length:
        length_limit = preferred_length
    # length we prefer using to avoid context-less transcription issue

    # initialization
    output_count = 0
    outfile = out_file_path(audio_dir, output_count)
    clip_duration = 0
    data = []
    clip_count = 0

    new_starts = []
    for subdir, dirs, files in os.walk(audio_dir):
        for i in range(0, len(files)):
            file_name = "chunk-%d.wav" % i
            file_path = os.path.join(subdir, file_name)
            with contextlib.closing(wave.open(file_path, 'rb')) as f:
                frames = f.getnframes()
                rate = f.getframerate()
                duration = frames / float(rate)
                print ('process clip %s duration %f, current total duration %f' % (file, duration, clip_duration))
                # if concatenating next clip won't make the combined clip exceed the length limit, add the next clip
                if clip_duration + duration <= preferred_length:
                    clip_duration += duration
                    data.append([f.getparams(), f.readframes(f.getnframes())])
                    f.close()
                    if clip_count == 0:
                        new_starts.append(starts[i])
                        print('clip start: %f' % (new_starts[-1]))
                    clip_count += 1
                    print (
                        'added to the previous clip %s duration %f - total duration %f' % (
                            file, duration, clip_duration))
                else:
                    if clip_count > 0:
                        # combine the previous clips
                        output = wave.open(outfile, 'wb')
                        output.setparams(data[0][0])
                        for params, frames in data:
                            output.writeframes(frames)
                        output.close()
                        print('combine %d clips into %s - clip_duration %f' % (clip_count, outfile, clip_duration))
                        print('\nend_at: %f\n' % (new_starts[-1] + clip_duration))
                        output_count += 1
                    outfile = out_file_path(audio_dir, output_count)
                    clip_duration = 0
                    data = []
                    clip_count = 0
                    # if the current clip is too long, slice clip into smaller pieces with equal length
                    if duration > length_limit:
                        n = int(math.ceil(duration / length_limit))
                        for j in range(0, n):
                            extract_slice(f, outfile,
                                          long(j * duration / n * 1000),
                                          long((j + 1) * duration / n * 1000))
                            print('slice audio %s into sub-audio %s' % (file, outfile))
                            new_starts.append(starts[i] + j * duration / n)
                            print('clip start: %f' % (new_starts[-1]))
                            output_count += 1
                            outfile = out_file_path(audio_dir, output_count)
                        print('\nend_at: %f\n' % (new_starts[-1] + duration / n))
                    else:
                        clip_duration += duration
                        data.append([f.getparams(), f.readframes(f.getnframes())])
                        f.close()
                        if clip_count == 0:
                            new_starts.append(starts[i])
                            print('clip start: %f' % (new_starts[-1]))
                        clip_count += 1
            os.remove(file_path)
    if clip_count > 0:  # combine the remaining pieces
        output = wave.open(outfile, 'wb')
        output.setparams(data[0][0])
        for params, frames in data:
            output.writeframes(frames)
        output.close()
        print('combine %d clips into %s - clip_duration %f' % (clip_count, outfile, clip_duration))
        print('\nend_at: %f\n' % (new_starts[-1] + clip_duration))
    return new_starts


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
