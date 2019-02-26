#!/usr/bin/env python3

import asyncio
import json
import websockets
import subprocess
import os
import urllib
import hashlib
import fcntl

connected = dict()

async def decode(websocket, path):
    model = dict(urllib.parse.parse_qsl(urllib.parse.urlsplit(path).query))['model']
    datadir = os.path.dirname(os.path.realpath(__file__)) + '/data'
    os.makedirs(datadir, exist_ok=True)

    data = connected[websocket]['audio']
    recid = hashlib.sha3_256(data).hexdigest()
    datafile = datadir + '/' + recid + '.' + connected[websocket]['options']['content-type'].split('/')[-1]
    textfile = datafile + '.txt'
    lockfile = datafile + '.lock'

    with open(lockfile, 'wb') as lf:
        fcntl.flock(lf, fcntl.LOCK_EX)

        if not os.path.isfile(textfile):
            with open(datafile, 'wb') as df:
                df.write(data)

            subprocess.run(
                f'echo ./decode.sh {datafile} {model} | /mount/arbeitsdaten41/projekte/asr-2/denisopl/gentoo-sumpfweihe/startprefix',
                shell=True, capture_output=True
            )

        fcntl.flock(lf, fcntl.LOCK_UN)

    rindex = 0

    with open(textfile, encoding='utf-8') as f:
        for l in f:
            transcript = ''
            results = {
                'results': [
                    {
                        'word_alternatives': [],
                        'keywords_result': {},
                        'alternatives': [{'timestamps': [], 'confidence': 1.0}],
                        'final': True
                    }
                ],
                'result_index': rindex
            }

            words = l.strip().split(' ')
            start = float(words[0][-17:-9])
            end = float(words[0][-8:])

            for word in words[1:]:
                transcript += ' ' + word

                results['results'][0]['word_alternatives'].append({
                    'start_time': start,
                    'end_time': end,
                    'alternatives': [{'confidence': 1.0, 'word': word}]
                })

                results['results'][0]['alternatives'][0]['timestamps'].append([word, start, end])

            results['results'][0]['alternatives'][0]['transcript'] = transcript.strip()

            await websocket.send(json.dumps(results))
            rindex += 1

async def handler(websocket, path):
    # Register.
    connected[websocket] = dict()
    connected[websocket]['audio'] = b''

    try:
        async for message in websocket:
            if type(message) is str:
                m = json.loads(message)
                if m['action'] == 'stop':
                    await decode(websocket, path)
                    break
                else:
                    if m['action'] == 'start':
                        connected[websocket]['options'] = m
                    await websocket.send('{"state":"listening"}')


            elif type(message) is bytes:
                connected[websocket]['audio'] += message

    finally:
        # Unregister.
        del connected[websocket]

start_server = websockets.serve(handler, 'localhost', 8765)

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()
