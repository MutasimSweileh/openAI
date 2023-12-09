import base64
import hashlib
import json
import os
import re
import uuid
import requests
import tls_client
from twocaptcha import TwoCaptcha


class ChatGPT:
    def __init__(self):
        self.sessionKey = None
        self.arkose_token = None
        self.recent_conversations = None
        self.client = tls_client.Session(
            client_identifier="chrome112",
            random_tls_extension_order=True
        )

    class CustomException(Exception):
        def __init__(self, message):
            self.message = message

        def getJSON(self):
            if type(self.message) is dict:
                return self.message
            return {'message': self.message, "success": False}

        def __str__(self):
            return self.getJSON()['message']

    def generate_code_verifier(self):
        # 随机生成一个长度为 32 的 code_verifier
        token = os.urandom(32)
        code_verifier = base64.urlsafe_b64encode(token).rstrip(b'=')
        return code_verifier.decode('utf-8')

    def generate_code_challenge(self, code_verifier):
        # 对 code_verifier 进行哈希处理，然后再进行 base64url 编码，生成 code_challenge
        m = hashlib.sha256()
        m.update(code_verifier.encode('utf-8'))
        code_challenge = base64.urlsafe_b64encode(m.digest()).rstrip(b'=')
        return code_challenge.decode('utf-8')

    def refresh_access_token(self, refresh_token):
        url = "https://auth0.openai.com/oauth/token"
        payload = json.dumps({
            "redirect_uri": "com.openai.chat://auth0.openai.com/ios/com.openai.chat/callback",
            "grant_type": "refresh_token",
            "client_id": "pdlLIX2Y72MIl2rhLhTE9VV9bN905kBh",
            "refresh_token": refresh_token
        })
        headers = {}
        headers["Content-Type"] = "application/json"
        session = requests.Session()
        response = session.post(url, headers=headers, data=payload)
        json_response = response.json()
        # print(json_response)
        return json_response

    def get_access_token(self, username, password=None):
        if not password:
            password = username
        code_verifier = self.generate_code_verifier()
        code_challenge = self.generate_code_challenge(code_verifier)
        print("code_verifier: ", code_verifier)
        print("code_challenge: ", code_challenge)
        url = "https://ai.fakeopen.com/auth/preauth"
        response = requests.request("GET", url)
        json_data = json.loads(response.text)
        preauth_cookie = json_data["preauth_cookie"]
        print("preauth_cookie: ", preauth_cookie)
        url = f"https://auth0.openai.com/authorize?client_id=pdlLIX2Y72MIl2rhLhTE9VV9bN905kBh&audience=https%3A%2F%2Fapi.openai.com%2Fv1&redirect_uri=com.openai.chat%3A%2F%2Fauth0.openai.com%2Fios%2Fcom.openai.chat%2Fcallback&scope=openid%20email%20profile%20offline_access%20model.request%20model.read%20organization.read%20offline&response_type=code&code_challenge={code_challenge}&code_challenge_method=S256&prompt=login&preauth_cookie={preauth_cookie}"
        session = requests.Session()
        response = session.get(url)
        if response.status_code == 429:
            raise self.CustomException("Too many requests")
        url = response.url
        headers = response.headers
        # print("status_code: ", response.status_code, "url: " + url)
        state = url.split("state=")[1]
        payload = {
            'state': state,
            'username': username,
            'js-available': True,
            'webauthn-available': True,
            'webauthn-platform-available': True,
            'is-brave': False,
            'action': "default",
        }
        headers = {}
        headers["Content-Type"] = "application/x-www-form-urlencoded"
        response = session.post(
            url, data=payload, headers=headers)
        url = response.url
        if response.status_code == 429:
            raise self.CustomException("Too many requests")
        # print("status_code: ", response.status_code, "url: " + url)
        state = url.split("state=")[1]
        payload = {
            'state': state,
            'username': username,
            'password': password,
            'action': "default",
        }
        headers["Content-Type"] = "application/x-www-form-urlencoded"
        try:
            response = session.post(url, headers=headers,
                                    data=payload)
            # print(response.text)
        except Exception as e:
            e = str(e)
            e = e.split("code=")[1].strip("'")
            code = e
        url = "https://auth0.openai.com/oauth/token"
        payload = json.dumps({
            "redirect_uri": "com.openai.chat://auth0.openai.com/ios/com.openai.chat/callback",
            "grant_type": "authorization_code",
            "client_id": "pdlLIX2Y72MIl2rhLhTE9VV9bN905kBh",
            "code": code,
            "code_verifier": code_verifier
        })
        headers["Content-Type"] = "application/json"
        response = session.post(url, headers=headers, data=payload)
        json_response = response.json()
        # print(json_response)
        return json_response

    def request(self, endpoint, options={}):
        try:
            api = "/backend-api" if endpoint.find(
                "api") == -1 else ""
            url = f"https://chat.openai.com{api}" + endpoint
            if endpoint.find("http") != -1:
                url = endpoint
            # print(url)
            headers = {
                "Content-Type": "application/json",
                "Authorization": "Bearer "+self.sessionKey
            }
            headers = {**headers, **options.get('headers', {})}
            headers["origin"] = 'https://chat.openai.com/'
            data = options.get('data', "{}")
            accept = headers.get('Accept', 'application/json')
            headers["Accept"] = accept
            data = json.dumps(data)
            method = options.get('method', "GET")
            # print(options)
            if method == "GET":
                response = self.client.get(url, headers=headers)
            else:
                response = self.client.post(url, headers=headers, data=data)
                # print(response)
            if accept == "application/json":
                response = response.json()
                if "detail" in response or "error" in response:
                    message = response.get("detail", response.get("error"))
                    raise self.CustomException(message)
            else:
                result = response.text
                # print(response.status_code)
                # print(result)
                regex = r"data: {.*}$"
                matches = re.findall(regex, result, re.MULTILINE)
                if len(matches) == 0:
                    response = response.json()
                    message = response.get("detail", response.get("error"))
                    raise self.CustomException(message)
                matches = filter(lambda x: x.find("error") != -1, matches)
                # matches = filter(lambda x: x.find("content") != -1, matches)
                matches = list(matches)
                match = matches[-1]
                match = match.replace("data: ", "").strip()
                response = json.loads(match)
                if "message" in response and not response["message"]:
                    message = response.get("detail", response.get("error"))
                    raise self.CustomException(message)

            return response
        except Exception as e:
            print(e)
            raise self.CustomException(str(e))

    def init(self, sessionKey=None):
        if sessionKey:
            self.sessionKey = sessionKey
        if not self.sessionKey:
            raise self.CustomException("Session key not found")
        self.recent_conversations = self.getConversations()
        return {"success": True, "recent_conversations": self.recent_conversations}

    def getConversations(self):
        conversations = self.request(
            "/conversations?offset=0&limit=5&order=updated")
        conversations = conversations["items"]
        return conversations

    def conversation_limit(self):
        conversations = self.request(
            "/public-api/conversation_limit")
        return conversations

    def get_openai_token(self):
        # if self.arkose_token:
        #     return self.arkose_token
        solver = TwoCaptcha('9234cf1ef978837f23f917b9d9cb0541')
        surl = "https://tcr9i.chat.openai.com"
        pkey = "35536E1E-65B4-4D96-9D97-6ADB7EFF8147"
        url = "https://chat.openai.com"
        result = solver.funcaptcha(sitekey=pkey,
                                   url=url,
                                   surl=surl)
        result = result["code"]
        print(result)
        self.arkose_token = result
        return result

    def get_token(self):
        url = "https://tcr9i.chat.openai.com/fc/gt2/public_key/35536E1E-65B4-4D96-9D97-6ADB7EFF8147"
        payload = 'public_key=35536E1E-65B4-4D96-9D97-6ADB7EFF8147&site=https%3A%2F%2Fchat.openai.com%2F&userbrowser=Mozilla%2F5.0%20(Windows%20NT%2010.0%3B%20Win64%3B%20x64)%20AppleWebKit%2F537.36%20(KHTML%2C%20like%20Gecko)%20Chrome%2F118.0.0.0%20Safari%2F537.36&capi_version=1.5.2&capi_mode=lightbox&style_theme=default&rnd=0.6021469417347318&bda=eyJjdCI6ImlTRlNZY2RqOGFEYXo3d1U2NnBIUVVGc2s5QS9icmdtRXZYNC9tRTVSOGZLNW96UGZhZU5zeWRYOGtkRzB1NklKSG5XOEZIRGxCbWI2MnZBNHZnUFZkN0t2Z2pjc2hXbGo4Z2YvcDdrTThBRDNPa3FGUk80d3pyT29hdm1iWUlRSFc0YWFoM3RGa0xUcGJRZVNhQWV0YjdQZ2JOQjdJZ1pkTkU1MWttckg4QlpqY09YTHo0N2tUbnBMeXlYN3dJcjVUYm4vbjVDL0MvOVBITC9mY016cm1WR3NFNE9XUnhWeFVveTZ1ZlVQcitWN2pHTkJFdUNVTXBTUm4xaEdsb0dhWUg5NGhVcVFJRkpueGc1dlhMUmpidHN1K244ZkZvNWR3eldZNU4rb1F2a09kai91aEg3Y0ZqOUJKM0NLSjVwYWVWNU9RaTUya0gwMWQzS1JXckZZU1ppVkdnV3B2MThkMUR2bkFGOEJyOFRXYyt4d2NLdVJBZHZRbkRvSGhORlRSaDFZOFhyVngwc3NPbkdYaHNwVjRWeTNiYmtBZzJObHNHOEtVNkJQQTgxTEw4MW56dU0ySVczMENKNHhhRmIrZDFIMnNWYlJldDg2N3BSV2pDOVdGNDhEYzliK3hEeW9JZThsZDRhUFpEYVZBTVpBRk9KNTN2c2M4MVUrWC9yV0Q3RWpZV1EreFRER2VFcElKT0I5RExRVXYvdFJmbzZ2dVdqTTJsd3Z4L2l1azNEKzBmSjF5aTdpR2p0UnM2cWtmcjhYcStyQzVyd3JjYVdVL3dxZnhDV28yblRVbXJITk4vZUsrM0g2eVBIck1xeUdsQmVTQTlZcWIyWXFGTmcwMVh2eGtQcHNSL3NIYnI2MjJLNWFLNkp4OUNFWUdxdkxIZGdwaHZZc1I3emJWWEwyZ0grQVRWekZNWnEyamlvNHl3WWJHUjIvcTlNajQ0M1grNTBsQThXbnFERWszbUpLd0ZaZDdTemNSQStoUGtyZ0d2SG1BbkFCNmw4TGNwUTdxL0s4TkwxSzRaUHFQTVYvTENrNnRPb1NnQXpjM3ZWc2hYMllQQjFvUDZhY2Z1MnB4aFA5VE0zZnZLYnFCazB5N2wwZzZESGI0cVptdTNxdmxpTnJUeHA2czZuNlFqSDlSeWpFTDF3R2pTeDVPclRxOFJLMWxwY3lNb0hBNEtENVcxTjBDVmZlY2czdWUxWURqYlZ3UGZJTWIyY3k3SXdjTkVGdHhldFFxaGRNS1VXZUV4ajFjUnJ3UnRLVW11NEhLWmpEYThhcDlqNXpvdWtOSVVhSmlkUUhrTnJqUTBoNGlUYUt5K3BoUHkxTW9MZWJFaWxaam5aOFhoNERGaHVHL25VTVVIZmZpMGhBVmNubU5UMFZLTXZ0dERSWWluQ2xmNVJnVlp5cFlGVk5RcC91em9WbnRRbkNSSUxUWkpVaWhDckZrWVNLQTZYZHczMVljQWE5M3pFTVIzSDJXMDRDMWhGelVMSXR6R2dLWGFLNzh6UXpvLzNyZWVoTElUTFVNZmRUTTlnQzVTYmlKMHBxam91R3QraGxPNm5qTytuYnRCMFZTVFFVcEZSZXFmNzYxZHN2S1dFRHJjUEdLN0JwVzRoMEJBN0pZdWM5OEZHSTI0Ulh3S01tcDQ1b1N2WFBSc2kvWlRaT3FNZnB1MllGODZrRlNtZ3FyZmhCZlpsR2VYV1lUbGN6cGoyRWNWVnlJWlBycFp4dzZEOUozaTR4eXFZNDJoU0pUaFVBNGlETGF0SkgxN1Z5MUt0WUdtZjQ2VVBCTDUvL3dHNks0OFMxUjZzYkQxZ09NZGdXMlMvWloxRkQxZE1jY0NiZWlEeWYvVWw4ekppZzJHZ3hZOXNXajN2YnNKNXhEd0E4VU95QXgya09GekFOdkVMam9qcURaN2JLVHo5M2srZ0Rsb3IxeTlXWmZmOUI0bVZlZU12d1N2d0plSE1hWVR5aGZzZGUyOGZXSUE2L2kwV0k4Q2dpRHlPU1VXcHZsenJJL0x6OThyWGVOQUtqODVKNDlpN3FENkpUWFN5NUtqckNhNlhzWGFxcWgxQ3hSQ0NCU1VrWFMybUN0dXd2VzVrREprKzg5bldPQjVsRU0yeHV1cWNoS3Y4WjZrdmgwcW1UaDZBSHQ1Q1VwSHBpSFI2aXJiYTV5UkpDd1pwa0w2VmZ2b2NFcGRJbkpXS3pJRmhTUG9LYUsrZjVDL1VOMTJaMzJZdFVtbGNhV0hKZUVCOHNxVHp3ajRqTE94QU10SEswZnN2SHQrcHZjd3ZjUG1VdHpHRXhCRno5K09DOXVrK3A1RkxmY3Y1cWg4ZE1uaEkybW5hMytoNjBWd0V1NEJTZmxNSy9BTE5TaitTeVUyVDNKT3BFZFd4TS8raGJGRGxibXZhWlFiYmR3REVTT3YzK1pIZU9ZSXF3V21LVVdaSWhxakY5bkw0dWtmdUhIRjdoMnNPVnRpKzF2OEV1cWptYTErYTJMdmt3Ujh2bTFOVlJxZUtBLzRkcUpaaENKYTlsaXVkTUQ0VExrK1FhQkNnaDQwSWh2VVR4QWxaUzljNG1oTzU2eEVnTWJSZGx5N0hmNGVIdVBmblB6UEpyaGtHVTM1NVNPSlBYb3FyU0hMUzNaM0taOHFZQVFSOXBNSmJWNkJPK1NOQ21LVmxmdjRrZVR6ZzNSTk96OFFzb1FGNTh4MFg3aWJzTEQwL05VSmQwWkV4eGdDRFRmcHRiZUJIVG1Walk3Y2hQZDlIYjJGQ05hS2dFWlRyLzRzUFNqZlBUTTdLRjQrekNWZEZGN1NnZXpQQlVubTRoQTB5Q0ZsUW1zZ3Q0bTg5UnZZZ2F4ZWU3Z1ZlUU5CTkwvZ09UZDlWRllEQlJFenVlcHgrYlZaaURxVjljaFAvM2NYQjd0MWxKOFNYZ1d0WW1TdFJ1NGQ5bWRRZWF6eVhuWXQwNGtGcG9URDhuc2M4eTR3c3pOZlhrbWY3U2RqWDVaQjFmNlBmR2JoUEpDOEFTOG1SdUZLNHQxY3JNWFBqWTNUdU9BMVVtUjFWTzFBeFZ0TFlXSllkLzkrcU0xS2pydURSQmcvMCtPNTdpeTJ5UnZsY2xPVU9NVUlVSG5zNnk2UW1iVjQrOEoyVWQzZnM4YWZJY3JjVkVZeWh1cEtpWkRyWEJmeGo3UzEzbWFsbTE0WFpYR2RxSmFWeEVCYmxBeC9hTUgyMldCcmZScUFTVkRsLzFwOWxQQWpnZVgxR1JUcFNVQlU0NjVxVHY0WEppQjIzYU9EeFpUOVlUSTEvTklzaHo0RmpwVUxpcFRBTUtQRWwydUtsdkJzUFJLNDJwSkw4cFcyZ1BpbXlnVjV2TysvMHgwaWJPTE1DTjdPeGhHTCtkeWVuTTAwYzdBWHZlc3RaNzJ6TWVGdnV2b2VTR2NicTBrRHRHMCs3OHRMbmt1cVBSSE1hUWc0YkRmWEVSTTJzOFNJaEQ4T2NieTR4c29xa2NFRW0yNjYzdWZDZTJPUzI5enR0MUZDNTJHeG0vdEpiUU1tUjZHL3ZpVnN6RDBHTjhxbXA0Q1Jvd0MrMWNTdlBIemYycnUrbEZ6amRoU3piNE9Kbm1SVGFXSm41MVBra3B6aFIzRWlhUElmRkJPSVBNQlhSNUZnSHplN1d4U1R6UDU0RXN0bTZZU2VHb05Ra0QzejY4RkFhNldqZFRNcXNQNHNLbEVvekJCMFBpWjNEanpNazNGWElhSEVaS3p1RlNjZkFHMU5YRk9LTnNLU1JEM2hsRnFCemltODFZeFRqb1BEcWlRVWJLdElTdWVMSnc2dmpUNVBYN0d2V2hrRkZjb0lYNzRZcVYrTmpmYStXQ0NEQWZZN09DdmlZMnhIMGtvRTNMcmtqaHZOSVZhVERBOW5UNDVERjUweWVodHJseW9QVm4rTG1lbzBPME0vTzh5cG1aSGpGaEttL080S3JzbG1ld0FrMHNEQXRnNGdwajJqNVpML0NhK1hrUElxQUExcEY3cWVmMjBmRklNWjl5Q0FJWDRzZlBYdnFMeVVXRC9JWVM4SXFsekxPZWRkWGd2b0c0cUdVcFRlQy9qMkhtb0t1cUNRSGtvRG1OcVVtdXBGZVByUUwyN2FOWlA5bmNzTTJubVRVQ1A3Q1VyMVVVODR5S251ZWhrNjhKQUhKVWdZOEUzUE1oZW1ON292RXROTkNsYjhwUVh5blhCOFdPSVlNamJIZVcyY1FUUTNyaTJGU3VseGVZcG9wd2VNV0lkSmFPYm1MZ0lVU1N2eHRwb2pkeFBSSXZUWW1FLy9XOGdLMHZFbEVPQSt3NmlXVjFBZzdoeXozTTR3RzZ5R1BQYkVmeUFSQlBsaEZLYWhPWm9ReUxxT0xFc29xbmp5ZzVHRmlxK1B1VEUrR2lmRFE4dzNkd0hDU1ZDZmZSTE9ralE0cDhpNHlVVExUQTZNNG84OWNUM1ZTODJaMEVOeG1yMkVzQnU3VlEyLzJUaG4rcDN4d1F6MmJtOWtqc2Roc3RwbEg4ZWJXL1lwVHJHZHdDc0x3U1cyK2E2dU5YanZuY2czRUpvVzg5UXJHZjBtR2laR1JKVGx2YWNkZDZCNkpSN0p6bklFQ0I1NWVMUDBnWm42S0ZwUzNSZUhQK1VVUjQxaGtldmpvUk1BdHFUbXFPMEdDSDlzRHNVUDVLTGF1SFZUZFl0SHZ1d1VHdVduQ3JjclpiT2NuVDRxbjkxOHhkWGpvcDU5bXN3OUptS1VRTEdoc0w1N3NvRTlvWUVUY3pNbGFlalhFaGhYb1hpWDNqV3haeWtmWFBHNWZPbHhVSVlKU1U4c1FvRGRZWE9RTzlXSTNwSTFYSjY5dFZFNXhjczBwSzBrby9NNHkrUWJNUFBZZ1pON25uUzdNUXhPTGtIaGp3Rm5tZnkzeWl0T0V0M3NSTWgwWE15UUZBTmk1UEVPNTk1UTc1aTBXVzJ3b29FVmRPenlOV0swcXhlOWkxZG1NQmVsQit2MFh0cHZvaWUwNDYraFlsV0YrMVlTcWpiQ2psQ1F3SisvVFpDc0hHTXhPblFMbmlLUEM4WEl3S0JnSy9ieUNZaXJhZmovTHRWYzdvL2lMSFVpNXlCWG5saE02eWUxS3B1UTlMM2w4NEJNb1ZSL01PWUR3YVhTWDFoOXQ1ZWJGNUhEbW4vbjk3TGtnQk1rVGFMV3g1NXM2UXEzZHJwcTZkK2ZiOENCVFdub0hHQ1VpOWp4L3IzMTJHSXk4T3h5Z2VFbmhMWHEwbFNQd055UTREUVFxV3RmVHA0VjdmYXJMRzl0c3IxRUtGa042blpZVVdRbGVjczNnbXpvMkxqWlVnQkFSdWtPTzMvVWZrWEdFdnRkSVNKSXFhOVNVVjgwb29QT3RuQWJLSE5jNVhrVWVqSXpmQ2w4M29DOVNNZStFWWhUYkwrS2VpanljaDFsYklWYUhpL1BpYTZJcmh6ZlR6dFJ6cVhnQjk1eHJkWThvNWw1U0pwNzNUWWdVTk1KVFFsVW5wYStTWEljNVZDR2ljV2RrVHFxdElhbDU1WHBvd0ZVQStLK2pIQm1WblprNkhPWk5PMGw2KzZFOFdXU3F4V09US0lWb3RueUJkbTNyNUZkS05zV0ZrVUI3UFkzenpyS3pCdm93ZENUYlRDMlF2YmFocnhPd1dHQjNPY1VGU2ZIOVZIOXhSVTBCUHlEMFJvSnN3RC9xR1BRWkEyMFM0RkNPeWN0RHhRMy9HWXBUUUFFbjdWWmtxNWV6M3FwV09EUFJGRWJpTjV6cFFST1FLTE90cmtvR2E4Y3Q5WFpkbnRpN2ZFeVIwY3lvVHlJSFM2RklZMjNXQnQwQy9nS012N1RxbnJHeGZRVmhGalYxNFoxNmQzMHBaMFptNjNaYW1JWE5Ia08yZGk3eXpqK2FubkNDdlZPRnpuN2ZlTHdBSEFmYnBUVENQVm1zZjF0a3hmczJiS0xhTDJRS3hveVROVzA1VmI0a2R4djJ3QkZlZ2JWWnBkNS9MZUZWbG81Nk1DaUl3VGRmSHpBWFR4QnZoOGcra0Y0OFhqSUZ3VnNIdGkzNmxYcDYwckRyelR0YVlOemE5SFFkMzRPYVQ0ZjllZWtwTXczR2FnclAraWx6SmpOY3NRYUMrOHlhc1pVSDhuc21kYUJMZGg4alZXY3o1NTFXZlhjV0NWcDR5NUZVZ0Fnb21FOUVtUnltZXVnbi94b0M1OWVtMzY2S3plNE0xSzF1RXN1eFU0OVBaNG5tUVJDT0t4MHE0c3Fja254Y05iK1UzU2I3VmxzYTlZdFFhZmlMS0RqYzIzNkY0WXYzUmVUbEthTThWVHhvVEorSGhmUEhpS1VoaFhSRzlRU25YUGxydms2U0FQMytNWDd3aXdzYWFsL3N2dUZFTE5mM09RQ0ltdGNpV0Y0WnZ3anI4NXJERVM2MXRTR3lueU5EM0RSUVlFZTl5U2QxT0NaY21xWGxIeTg3bUVzMTg1a01ScENLMzhZbUlQbWVDTXpJSS85YjFjSWxER29GbmJoa3lMU29aZlp1bkVEVVhEMUo3MkRmbE0zNDU4ZE9YNWU1SkM0bkkxN3dXNzRRSzdXd0hmbVNkRS9KT3BhUk9tSnhRRWRUTkE5OExvdjFlSmo3YUlXVXZNZnpTRmZRaEVJdU94c09XMjZBQWdaTHVBOHpTWVEzYm9pMmpPc3dsV1FRdk8xTFNHL2FIQ2ZTTGsycFAydGl2QUVOZjB0WFFDdFB6TGZaR1NRSEdWdVBOVkpva0dXSlZtNllGNlNTNnZmdDFrU05yY1pTZHNoZXlyaGdDbWVWQU9RMkhxNVRZUlljWUs5SUVWSEZRZjh4VERkVUNCSW91clVSekNadkczUVVrU1g4b05McmJ6cUxSMVJCYmZQbjdUV041cDBhSVhVcG1McW9jTjVzSGF2NTM5Ymcyd0g4dVIyU1RvSFJIM3dybWV5OXh0NFRoMFI3SVZoU0UvbzBQNHBQbkNmVTRUZkRIMlN3NnRTSGt2WjlkcW9SaFkrTUpsMnVpbkFQZERkcmkzQkNqRGU3WFhHcXdpYXNGdlNOblYrbmcvcGZobTZGVTd4cVlJU3FGRlUzbm1VbUplTndHMStDMjlyOGVDSGZNSFVQbm1FVGZDU04vTVhkL0VyM1pyRzNOZnRFR0g5MWhwUWt1UnI4a3ZVdU9DOTViUUI4TjNrV0lJSzFWOWJCbng1Q0h5d29xNnJzRzNTUFl1YTFLOTVqSlJMdE1Sem1iREpTWGRIUHIzMmtsMERzWko2ZGZaeVVYVUhwUE53QkhvditJNTEwK2Nxb0ZFbG5iTVRDY0hKNkVxZWorVHVPTjYvbGR3bGhuMElRK2lqazBlOTFNdHBiMEh1KzZlc01qWUV5eXU5bWpDVHpYSFlpWlp2SDdVNVNjd2F3TmdzREwzeHU2REZzVWhuSFdkLzJPbUo5TkRuSUdpV0pQQmxQSHg5Y0JxSWgxd2VRVkl6R3FGQmlvemJncExtbTBuWHNFcHhDSjNjd0grOGRxc2FabnVrRmpub25jME9CNmRoZlpMejBUME9zYjA4aVQ4ME93VlNRNDV6NE9xVVUwdW1JVGJ1Zllxa0U0Y3hGeTJ1Q1djam4vYWV1Z0ZTTXREWWNlVDJ3SnNIRkFEZW04VWxoNHI3UlVKWk44TTl0eE5XZk5IUGJrMHFVcFFuMkRRT05SVkxWeU9ydEp3b3RhU2gwbHBhY3B0ZDc4THlTNHNFeHVERCtTQjlvWXpQa29LYnNDa1haUk1CQzF0blRxSWxJMGswa2s4d2pHbkJ2Uy95TEN0OElubUxZT2RJSndYcDU3RWtBT01qS0JwWHdRZ3Q0RVdOYjVaVXlscGk1OXNtM2Vza2dCK2huZjhMSHdHOTNLZ1cyRWMvcHV5ZktyK1ZGN053QmtwbFU3VFpTekJaamFuL3dLcU5FSWNOVFNuVGl0NHRXOGkyNDkyUEFvOUFhUUd4cWl3Z0tLLzRrQUJEejZ1d2huMFNmaWcrNENXN0FSVmZWL0ZqTStLY2JteVkvT2VpcXk5R3NLUHlaMXpEV1Q3MlJjaGR2STFFRFNOZjB0b2lnYWlnVTEvV2x5N3lqSHBzVXdjcytKV1dlNEY2MFREZ3Y2ZHlvWG1UWnpCQ0JpNDRoekZIVlMwd01RQTl6WXpDeER0V2wrUHF1NStGdnFHMVFmckpKd0VjNVNadCtiQVVydlNHb1R1ZENyQ25Ba0hFWFRKQWEreEQxNkZCOTR6L2x4TFUvY3pLdTgyN2NJMkZyOUlaTzlsR1Z2QngxMXUySUhONVJaNDdOQm5tZnVmQ3d0KytNaWNGSDdYenUxRkl2NUtwUjFuODFYS1Q3KzB1Zk91aHN4Z3ZDZzJyU1p6cDNEZlVDVm1kYjAyRENpTmJKWHVYcnJmb1Y1S3drbk4rbmFPTGx0YkhDUFNyYW5jTEgrUGFxUEUzQ01PTnRQa2crVEJYKzIyMTdadE5yV0VqOXppMjVaMUlIbjFab3hWdHFPU09oa0J1dFBSTVF3bnRqMEM2L0NRaWEra1RjM2xGUFcrS285azREVjVLN2xzRFp1MGVKV09GMWxTZW1ybThvSjY4MFAwNzRTL2JVQmhHVnFxNnhZV1lJcEw0UUxlc1BmSUszenNXSGdQdkYxQ3BFTTM3Mi9pcVdPQ0s1bE5hNUxFM2ZRVFNQa3VWSVQ1bkhZTjd5SEEvTzA3NDFCaUJuRmR3NzNDUUVDY2dJSWk0bk5CZVU5aEYxdGgybENQOTVPNlVOZWVNMEdMZHpVN1BIZkhBUWVlTEhVdlN4K3Q1Ujh5a3RmOXJpL3pjekhWdkFwaUorQjZtV0doV0hjMklIUmpuNm1HdjZJWmVXTFdmdUZkUXF1TXVXM1hIRnFFdlc4bzdRRWZmWDVQQUdURDdpejVncWQvM0ExN3YrTlVhL1NBVW9vbzBWazlERUJxTmJNRDBOQ2tWOGdMakFZQ1ZCcStLOE8vSlFocVo5d1p4bWNEWHczZjJtY0JOSEZMQ3dWMGdNc0lIS05LaTc5U1FqVUZ0N042aFhFV082NFJrM3NRPT0iLCJpdiI6ImQyMTE4N2Y3NTE2N2M4ZmI0MTRjZmI0YWJiMjAwNmFjIiwicyI6IjJjMzY5MzgzNDJmNmU3YjIifQ%3D%3D'
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            # 'Cookie': '_cfuvid=AY.vWeq0BRAmyEH1xuHAIVg2NhHkbLbQC2Jr7QG2TWs-1698225817072-0-604800000'
        }
        response = requests.request("POST", url, headers=headers, data=payload)
        response = response.json()
        if "token" in response:
            return response["token"]
        return None

    def startConversation(self, message):
        # url = "https://api.pawan.krd/v1/conversation"
        url = "https://ai.fakeopen.com/api/conversation"
        url = "/conversation"
        # arkose_token = self.get_openai_token()
        arkose_token = self.get_token()
        # url = "https://api.pawan.krd/backend-api/conversation"
        # url = "https://bypass.churchless.tech/api/conversation"
        response = self.request(url, {
            "headers": {
                "Accept": "text/event-stream",
            },
            "method": "POST",
            "data": {
                "action": "next",
                "arkose_token": arkose_token,
                "messages": [
                    {
                        "id": str(uuid.uuid4()),
                        "role": "user",
                        "author": {"role": "user"},
                        "content": {
                            "content_type": "text",
                            "parts": [message]
                        },
                    }
                ],
                "conversation_id": None,
                "timezone_offset_min": -180,
                "history_and_training_disabled": False,
                "parent_message_id": str(uuid.uuid4()),
                "model": "text-davinci-002-render-sha",
            }
        })
        return response

    def getConversation(self, id):
        conversation = filter(
            lambda x: x["id"] == id or x["title"] == id, self.recent_conversations)
        conversation = list(conversation)
        if len(conversation) > 0:
            conversationID = conversation[0]["id"]
            conversation = self.request(
                "/conversation/"+conversationID)
            return conversation
        raise self.CustomException("Conversation not found")


