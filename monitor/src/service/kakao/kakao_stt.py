import requests
import json

class KakaoStt:
    def __init__(self):
        pass

    def init(self):
        print('initialize kakao stt')
        self.kakao_speech_url = "https://kakaoi-newtone-openapi.kakao.com/v1/recognize"
        self.rest_api_key = '89265aa43ac1b275d068d8acae36b70f'
        self.headers = {
            "Content-Type": "application/octet-stream",
            "X-DSS-Service": "DICTATION",
            "Authorization": "KakaoAK " + self.rest_api_key,
        }

    def get_text_from_wav(self, filename):
        print('read wav file from ' + filename)

        try:
            fp = open(filename, 'rb')
            audio = fp.read()
        except:
            print('cannot open ' + filename)
            text = 'error'
            return text

        res = requests.post(self.kakao_speech_url, headers=self.headers, data=audio)
        print(res.text)

        if res.text.find('finalResult') > 0:
            print(res.text)
            result_json_string = res.text[res.text.index('{"type":"finalResult"'):res.text.rindex('}')+1]
            result = json.loads(result_json_string)
            print(result['value'])
            text = result['value']
        else:
            text = 'error'

        return text