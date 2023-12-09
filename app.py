import atexit
import json
from multiprocessing import Process
import os
from random import randint
import shlex
import subprocess
from time import sleep
from apscheduler.schedulers.background import BackgroundScheduler
import time

import pyperclip
from BaseDriver import BaseDriver
from bedtime import computer_sleep
from chatgpt import ChatGPT
from claude import Claude, CustomException
from nlp import NLP
from webdriver import Driver
from gmail import getEmails, temp_mail
from sms import SMS
import requests
from twocaptcha import TwoCaptcha
from anticaptchaofficial.funcaptchaproxyless import *
from playwright.sync_api import Route
import signal
import sys
import threading
from flask import Flask, jsonify, make_response, request
from flask_httpauth import HTTPBasicAuth
from werkzeug.security import generate_password_hash, check_password_hash
import config

app = Flask(__name__)

auth = HTTPBasicAuth()

users = {
    "mohtasm": generate_password_hash("mohtasm10Q@@"),
    "susan": generate_password_hash("bye")
}


@auth.verify_password
def verify_password(username, password):
    if username in users and \
            check_password_hash(users.get(username), password):
        return username


class openAi:

    def __init__(self):
        self.email = None
        self.api_key = None
        self.driver = None
        self.error = ""
        self.emails = []
        self.changeIP = True
        self.user_dir = "playway"
        self.path = os.getcwd()+"/"
        self.is_multi = False
        self.do_openai = True
        self.solve_capcha = True
        self.isRuning = False
        self.success_accounts = 0
        self.do_dreamstudio = False
        self.do_monkeylearn = False
        self.do_claude = False
        self.do_scrapeowl = False
        self.do_scraperapi = False
        self.dr = Driver(Blocks=False)
        self.uc_dr = BaseDriver()
        self.tmpEmail = temp_mail()
        self.two_captcha = True
        self.sms = SMS()
        self.headless = True
        self.trysList = {}
        self.solver = TwoCaptcha(os.getenv("TwoCaptcha_API_KEY"))

    def vpn_requset(self, method):
        test_proc = subprocess.run([
            'expresso/expresso.exe', method], capture_output=True)
        stdout = test_proc.stdout
        # print(stdout)
        return stdout

    def reCaptcha(self, js, url=None):
        if not url:
            url = self.dr.driver.url
        if type(js) == str:
            js = json.loads(js)
        # print(js)
        print("Solving reCaptcha ..", js["sitekey"])
        try:
            result = self.solver.recaptcha(sitekey=js["sitekey"],
                                           url=url)
            result = result["code"]
        except Exception as e:
            print("reCaptcha error:", str(e))
            return None
        else:
            print("Solved! code:", result)
            return result

    def turnstile(self, js, url=None):
        if not url:
            url = self.dr.driver.url
        if type(js) == str:
            js = json.loads(js)
        print(js)
        print("Solving turnstile ..", js["sitekey"])
        try:
            result = self.solver.turnstile(sitekey=js["sitekey"],
                                           url=js["pageurl"], action=js["action"], data=js["data"], pagedata=js["pagedata"])
            result = result["code"]
        except Exception as e:
            print("turnstile error:", str(e))
            return None
        else:
            print("Solved! code:", result)
            return result

    def funCaptcha(self, js, url=None):
        if not url:
            url = self.dr.driver.url
        js = json.loads(js)
        # print(js)
        print("Solving funCaptcha for url "+url+" ..", js["pkey"])
        js["data"] = js.get("data", None)
        try:
            if self.two_captcha:
                self.solver = TwoCaptcha('9234cf1ef978837f23f917b9d9cb0541')
                result = self.solver.funcaptcha(sitekey=js["pkey"],
                                                url=url,
                                                surl=js["surl"])
                result = result["code"]
            else:
                self.solver = funcaptchaProxyless()
                self.solver.set_verbose(1)
                self.solver.set_key("035534bc538bd650db6aafab3fffa59c")
                self.solver.set_website_url(url)
                self.solver.set_website_key(js["pkey"])
                self.solver.set_js_api_domain(js["surl"])
                token = self.solver.solve_and_return_solution()
                if token != 0:
                    result = token
                else:
                    raise Exception(self.solver.error_code)
        except Exception as e:
            print("funCaptcha error:", str(e))
            return None
        else:
            print("Solved! code:", result)
            return result

    def VPN_reconnect(self):
        self.vpn_requset("disconnect")
        sleep(3)
        self.vpn_requset("connect")

    def reLogin(self):
        driver = self.dr.get_driver(user_dir=self.user_dir)
        driver.get_by_text("Log in", exact=True).click()
        driver.locator("#username").fill(self.email)
        driver.get_by_text("Continue", exact=True).click()
        driver.locator("#password").fill(self.email)
        driver.get_by_text("Continue", exact=True).click()
        while True:
            is_visible = driver.get_by_text("Open Gmail").is_visible()
            if is_visible:
                break
            user = driver.get_by_placeholder(
                "First name", exact=True)
            if user.is_visible():
                break
        account = self.getemailverification(is_visible)
        self.saveEmails()
        # if account:
        #     self.dr.close_driver()
        return account

    def delEmail(self):
        try:
            self.email = None
            self.tmpEmail.deleteEmail()
        except Exception as e:
            print("Fail delEmail:", str(e))

    def getAccount(self):
        try:
            self.error = ""
            if not self.do_openai:
                return self.is_multi
            balance = self.sms.get_balance()
            if balance < 5:
                print(
                    "OpenAI: current balance to get phone number not enough: ", balance)
                self.do_openai = False
                return self.is_multi
            self.getEmail()
            if not self.email:
                self.email = self.tmpEmail.getEmail(None)
            self.api_key = None
            # self.headless = False
            driver = self.uc_dr.get_driver(headless=self.headless)
            print("OpenAI: waiting for login page...")
            driver.goto("https://platform.openai.com/signup")
            driver.wait_for_timeout(timeout=3000)
            trys = 0
            while True:
                try:
                    is_login = driver.locator(".user-section", timeout=5)
                    if is_login.is_visible(timeout=1000):
                        return self.getKey(driver)
                    link = driver.get_by_text("Sign up", exact=True, timeout=5)
                    if link.is_visible(timeout=3000):
                        link.click()
                        break
                    username = driver.locator("#email")
                    if username.is_visible():
                        break
                    if trys > 7:
                        raise Exception("we can't find sign up page...")
                    driver.wait_for_timeout(timeout=1000)
                    trys += 1
                except Exception as e:
                    print("OpenAI error:", str(e))
                    pass
                    # driver.get_by_text("Log out", exact=True).click()
                    # driver.locator("#username").wait_for(timeout=10000)
            print("OpenAI: fill info...")
            username = driver.locator("#email")
            # username.wait_for(timeout=3000)
            username.type(self.email)
            driver.wait_for_timeout(timeout=2000)
            driver.get_by_text("Continue", exact=True).click()
            error = driver.locator(".ulp-input-error-message")
            if error.is_visible(timeout=2000):
                print("OpenAI:", error.text_content())
                self.saveEmails()
                return self.getAccount()
            password = driver.locator("#password")
            password.type("mohtasm10QQ@@")
            driver.wait_for_timeout(timeout=1000)
            driver.get_by_text("Continue", exact=True).click()
            driver.wait_for_timeout(timeout=1000)
            error = driver.get_by_text("Too many signups from the same IP")
            if error.is_visible(timeout=1000):
                error = error.text_content().strip()
                print("OpenAI:", error)
                if self.changeIP:
                    self.VPN_reconnect()
                    driver.wait_for_timeout(timeout=10000)
                    return self.getAccount()
                self.do_openai = False
                raise Exception(error)
            error = driver.locator(".ulp-input-error-message")
            if error.is_visible(timeout=1000):
                error = error.text_content().strip()
                print(error)
                if error.find("The user already exists") != -1:
                    self.delEmail()
                    return self.getAccount()
                self.saveEmails()
                return self.getAccount()
            driver.wait_for_timeout(timeout=2000)
            # driver.wait_for_url(url="**/onboarding")
            print("OpenAI: waiting for verify page...")
            trys = 0
            Verify = driver.get_by_text("Verify your email")
            while not Verify.is_visible() and trys < 7:
                available = driver.locator(".onb-auth-error-msg")
                if available.is_visible():
                    available = available.text_content().strip()
                    print("OpenAI:", available)
                    if available.find("services are not available") != -1:
                        if self.changeIP:
                            self.VPN_reconnect()
                            driver.wait_for_timeout(timeout=10000)
                            self.delEmail()
                            driver.close_driver()
                            return self.getAccount()
                        self.do_openai = False
                        raise Exception(available)
                    else:
                        self.delEmail()
                        return self.getAccount()
                driver.wait_for_timeout(timeout=1000)
                trys += 1
            account = self.getemailverification()
            return account
        except Exception as e:
            print("OpenAI error:", str(e))
            self.error = str(e)
        finally:
            self.uc_dr.close_driver(True)
            self.sms.set_status()
            if not self.do_claude:
                self.delEmail()
        return None

    def saveData(self, temps=False, **kwargs):
        # dreamstudio
        url = "https://app.restoviebelle.com/openai.php"
        if temps == True:
            url += "?table=dreamstudio"
        elif temps:
            url += "?table="+temps
        if kwargs:
            payload = kwargs
        else:
            payload = {'api_key': self.api_key,
                       'email': self.email}
        headers = {}
        self.success_accounts += 1
        response = requests.request(
            "POST", url, headers=headers, data=payload)
        print(response.text)

    def getKey(self, driver, numa=0):
        driver = self.uc_dr.get_driver(headless=self.headless)
        print("OpenAI: waiting for account page...")
        try:
            driver.wait_for_url("**/overview")
        except:
            pass
        self.sms.set_status(6)
        print("OpenAI: get api key..")
        trys = 0
        # while True:
        #     try:
        f = driver.get_by_placeholder(
            "First name", exact=True, timeout=5)
        if f.is_visible():
            return self.getemailverification(False)
        self.api_key = None
        is_capche = False
        excuded = {}
        tryN = None
        while True:
            if trys >= 2:
                break
            try:
                if not is_capche:
                    driver.goto("https://platform.openai.com/api-keys")
                    verification = driver.get_by_text("Start verification")
                    if verification.is_visible():
                        verification.click()
                        driver.wait_for_timeout(timeout=3000)
                        print("OpenAI: waiting for select country...")
                        country = driver.locator(".phone-country-select")
                        if not country.is_visible(timeout=5000):
                            error = driver.locator(".onb-form-error-msg")
                            if error.is_visible():
                                error = error.text_content().strip()
                                print("OpenAI:", error)
                                continue
                        print("OpenAI: get phone number...")
                        country.click()
                        # driver.wait_for_timeout(timeout=60000000)
                        driver.wait_for_timeout(timeout=3000)
                        while True:
                            # continue
                            if tryN:
                                c = tryN
                            else:
                                c = self.sms.getrandcountry(excuded)
                            number = self.sms.get_number(c)
                            if not number:
                                print("OpenAI: no number found error=",
                                      self.sms.error)
                                if self.sms.error.find("Not enough funds") != -1:
                                    self.do_openai = False
                                    self.delEmail()
                                if self.sms.error.find("no free numbers") != -1:
                                    continue
                                return self.sms.error
                            break
                        country.locator("input").type(c)
                        driver.wait_for_timeout(timeout=1000)
                        country.locator("input").press("Enter")
                        # driver.locator(
                        #     "[id*='react-select-3-option']").get_by_text(c).click()
                        is_w = False
                        while True:
                            d = driver.locator(
                                ".phone-input-number").locator("input")
                            d.type(number)
                            wats = driver.locator(
                                "[for=whatsapp-opt-in-radio-no]")
                            if wats.is_visible():
                                wats.click()
                                driver.wait_for_timeout(timeout=2000)
                                driver.get_by_text("Send code via SMS").click()
                            else:
                                driver.get_by_text("Send code").click()
                                # d.press("Enter")
                            isd = False
                            isd2 = False
                            code = None
                            trys = 0
                            ctrys = 0
                            fails = 0
                            is_solved = False
                            driver.wait_for_timeout(timeout=3000)
                            resend = False
                            while True:
                                inp = driver.locator(
                                    ".onb-phone-check-input")
                                if inp.is_visible():
                                    inp = inp.locator("input")
                                    code = self.sms.get_sms(resend)
                                    if not code:
                                        # Resend code
                                        if not resend:
                                            driver.get_by_text(
                                                "Resend code").click()
                                            resend = True
                                            continue
                                        driver.reload()
                                        tryN = None
                                        isd = True
                                        isd2 = False
                                    break
                                else:
                                    if trys >= 20:
                                        self.sms.set_status()
                                        driver.reload()
                                        isd = True
                                        # tryN = c
                                        isd2 = False
                                        break
                                    error = driver.locator(
                                        ".onb-form-error-msg")
                                    try:
                                        if not is_solved:
                                            if ctrys >= 2:
                                                if self.changeIP:
                                                    self.VPN_reconnect()
                                                    driver.wait_for_timeout(
                                                        timeout=30000)
                                                    self.delEmail()
                                                    self.uc_dr.close_driver()
                                                    return self.getAccount()
                                                # return None
                                                driver.reload()
                                                # tryN = c
                                                isd = True
                                                isd2 = False
                                                break
                                            # solver = driver.frame_locator(
                                            #     "iframe[src*=arkose]")
                                            # solver_inner = driver.locator(
                                            #     ".captcha-solver_inner")
                                            # if solver_inner.is_visible():
                                            #     js = solver_inner.evaluate(
                                            #         "node => node.dataset.json")
                                            #     trys = 0
                                            #     if not self.solve_capcha:
                                            #         self.sms.set_status()
                                            #         self.VPN_reconnect()
                                            #         driver.wait_for_timeout(
                                            #             timeout=10000)
                                            #         self.delEmail()
                                            #         self.dr.close_driver()
                                            #         return self.getAccount()
                                            #     result = self.funCaptcha(js)
                                            #     if result:
                                            #         solver_inner.evaluate(
                                            #             "(node,code) => node.value = code", result)
                                            #         solver_inner.click()
                                            #         is_solved = True
                                            #     else:
                                            #         ctrys += 1
                                            # else:
                                            #     driver.default_content()
                                    except Exception as e:
                                        print(
                                            "funCaptcha: there is not captcha!")
                                    if error.is_visible():
                                        error = error.text_content().strip()
                                        if error.find("Our systems have detected unusual activity") != -1:
                                            if self.changeIP:
                                                self.VPN_reconnect()
                                                driver.wait_for_timeout(
                                                    timeout=10000)
                                                self.delEmail()
                                                self.uc_dr.close_driver()
                                                return self.getAccount()
                                            fails += 1
                                        if error.find("not available in your country") != -1:
                                            excuded.append(self.sms.country)
                                        print("OpenAI:", error,
                                              "fails:", fails)
                                        self.sms.set_status()
                                        tryN = None
                                        d.fill("")
                                        if error.find("too many phone verification requests") != -1:
                                            driver.wait_for_timeout(
                                                timeout=60000)
                                        else:
                                            driver.wait_for_timeout(
                                                timeout=3000)
                                        driver.reload()
                                        isd = True
                                        isd2 = False
                                        break
                                        # isd2 = True
                                        # break
                                    driver.wait_for_timeout(timeout=1000)
                                    # print("Trys: ",trys)
                                    trys += 1
                            if isd2:
                                isd2 = False
                                continue
                            break
                        if isd:
                            isd = False
                            continue
                    inp.type(code)
                    btn = driver.get_by_text("Continue")
                    if btn.is_visible():
                        btn.click()
                driver.get_by_text("Create secret key").click()
                driver.wait_for_timeout(timeout=3000)
                Done = driver.get_by_text("Done")
                Done.wait_for(timeout=20000)
                key = driver.locator(
                    ".modal-body").locator("input").get_attribute("value")
                print("OpenAI: api key", key)
                self.api_key = key
                break
            except Exception as e:
                print("getKey error:", str(e))
                break
                trys += 1
        if not self.api_key:
            return self.getKey(driver)
        #     break
        # except:You exceeded your current quota, please check your plan and billing details.
        #     trys += 1
        # if not self.api_key:
        #     driver.reload()
        #     return self.getKey(driver)
        self.saveEmails()
        self.tmpEmail.setData("openai", email=self.email,
                              api_key=self.api_key, active=1)
        # try:
        #     _chatgpt = ChatGPT()
        #     token = _chatgpt.get_access_token(self.email)
        #     accessToken = token["access_token"]
        #     refresh_token = token["refresh_token"]
        #     self.tmpEmail.setData("openai", email=self.email, api_key=self.api_key,
        #                           access_token=accessToken, refresh_token=refresh_token, active=1)
        # except:
        #     pass
        # self.saveData()
        # driver.wait_for_timeout(timeout=300000)
        # if not self.is_multi:
        #     Done.click()
        #     driver.locator(".user-section").click()
        #     driver.get_by_text("Log out", exact=True).click()
        #     driver.locator("#username").wait_for(timeout=10000)
        return self.api_key

    def get_script(self):
        with open('zon_interceptor.js', 'r') as f:
            r = f.read()
            # print(r)
            return r

    def solveCapcha(self):
        driver = self.dr.driver
        ctrys = 0
        try:
            while True:
                if ctrys >= 2:
                    if self.changeIP:
                        self.VPN_reconnect()
                        driver.wait_for_timeout(
                            timeout=30000)
                        self.delEmail()
                        self.dr.close_driver()
                        return False
                    driver.reload()
                # solver = driver.frame_locator(
                #     "iframe[src*=cloudflare]").first
                solver_inner = driver.locator(
                    ".captcha-solver_inner")
                if solver_inner.is_visible():
                    js = solver_inner.evaluate(
                        "node => node.dataset.json")
                    if not self.solve_capcha:
                        self.sms.set_status()
                        self.VPN_reconnect()
                        driver.wait_for_timeout(
                            timeout=10000)
                        self.delEmail()
                        self.dr.close_driver()
                        return False
                    result = self.turnstile(js)
                    if result:
                        solver_inner.evaluate(
                            "(node,code) => node.value = code", result)
                        solver_inner.click()
                        return True
                    else:
                        ctrys += 1
                else:
                    driver.wait_for_timeout(timeout=3000)
        except Exception as e:
            print("funCaptcha: there is not captcha!")

    def getemailverification(self, email=True):
        e = None
        # self.solveCapcha()
        print("OpenAI: waiting for email message...")
        driver = self.uc_dr.get_driver(headless=self.headless)
        taa = 0
        while True:
            if taa >= 5:
                # Resend email #onb-resend-email-btn
                driver.locator(".onb-resend-email-btn").click()
                # driver.get_by_text("Resend email", exact=True).click()
                driver.wait_for_timeout(timeout=3000)
            if taa >= 10:
                self.uc_dr.close_driver(True)
                return self.getAccount()
            if email:
                e = self.tmpEmail.getMessages("noreply@tm.openai.com")
            driver.wait_for_timeout(timeout=3000)
            if not email or e:
                if e:
                    link = e[0]
                    driver.goto(link)
                excuded = []
                name = self.email.split("@")[0].split(".")
                name = list(map(lambda v: str(v).capitalize(), name))
                print("OpenAI: fill info...", name)
                fails = 0
                tryN = None
                while True:
                    driver.get_by_placeholder(
                        "Full name", exact=True).fill(" ".join(name))
                    # driver.get_by_placeholder(
                    #     "Last name", exact=True).fill(name[1])
                    driver.wait_for_timeout(timeout=1000)
                    d = driver.get_by_placeholder(
                        "Birthday", exact=True)
                    # y = randint(1900,1995)
                    d.type(
                        f"{str(randint(1, 12)).zfill(2)}/{str(randint(1, 30)).zfill(2)}/{randint(1900,1995)}")
                    # d.press("Enter")

                    while True:
                        try:
                            if driver.locator(".onb-uinfo-continue", timeout=5).is_visible():
                                driver.locator('.onb-uinfo-continue').click()
                                driver.sleep(3)
                                continue
                            else:
                                break
                        except:
                            pass
                    break
                self.api_key = self.getKey(driver)
                # driver.wait_for_timeout(timeout=3000)
                return self.api_key
                # Kenya = driver.get_by_text("Kenya")
                # Kenya.wait_for(timeout=6000, state="visible")
                # Kenya.nth(1).click()
                # driver.wait_for_timeout(timeout=100000)
            else:
                sleep(3)
                taa += 1

    def isRuning3(self, runing=-1):
        return False
        if os.path.exists("isRun.txt"):
            f = open('isRun.txt', 'r')
            d = f.read()
            f.close()
            if d.find("True") != -1 and runing == -1:
                return True
        if runing != -1:
            f = open('isRun.txt', 'w')
            f.write(str(runing))
            f.close()
        return False

    def claude3(self, **kwargs):
        email = kwargs.get("email", self.email)
        close = kwargs.get("close", True)
        try:
            temp = False
            if not self.do_claude:
                return None
            self.getEmail()
            if not email:
                email = self.tmpEmail.getGmail(uses="claude")
            if not self.email:
                email = self.gmail(email=email, close=False)
            if not email:
                return None
            self.email = email
            self.dr.Blocks = False
            driver = self.dr.get_driver(
                user_dir=None, headless=self.headless)
            print("Claude: go to account ...")
            driver.goto("https://claude.ai/login")
            driver.wait_for_timeout(timeout=3000)
            print("Claude: fill info ...")
            name = email.split("@")[0].split(".")
            name.append("claude")
            name = list(map(lambda v: str(v).capitalize(), name))
            # driver.locator("#email").fill(email)
            with driver.context.expect_page() as new_page_info:
                driver.get_by_text("Continue with Google").click()
            new_page = new_page_info.value
            new_page.wait_for_load_state()
            new_page.locator("div[data-identifier*=gmail]").nth(0).click()
            self.api_key = None

            def resource(route):
                # if route.request.url.find("auth/verify_google") != -1:
                if route.request.url.find("auth/verify_code") != -1:
                    code = route.request.post_data_json
                    self.api_key = _claude.login(code)
                route.continue_()
            driver.route("**/*", resource)
            while True:
                if not self.api_key:
                    driver.wait_for_timeout(timeout=3000)
                    continue
                self.saveEmails("claude")
                self.saveData("claude")
                self.tmpEmail.upGmail(uses="claude")
                print("Claude: api key", self.api_key)
                return self.api_key
        except Exception as e:
            self.error = str(e)
            print("Claude error:", str(e))
        finally:
            if close:
                self.delEmail()
                self.dr.close_driver(True)

    def claude(self, **kwargs):
        email = kwargs.get("email", None)
        close = kwargs.get("close", True)
        try:
            temp = False
            if not self.do_claude:
                return None
            self.getEmail()
            if not email:
                email = self.tmpEmail.getGmail(uses="claude")
            if not email:
                email = self.tmpEmail.getGmail(table="outlook", uses='claude')
            if not email:
                email = self.tmpEmail.getData("claude", api_key='')
            # if not self.email:
            if not email:
                email = self.outlook(close=False)
            if not email:
                return None
            if type(email) == list:
                email = email[0]["email"]
            # email = email.strip()
            self.email = email
            email = email.strip()
            self.tmpEmail.email = email
            self.dr.Blocks = False
            driver = self.uc_dr.get_driver(
                headless=self.headless, user_dir=None)
            print("Claude: go to account ...", email)
            driver.goto("https://claude.ai/chat/")
            driver.wait_for_timeout(timeout=5000)

            def resource(route):
                if route.request.url.find("auth/send_code") != -1:
                    code = route.request.post_data_json
                    code = _claude.get_key(code)
                    print(code)
                if route.request.url.find("auth/verify_code") != -1:
                    code = route.request.post_data_json
                    self.api_key = _claude.login(code)
                route.continue_()
            # driver.route("**/*", resource)
            print("Claude: fill info ...")
            name = email.split("@")[0].split(".")
            name.append("claude")
            name = list(map(lambda v: str(v).capitalize(), name))

            isd = False
            inp = None
            self.vpn_requset("disconnect")
            em = driver.locator("#email")
            try:
                em.wait_for()
            except:
                self.vpn_requset("connect")
                self.dr.close_driver(True)
                return self.claude()
            em.fill(email)
            try:
                while True:

                    inp = driver.locator("#code")
                    btn = driver.locator("[data-testid=\"continue\"]")
                    try:
                        # not btn.is_visible(timeout=5000) or
                        if inp.is_visible():
                            # self.vpn_requset("connect")
                            break
                    except Exception as e:
                        print("Claude code:", str(e))
                    if btn.is_disabled(timeout=5000):
                        continue
                    else:
                        btn.click(timeout=5000)
                        driver.wait_for_timeout(timeout=5000)
                    error = driver.locator("[id*=error]")
                    if error.is_visible():
                        error = error.text_content().strip()
                        if error.find("There was an error sending you a login link") != -1 and self.changeIP:
                            # self.VPN_reconnect()
                            # self.vpn_requset("disconnect")
                            # driver.wait_for_timeout(timeout=10000)
                            isd = True
                            continue
                        # raise Exception(error)
                    # break
            except Exception as e:
                print("Claude error 1:", str(e))
            self.vpn_requset("connect")
            print("Connect and get code:", email)
            try:
                inp = driver.locator("#code")
                inp.wait_for(timeout=30000)

                # inp.fill("123445")
                # data-testid="code"
            except Exception as e:
                print("Claude error code:", str(e))
                # return self.claude(**kwargs)
            code = None
            number = False
            resend = False
            trys = 0
            numa = None
            coded = None
            while True:
                if trys > 7:
                    self.tmpEmail.setData("claude", email=self.email, active=0)
                    return "ERROR"
                print("Claude: get code:", email)
                if not numa:
                    coded = self.tmpEmail.getMessages(
                        "support@mail.anthropic.com")
                if coded:
                    numa = coded[0]
                    print("Claude: get code:", email, numa)
                    inp.fill(numa)
                    inp.evaluate("(node,code)=> node.value = code", numa)
                    driver.wait_for_timeout(timeout=5000)
                    driver.locator("[data-testid=\"continue\"]").click()
                    driver.wait_for_timeout(timeout=5000)
                    error = driver.locator("[id*=error]")
                    if error.is_visible():
                        if error.text_content().strip().find("There was an error verifying your code") != -1:
                            self.vpn_requset("disconnect")
                        continue
                    break
                driver.wait_for_timeout(timeout=3000)
                # sleep(3)
                trys += 1
            print("Claude: fill info 2...")
            while True:
                try:
                    error = driver.locator("[id*=error]", 5)
                    if error.is_visible():
                        error = error.text_content().strip()
                        print("Claude error:", error)
                        # if error.find("There was an error verifying your code") != -1:
                        #     self.vpn_requset("disconnect")
                        # break
                    fullname = driver.locator("#fullname", 5)
                    # chat = driver.get_by_text("Start a new chat", exact=True)
                    menu = driver.locator(
                        "button[data-testid='command-menu']", 5)
                    # plans = driver.get_by_text(
                    #   "Get notified about paid plans", exact=True)
                    if fullname.is_visible():
                        try:
                            fullname.wait_for(timeout=10000)
                            displayname = driver.locator("#displayname")
                            fullname.fill(" ".join(name))
                            displayname.fill(" ".join(name))
                            driver.get_by_label("18 years old").click()
                            driver.get_by_label("I agree to").click()
                            driver.get_by_text("Continue", exact=True).click()
                        except Exception as e:
                            print("Claude error:", str(e))
                    elif menu.is_visible():
                        if menu.is_visible():
                            menu.click()
                        break
                    phone = driver.locator("#phone", 5)
                    if phone.is_visible():
                        c = self.sms.getrandcountry([], "acz")
                        driver.locator(
                            "div[aria-controls*='country-listbox']").click()
                        driver.wait_for_timeout(timeout=1000)
                        driver.locator(
                            f"li[data-country-code='{c}']").click()
                        number = self.sms.get_number(c)
                        if not number:
                            print("OpenAI: no number found error=",
                                  self.sms.error)
                            if self.sms.error.find("Not enough funds") != -1:
                                self.do_openai = False
                                return None
                            if self.sms.error.find("no free numbers") != -1:
                                continue
                            raise Exception(self.sms.error)
                        else:
                            phone.fill(number)
                            driver.get_by_text(
                                "Send SMS Code", exact=True).click()
                            driver.wait_for_timeout(timeout=5000)
                            phone_error = driver.locator(
                                "#phone-error")
                            if phone_error.is_visible():
                                phone_error = phone_error.text_content().strip()
                                print("Claude error:", phone_error)
                                continue
                    inp = driver.locator("#code")
                    if number and inp.is_visible():
                        code = self.sms.get_sms()
                        if code:
                            inp.fill(code)
                            driver.get_by_text("Verify Code").click()
                            driver.wait_for_timeout(timeout=3000)
                    Next = driver.get_by_text("Next", exact=True)
                    Finish = driver.get_by_text("Finish", exact=True)
                    if Next.is_visible():
                        Next.click()
                    elif Finish.is_visible():
                        Finish.click()
                    driver.wait_for_timeout(timeout=2000)
                except Exception as e:
                    print("Claude error 2:", str(e))
            # driver.wait_for_timeout(timeout=3000000)
            sessionKey = self.uc_dr.get_cookies(True)
            sessionKey = sessionKey["sessionKey"]
            self.api_key = sessionKey
            self.saveEmails("claude")
            # self.saveData("claude")
            self.tmpEmail.upGmail(uses="claude")
            self.tmpEmail.setData("claude", email=self.email,
                                  api_key=self.api_key, active=1)
            print("Claude: api key", self.api_key)
            return self.api_key
        except Exception as e:
            self.error = str(e)
            print("Claude error:", str(e))
        finally:
            if close:
                self.delEmail()
                self.uc_dr.close_driver(True)
        return None

    def claude2(self, email=None):
        try:
            temp = False
            if not self.do_claude:
                return None
            self.getEmail()
            if not email:
                temp = True
                email = self.tmpEmail.getEmail(None)
            else:
                email = self.tmpEmail.getAlias(email)
                # return None
            if not email:
                return None
            self.email = email
            self.dr.Blocks = False
            # proxy = {
            #     'server': "51.77.203.120:3128",
            #     'username': 'mohtasm',
            #     'password': 'mohtasm10QQ',
            # }
            driver = self.dr.get_driver(
                user_dir=None, headless=self.headless)
            print("Claude: go to account ...")
            driver.goto("https://claude.ai/login")
            driver.wait_for_timeout(timeout=3000)
            print("Claude: fill info ...")
            name = email.split("@")[0].split(".")
            name = list(map(lambda v: str(v).capitalize(), name))
            driver.locator("#email").fill(email)
            driver.get_by_text("Continue with email").click()
            driver.wait_for_timeout(timeout=3000)
            error = driver.locator("[id*=error]")
            if error.is_visible():
                error = error.text_content().strip()
                if error.find("There was an error sending you a login link") != -1 and self.changeIP:
                    self.VPN_reconnect()
                    driver.wait_for_timeout(timeout=10000)
                    self.delEmail()
                    return self.claude()
                raise Exception(error)
            # driver.screenshot(path="screenshot.png")
            inp = driver.locator("#code")
            inp.wait_for(timeout=30000)
            code = None
            while True:
                if temp:
                    code = self.tmpEmail.getMessages(
                        "support@mail.anthropic.com")
                else:
                    code = getEmails("support@mail.anthropic.com")
                if code:
                    inp.fill(code[0])
                    driver.get_by_text("Continue with login code").click()
                    break
            if temp:
                error = driver.locator("[id*=error]")
                if error.is_visible():
                    error = error.text_content().strip()
                    print("Claude error:", error)
                driver.wait_for_url("**/onboarding**")
                try:
                    fullname = driver.locator("#fullname")
                    fullname.wait_for(timeout=10000)
                    displayname = driver.locator("#displayname")
                    fullname.fill(" ".join(name))
                    displayname.fill(" ".join(name))
                    driver.get_by_label("18 years old").click()
                    driver.get_by_label("I agree to").click()
                    driver.get_by_text("Continue", exact=True).click()
                    while True:
                        Next = driver.get_by_text("Next", exact=True)
                        Finish = driver.get_by_text("Finish", exact=True)
                        if Next.is_visible():
                            Next.click()
                        elif Finish.is_visible():
                            Finish.click()
                            break
                    driver.wait_for_url("**/chat**")
                except:
                    pass
            else:
                driver.wait_for_url("**/chat**")
            # driver.wait_for_timeout(300000)
            # driver.wait_for_url("**/chat**")
            sessionKey = self.dr.get_cookies(True)
            sessionKey = sessionKey["sessionKey"]
            self.api_key = sessionKey
            self.saveEmails("claude")
            self.saveData("claude")
            print("Claude: api key", sessionKey)
            return sessionKey
            driver.wait_for_timeout(30000)
        except Exception as e:
            self.error = str(e)
            print("Claude error:", str(e))
        finally:
            # self.tmpEmail.deleteEmail()
            self.dr.close_driver(True)

    def bard(self, email, password):
        try:
            self.headless = False
            driver = self.dr.get_driver(
                user_dir=None, headless=self.headless)
            print("bard: go to account ...")
            driver.goto("https://bard.google.com/")
            driver.wait_for_timeout(timeout=3000)
            solver_inner = driver.locator(
                ".captcha-solver_inner")
            if solver_inner.is_visible():
                js = solver_inner.evaluate(
                    "node => node.dataset.json")
                print(js)
            driver.get_by_text("Sign in", exact=True).nth(1).click()
            driver.wait_for_timeout(timeout=3000)
            print("bard: fill info ...")
            d = driver.locator("#identifierId")
            d.fill(email)
            d.press("Enter")
            driver.wait_for_timeout(timeout=3000)
            # driver.locator(
            #     "[data-primary-action-label=Next]").locator("button[name=Next]").click()
            d = driver.locator("input[name=Passwd]")
            d.fill(password)
            d.press("Enter")
            # driver.locator(
            #     "[data-primary-action-label=Next]").locator("button[name=Next]").nth(1).click()
            driver.wait_for_timeout(timeout=60000)
        except Exception as e:
            self.error = str(e)
            print("bard error: ", self.error)
            return None
        finally:
            self.dr.close_driver(True)

    def gmail_login(self, email):
        if type(email) is str:
            email = self.tmpEmail.getGmail(email=email)
        if not email:
            return None
        Passwd = email[0]["password"]
        email = email[0]["email"]
        driver = self.dr.get_driver(
            user_dir=None, headless=self.headless)
        driver.goto("https://www.google.com/?hl=en")
        driver.get_by_text("Sign in", exact=True).nth(0).click()
        driver.locator("#identifierId").fill(email)
        driver.get_by_text("Next", exact=True).nth(0).click()
        is_solve = False
        while True:
            p = driver.locator("input[name=Passwd]")
            if p.is_visible():
                p.fill(Passwd)
                driver.get_by_text("Next", exact=True).nth(0).click()
                break
            Captcha = driver.locator("#captchaimg")
            if not is_solve and Captcha.is_visible():
                src = Captcha.get_attribute("src")
                src = "https://accounts.google.com"+src
                print(src)
                try:
                    result = self.solver.normal(src)
                    code = result["code"]
                    print(code)
                    driver.locator("#ca").fill(code)
                    driver.get_by_text("Next", exact=True).nth(0).click()
                    driver.wait_for_timeout(timeout=3000)
                    reenter = driver.get_by_text(
                        "Please re-enter the characters")
                    if not reenter.is_visible():
                        is_solve = True
                except Exception as e:
                    print(e)
        is_verification = False
        while True:
            try:
                verification = driver.get_by_text("Get a verification code at")
                if verification.is_visible():
                    verification.click()
                    driver.wait_for_timeout(timeout=3000)
                    is_verification = True
                if is_verification:
                    code = getEmails("noreply@google.com")
                    if code:
                        driver.locator("#idvPinId").fill(code[0])
                        driver.get_by_text("Next", exact=True).nth(0).click()
                        is_verification = False
                v = driver.get_by_text("Verify your identity", exact=True)
                if v.is_visible():
                    country = driver.locator("#countryList")
                    print("OpenAI: get phone number...")
                    c = "India"
                    while True:
                        while True:
                            c = self.sms.getrandcountry([], "go")
                            number = self.sms.get_number(c)
                            if not number:
                                print("OpenAI: no number found error=",
                                      self.sms.error)
                                if self.sms.error.find("Not enough funds") != -1:
                                    self.do_openai = False
                                    self.delEmail()
                                if self.sms.error.find("no free numbers") != -1:
                                    continue
                                return None
                            break
                        country.click()
                        driver.wait_for_timeout(timeout=1000)
                        country.get_by_text(c+" (").nth(0).click(force=True)
                        driver.locator("#deviceAddress").fill(number)
                        driver.locator("#next-button").click()
                        driver.wait_for_timeout(timeout=3000)
                        error = driver.locator("#error")
                        if error.is_visible():
                            error = error.text_content().strip()
                            print("Gmail:", error)
                            if error.find("been used too many times") != -1 or error.find("phone number cannot be used") != -1:
                                continue
                        inp = driver.locator("#smsUserPin")
                        code = self.sms.get_sms()
                        if not code:
                            driver.go_back()
                            continue
                        inp.fill(code)
                        break
                    driver.locator("#next-button").click()
                    driver.wait_for_timeout(timeout=3000)
                notnow = driver.get_by_text("Not now", exact=True)
                if notnow.is_visible():
                    notnow.nth(0).click(force=True)
                    driver.wait_for_timeout(timeout=3000)
                q = driver.locator("[name=q]")
                if q.is_visible():
                    break

            except:
                pass
        self.add_auth()
        return email

    def outlook(self, **kwargs):
        close = kwargs.get("close", True)
        email = kwargs.get("email", None)
        try:
            if email:
                return self.gmail_login(email)
            self.getEmail()
            self.email = self.tmpEmail.getEmail()
            if not self.email:
                return None
            # self.headless = False
            email = self.email
            driver = self.uc_dr.get_driver(
                user_dir=None, headless=self.headless)
            print("Outlook: fill info ...")
            name = email.split("@")[0].split(".")
            # name = list(map(lambda v: str(v).capitalize(), name))
            driver.goto("https://outlook.live.com/mail/0/inbox?nlp=1")
            driver.wait_for_timeout(timeout=3000)
            driver.locator("#signup").click()
            driver.get_by_text("Get a new email address",
                               exact=True).nth(0).click()
            driver.wait_for_timeout(timeout=3000)
            driver.locator("#MemberName").fill("".join(name))
            driver.locator("#iSignupAction").click()
            password = "mohtasm10QQ@@"
            driver.locator("#PasswordInput", 20).nth(0).fill(password)
            driver.locator("#iSignupAction").click()
            driver.locator("#FirstName").fill(name[0].capitalize())
            driver.locator("#LastName").fill(name[1].capitalize())
            driver.locator("#iSignupAction").click()
            driver.locator("#BirthMonth").select_option("3")
            driver.locator("#BirthDay").select_option("15")
            driver.locator("#BirthYear").fill("1994")
            driver.locator("#iSignupAction").click()
            driver.wait_for_timeout(timeout=5000)
            trys = 0
            while True:
                driver.captcha()
                c = driver.locator("#unified-consent-continue-button").nth(0)
                if c.is_visible():
                    c.click(force=True)
                    break
                continue
                # solver = driver.frame_locator(
                #     "iframe[src*=arkose]").first
                # solver = solver.frame_locator(
                #     "iframe[src*=arkose]").first
                solver_inner = driver.locator(
                    ".captcha-solver_inner")
                js = solver_inner.evaluate(
                    "return node.dataset.json")
                if js is None:
                    continue
                trys = 0
                if not self.solve_capcha:
                    return None
                result = self.funCaptcha(js)
                if result:
                    solver_inner.evaluate(
                        "(node,code) => node.value = code", result)
                    solver_inner.click()
                    driver.wait_for_timeout(timeout=5000)
                    break
                else:
                    trys += 1
            # driver.get_by_text("Continue", exact=True).nth(0).click()
            driver.wait_for_url("**/mail**")
            driver.goto("https://app.restoviebelle.com/hotmail.php")
            driver.wait_for_timeout(timeout=3000)
            driver.locator("#idBtn_Accept").click()
            driver.wait_for_url("**state=**")
            driver.wait_for_timeout(timeout=3000)
            email = "".join(name)+"@outlook.com"
            return email
            # driver.wait_for_timeout(timeout=600000)
        except Exception as e:
            self.error = str(e)
            print("Chatgpt error: ", self.error)

        finally:
            if close:
                self.uc_dr.close_driver(True)
        return None

    def gmail(self, **kwargs):
        close = kwargs.get("close", True)
        email = kwargs.get("email", None)
        try:
            if email:
                return self.gmail_login(email)
            self.getEmail()
            self.email = self.tmpEmail.getEmail()
            if not self.email:
                return None
            # self.headless = False
            email = self.email
            driver = self.dr.get_driver(
                user_dir=None, headless=self.headless)
            print("Gmail: fill info ...")
            name = email.split("@")[0].split(".")
            name = list(map(lambda v: str(v).capitalize(), name))
            driver.goto("https://www.google.com/")
            driver.wait_for_timeout(timeout=3000)
            driver.get_by_text("Sign in", exact=True).nth(0).click()
            driver.wait_for_timeout(timeout=3000)
            driver.get_by_text("Create account", exact=True).nth(0).click()
            driver.wait_for_timeout(timeout=3000)
            personal = driver.get_by_text("For my personal use",
                                          exact=True)
            if personal.is_visible():
                personal.nth(0).click(force=True)
            driver.locator("#firstName").fill(name[0])
            d = driver.locator("#lastName")
            d.fill(name[1])
            driver.get_by_text("Next", exact=True).nth(0).click()
            driver.locator("#month").select_option("3")
            driver.locator("#day").fill("15")
            driver.locator("#year").fill("1994")
            d = driver.locator("#gender")
            d.select_option("1")
            # d.press("Enter")
            driver.get_by_text("Next", exact=True).nth(0).click()
            email = driver.locator("#selectionc0")
            email.click()
            email = email.text_content().strip()
            print(email)
            password = "mohtasm10QQ@@"
            driver.get_by_text("Next", exact=True).nth(0).click()
            driver.locator("#passwd input").nth(0).fill(password)
            driver.locator("#confirm-passwd input").nth(0).fill(password)
            driver.get_by_text("Next", exact=True).nth(0).click()
            while True:
                couldnot = driver.get_by_text("we could not create").nth(0)
                if couldnot.is_visible():
                    couldnot = couldnot.text_content().strip()
                    print("Gmail:", couldnot)
                    return None
                country = driver.locator("#countryList")
                if country.is_visible():
                    break
            print("OpenAI: get phone number...")
            c = "India"
            while True:
                while True:
                    c = self.sms.getrandcountry([], "go")
                    number = self.sms.get_number(c)
                    if not number:
                        print("OpenAI: no number found error=", self.sms.error)
                        if self.sms.error.find("Not enough funds") != -1:
                            self.do_openai = False
                            self.delEmail()
                        if self.sms.error.find("no free numbers") != -1:
                            continue
                        return None
                    break
                country.click()
                country.type(c)
                driver.wait_for_timeout(timeout=1000)
                driver.locator(
                    "[role=listbox]").get_by_text(c+" (").nth(0).click()
                driver.locator("#phoneNumberId").fill(number)
                driver.get_by_text("Next", exact=True).nth(0).click()
                driver.wait_for_timeout(timeout=5000)
                errors = driver.locator("[aria-live=polite]")
                is_error = False
                for i in range(errors.count()):
                    error = errors.nth(i)
                    if error and error.is_visible() and error.text_content().strip():
                        error = error.text_content().strip()
                        print("Gmail:", error)
                        if error.find("been used too many times") != -1 or error.find("phone number cannot be used") != -1 or error.find("number format") != -1:
                            # self.sms.set_status()
                            is_error = True
                            break
                if is_error:
                    continue
                inp = driver.locator("#code")
                code = self.sms.get_sms()
                if not code:
                    new_code = driver.get_by_text(
                        "Get new code", exact=True)
                    if new_code.is_visible():
                        new_code.nth(0).click()
                    continue
                inp.fill(code)
                break
            driver.get_by_text("Next", exact=True).nth(0).click()
            # driver.locator("#recoveryEmailId").fill("mohtasm.com@gmail.com")
            # driver.get_by_text("Next", exact=True).nth(0).click()
            driver.get_by_text("Skip", exact=True).nth(0).click()
            driver.wait_for_timeout(timeout=3000)
            while True:
                try:
                    driver.get_by_text("Skip", exact=True).nth(0).click()
                    driver.get_by_text("Next", exact=True).nth(0).click()
                    driver.get_by_text("I agree", exact=True).nth(0).click()
                    break
                except:
                    pass
            driver.wait_for_timeout(timeout=3000)
            # driver.get_by_text("Confirm", exact=True).click(force=True)
            driver.get_by_role(role="button", name="Confirm").click(force=True)
            # driver.locator("role=button[name='Confirm']")
            driver.locator("[name=q]").wait_for()
            self.saveData("gmail", email=email, password=password)
            self.add_auth()
            # print("Gmail:", email, password)
            self.email = email
            self.tmpEmail.gmail = {"email": email,
                                   "password": password, "uses": ""}
            return email
            # driver.wait_for_timeout(timeout=600000)
        except Exception as e:
            self.error = str(e)
            print("Chatgpt error: ", self.error)

        finally:
            if close:
                self.dr.close_driver(True)
        return None

    def add_auth(self):
        try:
            driver = self.dr.driver
            driver.goto(
                "https://app.restoviebelle.com/openai.php?get=auth")
            driver.wait_for_timeout(timeout=3000)
            btn = driver.locator("div[data-identifier*='gmail.com']").nth(0)
            btn.evaluate("(node) => node.click()")
            # driver.get_by_text("Advanced", exact=True).nth(0).click()
            # driver.wait_for_timeout(timeout=2000)
            driver.wait_for_load_state("domcontentloaded")
            driver.get_by_text("(unsafe)").nth(
                0).evaluate("(node) => node.click()")
            driver.wait_for_load_state("domcontentloaded")
            driver.wait_for_timeout(timeout=3000)
            trys = 0
            while True:
                if trys >= 10:
                    raise Exception("too many tries")
                if driver.url.find("myaccount.google.com") != -1:
                    raise Exception("wrong url!")
                already = driver.get_by_text("already has some access")
                Select = driver.get_by_text("Select all", exact=True).nth(0)

                if already.is_visible():
                    break
                if Select.is_visible():
                    Select.evaluate("(node) => node.click()")
                    driver.wait_for_timeout(timeout=3000)
                    Select2 = driver.locator(
                        "input[aria-labelledby='selectioni3']").nth(0)
                    if Select2.is_checked():
                        break
                    else:
                        raise Exception("Select all not checked")
                trys += 1
                driver.wait_for_timeout(timeout=3000)
            driver.wait_for_timeout(timeout=3000)
            driver.get_by_text("Continue", exact=True).nth(0).click()
            driver.wait_for_url("**state=**")
        except Exception as e:
            print("add_auth error: ", str(e))
            return self.add_auth()
        # driver.wait_for_timeout(timeout=50000000)

    def add_email(self):
        driver = self.dr.driver
        driver.goto(
            "https://mail.google.com/mail/u/0/?tab=rm&ogbl#settings/fwdandpop")
        driver.locator("input[value='Add a forwarding address']").click()
        with driver.context.expect_page() as new_page_info:
            alertdialog = driver.get_by_role("alertdialog")
            alertdialog.wait_for()
            alertdialog.locator("input").nth(0).fill("mohtasm.com@gmail.com")
            alertdialog.get_by_role("button", name="next").click()
        new_page = new_page_info.value
        new_page.wait_for_load_state()
        new_page.locator("input[value=Proceed]").nth(0).click()
        confirmation = driver.get_by_text("A confirmation link has been")
        confirmation.wait_for()
        while True:
            c = getEmails("forwarding-noreply@google.com")
            if c:
                driver.goto(c[0])
                driver.locator("input[value='Confirm']").click()
                break
        driver.goto(
            "https://mail.google.com/mail/u/0/?tab=rm&ogbl#settings/fwdandpop")
        driver.locator("input[name=sx_em][value='1']").click()
        driver.get_by_text("Save Changes", exact=True).nth(0).click()

    def chatgpt2(self, email):
        try:
            if not email:
                email = self.tmpEmail.getData("openai", access_token='')
                if email:
                    email = email[0]["email"]
            if not email:
                return None
            driver = self.dr.get_driver(
                user_dir=None, headless=self.headless)
            print("Chatgpt: go to account ...")
            driver.goto("https://chat.openai.com/")
            driver.wait_for_timeout(timeout=3000)
            driver.get_by_text("Log in", exact=True).click()
            print("Chatgpt: fill info ...")
            driver.locator("#username").fill(email)
            driver.get_by_text("Continue", exact=True).click()
            driver.locator("#password").fill(email)
            driver.get_by_text("Continue", exact=True).nth(1).click()
            driver.get_by_text("New chat", exact=True).wait_for()
            driver.goto("https://chat.openai.com/api/auth/session")
            html = driver.locator("pre")
            token = json.loads(html.text_content())
            accessToken = token["accessToken"]
            self.tmpEmail.setData("openai", email=email,
                                  access_token=accessToken)
            print(accessToken)
            return accessToken
        except Exception as e:
            self.error = str(e)
            print("Chatgpt error: ", self.error)
            return None
        finally:
            self.dr.close_driver(True)

    def chatgpt(self, email, refresh_token=None):
        try:
            if not refresh_token:
                if not email:
                    email = self.tmpEmail.getData("openai", access_token='')
                    # print(email)
                    if email:
                        refresh_token = email[0]["refresh_token"]
                        email = email[0]["email"]
                if not email:
                    return None
            _chatgpt = ChatGPT()
            print(email, refresh_token)
            if refresh_token:
                token = _chatgpt.refresh_access_token(refresh_token)
            else:
                token = _chatgpt.get_access_token(email)
                refresh_token = token["refresh_token"]
            accessToken = token["access_token"]
            self.tmpEmail.setData("openai", email=email,
                                  access_token=accessToken, refresh_token=refresh_token)
            print(accessToken)
            return accessToken
        except Exception as e:
            self.error = str(e)
            if self.error.find("Too many") != -1 and self.changeIP:
                self.VPN_reconnect()
                sleep(10)
                return self.chatgpt(email)
            print("Chatgpt error: ", self.error)

        finally:
            self.dr.close_driver(True)
        return None

    def get_pintrest(self, username, password):
        # username = "admin@restoviebelle.com"
        # password = "mohtasm10QQ@@"
        try:
            if not username or not password:
                self.error = "Username and password is required!"
                return None
            self.dr.Blocks = False
            # self.headless = False
            driver = self.dr.get_driver(
                user_dir=None, headless=self.headless)
            print("Pinterest: go to account ...")
            driver.goto("https://www.pinterest.com/SnakeSnuggles/")
            driver.wait_for_timeout(timeout=3000)
            driver.locator("body").evaluate(
                "(node) => node.removeAttribute('style')")
            driver.locator("[data-test-id=login-button]").click()
            print("Pinterest: fill info ...")
            driver.locator("#email").fill(username)
            driver.locator("#password").fill(password)
            try:
                driver.locator(
                    "[data-test-id=registerFormSubmitButton]").locator("button").click(timeout=0)
            except Exception as e:
                print("Pinterest error: can't click to login button ...")
                return self.get_pintrest(username, password)
            driver.wait_for_timeout(timeout=3000)
            error = driver.locator("[id*=error]")
            if error.is_visible():
                error = error.text_content()
                raise Exception(error)
            cookies = self.dr.http_cookies()
            f = open(f"pinterest_bot_cookie{username}", "w")
            f.write(cookies)
            f.close()
            return cookies
        except Exception as e:
            self.error = str(e)
            print("Pinterest error: ", self.error)

        finally:
            self.dr.close_driver(True)
        return None

    def saveEmails(self, temps=False, file="tempemail"):
        return None
        sp = "openai:"
        if temps == True:
            sp = "dreamstudio:"
        elif temps:
            sp = temps+":"
        self.emails.append(self.email)
        with open(file+'.txt', 'w') as f:
            def e(v):
                if v.strip() == self.email:
                    if self.api_key:
                        v = f"{sp}{v.strip()}:{self.api_key}\n"
                    else:
                        v = sp+v
                return v
            self.emails = map(e, self.emails)
            # self.emails = list(set(self.emails))
            f.writelines(self.emails)
            f.close()
            # self.getEmail()

    def dreamstudio(self, url=None):
        try:
            self.error = ""
            if not self.do_dreamstudio:
                return False
            self.getEmail()
            if not self.email:
                self.email = self.tmpEmail.getEmail(None)
            if not self.email:
                return None
            # self.email = "de.yohalu@everysimply.com"
            self.api_key = None
            is_active = url
            driver = self.dr.get_driver(user_dir=None, headless=self.headless)
            if not url:
                url = "https://dreamstudio.ai/account"
            driver.goto(url)
            print("Dreamstudio: waiting for login page...")
            if not is_active:
                driver.wait_for_url("**/login**")
            is_login = False
            login = driver.locator("#username")
            if login.is_visible(timeout=3000):
                login.nth(0).click()
                if not is_active:
                    driver.get_by_text(text="Sign up", exact=True).click()
                # driver.wait_for_timeout(timeout=3000)
                print("Dreamstudio: fill info...")
                driver.locator(
                    "#email" if not is_active else "#username").fill(self.email)
                driver.locator("#password").fill("mohtasm10QQ@@")
                driver.get_by_text(text="Continue", exact=True).click()
                trys = 0
                while True:
                    error = driver.locator("#prompt-alert")
                    if error.is_visible(timeout=3000):
                        error = error.text_content().strip()
                        print("Dreamstudio:", error)
                        if error.find("Something went wrong") != -1:
                            self.delEmail()
                            return self.dreamstudio()
                    try:
                        driver.wait_for_url("**/generate")
                        break
                    except:
                        if trys > 7:
                            raise Exception(
                                "Dreamstudio: Timeout to find generate page...")
                        trys += 1
                        driver.wait_for_timeout(timeout=1000)
                print("Dreamstudio: waiting for email message ...")
                trys = 0
                while not is_active:
                    # e = self.tmpEmail.getMessages("dreamstudio@stability.ai")
                    e = self.tmpEmail.getMessages("platform@stability.ai")
                    if e:
                        link = e[0]
                        driver.goto(link)
                        self.closeModal(driver)
                        login = driver.get_by_role(role="button", name="Login")
                        if login.is_visible(timeout=3000):
                            login.nth(0).click()
                        Accept = driver.get_by_role(
                            role="button", name="Accept").nth(0)
                        if Accept.is_visible(timeout=3000):
                            Accept.click()
                        break
                    if trys > 10:
                        self.delEmail()
                        self.dr.close_driver(True)
                        return self.dreamstudio()
                    trys += 1
                    driver.wait_for_timeout(timeout=3000)
            else:
                is_login = True
            driver.wait_for_url("**/generate")
            print("Dreamstudio: go to account ...")
            driver.goto("https://dreamstudio.ai/account")
            driver.wait_for_url("**/account")
            self.closeModal(driver)
            print("Dreamstudio: get api key from account ...")
            m = driver.locator(
                ".rounded.border.border-zinc-700.bg-zinc-800.p-5.h-fit.w-1\/2.grow.self-start.overflow-x-auto.truncate")
            m.locator("button").nth(2).click()
            Confirm = driver.get_by_role(role="button", name="Confirm")
            if Confirm.is_visible(timeout=5000):
                Confirm.nth(0).click()
            key = m.get_by_text(text="sk-").text_content()
            cr = driver.locator(
                ".rounded.border.border-zinc-700.bg-zinc-800.p-5.flex.h-fit.flex-col")
            print("Dreamstudio: waiting for credits ...")
            c = None
            trys = 0
            while not c:
                c = cr.locator("span").nth(0).text_content()
                if trys >= 15:
                    return self.dreamstudio("https://dreamstudio.ai/generate")
                trys += 1
                driver.wait_for_timeout(timeout=2000)
            print("Credits: ", c)
            self.api_key = key
            self.saveEmails(True)
            self.saveData(True)
            print("Dreamstudio: api key", key)
            return key
        except Exception as e:
            print("Dreamstudio error:", str(e))
            self.error = str(e)

        finally:
            if not self.is_multi or not self.do_openai:
                self.tmpEmail.deleteEmail()
            self.dr.close_driver()
        return None
        # driver.wait_for_timeout(timeout=30000)

    def scraperapi(self):
        try:
            self.error = ""
            if not self.do_scraperapi:
                return False
            self.getEmail()
            if not self.email:
                self.email = self.tmpEmail.getEmail(None)
            if not self.email:
                return None
            email = self.email
            self.api_key = None
            # self.headless = False
            driver = self.dr.get_driver(user_dir=None, headless=self.headless)
            url = "https://dashboard.scraperapi.com/signup"
            driver.goto(url)
            print("Scraperapi: fill info ...")
            driver.wait_for_timeout(timeout=3000)
            name = email.split("@")[0].split(".")
            name.append("mutasim")
            driver.locator("#email").fill(email)
            driver.locator("#password").fill("mohtasm10QQ@@")
            solver_inner = driver.locator(
                ".captcha-solver_inner")
            solver_inner.wait_for()
            ctrys = 0
            if solver_inner.is_visible():
                js = solver_inner.evaluate(
                    "node => node.dataset.json")
                result = self.reCaptcha(js)
                if result:
                    solver_inner.evaluate(
                        "(node,code) => node.value = code", result)
                    solver_inner.click()
                else:
                    ctrys += 1
            # driver.locator("#g-recaptcha-response").evaluate(
            #     "(node,code) => node.innerText = code", code)
            driver.wait_for_timeout(timeout=3000)
            driver.locator("#terms").click()
            driver.get_by_text("Sign up with email", exact=True).click()
            while True:
                Activation = driver.get_by_text(
                    "Send Activation Email", exact=True)
                blocked = driver.get_by_text(
                    "IP address has been blocked")
                if Activation.is_visible():
                    Activation.click()
                    break
                if blocked.is_visible():
                    if self.changeIP:
                        self.VPN_reconnect()
                        driver.wait_for_timeout(timeout=10000)
                        return self.scraperapi()
                        driver.get_by_text(
                            "Sign up with email", exact=True).click()
                        continue
                    self.error = blocked.text_content().strip()
                    return None
            while True:
                e = self.tmpEmail.getMessages("support@scraperapi.com")
                if e:
                    link = e[0]
                    driver.goto(link)
                    break
                driver.wait_for_timeout(timeout=3000)
            while True:
                driver.wait_for_timeout(timeout=3000)
                try:
                    c = driver.get_by_text("Skip", exact=True)
                    if c.is_visible():
                        c.click()
                    # c = driver.get_by_text("Software Engineer")
                    # if c.is_visible():
                    #     c.click()
                    #     driver.get_by_text("Data Research").click()
                    #     driver.get_by_text(
                    #         "Basic understanding of scraping APIs").click()
                    #     driver.get_by_role("button", name="Next").click()
                    key = driver.get_by_text(
                        "http://api.scraperapi.com?api_key=").nth(0)
                    if key.is_visible():
                        key = key.text_content()
                        key = key.split("api_key=")[1].split("&")[0]
                        break
                except Exception as e:
                    print("Scraperapi error:", str(e))
            self.api_key = key
            self.saveEmails("scraperapi")
            self.saveData("scraperapi")
            print("Scraperapi: api key", key)
            return key

        except Exception as e:
            print("Scrapeowl error:", str(e))
            self.error = str(e)
        finally:
            if not self.is_multi or not self.do_openai:
                self.delEmail()
                self.dr.close_driver(True)
            else:
                self.dr.close_driver()
        return None

    def monkeylearn(self):
        try:
            self.error = ""
            if not self.do_monkeylearn:
                return False
            self.getEmail()
            if not self.email:
                self.email = self.tmpEmail.getEmail()
            if not self.email:
                return None
            email = self.email
            self.api_key = None
            self.headless = False
            driver = self.dr.get_driver(user_dir=None, headless=self.headless)
            url = "https://monkeylearn.com/signup"
            driver.goto(url)
            # driver.wait_for_timeout(timeout=3000)
            print("Monkeylearn: fill info ...")
            name = email.split("@")[0].split(".")
            driver.locator("#first_name").fill(name[0])
            driver.locator("#last_name").fill(name[1])
            driver.locator("#email").fill(email)
            driver.locator("#password").fill("mohtasm10QQ@@")
            op = driver.locator("#data_type")
            op.select_option(index=1)
            op.press("Enter")
            op = driver.locator("#recurrency")
            op.select_option(index=1)
            op.press("Enter")
            op = driver.locator("#data_volume")
            op.select_option(index=1)
            op.press("Enter")
            # driver.locator("input[name=Create your account]").click()
            driver.get_by_text("Create your account").click()
            driver.wait_for_timeout(timeout=3000)
            is_active = False
            while True:
                try:
                    Confirm = driver.get_by_text("Thank you for signing up!",
                                                 exact=True)
                    error = driver.get_by_text("too many requests")
                    if error.is_visible():
                        error = error.text_content().strip()
                        print("Monkeylearn:", error)
                        if self.changeIP:
                            self.VPN_reconnect()
                            driver.wait_for_timeout(timeout=10000)
                            return self.monkeylearn()
                        self.do_monkeylearn = False
                        raise Exception(error)
                    if not is_active and not Confirm.is_visible():
                        errors = driver.locator("[class*=formFieldErrors]")
                        for i in range(errors.count()):
                            error = errors.nth(i)
                            if error and error.is_visible() and error.text_content().strip():
                                error = error.text_content().strip()
                                print("Monkeylearn:", error)
                                if error.find("email is already in use") != -1:
                                    self.saveEmails("monkeylearn")
                                    return self.monkeylearn()
                                self.delEmail()
                                return None
                        continue
                    is_active = True
                    e = self.tmpEmail.getMessages("hello@monkeylearn.com")
                    if e:
                        link = e[0]
                        driver.goto(link)
                        break
                    driver.wait_for_timeout(timeout=3000)
                except Exception as e:
                    print("Monkeylearn error: ", str(e))
            print("Monkeylearn: waiting for api key...")
            driver.wait_for_url("**/studio/templates**")
            driver.goto(
                "https://app.monkeylearn.com/studio/my-account#api-key")
            driver.locator(".api-key").click()
            # driver.wait_for_timeout(timeout=3000)
            c = driver.evaluate("navigator.clipboard.readText()")
            print("Monkeylearn: api key: ", c)
            self.api_key = c
            self.saveEmails("monkeylearn")
            self.saveData("monkeylearn")
            return c
        except Exception as e:
            print("Monkeylearn error: ", str(e))
            self.error = str(e)
        finally:
            if not self.is_multi or not self.do_openai:
                self.tmpEmail.deleteEmail()
                self.dr.close_driver(True)
            else:
                self.dr.close_driver()

    def scrapeowl(self, **kwargs):
        email = kwargs.get("email", self.email)
        try:
            self.error = ""
            if not self.do_scrapeowl:
                return False
            self.getEmail()
            if not email:
                email = self.tmpEmail.getGmail(uses="scrapeowl")
            if not self.email:
                email = self.gmail(email=email, close=False)
            if not email:
                return None
            self.email = email
            self.api_key = None
            driver = self.dr.get_driver(user_dir=None, headless=self.headless)
            url = "https://app.scrapeowl.com/register"
            driver.goto(url)
            print("Scrapeowl: fill info ...")
            driver.locator("a[href*=google]").click()
            btn = driver.locator("div[data-identifier*='gmail.com']").nth(0)
            btn.evaluate("(node) => node.click()")
            driver.wait_for_url("**/dashboard")
            key = driver.get_by_text(
                "https://api.scrapeowl.com/v1/scrape")
            key = key.text_content()
            key = key.split("api_key=")[1].split("&")[0]
            self.api_key = key
            self.saveEmails("scrapeowl")
            self.saveData("scrapeowl")
            self.tmpEmail.upGmail(uses="scrapeowl")
            print("Scrapeowl: api key", key)
            return key
        except Exception as e:
            # print(e)
            print("Scrapeowl error:", str(e))
            self.error = str(e)

        finally:
            if not self.is_multi or not self.do_openai:
                self.tmpEmail.deleteEmail()
                self.dr.close_driver(True)
            else:
                self.dr.close_driver()
        return None

    def scrapeowl2(self):
        try:
            self.error = ""
            if not self.do_scrapeowl:
                return False
            self.getEmail()
            if not self.email:
                self.email = self.tmpEmail.getEmail()
            if not self.email:
                return None
            email = self.email
            self.api_key = None
            self.headless = False
            driver = self.dr.get_driver(user_dir=None, headless=self.headless)
            url = "https://app.scrapeowl.com/register"
            driver.goto(url)
            # driver.wait_for_timeout(timeout=3000)
            print("Scrapeowl: fill info ...")
            driver.locator("a[href*=github]").click()
            driver.get_by_text("Create an account", exact=True).click()
            name = email.split("@")[0].split(".")
            name.append("mutasim")
            driver.locator("#user_login").fill("".join(name))
            driver.locator("#user_email").fill(email)
            driver.locator("#user_password").fill(email)
            driver.wait_for_timeout(timeout=5000)
            ctrys = 0
            is_solved = True
            while True:
                try:
                    # nex = driver.get_by_text("First, let's create your user account")
                    nex = driver.get_by_text("You're almost done!")
                    if nex.is_visible():
                        break
                    signup_button = driver.locator("#signup_button")
                    if signup_button.is_visible() and not signup_button.is_disabled():
                        signup_button.click()
                        # break
                    else:
                        print("Scrapeowl: waiting for captcha...")
                    if not is_solved:
                        solver = driver.frame_locator(
                            "iframe[src*=octocaptcha]")
                        solver = solver.frame_locator(
                            "iframe[src*=arkoselabs]")
                        solver_inner = solver.locator(
                            ".captcha-solver_inner")
                        if solver_inner.is_visible():
                            js = solver_inner.evaluate(
                                "node => node.dataset.json")
                            result = self.funCaptcha(js)
                            if result:
                                solver_inner.evaluate(
                                    "(node,code) => node.value = code", result)
                                solver_inner.click()
                                is_solved = True
                                driver.wait_for_timeout(timeout=3000)
                                signup_button = driver.locator(
                                    "#signup_button")
                                signup_button.click()
                                # break
                            # First, let's create your user account
                            else:
                                if ctrys >= 1:
                                    return self.scrapeowl()
                                ctrys += 1
                except Exception as e:
                    print("Scrapeowl error:", str(e))

            driver.wait_for_url("**/account_verifications**")
            # driver.locator("#signup_button").click()
            # driver.wait_for_timeout(timeout=30000)
            # name = list(map(lambda v: str(v).capitalize(), name))
            # form = driver.locator("form")
            # form.wait_for()
            # form = form.locator("input")
            # form.nth(0).fill(name[0])
            # form.nth(1).fill(name[1])
            # form.nth(2).fill(email)
            # form.nth(3).fill(email)
            # driver.get_by_text("Sign Up", exact=True).click()
            # driver.get_by_text("Confirm your email address",
            #                    exact=True).wait_for()
            is_active = False
            while True:
                # Confirm = driver.get_by_text("Confirm your email address",
                #                              exact=True)
                # if not is_active and not Confirm.is_visible():
                #     errors = driver.locator(".mt-1.text-xs.text-red-600")
                #     for i in range(errors.count()):
                #         error = errors.nth(i)
                #         if error and error.is_visible() and error.text_content().strip():
                #             error = error.text_content().strip()
                #             print("Scrapeowl:", error)
                #             if error.find("email is already in use") != -1:
                #                 self.saveEmails("scrapeowl")
                #                 return self.scrapeowl()
                #             self.delEmail()
                #             return None
                #     continue
                is_active = True
                e = self.tmpEmail.getMessages("noreply@github.com")
                if e:
                    link = e[0]
                    driver.goto(link)
                    break
                driver.wait_for_timeout(timeout=3000)
            key = self.get_scrapeowlkey(driver)
            self.api_key = key
            self.saveEmails("scrapeowl")
            self.saveData("scrapeowl")
            print("Scrapeowl: api key", key)
            return key
        except Exception as e:
            # print(e)
            print("Scrapeowl error:", str(e))
            self.error = str(e)
        finally:
            if not self.is_multi or not self.do_openai:
                self.tmpEmail.deleteEmail()
                self.dr.close_driver(True)
            else:
                self.dr.close_driver()
        return None

    def Scrapeowl_slover(self, driver):
        pass

    def get_scrapeowlkey(self, driver):
        driver.goto("https://app.scrapeowl.com/register")
        print("Scrapeowl: fill info ...")
        driver.locator("a[href*=github]").click()
        driver.wait_for_timeout(timeout=3000)
        spam = driver.get_by_text("You are marked as spam").nth(0)
        if spam.is_visible():
            self.dr.close_driver(True)
            self.tmpEmail.deleteEmail()
            return self.scrapeowl()
        driver.get_by_text("Authorize ScrapeOwl", exact=True).nth(0).click()
        driver.locator("#js-oauth-authorize-btn").click()
        driver.wait_for_url("**/dashboard")
        # driver.wait_for_timeout(timeout=3000)
        key = driver.get_by_text(
            "https://api.scrapeowl.com/v1/scrape")
        key = key.text_content()
        key = key.split("api_key=")[1].split("&")[0]
        return key
        # js-oauth-authorize-btn

    def closeModal(self, driver):
        try:
            modal = driver.get_by_text(text="Get started").nth(0)
            if modal.is_visible(timeout=4000):
                modal = driver.locator("#modal-root")
                modal.locator("button").nth(2).click()
                driver.get_by_text(
                    text="I agree to the terms of service").nth(0).click()
                driver.get_by_role(role="button", name="Accept").nth(0).click()
                driver.wait_for_timeout(timeout=5000)
                self.dr.close_tab()
        except Exception as e:
            print("Dreamstudio closemodal error:", str(e))

    def do_accounts(self):
        self.is_multi = True
        c = self.dreamstudio()
        c = self.scraperapi()
        # c = self.scrapeowl()
        # c = self.monkeylearn()
        c = self.claude()
        c = self.getAccount()
        if self.error.find("Connection") != -1 and self.changeIP:
            self.VPN_reconnect()
            self.do_accounts()
        return c

    def getEmail(self, temps="tempemail"):
        lines = []
        return []
        if not os.path.exists(temps+".txt"):
            open(temps+'.txt', 'w').close()
        with open(temps+'.txt') as f:
            lines = f.readlines()
            lines = list(lines)
            spt = ":"
            line = list(filter(lambda x: str(x).count(spt) == 0, lines))
            # line = list(set(line))
            self.emails = lines
            if temps != "tempemail":
                print("Emails Count: ", len(line))
            if len(line) > 0:
                self.email = line[0].strip().split(
                    ":")[0].replace("#", "").replace("*", "")
                if temps != "tempemail":
                    print("getEmail:", self.email)
            f.close()


