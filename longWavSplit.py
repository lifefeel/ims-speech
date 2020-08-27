import os
import sys
import shutil
from pydub import AudioSegment
from pydub.silence import split_on_silence

# file = '/Users/jplee/Dropbox/2020년/2020.05_그랜드챌린지/데이터/sample_data_16k/file003_e.wav'
datadirIn='./sample_data_16k/eighteen2/'
fileInDir='./sample_data_16k/eighteen2/'
datadirOut='../espnet/egs/korean/asr3/downloads/KoreanSpeech/test/test_01/'
wavtype='.wav'
#file = './sample_data_16k/file001_e.wav'
#file = 'file001_n'
#Dir. for Output file

fileIn = sys.argv[1]
print (fileInDir + fileIn)
#file = './sample_data_16k/file002_e.wav'
#file = './sample_data_16k/file003_e.wav'

def createFolder(directory):
    try:
        if not os.path.exists(directory) :
            os.makedirs(directory)
        else:
            shutil.rmtree(directory)
            os.makedirs(directory)

    except OSError:
        print("Error: Creating directory" + directory)

# splint long wave file into many dir with some files
def split_audio(file, dest_path, dest_pathOrg='./sample_data_16k'):

    vadcommand = "./vadR1.sh  " + file
    print(vadcommand)
    os.system(vadcommand)

    # REading segmentation Result
    Segfile = open("./temp/segmentation/output_seg/segments",'r')
    i=0
    dur=0.0
    old_endmsec=0.0
    max_silDur = max_voiceDur = 0.0
    SegDur={}
    VoDur = {}
    while True:
        line = Segfile.readline()
        if not line:
            break
        words = line.split()
        startmsec = float(words[2])
        endmsec = float(words[3])
        silDur = startmsec - old_endmsec
        if silDur > max_silDur :
            max_silDur = silDur
        voiceDur = endmsec - startmsec
        if voiceDur > max_voiceDur:
            max_voiceDur = voiceDur
        dur = dur + silDur + voiceDur
        SegDur[i]=silDur
        VoDur[i] = voiceDur
        old_endmsec = endmsec
        i = i + 1
    Segfile.close()
    ## Duration from Sound File
    sound_file = AudioSegment.from_wav(file)
    DurSound = len(sound_file)
    print("DurSound=", DurSound, )

    SegNumf = float(DurSound) / 40000.0
    if SegNumf - int(SegNumf) > 0.5:
        SegNum = int(SegNumf) + 1
    else :
        SegNum = int(SegNumf)
    print("Maximun seg number=",i,"DurSound=",DurSound, "Recomended SegNum=",SegNum, SegNumf,"max_voiceDur=",max_voiceDur, "max_silDur=",max_silDur)

    # Sorted by higher value
    res = sorted(SegDur.items(),key=(lambda x:x[1]),reverse = True)
    ##print(res)
    SegInf = {}
    i=0
    for i in range(SegNum):
        SegInf[res[i][0]] = res[i][1]
    # Sorted by lower key
    res1 = sorted(SegInf.items())
    ##print(res1)

    i=0
    sdur =0.0
    tdur = 0.0
    dirNum=0
    lSeg ={}
    lSegSil={}
    for key,value in res1 :
        while  i < key :
            sdur = sdur + VoDur[i] + SegDur[i]
            #print("sdur=",sdur)
            i = i + 1
        # For Segmented file of 40 sec
        lSeg[dirNum]= sdur + SegDur[key]/2.0
        lSegSil[dirNum] = SegDur[key]

        sdur = sdur + SegDur[key] + VoDur[key]

        dirNum = dirNum + 1
        i = i + 1
    #print("sdur=", sdur)
    startDur=0.0
    lSegDur={}
    for i in range(dirNum):
        lSegDur[i]= lSeg[i]  - startDur
        #print("lSeg[",i,"]=",lSeg[i], "lSegDur=",lSegDur[i],"lSegSil=",lSegSil[i])
        print("lSeg[%3d]= %8.2f lSegDur= %8.2f lSegSil= %8.2f" %(i, lSeg[i],lSegDur[i],lSegSil[i]))
        startDur = lSeg[i]
    DurSound = int(DurSound/10)
    fDurSound = float(DurSound) / 100.0
    lSegDur[dirNum] = fDurSound - startDur
    lSeg[dirNum] = fDurSound
    print("Last Seg= %8.2f SegDur= %8.2f " %(fDurSound, lSegDur[dirNum]))

    ## Reduced Segmented File to approximated 40 sec
    finalSeg = {}
    sdur = 0.0
    finalNum=0
    mergeFlag=0
    for i in range(dirNum+1):
        if lSegDur[i] < 20.0: # Merge to next Seg file
            if mergeFlag == 1 : # For continual Flag = 1
                sdur = lSegDur[i] + sdur
            else: # First Flag=1
                sdur = lSegDur[i]
                mergeFlag=1
        else:
            if mergeFlag == 1 : # Add sdur to Current
                finalSeg[finalNum] = lSeg[i]
                finalNum = finalNum + 1
                sdur = 0.0
                mergeFlag = 0
            else:
                finalSeg[finalNum] = lSeg[i]
                finalNum = finalNum + 1
    print( "finalNum of Segmentation = ",finalNum, " From ",dirNum+1)
    finalDur ={}
    startDur = 0.0
    for i in range(finalNum ):
        finalDur[i]= finalSeg[i] - startDur
        ##print("temp final Seg[",i,"]=",finalSeg[i],finalDur[i])
        startDur = finalSeg[i]

    for i in range(finalNum,0,-1) :
        finalSeg[i] = finalSeg[i-1]
    finalSeg[0] = 0.0

    ##for i in range(finalNum):
        ##print("final Seg[", i, "]=", finalSeg[i], finalDur[i])



    positionsWave = []
    positionsFlac = []
    i=0
    for i in range(finalNum):

        out_filewav = os.path.join(dest_pathOrg, "file_{:02d}.wav".format(i))

        #print(out_filewav, finalSeg[i], finalDur[i])


        startmsec= int(finalSeg[i]*100)
        endmsec = int(finalDur[i]*100)

        finalSeg[i] = startmsec / 100.0
        finalDur[i] = endmsec / 100.0

        #print(out_filewav, finalSeg[i], finalDur[i])

        positionsWave.append((out_filewav, finalSeg[i], finalDur[i]))

        seg_sound = sound_file[startmsec:endmsec]
        seg_sound.export(out_filewav, format="wav")

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

##for file,start, end in positions:
    ##print(file,"  ",f'{start} - {end}')


resultfilenameOut= fileInDir + fileIn + 'Out.txt'
fp = open(resultfilenameOut,"w",encoding='utf-8')

for file,start, end in positions:
    txtout = file + "  " + str(start) + ' - ' + str(end)
    print (txtout)
    txtout = txtout + '\n'
    fp.write(txtout)

fp.close()


