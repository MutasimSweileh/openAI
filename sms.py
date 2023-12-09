import random
from time import sleep
from smsactivate.api import SMSActivateAPI
# SMSActivateAPI Contains all basic tools for working with the SMSActivate API
API_KEY = "b1f58d298f34Ad9eed93894927e20789"
sa = SMSActivateAPI(API_KEY)

sa.debug_mode = False
# Used for debugging. When debug_mode is active, all responses from the server and class will be output to the console
# print(sa.version())


class SMS:

    def __init__(self):
        self.activationId = None
        self.phoneNumber = None
        self.status = None
        self.pedding_list = []
        self.error = ""
        self.country = ""
        self.trys = 0
        self.last_c = None
        self.service = "dr"
        self.balance = 0
        self.trysList = {}
        self.c = {}
        self.c["dr"] = {
            # "Kenya": [8, 3],
            "Indonesia": 6,  # free
            # "Romania": [32, 2],  # free
            # "Colombia": [33, 2],
            "Chile": 151,
            "Armenia": 148,
            "Philippines": 4,
            "Kazakhstan": 2,
            # "Uruguay": [156, 3],
            # "Kyrgyzstan": [11, 3], #unusebale
            # "Paraguay": [87, 3],
            # "England": [16, 2],
            # "Tajikistan": [143, 3],
            # "Venezuela": [70, 2]
        }
        self.c["acz"] = {
            # "us": 12,
            "gb": 16
        }
        self.c["go"] = {
            "India": 22,
            "Vietnam": 10,
            # "Sierraleone": 115,
            "Canada": 36,
            "Indonesia": 6,
            "Myanmar": 5,
            "Russia": 0,
            "Chile": 151,
            "Romania": 32,
            "Philippines": 4,
            "United States": 12,
            "Tajikistan": 143
        }
        self.get_numbers()
        self.clear_old()
        self.last_activation = []

    def get_anthor(self):
        self.set_status()

    def get_sms(self, resend=False):
        if not self.activationId:
            return None
        status = self.get_status()
        print(status)
        if str(status).find("STATUS_OK") != -1:
            code = str(status).split(":")[-1]
            print(code)
            self.set_status(6)
            balance = self.balance
            balance = self.get_balance() - balance
            print("Activation Cost:", balance)
            return code
        else:
            if self.trys >= 15:
                if resend:
                    self.set_status()
                return None
            sleep(5)
            self.trys += 1
            return self.get_sms()

    def get_numbers(self):
        numbers = sa.getActiveActivations()
        if numbers and "activeActivations" in numbers:
            numbers = list(numbers["activeActivations"])
            for number in numbers:
                self.pedding_list.append(number["activationId"])
        print(self.pedding_list)
        return numbers

    def get_activation(self):
        re = sa.getActiveActivations()
        sms = list(re["activeActivations"])
        print(sms)
        return sms[-1]

    def get_balance(self):
        balance = sa.getBalance()
        print("Current balance:", balance["balance"])
        self.balance = float(balance["balance"])
        return self.balance

    def all_in_list(self):
        last_activation = self.last_activation
        clist = self.c[self.service]
        rea = []
        for country, number in clist.items():
            if country not in last_activation:
                rea.append(country)
        return rea

    def getrandcountry(self, excuded=[], service="dr"):
        clist = self.c[service]
        self.service = service
        calist = self.all_in_list()
        if len(calist) == 0:
            self.last_activation = []
            country, capital = random.choice(list(clist.items()))
        else:
            clist = calist
            country = random.choice(clist)
        if country in excuded:
            return self.getrandcountry(excuded, service)
        return country

    def get_number(self, country="Kenya", maxPrice="10.00", freePrice=True):
        # if self.phoneNumber:
        #     return self.phoneNumber
        service = self.service
        c = self.c[service]
        self.country = country
        country = c[country]
        self.set_status()
        self.last_c = self.country
        self.trys = 0
        # claro
        # if freePrice:
        #     maxPrice = "10.00"
        number = None
        try:
            number = sa.getNumberV2(
                service=service, country=country, freePrice=freePrice, maxPrice=maxPrice)
            if self.country not in self.last_activation:
                self.last_activation.append(self.country)
            self.phoneNumber = number["phoneNumber"]
            # self.phoneNumber = str(self.phoneNumber)[country[1]:]
            self.activationId = number["activationId"]
            self.last_c = self.country
            print("GetNumber from country ",
                  self.country, ":", number["phoneNumber"], ", activationCost:", number["activationCost"], ", activationOperator:", number["activationOperator"])
            return self.phoneNumber
        except Exception as e:
            m = str(e)
            if "message" in number:
                m = number["message"]
            if "msg" in number:
                m = number["msg"]
            print("GetNumber", self.country, "error:", m)
            if m == "WRONG_MAX_PRICE":
                # print(number)
                return self.get_number(self.country, None)
            # if m.find("no free numbers") != -1:
            #     return self.get_number(self.country, False)
            self.error = m
        return None

    def clear_old(self):
        pedding_list = self.pedding_list
        for v in pedding_list:
            status = sa.setStatus(id=v, status=8)
            if status != "EARLY_CANCEL_DENIED":
                print("Cancel activation for #", v)
                self.pedding_list.remove(v)

    def set_status(self, status=8):
        try:
            if not self.activationId:
                return None
            if status == 8:
                self.update_list(-1)
            else:
                self.update_list()
            self.clear_old()
            status = sa.setStatus(id=self.activationId, status=status)
            if status == "EARLY_CANCEL_DENIED":
                self.pedding_list.append(self.activationId)
            print("setStatus: ", status, "for county", self.last_c)
            self.activationId = None
            self.phoneNumber = None
        except Exception as e:
            print("set_status error:", str(e))
        return status

    def update_list(self, a=1):
        c = self.last_c
        trysList = self.trysList
        if c in trysList:
            trysList[c] += a
        else:
            trysList[c] = a
        print("Update List:", trysList)
        return trysList

    def get_status(self):
        status = sa.getStatus(id=self.activationId)
        try:
            self.status = sa.activationStatus(status)
            return self.status["status"]
        except Exception as e:
            if "msg" in status:
                m = status["msg"]
            if "message" in status:
                m = status["message"]
            print(m)
        return None


# print(sms.getrandcountry())
# sms = SMS()
# sms.service = "go"
# sms.get_number("Tajikistan")
# sms.get_status()
