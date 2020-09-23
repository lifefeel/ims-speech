import json
import os
import sys
import shutil
from pydub import AudioSegment
from pydub.silence import split_on_silence
import speech_recognition as sr

from utils import *

dir_path = './sample_data_16k/playlist_xx'

def split_audio(file, dest_path, use_stt=False):

    vadcommand = "./vadR1.sh  " + file
    print(vadcommand)
    os.system(vadcommand)

    # REading segmentation Result
    Segfile = open("./temp/segmentation/output_seg/segments",'r')
    sound_file = AudioSegment.from_wav(file)
    outputs = []
    
    i=0
    while True:
        line = Segfile.readline()
        if not line:
            break
        words = line.split()

        out_filewav = os.path.join(dest_path, "chunk_{:02d}.wav".format(i))
        
        startmsec= int(float(words[2])*1000)
        endmsec = int(float(words[3])*1000)

        seg_sound = sound_file[startmsec:endmsec]
        seg_sound.export(out_filewav, format="wav")
            
        output = {}
        output['file'] = out_filewav
        output['start'] = str(words[2])
        output['end'] = str(words[3])

        if use_stt:
            result = recognize(out_filewav)
            transcript = result['alternative'][0]['transcript'] if len(result) > 0 else ''

            output['text'] = transcript
        
        outputs.append(output)
        
        i = i+1
        
    Segfile.close()

    return outputs

files = os.listdir(dir_path)
files = sorted(files)

curdir = dir_path

for file in files:
    filename, file_extension = os.path.splitext(file)
    if file_extension != '.mp4':
        continue

    print(file)

    #
    # mp4 to wav
    #
    in_file = os.path.join(curdir, file)  # ~/001.mp4
    wav_file = os.path.join(curdir, f'{filename}.wav')  # ~/001.wav 
    ffmpeg_extract_wav(in_file, filename)  # filename + '.wav'

    #
    # Split wav & save to json
    #
    dest_path = '/tmp/wav_split'
    createFolder(dest_path)

    outputs = split_audio(wav_file, dest_path)  # save to temporary path because of not using this time.

    for output in outputs:
        file = output['file']
        start = output['start']
        end = output['end']
        
        print(f'{file}\t{start} - {end}')
        
    json_file = os.path.join(curdir, f'{filename}.json')
    save_to_json(outputs, json_file)

    #
    # Split video to 40 seconds
    #
    video_file = os.path.join(curdir, f'{filename}.mp4')
    
    split_video(video_file, json_file)


    #
    # Split sub wav file & save to json
    #
    subdir = os.path.join(curdir, filename)  # ~/001
    sub_files = os.listdir(subdir)
    sub_files = sorted(sub_files)

    for sub_file in sub_files:
        filename, file_extension = os.path.splitext(sub_file)
        if file_extension != '.wav':
            continue

        dest_path = os.path.join(subdir, filename)  # ~/001/chunk_01
        createFolder(dest_path)

        inputfile = os.path.join(subdir, sub_file)  # ~/001/chunk_01.wav

        outputs = split_audio(inputfile, dest_path, use_stt=True)
        
        for output in outputs:
            file = output['file']
            start = output['start']
            end = output['end']
            text = output['text']
            
            print(f'{file}\t{start} - {end}\t\t{text}')

        json_file = os.path.join(subdir, f'{filename}.json')
        save_to_json(outputs, json_file)


    break

print('Finished!')


