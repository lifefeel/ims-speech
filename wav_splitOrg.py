import os
from pydub import AudioSegment
from pydub.silence import split_on_silence

# file = '/Users/jplee/Dropbox/2020년/2020.05_그랜드챌린지/데이터/sample_data_16k/file003_e.wav'
file = './sample_data_16k/file001_e.wav'
file = './sample_data_16k/file001_n.wav'

def split_audio(file, dest_path='./'):
    sound_file = AudioSegment.from_wav(file)
    audio_chunks = split_on_silence(sound_file,
                                    # must be silent for at least half a second
                                    min_silence_len=500,
                                    keep_silence=True,

                                    # consider it silent if quieter than -16 dBFS
                                    silence_thresh=-35
                                    )

    start_pos = 0
    positions = []
    for i, chunk in enumerate(audio_chunks):
        duration = chunk.duration_seconds
        end_pos = start_pos + duration
        out_file = os.path.join(dest_path, "chunk_{:02d}.wav".format(i))
        print(f"exporting : {out_file}, {start_pos} - {end_pos}")
        chunk.export(out_file, format="wav")

        positions.append((start_pos, end_pos))
        start_pos = end_pos

    return positions

positions = split_audio(file)

for start, end in positions:
    print(f'{start} - {end}')
