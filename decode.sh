#!/bin/bash

set -e
set -u
set -o pipefail

LD_LIBRARY_PATH="${LD_LIBRARY_PATH:-}"
PS1="${PS1:-}"
PYTHONPATH="${PYTHONPATH:-}"

file=$(realpath "$1")
language=$2
recid=$(basename "${file}" | md5sum | awk '{print $1}')

basedir=$(realpath $(dirname $0))
workdir=$(mktemp -d)
model=/home/users2/denisopl/arbeitsdaten/models/${language}

# Segment the audio
mkdir -p ${workdir}/data/${recid}
ffmpeg -i "${file}" -acodec pcm_s16le -ar 16000 -ac 1 ${workdir}/data/${recid}.wav
echo "${recid} sox ${workdir}/data/${recid}.wav -t wav -r 8k - |" > ${workdir}/data/${recid}/wav.scp
echo "${recid} ${recid}" > ${workdir}/data/${recid}/utt2spk
echo "${recid} ${recid}" > ${workdir}/data/${recid}/spk2utt
cd ${basedir}/espnet/tools/kaldi/egs/aspire/s5

steps/segmentation/detect_speech_activity.sh \
	--cmd run.pl \
	--nj 1 \
	--convert-data-dir-to-whole false \
	--graph-opts "--min-silence-duration=0.03 --min-speech-duration=0.3 --max-speech-duration=30.0" \
	--transform-probs-opts "--sil-scale=0.1" \
	--extra-left-context 79 \
	--extra-right-context 21 \
	--frames-per-chunk 150 \
	--extra-left-context-initial 0 \
	--extra-right-context-final 0 \
	--acwt 0.3 \
	${workdir}/data/${recid} \
	/home/users2/denisopl/arbeitsdaten/models/tdnn_stats_asr_sad_1a \
	${workdir}/mfcc_hires \
	${workdir}/segmentation \
	${workdir}/segmentation/${recid}

echo "${recid} ${workdir}/data/${recid}.wav" > ${workdir}/data/${recid}/wav.scp
cp ${workdir}/segmentation/${recid}_seg/segments ${workdir}/data/${recid}/
awk '{print $1" text"}' ${workdir}/data/${recid}/segments > ${workdir}/data/${recid}/text
awk '{print $1" "$1}' ${workdir}/data/${recid}/segments > ${workdir}/data/${recid}/utt2spk
cd ${basedir}

# Recognize the speech
cd ${basedir}/espnet/egs/multi_${language}/asr1/
. ./path.sh
decode_cmd=run.pl
nj=$(cat <(wc -l ${workdir}/data/${recid}/segments | awk '{print $1}') <(grep -c vendor_id /proc/cpuinfo) | sort -g | head -n1)
utils/fix_data_dir.sh ${workdir}/data/${recid}
steps/make_fbank_pitch.sh --cmd ${decode_cmd} --nj ${nj} --write_utt2num_frames true ${workdir}/data/${recid} ${workdir}/feats/${recid}
utils/fix_data_dir.sh ${workdir}/data/${recid}
dumpdir=${workdir}/dump/${recid}
dump.sh --cmd ${decode_cmd} --nj ${nj} --do_delta false ${workdir}/data/${recid}/feats.scp ${model}/cmvn.ark ${workdir}/exp/${recid} ${dumpdir}
data2json.sh --feat ${dumpdir}/feats.scp --bpecode ${model}/bpe.model ${workdir}/data/${recid} ${model}/units.txt > ${dumpdir}/data.json
splitjson.py --parts ${nj} ${dumpdir}/data.json

${decode_cmd} JOB=1:${nj} ${dumpdir}/log/decode.JOB.log \
	asr_recog.py \
		--ngpu 0 \
		--backend pytorch \
		--recog-json ${dumpdir}/split${nj}utt/data.JOB.json \
		--result-label ${dumpdir}/result.JOB.json \
		--model ${model}/asr/model.dat  \
		--beam-size 20 \
		--penalty 0.0 \
		--maxlenratio 0.0 \
		--minlenratio 0.0 \
		--ctc-weight 0.5 \
		--rnnlm ${model}/lm/model.dat \
		--lm-weight 0.5 \
		$(cat ${model}/asr_recog.conf 2>/dev/null || true)

concatjson.py ${dumpdir}/result.*.json > ${dumpdir}/result.json
json2trn.py ${dumpdir}/result.json ${model}/units.txt ${dumpdir}/ref.trn ${dumpdir}/hyp.trn
sed -i 's/<blank> //g' ${dumpdir}/hyp.trn
filt.py -v ${model}/non_lang_syms.txt ${dumpdir}/hyp.trn > ${dumpdir}/hyp.trn.filtered
spm_decode --model=${model}/bpe.model --input_format=piece < ${dumpdir}/hyp.trn.filtered | sed -e "s/▁/ /g" > ${dumpdir}/hyp.wrd.trn

perl -p -e 's/^(.*)\(.+(.{15})\)$/$2 $1/g' ${dumpdir}/hyp.wrd.trn | sort > "${file}.txt"
rm -rf ${workdir}
