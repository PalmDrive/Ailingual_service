import wave
import contextlib
import math
import os

def fixClipLength(audio_dir):
    output_count = 0
    outfile = outFilePath(audio_dir, output_count)
    total_duration = 0
    data = []
    clip_count = 0
    for subdir, dirs, files in os.walk(audio_dir):
        for i in range(0, len(files)):
            file = "chunk-%d.wav" % i
            fname = os.path.join(subdir, file)
            with contextlib.closing(wave.open(fname,'rb')) as f:
                frames = f.getnframes()
                rate = f.getframerate()
                duration = frames / float(rate)
                print ('process clip %s duration %d, current total duration %d' % (file, duration, total_duration))
                if total_duration + duration <= 60: # if concatenating next clip won't make the combined clip exceed the length limit, add the next clip
                    total_duration += duration
                    data.append( [f.getparams(), f.readframes(f.getnframes())] )
                    f.close()
                    clip_count += 1
                    print ('added to the previous clip %s duration %d - total duration %d' % (file, duration, total_duration))
                else:
                    if clip_count > 0:
                        if clip_count > 1: # combine the preivous clips
                            output = wave.open(outfile, 'wb')
                            output.setparams(data[0][0])
                            for params,frames in data:
                                output.writeframes(frames)
                            output.close()
                            print('combine %d clips into %s - total_duration %d' % (clip_count, outfile, total_duration))
                        else: # just rename file when there's only one clip
                            os.rename(file, outfile)
                            print('rename file %s to %s' % (file, outfile))
                        output_count += 1
                    if duration > 60: # if the current clip is too long, slice clip into smaller pieces with equal length
                        n = int(math.ceil(duration/60))
                        for i in range(0, n):
                            slice(file, outfile, i * duration / n * 1000, (i+1) * duration / n * 1000)
                            print('slice audio %s into sub-audio %s' % (file, outfile))
                            output_count += 1
                            outfile = outFilePath(audio_dir, output_count)
                    outfile = outFilePath(audio_dir, output_count)
                    total_duration = 0
                    data = []
                    clip_count = 0
            os.remove(fname)
    if clip_count > 0: # combine the remaining pieces
        if clip_count > 1: # combine the preivous clips
            output = wave.open(outfile, 'wb')
            output.setparams(data[0][0])
            for params,frames in data:
                output.writeframes(frames)
            output.close()
            print('combine %d clips into %s - total_duration %d' % (clip_count, outfile, total_duration))
        else: # just rename file when there's only one clip
            os.rename(file, outfile)
            print('rename file %s to %s' % (file, outfile))

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