openai = openAi()
_claude = Claude()
_chatgpt = ChatGPT()
# @app.route("/")


def signal_handler(sig, frame):
    print('You pressed Ctrl+C!')
    openai.isRuning = False
    openai.isRuning3(False)
    openai.delEmail()
    openai.sms.set_status()
    openai.dr.close_driver(True)
    sys.exit(0)


signal.signal(signal.SIGINT, signal_handler)


@app.route("/get_html", methods=['POST', 'GET'])
@auth.login_required
def get_html():
    url = request.args.get("url", None)
    ajax = request.args.get("ajax", None)
    if not url or url == "undefined":
        return not_found(None)
    html = openai.dr.get_html(url, request.args)
    return html


@app.route("/monkeylearn", methods=['POST', 'GET'])
@auth.login_required
def monkeylearn():
    openai.do_monkeylearn = True
    c = openai.monkeylearn()
    if c:
        d = {
            'success': True,
            'data': c
        }
    else:
        d = {
            'success': False,
            'message': openai.error
        }
    return jsonify(d)


@app.route("/scraperapi", methods=['POST', 'GET'])
@auth.login_required
def scraperapi():
    openai.do_scraperapi = True
    openai.headless = False
    c = openai.scraperapi()
    if c:
        d = {
            'success': True,
            'data': c
        }
    else:
        d = {
            'success': False,
            'message': openai.error
        }
    return jsonify(d)


