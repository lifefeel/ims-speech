import json
import os
import sys
import shutil
from pydub import AudioSegment
from pydub.silence import split_on_silence

# file = '/Users/jplee/Dropbox/2020년/2020.05_그랜드챌린지/데이터/sample_data_16k/file003_e.wav'
datadirIn='./sample_data_16k/'
datadirOut='../espnet/egs/korean/asr3/downloads/KoreanSpeech/test/test_01/'
wavtype='.wav'
#file = './sample_data_16k/file001_e.wav'
#file = 'file001_n'
#Dir. for Output file
fileInDir='./sampleOut/'
fileIn = sys.argv[1]
print (fileInDir + fileIn)
#file = './sample_data_16k/file002_e.wav'
#file = './sample_data_16k/file003_e.wav'

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


def split_audio(file, dest_path, dest_pathOrg='./sample_data_16k'):

    vadcommand = "./vadR1.sh  " + file
    print(vadcommand)
    os.system(vadcommand)

    # REading segmentation Result
    Segfile = open("./temp/segmentation/output_seg/segments",'r')
    sound_file = AudioSegment.from_wav(file)
    positionsWave = []
    positionsFlac = []
    i=0
    while True:
        line = Segfile.readline()
        if not line:
            break
        words = line.split()

        out_filewav = os.path.join(dest_pathOrg, "chunk_{:02d}.wav".format(i))
        out_fileflac = os.path.join(dest_path, "chunk_{:02d}.flac".format(i))
        out_filetxt = os.path.join(dest_path, "chunk_{:02d}.txt".format(i))
        #print(out_file, words[2], words[3])
        positionsWave.append((out_filewav,words[2], words[3]))
        positionsFlac.append((out_fileflac,words[2], words[3]))
        startmsec= int(float(words[2])*1000)
        endmsec = int(float(words[3])*1000)

        seg_sound = sound_file[startmsec:endmsec]
        seg_sound.export(out_filewav, format="wav")
        seg_sound.export(out_fileflac, format="flac")
        with open(out_filetxt,"w") as ftxt :
            ftxt.write("실험 평가\n")
        i = i+1
    Segfile.close()

    return positionsWave

dest_path = datadirOut + fileIn + '01'
createFolder(datadirOut)
inputfile= datadirIn + fileIn + wavtype
print('inputfile=',inputfile,'dest_path=',dest_path)

createFolder(dest_path)

# Dir for wave file
des_dir_wav=fileInDir + fileIn +'Dir'
createFolder(des_dir_wav)

positions = split_audio(inputfile,dest_path,des_dir_wav)
nj = len(positions)

for file,start, end in positions:
    print(file,"  ",f'{start} - {end}')


output_list = []
for file,start, end in positions:
    elem = {}
    elem['file'] = file
    elem['start'] = str(start)
    elem['end'] = str(end)
    
    output_list.append(elem)
    
resultfilenameOut = fileInDir + fileIn + 'Out.json'
save_to_json(output_list, resultfilenameOut)




