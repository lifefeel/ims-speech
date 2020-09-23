import json
import os
import sys
import shutil
from pydub import AudioSegment
from pydub.silence import split_on_silence
import speech_recognition as sr

dir_path = './sample_data_16k/playlist_xx'

def save_to_json(data, filename='data.json'):
    if filename[-4:] != 'json':
        filename += '.json'

    with open(f'{filename}', 'w', encoding='utf-8') as fw:
        json.dump(data, fw, indent=4, ensure_ascii=False)


def createFolder(directory):
    try:
        if not os.path.exists(directory) :
            os.makedirs(directory)
        else:
            shutil.rmtree(directory)
            os.makedirs(directory)

    except OSError:
        print("Error: Creating directory" + directory)


def recognize(file):
    r = sr.Recognizer()
    test_speech = sr.AudioFile(file)
    with test_speech as source:
        # r.adjust_for_ambient_noise(source)
        audio = r.record(source)
    result = r.recognize_google(audio, language='ko-KR', show_all=True)

    return result


def split_audio(file, dest_path):

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
        
        result = recognize(out_filewav)
        transcript = result['alternative'][0]['transcript'] if len(result) > 0 else ''
            
        output = {}
        output['file'] = out_filewav
        output['start'] = str(words[2])
        output['end'] = str(words[3])
        output['text'] = transcript
        
        outputs.append(output)
        
        i = i+1
        
    Segfile.close()

    return outputs


dirs = os.listdir(dir_path)
dirs = sorted(dirs)

for dir in dirs:
    curdir = os.path.join(dir_path, dir)
    if not os.path.isdir(curdir):
        continue

    files = os.listdir(curdir)
    files = sorted(files)

    for file in files:
        filename, file_extension = os.path.splitext(file)
        if file_extension != '.wav':
            continue

        # Dir for wave file
        dest_path = os.path.join(curdir, filename)
        createFolder(dest_path)
        
        inputfile = os.path.join(curdir, file)

        outputs = split_audio(inputfile, dest_path)
        
        for output in outputs:
            file = output['file']
            start = output['start']
            end = output['end']
            text = output['text']
            
            print(f'{file}\t{start} - {end}\t\t{text}')

        json_file = os.path.join(curdir, f'{filename}.json')
        save_to_json(outputs, json_file)
