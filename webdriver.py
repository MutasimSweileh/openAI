import datetime
import math
import random
import string
from playwright.sync_api import sync_playwright, Page, Route
from playwright._impl._locator import Locator
from undetected_playwright import stealth_sync
# from playwright_stealth import stealth_sync
from time import sleep
from os import getcwd
from playwright.async_api import async_playwright
import os

from seleniumbase import Driver as BaseDriver
import time


class Driver():
    def __init__(self, headless=False, images=False, ajax=False, proxy=False, Blocks=True, **kwargs) -> None:

        self.driver_executable_path = None
        self.browser_executable_path = None
        self.block_images = images
        self.headless = headless
        self.driver = None
        self.proxy = proxy
        self.playwright = None
        self.Blocks = Blocks
        self.ajax = ajax or False
        self.maxTry = 5
        self.curTry = 1
        self.kwargs = kwargs

    def extract(self, el, type="text", tryed=True, noHast=None, noFind=None):
        text = ""
        if isinstance(el, str):
            el = self.driver.locator(el)
        tagName = str(el.evaluate("node => node.tagName")).lower()
        if type == "text" and tagName == "input":
            type = "value"
        if type == "text":

            text = el.text_content()
        elif type == "value":
            text = el.get_attribute("value")
        elif type == "html":
            text = el.inner_html()
        else:
            text = el.get_attribute(type)
        if not bool(text) and tryed or noHast is not None and text.count(noHast) > 0:
            sleep(2)
            if noFind and noFind.is_visible():
                return ""
            return self.extract(el, type, tryed, noHast)
        return text

    def click(self, el: Locator, clicks=1):
        if isinstance(el, str):
            el = self.find_element(el)
        for i in range(0, clicks):
            el.click()

    def find_child(self, el: str, el2: str):

        el = self.find_element(el).first

        return el.locator(el2)

    def block_resource(self, route):
        blocks = ["css", "font", "stylesheet"]
        blocks = ["font", "image"]
        if self.block_images:
            blocks.append("image")
        if not self.Blocks:
            blocks = []
        elif route.request.resource_type in blocks:
            route.abort()
        else:
            route.continue_()

    def get_user_agent(self):
        return self.driver.evaluate("() => navigator.userAgent")

    def get_params(self) -> None:
        page = self.driver
        self.browser_language = self.kwargs.get(
            "browser_language",
            page.evaluate("""() => { return navigator.language; }"""),
        )
        self.browser_version = page.evaluate(
            """() => { return window.navigator.appVersion; }"""
        )

        if len(self.browser_language.split("-")) == 0:
            self.region = self.kwargs.get("region", "US")
            self.language = self.kwargs.get("language", "en")
        elif len(self.browser_language.split("-")) == 1:
            self.region = self.kwargs.get("region", "US")
            self.language = self.browser_language.split("-")[0]
        else:
            self.region = self.kwargs.get(
                "region", self.browser_language.split("-")[1])
            self.language = self.kwargs.get(
                "language", self.browser_language.split("-")[0]
            )

        self.timezone_name = self.kwargs.get(
            "timezone_name",
            page.evaluate(
                """() => { return Intl.DateTimeFormat().resolvedOptions().timeZone; }"""
            ),
        )
        self.device_id = "".join(
            random.choice(string.digits) for num in range(19)
        )
        self.width = page.evaluate("""() => { return screen.width; }""")
        self.height = page.evaluate("""() => { return screen.height; }""")

    def close_tab(self, tab=-1):
        pages = self.driver.context.pages
        if len(pages) > 1:
            pages[tab].close()

    def get_script(self):
        with open('zon_interceptor.js', 'r') as f:
            r = f.read()
            # print(r)
            return r

    def get_driver(self, user_data_dir=None, **kwargs):
        self.driver = BaseDriver(uc=True)
        return self.driver

    def get_driver(self, user_dir=None, **kwargs) -> Page:
        if kwargs.get("user_data_dir", None) is not None:
            user_data_dir = os.getcwd() / user_data_dir
        headless = kwargs.get("headless", self.headless)
        handler = kwargs.get("handler", None)
        # self.Blocks = kwargs.get("block", self.Blocks)
        # user_dir = 'playwright'
        if user_dir is not None:
            user_dir = os.path.join(os.getcwd(), user_dir)
        self.options = {
            "headless": headless,
            "handle_sigint": True,
            "handle_sigterm": True,
            "handle_sighup": True,
            # "user_data_dir": os.path.expanduser('~')+'\\AppData\\Local\\Google\\Chrome\\User Data',
            # "executable_path": 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
            "user_data_dir": user_dir,
            # "permissions": ['clipboard-read', 'clipboard-write']
            # "no_viewport": True
            # "devtools": True,
            "chromium_sandbox": False,
        }
        args = [
            "--start-maximized",
            "--disable-web-security",
            # "--no-sandbox",
            "--disable-setuid-sandbox",
            "--disable-renderer-backgrounding",
            "--test-type",
            "--log-level=3",
            "--ignore-certificate-errors",
            "--allow-file-access-from-files",
            "--allow-insecure-localhost",
            "--allow-running-insecure-content",
        ]
        path_to_extension = os.path.join(
            os.getcwd(), "ifibfemgeogfhoebkmokieepdoobkbpo")
        path_to_extension = None
        if path_to_extension and user_dir:
            args = [
                f"--disable-extensions-except={path_to_extension}",
                f"--load-extension={path_to_extension}",
            ]
        if self.proxy:
            self.options["proxy"] = {
                "server": self.proxy
            }
        if user_dir is None:
            del self.options["user_data_dir"]
        self.options = {**self.options, **kwargs}

        if self.driver is None:
            if not self.playwright:
                self.playwright = sync_playwright().start()
            get_device = self.playwright.devices["Desktop Chrome"]
            # print(get_device)
            # raise Exception("ex")
            device = {
                "no_viewport": True,
                "ignore_https_errors": True,
                "bypass_csp": True,
                "java_script_enabled": True
            }
            if self.options["headless"]:
                device = get_device
            channel = "chrome"
            # channel = None
            if user_dir:
                self.browser = self.playwright.chromium.launch_persistent_context(channel=channel,
                                                                                  args=args,  **self.options, **device)
                self.context = self.browser
            else:
                self.browser = self.playwright.chromium.launch(channel=channel,
                                                               args=args,  **self.options)
                self.context = self.browser.new_context(**device)
                # self.browser = self.playwright.chromium.launch(
                #     headless=False, args=["--no-sandbox", "--disable-setuid-sandbox"], channel="chrome")
                # self.context = self.browser.new_context()
            # stealth_sync(self.context)
            # self.browser.set_default_context_opener_policy("same-origin")
            self.context.clear_cookies()
            self.context.grant_permissions(
                permissions=['clipboard-read', 'clipboard-write'])
            stealth_sync(self.context)
            self.driver = self.context.new_page()
            path = self.kwargs.get("path", os.getcwd())
            # path = path+"/zon_interceptor.js"
            self.driver.add_init_script(path=path+"/zon_interceptor.js")
            self.driver.add_init_script(path=path+"/recaptcha_interceptor.js")
            # print("Blocks:", self.Blocks)
            # self.driver.route("**/*", self.resource)
            if handler:
                self.driver.route("**/*", handler)
            # self.driver.route("**/*.{png,jpg,jpeg}",
            #                   lambda route: route.request.post_data_json)
            if self.Blocks:
                self.driver.route(
                    "**/*", self.block_resource)
        return self.driver

    def resource(self, route):
        if route.request.url.find("auth/verify_google") != -1:
            print(route.request.post_data)
            print(route.request.post_data_json)
        #     route.abort()
        # else:
        route.continue_()

    def find_element(self, val: str, tr=True) -> Locator:
        try:
            loginContainer = self.driver.locator(val)
            loginContainer.wait_for(timeout=5000)
        except:
            loginContainer = None
        if loginContainer is None and tr and self.curTry < self.maxTry:
            self.curTry += 1
            sleep(2)
            return self.find_element(val)
        self.curTry = 1
        return loginContainer

    def close_driver(self, force=False):
        try:
            if self.driver is not None:
                # self.driver.close()
                self.context.close()
                self.browser.close()
            if force and self.playwright:
                self.playwright.stop()
                self.playwright = None
        except Exception as e:
            print("Failed to close driver: %s" % e)
            # self.driver.quit()
        self.driver = None

    def http_cookies(self):
        cookies = self.context.cookies()
        cstr = "# Netscape HTTP Cookie File\n# https://curl.se/docs/http-cookies.html\n# This file was generated by libcurl! Edit at your own risk.\n\n#HttpOnly_.pinterest.com	TRUE	/	TRUE	_pinterest_sess_expiration	_pinterest_sess	_pinterest_sess_v\n#HttpOnly_.pinterest.com	TRUE	/	TRUE	_auth_expiration	_auth	_auth_v\n#HttpOnly_www.pinterest.com	FALSE	/	FALSE	_routing_id_expiration	_routing_id	_routing_id_v\n.pinterest.com	TRUE	/	FALSE	_b_expiration	_b	_b_v"
        for c in cookies:
            if c["name"] not in ["_pinterest_sess", "_auth", "_routing_id", "_b"]:
                continue
            expiration = math.trunc(c["expires"])
            # expiration = datetime.datetime.utcfromtimestamp(c["expires"])
            # expiration = expiration / 1000 + 100000
            cstr = cstr.replace(f"{c['name']}_v", c["value"])
            cstr = cstr.replace(
                f"{c['name']}_expiration", str(expiration))
            # cstr += f"\n{ht}{c['domain']}  {sub}  {c['path']}  {str(c['secure']).upper()}  {c['expires']}  {c['name']}	 {c['value']}"
        return cstr

    def get_cookies(self, dic=False, convert=False):
        cookies = self.context.cookies()

        mycookies = {}
        if convert:
            mycookies = ""
        if dic or convert:
            for c in cookies:
                if convert:
                    mycookies += f'{c["name"]}={c["value"]};'
                else:
                    mycookies[c["name"]] = c["value"]
            return mycookies
        return cookies

    def get_html(self, url, args={}):
        html = ""
        try:
            driver = self.get_driver(headless=True)
            driver.goto(str(url))
            timeout = args.get("timeout", 3000)
            driver.wait_for_timeout(timeout)
            html = driver.content()
            ajax = args.get("ajax", self.ajax)
            if ajax:
                driver.wait_for_timeout(3000)
                findtable = driver.locator("html")
                html = findtable.inner_html()
        except Exception as e:
            print("Get html error:", str(e))
        finally:
            # await driver.wait_for_timeout(5000)
            self.close_driver(True)
        return html


# dr = Driver()
# d = dr.get_driver(headless=False)
# d.goto("https://bot.sannysoft.com/")
# d.wait_for_timeout(100000)
