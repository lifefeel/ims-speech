import json
import os
import sys
import shutil
import tempfile
from zipfile import ZipFile

from pydub import AudioSegment
from pydub.silence import split_on_silence
import speech_recognition as sr

from utils import *

dir_path = './sample_data_16k/playlist_xx_test'

def split_audio(file, dest_path, use_stt=False):
    tempdir = tempfile.mkdtemp()
    vadcommand = f'./vadR1_new.sh {file} {tempdir}'
    print(vadcommand)
    os.system(vadcommand)

    # REading segmentation Result
    Segfile = open(os.path.join(tempdir, "segmentation/output_seg/segments"),'r')
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
    shutil.rmtree(tempdir)

    return outputs

files = os.listdir(dir_path)
files = sorted(files)

curdir = dir_path

for file in files:
    filename, file_extension = os.path.splitext(file)
    if file_extension != '.mp4':
        continue

    print(f'Start : {file}')

    #
    # mp4 to wav
    #
    print('\n## mp4 to wav')
    in_file = os.path.join(curdir, file)  # ~/001.mp4
    wav_file = os.path.join(curdir, f'{filename}.wav')  # ~/001.wav 
    
    if not os.path.exists(wav_file):
        ffmpeg_extract_wav(in_file, wav_file)
    else:
        print(f'File exists : {wav_file}')

    #
    # Split wav & save to json
    #
    print('\n## Split wav & save to json')
    json_file = os.path.join(curdir, f'{filename}.json')

    if not os.path.exists(json_file):
        dest_path = '/tmp/wav_split'
        createFolder(dest_path)

        outputs = split_audio(wav_file, dest_path)  # save to temporary path because of not using this time.

        for output in outputs:
            file = output['file']
            start = output['start']
            end = output['end']
            
            print(f'{file}\t{start} - {end}')
        
        save_to_json(outputs, json_file)
    else:
        print(f'File exists : {json_file}')


    #
    # Split video to 40 seconds
    #
    print('\n## Split video to 40 seconds')
    video_file = os.path.join(curdir, f'{filename}.mp4')
    
    video_split_infos = split_video(video_file, json_file)
    
    for video_split_info in video_split_infos:
        print(video_split_info)

    split_info_file = os.path.join(curdir, f'{filename}_split.json')
    if not os.path.exists(split_info_file):
        save_to_json(video_split_infos, split_info_file)

    #
    # Split sub wav file & save to json
    #
    print('\n## Split sub wav file & save to json')

    zip_file = os.path.join(curdir, f'{filename}.zip')
    if os.path.exists(zip_file):
        print(f'File exists : {zip_file}')
        continue

    subdir = os.path.join(curdir, filename)  # ~/001
    sub_files = os.listdir(subdir)
    sub_files = sorted(sub_files)

    for sub_file in sub_files:
        sub_filename, file_extension = os.path.splitext(sub_file)
        if file_extension != '.wav':
            continue

        dest_path = os.path.join(subdir, sub_filename)  # ~/001/chunk_00
        dest_files = os.listdir(dest_path) if os.path.exists(dest_path) else []
        
        if len(dest_files) > 0:
            print(f'Files esixt in dir : {dest_path}')
            continue

        createFolder(dest_path)

        inputfile = os.path.join(subdir, sub_file)  # ~/001/chunk_00.wav

        outputs = split_audio(inputfile, dest_path, use_stt=True)
        
        for output in outputs:
            file = output['file']
            start = output['start']
            end = output['end']
            text = output['text']
            
            print(f'{file}\t{start} - {end}\t\t{text}')

        json_file = os.path.join(subdir, f'{sub_filename}.json')
        save_to_json(outputs, json_file)

    #
    # Write to zip file
    #
    print('\n## Write to zip file')
    print(f'Write to : {zip_file}')

    to_delete_files = []
    with ZipFile(zip_file, 'w') as zip:
        sub_files = os.listdir(subdir)
        sub_files = sorted(sub_files)
        
        for sub_file in sub_files:
            file = os.path.join(subdir, sub_file)
            
            if not os.path.isfile(file):
                continue

            zip.write(file, arcname=f'{filename}/{sub_file}')
            to_delete_files.append(file)

    #
    # Delete files
    #
    for file in to_delete_files:
        os.remove(file)


print('Finished!')


