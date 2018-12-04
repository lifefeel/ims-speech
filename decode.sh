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
segmenter=${basedir}/kaldi-offline-transcriber
recognizer=${basedir}/espnet
workdir=${segmenter}/build
model=/home/users2/denisopl/arbeitsdaten/models/${language}

# Segment the audio
mkdir -p ${workdir}/audio/base
sox "${file}" -c 1 -b 16 ${workdir}/audio/base/${recid}.wav rate -v 16k
cd ${segmenter}
make build/trans/${recid}/utt2spk
sed -i -e 's! build/! '${workdir}'/!g' build/trans/${recid}/wav.scp
nj=$(wc -l ${workdir}/trans/${recid}/segments | awk '{print $1}')
awk '{print $1" example"}' ${workdir}/trans/${recid}/segments > ${workdir}/trans/${recid}/text
cd ${basedir}

# Recognize the speech
cd ${recognizer}/egs/multi_${language}/asr1/
. ./path.sh
. ./cmd.sh
utils/fix_data_dir.sh ${workdir}/trans/${recid}
steps/make_fbank_pitch.sh --cmd ${decode_cmd} --nj ${nj} --write_utt2num_frames true ${workdir}/trans/${recid} ${workdir}/feats/${recid}
utils/fix_data_dir.sh ${workdir}/trans/${recid}
dumpdir=${workdir}/dump/${recid}
dump.sh --cmd ${decode_cmd} --nj ${nj} --do_delta false ${workdir}/trans/${recid}/feats.scp ${model}/cmvn.ark ${workdir}/exp/${recid} ${dumpdir}
data2json.sh --feat ${dumpdir}/feats.scp --bpecode ${model}/bpe.model ${workdir}/trans/${recid} ${model}/units.txt > ${dumpdir}/data.json
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

perl -p -e 's/^(.*)\(.+(.{17})\)$/$2 $1/g' ${dumpdir}/hyp.wrd.trn | sort > "${file}.txt"
rm -rf ${workdir}/audio/base/${recid}.wav ${workdir}/*/${recid}