@app.route("/scrapeowl", methods=['POST', 'GET'])
@auth.login_required
def scrapeowl():
    openai.do_scrapeowl = True
    openai.headless = False
    c = openai.scrapeowl()
    if c:
        d = {
            'success': True,
            'data': c
        }
    else:
        d = {
            'success': False,
            'message': openai.error
        }
    return jsonify(d)


@app.route("/bard", methods=['POST', 'GET'])
@auth.login_required
def bard():
    # "mohtasm.com@gmail.com"
    if request.method == "POST":
        email = request.form.get("email", None)
        password = request.form.get("password", None)
    else:
        email = request.args.get("email", "snugglessnake@gmail.com")
        password = request.args.get("password", "mohtasm10Q@@")
    # openai.headless = False
    c = openai.bard(email, password)
    if c:
        d = {
            'success': True,
            'data': c
        }
    else:
        d = {
            'success': False,
            'message': openai.error
        }
    return jsonify(d)


@app.route("/chatgpt", methods=['POST', 'GET'])
@auth.login_required
def chatgpt():
    data = {**request.form, **request.args}
    sessionKey = data.get("sessionKey", None)
    conversationId = data.get("conversationId", None)
    prompt = data.get("prompt", None)
    try:
        # claude.setSessionKey("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")
        # claude.sessionKey = "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"
        _chatgpt.init(sessionKey)
        if conversationId:
            data = _chatgpt.getConversation(conversationId)
            # data = conversation.sendMessage(prompt)
        else:
            data = _chatgpt.startConversation(prompt)
        data = {
            'success': True,
            'data': data
        }
    except _chatgpt.CustomException as e:
        data = {
            'success': False,
            **e.getJSON()
        }
    return jsonify(data)


