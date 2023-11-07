import wave
import os, sys
import logging
import logger

from service.kakao import kakao_stt

class VoiceManager:
    def __init__(self):
        self.logger = logging.getLogger('log')
        self.kakao = kakao_stt.KakaoStt()
        self.channels = 1
        self.rate = 16000
        self.record_seconds = 5
        self.filename = 'tmp.wav'

    def __del__(self):
        self.logger.info('destroy speech manager')

    def init(self):
        self.logger.info('initialize speech manager')
        self.kakao.init()

    def run(self):
        self.logger.info('run speech manager')
        self.kakao.run()

    def shutdown(self):
        self.logger.info('shutdown speech manager')

    def get_text_from_voice(self):
        self.logger.info('get text from voice')
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
        text = self.kakao.get_text_from_wav(self.filename)
        #text = self.kakao.get_text_from_wav("heykakao.wav")

        self.logger.info('STT result : ' + text)

        if text != 'no such file':
            os.remove(self.filename)

        return text