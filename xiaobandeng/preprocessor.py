import wave
import contextlib
import math
import os

def fixClipLength(audio_dir, starts):
    # length limit of audio for VOP api
    length_limit = 60
    # length we prefer using to avoid non-context transcription issue
    preferred_length = 15

    # initialization
    output_count = 0
    outfile = outFilePath(audio_dir, output_count)
    clip_duration = 0
    data = []
    clip_count = 0

    new_starts = []
    for subdir, dirs, files in os.walk(audio_dir):
        for i in range(0, len(files)):
            file = "chunk-%d.wav" % i
            fname = os.path.join(subdir, file)
            with contextlib.closing(wave.open(fname,'rb')) as f:
                frames = f.getnframes()
                rate = f.getframerate()
                duration = frames / float(rate)
                print ('process clip %s duration %f, current total duration %f' % (file, duration, clip_duration))
                # if concatenating next clip won't make the combined clip exceed the length limit, add the next clip
                if clip_duration + duration <= preferred_length:
                    clip_duration += duration
                    data.append( [f.getparams(), f.readframes(f.getnframes())] )
                    f.close()
                    if clip_count == 0:
                        new_starts.append(starts[i])
                        print('clip start: %f' % (new_starts[-1]))
                    clip_count += 1
                    print ('added to the previous clip %s duration %f - total duration %f' % (file, duration, clip_duration))
                else:
                    if clip_count > 0:
                        # combine the preivous clips
                        output = wave.open(outfile, 'wb')
                        output.setparams(data[0][0])
                        for params,frames in data:
                            output.writeframes(frames)
                        output.close()
                        print('combine %d clips into %s - clip_duration %f' % (clip_count, outfile, clip_duration))
                        print('\nend_at: %f\n' % (new_starts[-1] + clip_duration))
                        output_count += 1
                    outfile = outFilePath(audio_dir, output_count)
                    clip_duration = 0
                    data = []
                    clip_count = 0
                    # if the current clip is too long, slice clip into smaller pieces with equal length
                    if duration > preferred_length:
                        n = int(math.ceil(duration/preferred_length))
                        for j in range(0, n):
                            slice(f, outfile, long(j * duration / n * 1000), long((j+1) * duration / n * 1000))
                            print('slice audio %s into sub-audio %s' % (file, outfile))
                            new_starts.append(starts[i] + j * duration / n)
                            print('clip start: %f' % (new_starts[-1]))
                            output_count += 1
                            outfile = outFilePath(audio_dir, output_count)
                        print('\nend_at: %f\n' % (new_starts[-1] + duration / n))
                    else:
                        clip_duration += duration
                        data.append( [f.getparams(), f.readframes(f.getnframes())] )
                        f.close()
                        if clip_count == 0:
                            new_starts.append(starts[i])
                            print('clip start: %f' % (new_starts[-1]))
                        clip_count += 1
            os.remove(fname)
    if clip_count > 0: # combine the remaining pieces
        output = wave.open(outfile, 'wb')
        output.setparams(data[0][0])
        for params,frames in data:
            output.writeframes(frames)
        output.close()
        print('combine %d clips into %s - clip_duration %f' % (clip_count, outfile, clip_duration))
        print('\nend_at: %f\n' % (new_starts[-1] + clip_duration))
    print(str(len(new_starts)))
    return new_starts

def outFilePath(dir,output_count):
    # return "pchunk-%d.wav" % output_count
    return os.path.join(dir, "pchunk-%d.wav" % output_count)

def slice(infile, outfilename, start_ms, end_ms):
    width = infile.getsampwidth()
    rate = infile.getframerate()
    fpms = rate / 1000 # frames per ms
    length = (end_ms - start_ms) * fpms
    start_index = start_ms * fpms

    out = wave.open(outfilename, "w")
    out.setparams((infile.getnchannels(), width, rate, length, infile.getcomptype(), infile.getcompname()))

    infile.rewind()
    anchor = infile.tell()
    infile.setpos(anchor + start_index)
    out.writeframes(infile.readframes(length))