@app.route("/getchatgpt", methods=['POST', 'GET'])
def getchatgpt(js=None):
    email = None
    data = {}
    if request:
        data = {**request.form, **request.args}
    email = data.get("email", None)
    refresh_token = data.get("refresh_token", None)
    c = openai.chatgpt(email, refresh_token)
    if c:
        d = {
            'success': True,
            'data': c
        }
    else:
        d = {
            'success': False,
            'message': openai.error
        }
    if js:
        return d
    return jsonify(d)


@app.route("/outlook", methods=['POST', 'GET'])
# @auth.login_required
def outlook():
    openai.headless = False
    email = None
    data = {}
    if request:
        data = {**request.form, **request.args}
    email = data.get("email", None)
    c = openai.outlook(email=email)
    if c:
        openai.email = c
        openai.do_scrapeowl = True
        openai.do_claude = True
        # c = openai.claude(close=False)
        # c = openai.scrapeowl()
    if c:
        d = {
            'success': True,
            'data': c
        }
    else:
        d = {
            'success': False,
            'message': openai.error
        }
    return jsonify(d)


@app.route("/gmail", methods=['POST', 'GET'])
@auth.login_required
def gmail():
    openai.headless = False
    email = None
    data = {}
    if request:
        data = {**request.form, **request.args}
    email = data.get("email", None)
    c = openai.gmail(email=email)
    if c:
        openai.email = c
        openai.do_scrapeowl = True
        openai.do_claude = True
        # c = openai.claude(close=False)
        # c = openai.scrapeowl()
    if c:
        d = {
            'success': True,
            'data': c
        }
    else:
        d = {
            'success': False,
            'message': openai.error
        }
    return jsonify(d)


