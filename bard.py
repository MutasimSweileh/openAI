import urllib.parse
import json
import re
import uuid
import requests
import tls_client


class CustomException(Exception):
    def __init__(self, message):
        self.message = message

    def getJSON(self):
        if type(self.message) is dict:
            return self.message
        return {'message': self.message, "success": False}

    def __str__(self):
        return self.getJSON()['message']


class Bard:
    def __init__(self):
        self.sessionKey = None
        self.cookies = 'SID=Zgjehk9Szy4yAnKqK5LkeTxEHHrPDb75LRJ3p6zvB2CTMBO7t8BaBcKiUGRI-W5Ljj6cew.; __Secure-1PSID=Zgjehk9Szy4yAnKqK5LkeTxEHHrPDb75LRJ3p6zvB2CTMBO7-yffvrd728sTgRkC2GS1dA.; __Secure-3PSID=Zgjehk9Szy4yAnKqK5LkeTxEHHrPDb75LRJ3p6zvB2CTMBO7fVZe-T8452ECLiMH4QWQhA.; HSID=AoXbZvVpgFE-InmJQ; SSID=A911RevnyLBjtsYO2; APISID=yZosJXsMzy5uZvXY/AMsvWDKn-OG34q2c1; SAPISID=R9wPhsO3158b7SVc/A3Hh1jE8_GWeeo3-G; __Secure-1PAPISID=R9wPhsO3158b7SVc/A3Hh1jE8_GWeeo3-G; __Secure-3PAPISID=R9wPhsO3158b7SVc/A3Hh1jE8_GWeeo3-G; SEARCH_SAMESITE=CgQI_pgB; OGPC=19036484-1:19022519-1:19031986-1:; 1P_JAR=2023-08-17-19; AEC=Ad49MVEaWPRfIyWjyUtxffeG9Laj1v29IVTPTIbJdGTiEUfFamix4-5DQMg; NID=511=dRYe4O92DN38wiN-aoUXv2Dt9SL7ESB0CvCuliPGRYt0vUGcAOhP8I_FylPdfcRIX6o8emdM5szLUCFgYHvmdwg2f19TtcLxaVmpXAb_ebT_ueUrrlKgQ-T-hVMY7Uav2UAZhnyKyHRPnGZUWKj7s0piue5bRKqUGHT165CzXYqieHH5iiXS-FhD_Www_X9FlAMeOniLZh9oqO8nXzN-dY7oj8sZcQZhBehhpL5ez_qIfxq4KxAMmjqcP1a6VZbwa3FBcIf8td61HrI9Igq42i_fz7kTrTphKW4ivx5fE1uE1SVXaCKJ_izAHQxKUZR_9cOdHH5pUO_HeN1tqUP3Krwku6gEbJId8c5VKN7s; __Secure-1PSIDTS=sidts-CjIBSAxbGcqkqhPl-FH3KD_JD0m7Mhh4m5T3YTgEsAPaAhPjnS-OmfuUcmzR9d6LawO8wRAA; __Secure-3PSIDTS=sidts-CjIBSAxbGcqkqhPl-FH3KD_JD0m7Mhh4m5T3YTgEsAPaAhPjnS-OmfuUcmzR9d6LawO8wRAA; SIDCC=APoG2W-8tUz-D6s8zd1nb2bBdy1I2OvD2q632S4UR9C2h2y9LAZhYYIBfWJ40kBzpO5PXAQEp4s; __Secure-1PSIDCC=APoG2W_h2f4qAqyskPhUa-P30khFSn7NSC3vJGb5QmxicBPxgthtiREB-JSejzLReBWxHsQomQ; __Secure-3PSIDCC=APoG2W8k9tH-qXxun-qcix7u7ocD5k73Ym0jnxsuJ-jR7dCWmM4rt09mhsHevvOftAhDFL7ebJw'
        self.recent_conversations = None
        self.client = tls_client.Session(
            client_identifier="chrome112",
            random_tls_extension_order=True
        )

    def request(self, endpoint=None, options={}):

        headers = {
            # "Content-Type": "application/json",
            "Cookie": self.cookies
        }
        url = "https://bard.google.com/"
        if endpoint:
            url = url + endpoint
        headers = {**headers, **options.get('headers', {})}
        headers["origin"] = 'https://bard.google.com/'
        data = options.get('data', "{}")
        # data = json.dumps(data)
        method = options.get('method', "GET")
        # print(options)
        # print(url)
        # print(data)
        if method == "GET":
            # headers.pop("Content-Type", None)
            response = self.client.get(url, headers=headers)
        else:
            response = self.client.post(url, headers=headers, data=data)
        str = response.text
        # print(str)
        op = open("bard.html", "w", encoding="utf-8")
        op.write(str)
        op.close()
        regex = r"data: {.*}$"
        if not endpoint:
            regex = r"SNlM0e\":\"(.*?)\""
            m = re.search(regex, str)
            if not m:
                message = "Could not get Google Bard."
                raise CustomException(message)
            return m.group(1)
        return str

    def init(self, cookies=None):
        if cookies:
            self.cookies = cookies
        if not self.cookies:
            raise CustomException("Cookies not found")
        self.sessionKey = self.request()
        return {"success": True, "sessionKey":  self.sessionKey}

    def getConversations(self):
        conversations = self.request(
            "/conversations?offset=0&limit=28&order=updated")
        conversations = conversations["items"]
        return conversations

    def send_message(self, message, ids={}):
        if not self.sessionKey:
            raise ValueError("Make sure to call Bard.init(SESSION_ID) first.")
        params = {
            "bl": "boq_assistant-bard-web-server_20230815.13_p1",
            "_reqID": str(ids["_reqID"]) if ids.get("_reqID") else "0",
            "rt": "c",
        }
        if len(message) > 10000:
            raise CustomException(
                "Google Bard currently only supports maximum context length up to 10000 characters.")
        message_struct = [
            [message],
            None,
            list(ids.values())[:3] if ids else [None, None, None],
        ]
        data = {
            "f.req": json.dumps([None, json.dumps(message_struct)]),
            "at": self.sessionKey,
        }
        url = "_/BardChatUi/data/assistant.lamda.BardFrontendService/StreamGenerate"
        for key, value in params.items():
            url += "&" if url.find("?") != -1 else "?"
            url += f"{key}={value}"
        response_data = self.request(url, {
            "method": "POST",
            "data": data,
        })
        try:
            chat_data = json.loads(response_data.split("\n")[3])[0][2]
        except Exception as e:
            raise CustomException(
                f"Google Bard encountered an error {str(e)}.")
        if not chat_data:
            raise CustomException(
                f"Google Bard encountered an error {response_data}.")
        parsed_chat_data = json.loads(chat_data)
        bard_response_data = json.loads(chat_data)[4][0]
        text = bard_response_data[1][0]
        images = [
            {
                "tag": x[2],
                "url": x[3][0][0],
                "source": {
                    "original": x[0][0][0],
                    "website": x[1][0][0],
                    "name": x[1][1],
                    "favicon": x[1][3]
                }
            } for x in bard_response_data[4]
        ] if bard_response_data[4] else None

        data = {
            "content": self.format_markdown(text, images),
            "images": images,
            "ids": {
                "conversationID": parsed_chat_data[1][0],
                "responseID": parsed_chat_data[1][1],
                "choiceID": parsed_chat_data[4][0][0],
                "_reqID": int(ids.get("_reqID", 0)) + 100000,
            },
        }
        return data

    def format_markdown(text, images):
        if not images:
            return text

        for image_data in images:
            formatted_tag = f"!{image_data['tag']}({image_data['url']})"
            text = text.replace(image_data['tag'], formatted_tag)

        return text

    def getConversation(self, id):
        conversation = filter(
            lambda x: x["id"] == id or x["title"] == id, self.recent_conversations)
        conversation = list(conversation)
        if len(conversation) > 0:
            conversationID = conversation[0]["id"]
            conversation = self.request(
                "/conversation/"+conversationID)
            return conversation
        raise CustomException("Conversation not found")


