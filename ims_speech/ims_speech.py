import os
import subprocess
from pydub import AudioSegment


def split_audio_ims_speech(file, dest_path, use_stt=False, ims_speech_path='ims-speech'):
    dest_path = os.path.abspath(dest_path)
    current_dir = os.getcwd()
    os.chdir(ims_speech_path)

    vad_file = './vadR1_new.sh'
    result = subprocess.run([vad_file, file, dest_path], capture_output=True, text=True)

    # print(result.stdout)
    print(result.stderr)

    os.chdir(current_dir)

    # Reading segmentation Result
    with open(os.path.join(dest_path, "segmentation/output_seg/segments"), 'r') as seg_file:
        sound_file = AudioSegment.from_wav(file)
        outputs = []

        for i, line in enumerate(seg_file):
            if not line:
                break
            words = line.split()

            out_filewav = os.path.join(dest_path, "chunk_{:02d}.wav".format(i))

            startmsec = int(float(words[2]) * 1000)
            endmsec = int(float(words[3]) * 1000)

            seg_sound = sound_file[startmsec:endmsec]
            seg_sound.export(out_filewav, format="wav")

            output = {}
            output['file'] = out_filewav
            output['start'] = str(words[2])
            output['end'] = str(words[3])

            if use_stt:
                result = recognize_google(out_filewav)
                transcript = result['alternative'][0]['transcript'] if len(result) > 0 else ''

                output['text'] = transcript

            outputs.append(output)
        print(f'segments count : {len(outputs)}')
    return outputs