@app.route("/claude", methods=['POST', 'GET'])
@auth.login_required
def claude():
    data = {**request.form, **request.args}
    sessionKey = data.get("sessionKey", None)
    conversationId = data.get("conversationId", None)
    prompt = data.get("prompt", None)
    try:
        # claude.setSessionKey("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")
        # claude.sessionKey = "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"
        _claude.init(sessionKey)
        if conversationId:
            conversation = _claude.getConversation(conversationId)
            data = conversation.sendMessage(prompt)
        else:
            data = _claude.startConversation(prompt, data)
        data = {
            'success': True,
            'data': data
        }
    except CustomException as e:
        data = {
            'success': False,
            **e.getJSON()
        }
    return jsonify(data)


@app.route("/nlp", methods=['POST', 'GET'])
@auth.login_required
def nlp():
    _nlp = NLP()
    data = {**request.form, **request.args}
    try:
        data = _nlp.call(data)
        return jsonify(data)
    except _nlp.CustomException as e:
        return jsonify(e.getJSON())


@app.route("/getclaude", methods=['POST', 'GET'])
@auth.login_required
def getclaude():
    if request.method == "POST":
        email = request.form.get("email", None)
    else:
        email = request.args.get("email", None)
    openai.headless = False
    openai.do_claude = True
    c = openai.claude(email=email)
    if c:
        d = {
            'success': True,
            'data': c
        }
    else:
        d = {
            'success': False,
            'message': openai.error
        }
    return jsonify(d)