chatgpt = Bard()
sessionKey = "SID=Zgjehk9Szy4yAnKqK5LkeTxEHHrPDb75LRJ3p6zvB2CTMBO7t8BaBcKiUGRI-W5Ljj6cew.; __Secure-1PSID=Zgjehk9Szy4yAnKqK5LkeTxEHHrPDb75LRJ3p6zvB2CTMBO7-yffvrd728sTgRkC2GS1dA.; __Secure-3PSID=Zgjehk9Szy4yAnKqK5LkeTxEHHrPDb75LRJ3p6zvB2CTMBO7fVZe-T8452ECLiMH4QWQhA.; HSID=AoXbZvVpgFE-InmJQ; SSID=A911RevnyLBjtsYO2; APISID=yZosJXsMzy5uZvXY/AMsvWDKn-OG34q2c1; SAPISID=R9wPhsO3158b7SVc/A3Hh1jE8_GWeeo3-G; __Secure-1PAPISID=R9wPhsO3158b7SVc/A3Hh1jE8_GWeeo3-G; __Secure-3PAPISID=R9wPhsO3158b7SVc/A3Hh1jE8_GWeeo3-G; SEARCH_SAMESITE=CgQI_pgB; OGPC=19036484-1:19022519-1:19031986-1:; AEC=Ad49MVEaWPRfIyWjyUtxffeG9Laj1v29IVTPTIbJdGTiEUfFamix4-5DQMg; NID=511=dRYe4O92DN38wiN-aoUXv2Dt9SL7ESB0CvCuliPGRYt0vUGcAOhP8I_FylPdfcRIX6o8emdM5szLUCFgYHvmdwg2f19TtcLxaVmpXAb_ebT_ueUrrlKgQ-T-hVMY7Uav2UAZhnyKyHRPnGZUWKj7s0piue5bRKqUGHT165CzXYqieHH5iiXS-FhD_Www_X9FlAMeOniLZh9oqO8nXzN-dY7oj8sZcQZhBehhpL5ez_qIfxq4KxAMmjqcP1a6VZbwa3FBcIf8td61HrI9Igq42i_fz7kTrTphKW4ivx5fE1uE1SVXaCKJ_izAHQxKUZR_9cOdHH5pUO_HeN1tqUP3Krwku6gEbJId8c5VKN7s; 1P_JAR=2023-08-17-20; __Secure-1PSIDTS=sidts-CjIBSAxbGThXIK9hvRlMgM8Pr71mdziAs7mwGL8fViwci7kj-XqhOd8bsftUjZ-ui4sBEBAA; __Secure-3PSIDTS=sidts-CjIBSAxbGThXIK9hvRlMgM8Pr71mdziAs7mwGL8fViwci7kj-XqhOd8bsftUjZ-ui4sBEBAA; SIDCC=APoG2W-zOc1y7a2o2zUv4-ad0JpzM_M48x1110m4mURJ96w7ppiEqICxX4bwspSY2pNyPfOakh8; __Secure-1PSIDCC=APoG2W9zcKkfEDsHvH4vBWpoRYQWOY8s7ETvrJqW4o4RdyCgUULvW5LKUM_sTTszhvbuFYug-Q; __Secure-3PSIDCC=APoG2W_CJtqxC99a0nXvtG9VL03KMbd_L2NGdvFEKgFSzf0BZa29xvKHPq9YidyTuhYav6_y_0"
chatgpt.init(sessionKey)
conversation = chatgpt.send_message("how to speak english?")
# conversation = chatgpt.getConversation("66ba097c-8a5e-4479-8681-85f23078a7e8")
# conversation = chatgpt.send_message("Hello World!")
print(conversation)
