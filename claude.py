from datetime import datetime
import os
import re
from time import sleep
import uuid
import requests
import tls_client
import json
from twocaptcha import TwoCaptcha

from gmail import temp_mail


class CustomException(Exception):
    def __init__(self, message):
        self.message = message

    def getJSON(self):
        if type(self.message) is dict:
            return self.message
        return {'message': self.message, "success": False}

    def __str__(self):
        return self.getJSON()['message']


class Claude:
    def __init__(self):
        self.sessionKey = None
        self.organizationId = None
        self.cookies = None
        self.recaptcha_code = None
        self.recent_conversations = None
        self.solver = TwoCaptcha(os.getenv("TwoCaptcha_API_KEY"))
        self.client = tls_client.Session(
            client_identifier="chrome112",
            random_tls_extension_order=True,
            debug=False
        )

    def scraperapi(self, email):
       # https://claude.ai/api/auth/send_code
        home = "https://dashboard.scraperapi.com/signup"
        session = requests.Session()
        response = session.get(home)
        print(response.cookies)
        url = "https://backend.scraperapi.com/users/sign-up/email"
        token = self.recaptcha_token(
            home, "6LfHgrYaAAAAAF2IC1gk2ACNLIEs9vBBtMJToNZz")
        payload = {
            "email": email,
            "password": "mohtasm10QQ@@",
            "token": token
        }
        headers = {
            'Content-Type': 'application/json',
        }
        response = session.post(url, headers=headers, json=payload)
        if response.text.find('sendActivationEmail') != -1:
            payload = {"email": email}
            url = "https://backend.scraperapi.com/users/sendActivationEmail"
            response = session.post(url, headers=headers, json=payload)
            print(response.text)
        else:
            print(response.text)
        return response

    def verify_code(self, email, code):
        # https://claude.ai/api/auth/send_code
        url = "https://claude.ai/api/auth/verify_code"
        payload = {
            "email_address": email,
            "code": code,
            "recaptcha_token": self.recaptcha_code,
            "recaptcha_site_key": "6LcdsFgmAAAAAMfrnC1hEdmeRQRXCjpy8qT_kvfy",
            "source": "claude"
        }
        headers = {
            'Content-Type': 'application/json',
        }
        print(payload)
        # session = requests.Session()
        # response = session.post(url, headers=headers, data=payload)
        response = self.client.post(url, headers=headers, json=payload)
        return response

    def recaptcha_token(self, url=None, site_key="6LcdsFgmAAAAAMfrnC1hEdmeRQRXCjpy8qT_kvfy"):
        if self.recaptcha_code:
            return self.recaptcha_code
        if not url:
            url = "https://claude.ai/login"
        token = self.solver.recaptcha(
            sitekey=site_key, url=url, enterprise=0, version="v3")
        code = token["code"]
        print(code)
        self.recaptcha_code = code
        return code

    def send_code(self, payload):
        url = "https://claude.ai/api/auth/send_code"
        if type(payload) is str:
            self.recaptcha_token(url)
            payload = {
                "email_address": payload,
                "recaptcha_token": self.recaptcha_code,
                "recaptcha_site_key": "6LcdsFgmAAAAAMfrnC1hEdmeRQRXCjpy8qT_kvfy",
                "source": "claude"
            }
        headers = {
            'Content-Type': 'application/json',
        }
        print(payload)
        response = self.client.post(url, headers=headers, json=payload)
        j = response.json()
        print(j)
        return j

    def get_key(self, playload):
        if type(playload) is str:
            email = playload
        else:
            self.recaptcha_code = playload["recaptcha_token"]
            email = playload["email_address"]
        code = self.send_code(playload)
        temp = temp_mail(email)
        if code["success"]:
            while True:
                code = temp.getMessages("support@mail.anthropic.com")
                if code:
                    code = code[0]
                    res = self.verify_code(email, code)
                    print(res.headers)
                    print(res.cookies)
                    print(res.json())
                    if res.status_code != 200:
                        return None
                    self.cookies = []
                    for c in res.cookies:
                        self.cookies.append(
                            {'name': c.name, 'value': c.value,
                                'domain': c.domain, 'path': c.path}
                        )
                    print(self.cookies)
                    self.sessionKey = res.cookies.get('sessionKey')
                    print(self.sessionKey)
                    return self.sessionKey
                sleep(3)

    def login2(self, code, google="verify_code"):
        google = "verify_google"
        headers = {
            "Content-Type": "application/json",
        }
        res = self.client.post(
            "https://claude.ai/api/auth/"+google, json=code, headers=headers)
        self.cookies = []
        for c in res.cookies:
            self.cookies.append(
                {'name': c.name, 'value': c.value,
                    'domain': c.domain, 'path': c.path}
            )
        self.sessionKey = res.cookies.get('sessionKey')
        print(self.sessionKey)
        return self.sessionKey

    class Conversation:
        def __init__(self, claude, args={}):
            self.claude = claude
            self.conversationId = args.get('conversationId', None)
            self.id = args.get('id', None)
            self.updated_at = args.get('updated_at', None)
            self.created_at = args.get('created_at', None)
            self.summary = args.get('summary', None)
            self.name = args.get('name', None)
            # print(args)
            self.request = claude.request
            # uuid.uuid4()

        def delete(self, args={}):
            response = self.claude.request(f"/api/organizations/{self.claude.organizationId}/chat_conversations/{self.conversationId}", {
                "headers": {
                    "Accept": "*/*",
                    "Cookie": "sessionKey="+self.claude.sessionKey
                },
                "method": "DELETE",
            })
            return response

        def sendMessage(self, message, args={}):
            if not message:
                raise CustomException("Message cannot be empty")
            attachments = args.get('attachments', [])
            timezone = args.get('timezone', "America/New_York")
            model = args.get('model', "claude-2")
            response = self.claude.request("/api/append_message", {
                "headers": {
                    "Accept": "text/event-stream,text/event-stream",
                    "Content-Type": "application/json",
                    "Cookie": "sessionKey="+self.claude.sessionKey
                },
                "method": "POST",
                "data": {
                    "organization_uuid": self.claude.organizationId,
                    "conversation_uuid": self.conversationId,
                    "text": message,
                    "attachments": attachments,
                    "completion": {
                        "prompt": message,
                        "timezone": timezone,
                        "model": model,
                    }
                }
            })
            response["id"] = self.conversationId
            return response

    def request(self, endpoint, options={}):
        url = 'https://claude.ai' + endpoint
        headers = options.get('headers', {
            "Content-Type": "application/json",
            "Cookie": "sessionKey="+self.sessionKey
        })
        headers["origin"] = 'https://claude.ai'
        data = options.get('data', "{}")
        accept = headers.get('Accept', 'application/json')
        headers["Accept"] = accept
        data = json.dumps(data)
        method = options.get('method', "GET")
        # print(url)
        if method == "DELETE":
            response = self.client.delete(url, headers=headers)
        elif method == "GET":
            response = self.client.get(url, headers=headers)
        else:
            response = self.client.post(url, headers=headers, data=data)

            # print(response)
        if accept == "application/json":
            response = response.json()
            # print(response)
            if "error" in response:
                message = response.get("detail", response["error"])
                message["endpoint"] = url
                # print(response)
                # print(data)
                raise CustomException(message)
        elif accept == "text/event-stream,text/event-stream":
            str = response.text
            regex = r"data: {.*}$"
            matches = re.findall(regex, str, re.MULTILINE)
            if len(matches) == 0:
                response = response.json()
                message = response.get("detail", response["error"])
                raise CustomException(message)
            data = []
            for match in matches:
                match = match.replace("data: ", "").strip()
                response = json.loads(match)
                data.append(response["completion"])
            response["completion"] = "".join(data)
        return response

    def init(self, sessionKey=None):
        if sessionKey:
            self.sessionKey = sessionKey
        if not self.sessionKey:
            raise CustomException("Session key not found")
        organizations = self.getOrganizations()
        if "error" in organizations:
            message = organizations.get("detail", organizations["error"])
            raise CustomException(message)
        self.organizationId = organizations[0]["uuid"]
        self.recent_conversations = self.getConversations()
        recent_conversations = self.recent_conversations
        for convo in recent_conversations[:5]:
            if self.check_date(convo.created_at):
                # print(convo.created_at)
                self.recent_conversations.remove(convo)
                convo.delete()
        return {"success": True, "organizationId": self.organizationId, "recent_conversations": self.recent_conversations}

    def startConversation(self, message, args={}):
        response = self.request(f"/api/organizations/{self.organizationId}/chat_conversations", {
            "method": 'POST',
            "data": {
                "name": "",
                "uuid": str(uuid.uuid4()),
            }
        })
        convoID = response["uuid"]
        convo = self.Conversation(
            self, {"conversationId": convoID, **response})
        conversation = convo.sendMessage(message, args)
        response = self.request("/api/generate_chat_title", {
            "method": 'POST',
            "data": {
                "organization_uuid": self.organizationId,
                "conversation_uuid": convoID,
                "message_content": message,
                "recent_titles": list(map(lambda x: x.name, self.recent_conversations))[-3:],
            }
        })
        conversation["title"] = response["title"]
        return conversation

    def getOrganizations(self):
        response = self.request("/api/organizations")
        return response

    def setSessionKey(self, sessionKey):
        self.sessionKey = sessionKey

    def getConversation(self, id):
        conversation = filter(
            lambda x: x.id == id or x.name == id, self.recent_conversations)
        conversation = list(conversation)
        if len(conversation) > 0:
            return conversation[0]
        raise CustomException("Conversation not found")

    def getConversations(self):
        response = self.request(
            f"/api/organizations/{self.organizationId}/chat_conversations")
        if "error" in response:
            message = response.get("detail", response["error"])
            raise CustomException(message)
        response = map(lambda convo: self.Conversation(
            self, {"conversationId": convo["uuid"], **convo, "id": convo["uuid"]}), response)
        response = list(response)
        return response

    def check_date(self, date_string):
        try:
            # date_string = "2023-08-22T21:38:19.452627+00:00"
            date_object = datetime.strptime(
                date_string, "%Y-%m-%dT%H:%M:%S.%f%z")
            if date_object.date() < datetime.today().date():
                # print('Date:', date_object.date())
                # print('Time:', date_object.time())
                # print('Date-time:', date_object)
                return True
        except ValueError:
            pass
            # raise CustomException("Invalid date")
        return False


claude = Claude()
# claude.send_code("YalegoGihuwico@outlook.com")
# print(claude.check_date("2023-08-22T21:38:19.452627+00:00"))
# claude.scraperapi("mohtasmtk@gmail.com")
# claude.recaptcha_token()
# claude.get_key("guhaciju@gmail.com")
# claude.login()
# try:
#     # claude.setSessionKey(
#     #   "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")
#     # claude.sessionKey = "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"
# sessionKey = "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"
# #     sessionKey = "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"
# # sessionKey = "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"
# claude.init(sessionKey)
#     # conversation = claude.startConversation("what is your name?")
#     conversation = claude.getConversation(
#         "3238f4df-0ddb-4ec3-b43d-88098b5b2acc")
#     conversation = conversation.delete()
#     print(conversation)
# except Exception as e:
#     print(e)