@app.route("/pintrest", methods=['POST', 'GET'])
@auth.login_required
def pintrest():
    if request.method == "POST":
        username = request.form.get("username", None)
        password = request.form.get("password", None)
    else:
        username = request.args.get("username", None)
        password = request.args.get("password", None)
    c = openai.get_pintrest(username, password)
    if c:
        d = {
            'success': True,
            'data': c
        }
    else:
        d = {
            'success': False,
            'message': openai.error
        }
    return jsonify(d)


@app.route("/app", methods=['POST', 'GET'])
# @auth.login_required
def do_app():
    images = True
    count = 300
    if openai.isRuning or openai.isRuning3():
        return jsonify({
            "success": False,
            "message": "The Task is already runing!"
        })
    openai.isRuning = True
    openai.headless = False
    openai.do_openai = True
    openai.do_dreamstudio = False
    openai.do_claude = False
    openai.do_scraperapi = False
    openai.isRuning3(True)
    for i in range(0, count):
        print("#", i+1)
        # if openai.do_dreamstudio:
        #     openai.do_openai = False
        #     dreamstudio = openai.dreamstudio()
        # else:
        dreamstudio = openai.do_accounts()
        Timeout = openai.error.find(
            "Timeout") == -1 and openai.error.find("load") == -1
        if not dreamstudio and Timeout:
            break
    openai.dr.close_driver(True)
    openai.isRuning = False
    openai.isRuning3(False)
    return jsonify({
        "success": True,
        "number_of_accounts": openai.success_accounts
    })


