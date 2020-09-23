import json
import os
import sys
import shutil
from pydub import AudioSegment
from pydub.silence import split_on_silence

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

        out_filewav = os.path.join(dest_path, "chunk_{:03d}.wav".format(i))
        
        startmsec= int(float(words[2])*1000)
        endmsec = int(float(words[3])*1000)

        seg_sound = sound_file[startmsec:endmsec]
        seg_sound.export(out_filewav, format="wav")
            
        output = {}
        output['file'] = out_filewav
        output['start'] = str(words[2])
        output['end'] = str(words[3])
        
        outputs.append(output)
        
        i = i+1
        
    Segfile.close()

    return outputs


files = os.listdir(dir_path)
files = sorted(files)

for file in files:
    curdir = dir_path
    filename, file_extension = os.path.splitext(file)
    if file_extension != '.wav':
        continue

    # Dir for wave file
    dest_path = '/tmp/wav_split'
    createFolder(dest_path)

    inputfile = os.path.join(curdir, file)

    outputs = split_audio(inputfile, dest_path)

    for output in outputs:
        file = output['file']
        start = output['start']
        end = output['end']
        
        print(f'{file}\t{start} - {end}')
        
    json_file = os.path.join(curdir, f'{filename}.json')
    save_to_json(outputs, json_file)

print('Finished!')


