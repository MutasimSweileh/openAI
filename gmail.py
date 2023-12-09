# import the required libraries
import tls_client
import json
import random
import re
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import pickle
import os.path
import base64
import email
from bs4 import BeautifulSoup
import requests
# Define the SCOPES. If modifying it, delete the token.pickle file.
SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.modify',
    'https://www.googleapis.com/auth/gmail.labels',
    'https://www.googleapis.com/auth/gmail.send'
]


def getEmails(fromemail="noreply@tm.openai.com"):
    # Variable creds will store the user access token.
    # If no valid token found, we will create one.
    creds = None

    # The file token.pickle contains the user access token.
    # Check if it exists
    if os.path.exists('token.pickle'):

        # Read the token from the file and store it in the variable creds
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)

    # If credentials are not available or are invalid, ask the user to log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'client_secret.json', SCOPES)
            creds = flow.run_local_server(port=0)

        # Save the access token in token.pickle file for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    # Connect to the Gmail API
    service = build('gmail', 'v1', credentials=creds)

    # request a list of all the messages
    result = service.users().messages().list(userId='me', maxResults=2,
                                             q=f"from:{fromemail} is:unread").execute()

    # We can also pass maxResults to get any number of emails. Like this:
    # result = service.users().messages().list(maxResults=200, userId='me').execute()
    messages = result.get('messages')

    # messages is a list of dictionaries where each dictionary contains a message id.

    # iterate through all the messages
    print(messages)
    if not messages:
        return None
    mylist = []
    for msg in messages:
        # Get the message from its id
        txt = service.users().messages().get(
            userId='me', id=msg['id']).execute()
       # print(txt)
        # Use try-except to avoid any Errors
        try:
            # Get value of 'payload' from dictionary 'txt'
            payload = txt['payload']
            headers = payload['headers']

            # Look for Subject and Sender Email in the headers
            for d in headers:
                if d['name'] == 'Subject':
                    subject = d['value']
                if d['name'] == 'From':
                    sender = d['value']

            # The Body of the message is in Encrypted format. So, we have to decode it.
            # Get the data and decode it with base 64 decoder.
            # print(payload['body']['data'])
            parts = payload.get('parts')
            if parts:
                parts = parts[0]
            else:
                parts = payload
            data = parts['body']['data']
            # print("data", data)
            data = data.replace("-", "+").replace("_", "/")
            decoded_data = base64.b64decode(data)

            # Now, the data obtained is in lxml. So, we will parse
            # it with BeautifulSoup library
            soup = BeautifulSoup(decoded_data, "lxml")
            # print("soup", soup)
            # soup2 = BeautifulSoup(decoded_data)
            body = soup.body()
            # print(body)
            # return False
            regex = r"<td.*?<div[^><]*?>(\d+)<\/div>"
            m2 = re.search(regex, str(body))
            regex = r"\((.*?)\)"
            m = re.search(regex, str(body))
            regex = r"href=\"([^\"]*?\/verify[^\"]*?)\""
            m3 = re.search(regex, str(body))
            regex = r"verification code is:\s+(\d+)\s+"
            m4 = re.search(regex, str(body))
            regex = r"(http.*?mail-settings.*?)$"
            m5 = re.search(regex, str(body), re.MULTILINE | re.DOTALL)
            if m3:
                mylist.append(m3.group(1).strip())
            elif m2:
                mylist.append(m2.group(1).strip())
            elif m:
                mylist.append(m.group(1).strip())
            elif m4:
                mylist.append(m4.group(1).strip())
            elif m5:
                mylist.append(m5.group(1).strip())

            service.users().messages().modify(userId='me', id=msg['id'], body={
                'removeLabelIds': ['UNREAD']}).execute()
            # Printing the subject, sender's email and message
            # print("Subject: ", subject)
            # print("From: ", sender)
            # print("Message: ", body)
            # print('\n')
        except Exception as e:
            print(str(e))
    if len(mylist) < 1:
        return None
    return mylist


