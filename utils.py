import ffmpeg
import json
import os
import shutil
import speech_recognition as sr

def ffmpeg_extract_wav(input_path, output_path):
    input_stream = ffmpeg.input(input_path)

    output_wav = ffmpeg.output(input_stream.audio, output_path, acodec='pcm_s16le', ac=1, ar='16k')
    output_wav.overwrite_output().run()


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


def recognize(file):
    r = sr.Recognizer()
    test_speech = sr.AudioFile(file)
    with test_speech as source:
        # r.adjust_for_ambient_noise(source)
        audio = r.record(source)
    result = r.recognize_google(audio, language='ko-KR', show_all=True)

    return result


def trim(input_path, output_path, start=30, end=60):
    input_stream = ffmpeg.input(input_path)

    vid = (
        input_stream.video
        .trim(start=start, end=end)
        .setpts('PTS-STARTPTS')
    )
    aud = (
        input_stream.audio
        .filter_('atrim', start=start, end=end)
        .filter_('asetpts', 'PTS-STARTPTS')
    )

    joined = ffmpeg.concat(vid, aud, v=1, a=1).node
    output = ffmpeg.output(joined[0], joined[1], output_path + ".mp4", strict='-2')
    output_wav = ffmpeg.output(aud, output_path + ".wav", acodec='pcm_s16le', ac=1, ar='16k')
    output.run()
    output_wav.overwrite_output().run()


def split_video(video_file, split_info_file, split_seconds=40.0):
    try:
        with open(split_info_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        print('file not exist :', split_info_file)
        return

    new_start = None
    new_end = 0.0
    file_idx = 0
    outputs = []
    output = {}

    dir_path = os.path.dirname(video_file)
    filename, file_extension = os.path.splitext(os.path.basename(video_file))

    out_path = os.path.join(dir_path, filename)
    print(f'out_path : {out_path}')

    try:
        os.mkdir(out_path)
    except FileExistsError:
        pass

    for i, elem in enumerate(data):
        file_path = elem['file']
        start = float(elem['start'])
        end = float(elem['end'])

        if not new_start:
            new_start = new_end

        if end - new_start >= split_seconds:
            try:
                next_start = float(data[i + 1]['start'])
            except IndexError:
                print('no next file.')
                next_start = end

            new_end = end + (next_start - end) / 2

            out_filename = f'chunk_{file_idx:02d}'
            out_file = os.path.join(out_path, out_filename)
            out_file_wav = f'{out_file}.wav'

            if not os.path.exists(out_file_wav):
                trim(video_file, out_file, start=new_start, end=new_end)
            else:
                print(f'File exists : {out_file_wav}')

            output['file'] = out_file_wav
            output['start'] = f'{new_start:.2f}'
            output['end'] = f'{new_end:.2f}'
            outputs.append(output)

            file_idx += 1
            new_start = None
            output = {}

    if new_start:
        out_filename = f'chunk_{file_idx:02d}'
        out_file = os.path.join(out_path, out_filename)
        out_file_wav = f'{out_file}.wav'

        if not os.path.exists(out_file_wav):
            trim(video_file, out_file, start=new_start, end=end)
        else:
            print(f'File exists : {out_file_wav}')

        output['file'] = out_file_wav
        output['start'] = f'{new_start:.2f}'
        output['end'] = f'{new_end:.2f}'
        outputs.append(output)

    return outputs