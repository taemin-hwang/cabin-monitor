import wave
import os, sys

import whisper

class Voice:
    def __init__(self):
        self.channels = 1
        self.rate = 16000
        self.record_seconds = 5
        self.filename = 'tmp.wav'
        self.model = whisper.load_model("small")

    def __del__(self):
        print('destroy speech manager')

    def init(self):
        print('initialize speech manager')
        self.kakao.init()

    def shutdown(self):
        print('shutdown speech manager')

    def get_voice(self):
        print('get text from voice')
        #arecord -r16000 -c1 -twav -fS16_LE -Dplughw:2,0 test16k.wav
        command = 'arecord '
        command += '-r'+str(self.rate)+' '
        command += '-c'+str(self.channels)+' '
        command += '-twav '
        command += '-fS16_LE '
        command += '-Dplughw:2,0 '
        command += '-d'+str(self.record_seconds)+' '
        command += self.filename

        os.system(command)
        # text = self.kakao.get_text_from_wav(self.filename)
        # text = self.kakao.get_text_from_wav("./src/service/kakao/heykakao.wav")
        result = self.model.transcribe("./src/service/heykakao.wav", language="ko")
        text = result["text"]
        print('STT result : ' + text)

        if text != 'no such file':
            os.remove(self.filename)

        return text