@app.cli.command()
def dochatgpt():
    for i in range(0, 200):
        print("#", i+1)
        j = getchatgpt(True)
        if not j['success']:
            break


@app.cli.command()
def doclaude():
    openai.headless = False
    openai.do_claude = True
    for i in range(0, 50):
        print("#", i+1)
        c = openai.claude()
        if not c:
            break


@app.cli.command()
def dooutlook():
    openai.headless = False
    for i in range(0, 50):
        print("#", i+1)
        c = openai.outlook()
        if not c:
            break


@app.cli.command()
def doscraperapi():
    for i in range(0, 50):
        print("#", i+1)
        openai.do_scraperapi = True
        openai.headless = False
        c = openai.scraperapi()
        if not c:
            break


@app.cli.command()
def scheduled():
    """Run scheduled job."""
    print('Create accounts ...')
    do_app()
    print('Done!')


def print_date_time():
    print(time.strftime("%A, %d. %B %Y %I:%M:%S %p"))


# scheduler = BackgroundScheduler()
# scheduler.add_job(func=print_date_time, trigger="interval", seconds=3)
# scheduler.start()

# # Shut down the scheduler when exiting the app
# atexit.register(lambda: scheduler.shutdown())


@app.errorhandler(404)
def not_found(error):
    # resp = make_response("404", 404)
    # resp.headers['X-Something'] = 'A value'
    status = 500
    message = 'Whoops!! something went wrong'
    return jsonify(
        status=status,
        message=message
    ), 500


