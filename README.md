# IMS-Speech

### Installation

```sh
$ git clone --recurse-submodules git@clarin06.ims.uni-stuttgart.de:Pavel/ims-speech.git
```
### download modelfile from https://kaldi-asr.org/models/m4

ln -s ../espnet/egs/korean/asr3/conf  conf
ln -s ../espnet/tools/kaldi/egs/aspire/s5/utils/run.pl run.pl
ln -s ../espnet/tools/kaldi/egs/aspire/s5/utils utils
ln -s ../espnet/tools/kaldi/egs/aspire/s5/steps steps
ln -s ../espnet     espnet

### Copy Mode for VAD to dir. for VAD + ASR 
cp ./models/en/conf/mfcc_hires.conf  ./conf


##
##  VAD + ASR for each segmentation
##
### Usage 1
#### Shell Command
```sh
sh example.sh or
python wav_split2.py  file002_e
```
##### vadR1.sh 수행 : speech segmentation  VAD
##### ../espnet/egs/korean/asr3/decode.sh 수행: ASR
### Changed from Original Version
* ./steps/segmentation/detect_speech_activityVad.sh
* ./steps/make_mfccVad.sh 

#### Output
```sh
./sampleOut
   file002_eOut.txt
```
  
### Usage 2 for fast speech segmentation Only(VAD)
```sh
$ ./vadR.sh file002_e.wav
```
### Usage 3 for traditional speech segmentation Only (VAD)
```sh
$ ./vad.sh file002_e.wav
```
#### Output
./temp/segmentation/output_seg/segmentation
#####
#### 13 segmentation
50e9ae7561526f097f01d0c9c47a8de3-0000154-0000302 50e9ae7561526f097f01d0c9c47a8de3 1.54 3.02
50e9ae7561526f097f01d0c9c47a8de3-0000354-0000508 50e9ae7561526f097f01d0c9c47a8de3 3.54 5.08
50e9ae7561526f097f01d0c9c47a8de3-0000604-0000903 50e9ae7561526f097f01d0c9c47a8de3 6.04 9.04
50e9ae7561526f097f01d0c9c47a8de3-0001091-0001403 50e9ae7561526f097f01d0c9c47a8de3 10.91 14.03
50e9ae7561526f097f01d0c9c47a8de3-0001433-0001563 50e9ae7561526f097f01d0c9c47a8de3 14.33 15.63
50e9ae7561526f097f01d0c9c47a8de3-0001593-0001764 50e9ae7561526f097f01d0c9c47a8de3 15.93 17.64
50e9ae7561526f097f01d0c9c47a8de3-0001927-0002066 50e9ae7561526f097f01d0c9c47a8de3 19.27 20.66
50e9ae7561526f097f01d0c9c47a8de3-0002119-0002624 50e9ae7561526f097f01d0c9c47a8de3 21.19 26.24
50e9ae7561526f097f01d0c9c47a8de3-0002654-0002945 50e9ae7561526f097f01d0c9c47a8de3 26.54 29.45
50e9ae7561526f097f01d0c9c47a8de3-0002994-0003147 50e9ae7561526f097f01d0c9c47a8de3 29.94 31.47
50e9ae7561526f097f01d0c9c47a8de3-0003575-0003695 50e9ae7561526f097f01d0c9c47a8de3 35.75 36.95
50e9ae7561526f097f01d0c9c47a8de3-0003778-0003923 50e9ae7561526f097f01d0c9c47a8de3 37.78 39.23
50e9ae7561526f097f01d0c9c47a8de3-0003964-0004171 50e9ae7561526f097f01d0c9c47a8de3 39.64 41.71




