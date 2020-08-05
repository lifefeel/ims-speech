#!/bin/bash

. ./path.sh || exit 1;
. ./cmd.sh || exit 1;

set -e
set -u
set -o pipefail

LD_LIBRARY_PATH="${LD_LIBRARY_PATH:-}"
PS1="${PS1:-}"
PYTHONPATH="${PYTHONPATH:-}"

file=$(realpath "$1")
#language=$2
recid=$(basename "${file}" | md5sum | awk '{print $1}')
#recid=local

basedir=$(realpath $(dirname $0))
#workdir=$(mktemp -d)
workdir=./temp
#model=$workdir/models/${language}
model=./models

# Remove old dir
if [ -e ${workdir}/data ]; then
        rm -rf ${workdir}/data
        echo ' removed ' ${workdir}/data
fi

if [ -e ${workdir}/mfcc_hires ]; then
        rm -rf ${workdir}/mfcc_hires
        echo ' removed ' ${workdir}/mfcc_hires
fi

if [ -e ${workdir}/segmentation ]; then
        rm -rf ${workdir}/segmentation
        echo ' removed ' ${workdir}/segmentation
fi

echo ' ** data dir=' ${workdir}/data/${recid}
if [ -e ${workdir}/data/${recid} ]; then
        rm -rf ${workdir}/data/${recid}
        echo ' removed ' ${workdir}/data/${recid}
fi
# Segment the audio
mkdir -p ${workdir}/data/${recid}
echo 'workdir='${workdir}
echo ${recid}
ffmpeg -i "${file}" -acodec pcm_s16le -ar 16000 -ac 1 ${workdir}/data/${recid}.wav 2>&1 
#duration=$(
	#ffmpeg -i "${file}" -acodec pcm_s16le -ar 16000 -ac 1 ${workdir}/data/${recid}.wav 2>&1 | \
	#grep Duration )
	#grep Duration | \
	#perl -p -e 'my ($h, $m, $s) = ($_ =~ /(\d\d):(\d\d):(\d\d\.\d\d)/); $_ = $h * 3600 + $m * 60 + $s;'
	#perl -p -e ' ($h, $m, $s) = ($_ =~ /(\d\d):(\d\d):(\d\d\.\d\d)/); '
#)
#echo 'duration=' $duration

Fromdate=`date "+%s"`
echo ' From date=' $Fromdate
duration=40
if (( $(echo "$duration > 30.0" |bc -l) )); then
	# Segment the audio
	echo "${recid} sox ${workdir}/data/${recid}.wav -t wav -r 8k - |" > ${workdir}/data/${recid}/wav.scp
	echo "${recid} ${recid}" > ${workdir}/data/${recid}/utt2spk
	echo "${recid} ${recid}" > ${workdir}/data/${recid}/spk2utt
	#cd ${basedir}/espnet/tools/kaldi/egs/aspire/s5
	echo ' sad_nnet_dir in vad.sh = ' ${model}/tdnn_stats_asr_sad_1a 

	steps/segmentation/detect_speech_activityVad.sh \
		--cmd run.pl \
		--nj 1 \
		--convert-data-dir-to-whole false \
		--graph-opts "--min-silence-duration=0.5 --min-speech-duration=1.0 --max-speech-duration=30.0" \
		--transform-probs-opts "--sil-scale=0.1" \
		--extra-left-context 79 \
		--extra-right-context 21 \
		--frames-per-chunk 150 \
		--extra-left-context-initial 0 \
		--extra-right-context-final 0 \
		--acwt 0.3 \
		--merge-consecutive-max-dur 10.0 \
		--segment_padding 0.1 \
		${workdir}/data/${recid} \
		${model}/tdnn_stats_asr_sad_1a \
		${workdir}/mfcc_hires \
		${workdir}/segmentation \
		${workdir}/segmentation/${recid}

	mkdir -p ${workdir}/segmentation/output_seg
	cp ${workdir}/segmentation/${recid}_seg/segments ${workdir}/segmentation/output_seg/
        echo ' segmentation=' ${workdir}/segmentation/output_seg

        cp ${workdir}/segmentation/${recid}_seg/segments ${workdir}/data/${recid}/
        ##awk '{print $1" text"}' ${workdir}/data/${recid}/segments > ${workdir}/data/${recid}/text
        ##awk '{print $1" "$1}' ${workdir}/data/${recid}/segments > ${workdir}/data/${recid}/utt2spk
        ##utils/fix_data_dir.sh ${workdir}/data/${recid}


else
	echo "${recid} ${duration}" | \
		awk '{printf("%s-%08d-%08d %s %.3f %.3f\n", $1, 0, $2 * 100, $1, 0, $2);}' \
		> ${workdir}/data/${recid}/segments
fi

	Todate=`date "+%s"`
	Dur=`echo "($Todate - $Fromdate)" | bc`
	echo 'Duration='  $Dur