if __name__ == '__main__':
    app.debug = True
    app.run(port=8090, use_reloader=False, debug=True)

# sys.exit(0)
# try:
#     if openai.isRuning():
#         print("The Task is already runing!")
#         sys.exit(0)

#     def signal_handler(signal, frame):
#         print('You pressed Ctrl+C!')
#         openai.isRuning(False)
#         openai.delEmail()
#         openai.sms.set_status()
#         openai.dr.close_driver()
#         sys.exit(0)
#     signal.signal(signal.SIGINT, signal_handler)
#     images = False
#     count = 5000
#     openai.isRuning(True)
#     for i in range(0, count):
#         print("#", i+1)
#         if images:
#             dreamstudio = openai.dreamstudio()
#         else:
#             dreamstudio = openai.do_accounts()
#         Timeout = openai.error.find("Timeout") == -1
#         if not dreamstudio and Timeout:
#             break
#     openai.isRuning(False)
# except Exception as e:
#     print(str(e))
#     pass


# if not images:
#     for i in range(0, count):
#         print(i)
#         dreamstudio = openai.dreamstudio()
# computer_sleep()
# openai.VPN_reconnect()
# openai.dr.get_driver(user_dir="playway")
# openai.dr.driver.goto(
#     "https://www.masterclass.com/articles/can-dogs-eat-artichokes")
# openai.dr.driver.wait_for_timeout(timeout=3000)
# openai.dr.close_driver()
# openai.dr.get_driver(user_dir=None,headless=True)
# openai.dr.driver.goto(
#     "https://www.masterclass.com/articles/can-dogs-eat-artichokes")
# print(openai.dr.driver.title())
# openai.dr.driver.wait_for_timeout(timeout=3000)
# openai.dr.close_driver()
# openai.dr.driver.wait_for_timeout(timeout=300000)
# openai.getAccount()
# args = ["C:\\Program Files\\Avast Software\\SecureLine VPN\\VpnNM.exe",
#         "chrome-extension://dmfdacibleoapmpfdgonigdfinmekhgpl/"]
# test = subprocess.call(args)
# print(test)
