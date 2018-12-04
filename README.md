# IMS-Speech

### Installation

```sh
$ git clone --recurse-submodules git@clarin06.ims.uni-stuttgart.de:Pavel/ims-speech.git
$ rsync -av /mount/arbeitsdaten/asr-2/denisopl/espnet-pytorch/tools/ ims-speech/espnet/tools/
$ rsync -av /mount/arbeitsdaten/asr-2/denisopl/espnet-pytorch/src/utils/kaldi_io_py.py ims-speech/espnet/src/utils/
```

### Usage

```sh
$ ims-speech/decode.sh somefile.wav # Transcription will be stored to somefile.wav.txt
```