class temp_mail():
    def __init__(self, email=None) -> None:
        self.email = email
        self.gmail = None
        self.last_email = []
        self.temp = None
        self.client = tls_client.Session(
            client_identifier="chrome112",
            random_tls_extension_order=True,
            debug=False
        )
        pass

    def deleteEmail(self):
        if not self.email:
            return None
        j = None
        try:
            url = "https://app.restoviebelle.com/openai.php?get=deleteTempMail&email=" + self.email
            response = requests.request("GET", url)
            j = json.loads(response.text)
            print("deleteEmail:", self.email)
        except Exception as e:
            print("DeleteEmail Error:", str(e))
        self.email = None
        # print(j)
        return j

    def getMessages(self, f=""):
        response = None
        try:
            url = f"https://app.restoviebelle.com/openai.php?get=getEmailMessages&from={f}"
            if self.email:
                url += "&email="+self.email
            if self.temp:
                url += "&temp="+self.temp
            # print(url)
            url = url.strip()
            response = self.client.get(url)
            if response.text is None:
                return None
            # print(response.text)
            j = response.json()
            if len(j) < 1:
                return None
            # print(j)
            return j
        except Exception as e:
            # print(response.text)
            print("getMessages Error:", str(e), response)
        return None

    def all_in_list(self, tempemails):
        last_activation = self.last_email
        rea = []
        for email in tempemails:
            if email not in last_activation:
                rea.append(email)
        return rea

    def getRandomEmail(self):
        tempemails = [
            "contact@theglossylocks.com",
            "admin@snakesnuggles.com",
            "admin@bikebesties.com",
            "mohtasm@everysimply.com",
        ]
        tempemails = self.all_in_list(tempemails)
        if len(tempemails) < 1:
            self.last_email = []
            return self.getRandomEmail()
        email = random.choice(tempemails)
        self.last_email.append(email)
        return email

    def getAlias(self, user):
        tempemails = [
            "contact@theglossylocks.com",
            "admin@snakesnuggles.com",
            "admin@bikebesties.com",
        ]
        email = filter(lambda x: user.find(
            x.lower().split("@")[1]) != 1, tempemails)
        email = list(email)[0]
        # print(email)
        self.email = None
        self.temp = email
        try:
            url = "https://app.restoviebelle.com/openai.php?get=getAliasMail&email=" + email
            url += "&user=" + user
            # print(url)
            response = requests.request("GET", url)
            j = json.loads(response.text)
            if j:
                self.email = user
                print("getAlias:", self.email)
        except Exception as e:
            print("getAlias error:", str(e))
        return self.email

    def upGmail(self, **kwargs):
        try:
            if not self.gmail:
                return None
            url = "https://app.restoviebelle.com/openai.php?get=upGmail"
            kwargs["email"] = self.gmail["email"]
            for key, value in kwargs.items():
                if key == "uses" and self.gmail["uses"]:
                    uses = self.gmail["uses"].split(",")
                    uses.append(value)
                    value = ",".join(uses)
                url += "&" + key + "=" + value
            response = requests.request("GET", url)
            j = json.loads(response.text)
            if j:
                print(j)
                return j
        except Exception as e:
            print("upGmail error:", str(e))
        return None

    def getGmail(self, **kwargs):
        # email = kwargs.get("email", None)
        try:
            url = "https://app.restoviebelle.com/openai.php?get=getGmail"
            for key, value in kwargs.items():
                url += "&" + key + "=" + value
            response = requests.request("GET", url)
            j = json.loads(response.text)
            if j:
                self.gmail = j[0]
                return j
                print("getEmail:", self.email)
        except Exception as e:
            print("getGmail error:", str(e))
        return None

    def setData(self, table, **kwargs):
        # email = kwargs.get("email", None)
        try:
            url = "https://app.restoviebelle.com/openai.php?set="+table
            # for key, value in kwargs.items():
            #     url += "&" + key + "=" + value
            response = requests.request("POST", url, data=kwargs)
            print(response.text)
            j = json.loads(response.text)
            if j:
                return j
        except Exception as e:
            print("setData error:", str(e))
        return None

    def getData(self, table, **kwargs):
        # email = kwargs.get("email", None)
        try:
            url = "https://app.restoviebelle.com/openai.php?get="+table
            for key, value in kwargs.items():
                url += "&" + key + "=" + value
            response = requests.request("POST", url, data=kwargs)
            j = json.loads(response.text)
            if j:
                return j
        except Exception as e:
            print("getData error:", str(e))
        return None

    def getEmail(self, email="mohtasm@everysimply.com"):
        if not email:
            email = self.getRandomEmail()
        self.email = None
        self.temp = email
        try:
            url = "https://app.restoviebelle.com/openai.php?get=getTempMail&email=" + email
            response = requests.request("GET", url)
            j = json.loads(response.text)
            if j:
                self.email = j["email"]
                print("getEmail:", self.email)
        except Exception as e:
            print("getEmail error:", str(e))
        return self.email