chatgpt = ChatGPT()
# # key = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCIsImtpZCI6Ik1UaEVOVUpHTkVNMVFURTRNMEZCTWpkQ05UZzVNRFUxUlRVd1FVSkRNRU13UmtGRVFrRXpSZyJ9.eyJodHRwczovL2FwaS5vcGVuYWkuY29tL3Byb2ZpbGUiOnsiZW1haWwiOiJqZXNpemkubWFuaUBldmVyeXNpbXBseS5jb20iLCJlbWFpbF92ZXJpZmllZCI6dHJ1ZX0sImh0dHBzOi8vYXBpLm9wZW5haS5jb20vYXV0aCI6eyJ1c2VyX2lkIjoidXNlci1uM3J6S3R0OXF2Rmd4cjA5RXBzWFBTV3gifSwiaXNzIjoiaHR0cHM6Ly9hdXRoMC5vcGVuYWkuY29tLyIsInN1YiI6ImF1dGgwfDY0YjJjMWMyODM4M2RhYzY1ZTRhNGYzMiIsImF1ZCI6WyJodHRwczovL2FwaS5vcGVuYWkuY29tL3YxIiwiaHR0cHM6Ly9vcGVuYWkub3BlbmFpLmF1dGgwYXBwLmNvbS91c2VyaW5mbyJdLCJpYXQiOjE2OTIxNTkxMzIsImV4cCI6MTY5MzM2ODczMiwiYXpwIjoiVGRKSWNiZTE2V29USHROOTVueXl3aDVFNHlPbzZJdEciLCJzY29wZSI6Im9wZW5pZCBwcm9maWxlIGVtYWlsIG1vZGVsLnJlYWQgbW9kZWwucmVxdWVzdCBvcmdhbml6YXRpb24ucmVhZCBvcmdhbml6YXRpb24ud3JpdGUgb2ZmbGluZV9hY2Nlc3MifQ.B9KHphpezGP5YSSIROWaYHbMMDileCZfviYUxNgjVTfOM4-RVrfNqODRf6NYMECXqH40h7Ho31pDQFrgL1qvdCbXZKB5IKS2TbgZf9D3Zc7oE1UQflWftKUaLlVgXbxcF2Zr3qWfV3cXCGozdJ81dGUUDwwlJjRpq0jukamdHNKCjWx0zPfZYnLcpl1GsV7LZuIYJnk6RmW7z5CksTPMo5u53l4bBLXdTPRqkoSQngDAeZWg2kXpFDpx0wXs2xz1rRgzOp_n_GfAehjWMMZMvtEOL-qBRpJlbmmYVDRhhdZM898_0_oOnjjDotqv8fMnXBJIH5bRU6njylaDeR530w"
# key = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCIsImtpZCI6Ik1UaEVOVUpHTkVNMVFURTRNMEZCTWpkQ05UZzVNRFUxUlRVd1FVSkRNRU13UmtGRVFrRXpSZyJ9.eyJodHRwczovL2FwaS5vcGVuYWkuY29tL3Byb2ZpbGUiOnsiZW1haWwiOiJmYW1hLndvc2FrZUBiaWtlYmVzdGllcy5jb20iLCJlbWFpbF92ZXJpZmllZCI6dHJ1ZX0sImh0dHBzOi8vYXBpLm9wZW5haS5jb20vYXV0aCI6eyJ1c2VyX2lkIjoidXNlci1nRkx3N2NqdUcwUlF2alpRb0l0QXlCTHcifSwiaXNzIjoiaHR0cHM6Ly9hdXRoMC5vcGVuYWkuY29tLyIsInN1YiI6ImF1dGgwfDY0ZGE5ZjcyODI3NzM5ZjFiYmRkMmVhZSIsImF1ZCI6WyJodHRwczovL2FwaS5vcGVuYWkuY29tL3YxIiwiaHR0cHM6Ly9vcGVuYWkub3BlbmFpLmF1dGgwYXBwLmNvbS91c2VyaW5mbyJdLCJpYXQiOjE2OTQ0NTc1MjgsImV4cCI6MTY5NTY2NzEyOCwiYXpwIjoicGRsTElYMlk3Mk1JbDJyaExoVEU5VlY5Yk45MDVrQmgiLCJzY29wZSI6Im9wZW5pZCBwcm9maWxlIGVtYWlsIG1vZGVsLnJlYWQgbW9kZWwucmVxdWVzdCBvcmdhbml6YXRpb24ucmVhZCBvZmZsaW5lX2FjY2VzcyJ9.TBl8xflN33R6qyEVqfnAUPSuhMj-bQ_jglGa2qrVdOCyAs4hHeuc8WZOfmeRwkW6Ni1FSHLgvOI4l2kCKigg4hu9dgV8aXz1WPZNbXepmNc1ZHpuxgzCN-z8dHB8Pbjnhsj22W48Xy-Tbe1uzAobBS9rzf9LUcLxDwa1crS5I6jGzV7m1SKs9V3cCIeb7smguBr3Yjzb0uIL26QkCGIKzSOGVZ8mNp0q91Kc3IRTHjMvjZrNEjmWxC6sqgsEH8gkPgxHHX4ItZ6pq6zcx4EEyaJbPt2ujPoY2jqdDX8Z0Omkm6T31Y6sVbeUgstmJMhiYyvrvpcysQUOofNCo2A5sQ"
# # # key = "pk-WGwlZEFATWDSBrCuVxswgGsBrMqQvszUOBxpIfyBeFsRWuYC"
key = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCIsImtpZCI6Ik1UaEVOVUpHTkVNMVFURTRNMEZCTWpkQ05UZzVNRFUxUlRVd1FVSkRNRU13UmtGRVFrRXpSZyJ9.eyJodHRwczovL2FwaS5vcGVuYWkuY29tL3Byb2ZpbGUiOnsiZW1haWwiOiJqZXNpemkubWFuaUBldmVyeXNpbXBseS5jb20iLCJlbWFpbF92ZXJpZmllZCI6dHJ1ZX0sImh0dHBzOi8vYXBpLm9wZW5haS5jb20vYXV0aCI6eyJwb2lkIjoib3JnLUZNTFpNMktGdkNFMEhacmRwVXJRNzByaiIsInVzZXJfaWQiOiJ1c2VyLW4zcnpLdHQ5cXZGZ3hyMDlFcHNYUFNXeCJ9LCJpc3MiOiJodHRwczovL2F1dGgwLm9wZW5haS5jb20vIiwic3ViIjoiYXV0aDB8NjRiMmMxYzI4MzgzZGFjNjVlNGE0ZjMyIiwiYXVkIjpbImh0dHBzOi8vYXBpLm9wZW5haS5jb20vdjEiLCJodHRwczovL29wZW5haS5vcGVuYWkuYXV0aDBhcHAuY29tL3VzZXJpbmZvIl0sImlhdCI6MTY5ODIwODUwMCwiZXhwIjoxNjk5MDcyNTAwLCJhenAiOiJUZEpJY2JlMTZXb1RIdE45NW55eXdoNUU0eU9vNkl0RyIsInNjb3BlIjoib3BlbmlkIGVtYWlsIHByb2ZpbGUgbW9kZWwucmVhZCBtb2RlbC5yZXF1ZXN0IG9yZ2FuaXphdGlvbi5yZWFkIG9yZ2FuaXphdGlvbi53cml0ZSBvZmZsaW5lX2FjY2VzcyJ9.C2HJFPiONE9AOE7DfIqfuWRBjNhtTs6Pm5yO6yy2q8Y9VnyQNrk92JJX7DE302lMjqWSDVLA_VRbhjmndjpjRFwK60rKKoFDX5OTjUkId6hB1JF1DU3V3Y776pJlUYSSYiLDsTNR1gDxhTS1G_qp0LRWzAU1rDyDrsV8QplJhF_QY9ZzMrSsrk6KEJlEVPWzP9c94hgfD_1Kw-Bqv1ogcn-PnKwNoTH-Ckx1p73F5PR4qk2EI1x97LDJ5rz6TsRHS60nb2UUQgyfuXS98pgacvp4rCAnkNnWnCHi80BBmgbnnGe1Q-VM3tlVymbHItWbCFikTYanpHXSCq8sOSBA0A"
# int = chatgpt.init(key)
# print(int)
# # # # # conversation = chatgpt.getConversation("66ba097c-8a5e-4479-8681-85f23078a7e8")
# conversation = chatgpt.startConversation("Hello World!")
# print(conversation)
