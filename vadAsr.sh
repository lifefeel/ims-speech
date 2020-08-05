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
duration=40
echo 'duration=' $duration
if (( $(echo "$duration > 30.0" |bc -l) )); then
	# Segment the audio
	echo "${recid} sox ${workdir}/data/${recid}.wav -t wav -r 8k - |" > ${workdir}/data/${recid}/wav.scp

	echo "${recid} ${recid}" > ${workdir}/data/${recid}/utt2spk
	echo "${recid} ${recid}" > ${workdir}/data/${recid}/spk2utt
	#cd ${basedir}/espnet/tools/kaldi/egs/aspire/s5
	echo ' sad_nnet_dir in vad.sh = ' ${model}/tdnn_stats_asr_sad_1a 

	steps/segmentation/detect_speech_activity.sh \
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


	cp ${workdir}/segmentation/${recid}_seg/segments ${workdir}/segmentation/output_seg/
	echo ' segmentation=' ${workdir}/segmentation/output

	cp ${workdir}/segmentation/${recid}_seg/segments ${workdir}/data/${recid}/
        awk '{print $1" text"}' ${workdir}/data/${recid}/segments > ${workdir}/data/${recid}/text
        awk '{print $1" "$1}' ${workdir}/data/${recid}/segments > ${workdir}/data/${recid}/utt2spk
        utils/fix_data_dir.sh ${workdir}/data/${recid}


	##echo ' segmentation=' ${workdir}/segmentation/output
	##cp ${workdir}/segmentation/output_seg/segments ${workdir}/data/output/segments
	##awk '{print $1" text"}' ${workdir}/data/output/segments > ${workdir}/data/output/text
	##awk '{print $1" "$1}' ${workdir}/data/output/segments > ${workdir}/data/output/utt2spk
	##utils/fix_data_dir.sh ${workdir}/data/output

	#cd ${basedir}

else
	echo "${recid} ${duration}" | \
		awk '{printf("%s-%08d-%08d %s %.3f %.3f\n", $1, 0, $2 * 100, $1, 0, $2);}' \
		> ${workdir}/data/${recid}/segments
fi

echo ' End of Segmentation' 

# Recognize the speech
echo "${recid} sox ${file} -t wav -r 16k - |" > ${workdir}/data/${recid}/wav.scp
awk '{print $1" text"}' ${workdir}/data/${recid}/segments > ${workdir}/data/${recid}/text
awk '{print $1" "$1}' ${workdir}/data/${recid}/segments > ${workdir}/data/${recid}/utt2spk

##cd ${basedir}/espnet/egs/librispeech/asr1/
##. ./path.sh
decode_cmd=run.pl
nj=$(cat <(wc -l ${workdir}/data/${recid}/segments | awk '{print $1}') <(grep -c vendor_id /proc/cpuinfo) | sort -g | head -n1)


utils/fix_data_dir.sh ${workdir}/data/${recid}
steps/make_fbank_pitch.sh --cmd ${decode_cmd} --nj ${nj} --write_utt2num_frames true ${workdir}/data/${recid} ${workdir}/feats/${recid}
utils/fix_data_dir.sh ${workdir}/data/${recid}
echo ' nj = ' $nj
dumpdir=${workdir}/dump/${recid}
echo '  dumpdir=' $dumpdir
modelCmvn=../espnet/egs/korean/asr3/data/train_clean
dump.sh --cmd ${decode_cmd} --nj ${nj} --do_delta false ${workdir}/data/${recid}/feats.scp ${modelCmvn}/cmvn.ark ${workdir}/exp/${recid} ${dumpdir}
# bpemode (unigram or bpe)
nbpe=5000
#nbpe=10000
bpemode=unigram
train_set=train_clean
dict=../espnet/egs/korean/asr3/data/lang_char/${train_set}_${bpemode}${nbpe}_units.txt
bpemodel=../espnet/egs/korean/asr3/data/lang_char/${train_set}_${bpemode}${nbpe}

data2json.sh --feat ${dumpdir}/feats.scp --bpecode ${bpemodel}.model ${workdir}/data/${recid} ${dict} > ${dumpdir}/data.json
echo 'After data2json.sh   dumpdir=' $dumpdir

backend=pytorch
lmtag=lm     # tag for managing LMs
ngpu=1         # number of gpus ("0" uses cpu, otherwise use gpu
lmexpname=train_rnnlm_${backend}_${lmtag}_${bpemode}${nbpe}_ngpu${ngpu}
lmexpdir=../espnet/egs/korean/asr3/exp/${lmexpname}
lang_model=rnnlm.model.best # set a language model to be used for decoding
modelLm=${lmexpdir}/${lang_model} 

recog_model=model.val5.avg.best
expname=train_clean_pytorch_train_specaug
expdir=../espnet/egs/korean/asr3/exp/${expname}
modelAsr=${expdir}/results/${recog_model}
decode_config=conf/decode.yaml
echo ' config=' ${decode_config}
echo ' modelAsr=' ${modelAsr}
echo ' modelLm=' ${modelLm}
echo ' dumpdir=' ${dumpdir}
exit 1
asr_recog.py \
	--config ${decode_config} \
	--ngpu 0 \
	--backend pytorch \
	--batchsize 0 \
	--recog-json ${dumpdir}/data.json \
	--result-label ${dumpdir}/result.json \
	--model ${modelAsr}  \
	--rnnlm ${modelLm} \
	--api v2

json2trn.py ${dumpdir}/result.json ${model}/units.txt ${dumpdir}/ref.trn ${dumpdir}/hyp.trn
sed -i 's/<blank> //g' ${dumpdir}/hyp.trn
filt.py -v ${model}/non_lang_syms.txt ${dumpdir}/hyp.trn > ${dumpdir}/hyp.trn.filtered
spm_decode --model=${model}/bpe.model --input_format=piece < ${dumpdir}/hyp.trn.filtered | sed -e "s/▁/ /g" > ${dumpdir}/hyp.wrd.trn

perl -p -e 's/^(.*)\(.+(.{15})\)$/$2 $1/g' ${dumpdir}/hyp.wrd.trn | sort > "${file}.txt"
rm -rf ${workdir}