# temp = temp_mail()

# temp.email = "loheru.huveheki@everysimply.com"
# code = temp.getMessages(
#     "platform@stability.ai")
# print(code)

# headers = {
#     'Origin': 'https://bard.google.com"',
#     # 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
#     # 'Content-Type': 'application/json',
#     'Cookie': 'SID=Zgjehk9Szy4yAnKqK5LkeTxEHHrPDb75LRJ3p6zvB2CTMBO7t8BaBcKiUGRI-W5Ljj6cew.; __Secure-1PSID=Zgjehk9Szy4yAnKqK5LkeTxEHHrPDb75LRJ3p6zvB2CTMBO7-yffvrd728sTgRkC2GS1dA.; __Secure-3PSID=Zgjehk9Szy4yAnKqK5LkeTxEHHrPDb75LRJ3p6zvB2CTMBO7fVZe-T8452ECLiMH4QWQhA.; HSID=AoXbZvVpgFE-InmJQ; SSID=A911RevnyLBjtsYO2; APISID=yZosJXsMzy5uZvXY/AMsvWDKn-OG34q2c1; SAPISID=R9wPhsO3158b7SVc/A3Hh1jE8_GWeeo3-G; __Secure-1PAPISID=R9wPhsO3158b7SVc/A3Hh1jE8_GWeeo3-G; __Secure-3PAPISID=R9wPhsO3158b7SVc/A3Hh1jE8_GWeeo3-G; SEARCH_SAMESITE=CgQI_pgB; OGPC=19036484-1:19022519-1:19031986-1:; 1P_JAR=2023-08-17-19; AEC=Ad49MVEaWPRfIyWjyUtxffeG9Laj1v29IVTPTIbJdGTiEUfFamix4-5DQMg; NID=511=dRYe4O92DN38wiN-aoUXv2Dt9SL7ESB0CvCuliPGRYt0vUGcAOhP8I_FylPdfcRIX6o8emdM5szLUCFgYHvmdwg2f19TtcLxaVmpXAb_ebT_ueUrrlKgQ-T-hVMY7Uav2UAZhnyKyHRPnGZUWKj7s0piue5bRKqUGHT165CzXYqieHH5iiXS-FhD_Www_X9FlAMeOniLZh9oqO8nXzN-dY7oj8sZcQZhBehhpL5ez_qIfxq4KxAMmjqcP1a6VZbwa3FBcIf8td61HrI9Igq42i_fz7kTrTphKW4ivx5fE1uE1SVXaCKJ_izAHQxKUZR_9cOdHH5pUO_HeN1tqUP3Krwku6gEbJId8c5VKN7s; __Secure-1PSIDTS=sidts-CjIBSAxbGcqkqhPl-FH3KD_JD0m7Mhh4m5T3YTgEsAPaAhPjnS-OmfuUcmzR9d6LawO8wRAA; __Secure-3PSIDTS=sidts-CjIBSAxbGcqkqhPl-FH3KD_JD0m7Mhh4m5T3YTgEsAPaAhPjnS-OmfuUcmzR9d6LawO8wRAA; SIDCC=APoG2W-8tUz-D6s8zd1nb2bBdy1I2OvD2q632S4UR9C2h2y9LAZhYYIBfWJ40kBzpO5PXAQEp4s; __Secure-1PSIDCC=APoG2W_h2f4qAqyskPhUa-P30khFSn7NSC3vJGb5QmxicBPxgthtiREB-JSejzLReBWxHsQomQ; __Secure-3PSIDCC=APoG2W8k9tH-qXxun-qcix7u7ocD5k73Ym0jnxsuJ-jR7dCWmM4rt09mhsHevvOftAhDFL7ebJw'
# }

# session = tls_client.Session(
#     client_identifier="chrome112",
#     random_tls_extension_order=True
# )
# url = "https://bard.google.com/"
# response = session.get(url, headers=headers)

# print(response)
# print(response.text)

# code = getEmails("support@scrapeowl.com")
# print(code)
# code = getEmails("support@mail.anthropic.com")
# print(code)
# code = getEmails("noreply@google.com")
# print(code)

# code = getEmails("forwarding-noreply@google.com")
# print(code)
