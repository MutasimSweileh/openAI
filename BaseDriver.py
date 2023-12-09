import json
import os
import zipfile
import requests
from seleniumbase import Driver as BaDriver
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.events import EventFiringWebDriver, AbstractEventListener
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
import time
from twocaptcha import TwoCaptcha
import config


class LactorDriver(WebElement):

    def __init__(self, element=None):
        self.element = element
        if element:
            self._parent = element._parent
            self._id = element._id
            super().__init__(element._parent,  element._id)

    def clear(self) -> None:
        return self.element.clear()

    def is_displayed(self, **kwargs):
        return self.is_visible(**kwargs)

    def is_visible(self, **kwargs):
        if not self.element:
            return False
        return self.element.is_displayed()

    def is_available(self, **kwargs):
        if not self.element:
            return False
        return self.element

    def select_option(self, value):
        select = Select(self.element)
        # select.select_by_visible_text(value)
        select.select_by_value(value)

    def get_attribute(self, attribute, **kwargs):
        return self.element.get_attribute(attribute)

    def text_content(self, **kwargs):
        text = self.element.text
        if not text:
            text = self._parent.execute_script(
                'return arguments[0].innerText', self.element)
        return text

    def fill(self, text, **kwargs):
        self.type(text, **kwargs)

    def click(self, **kwargs) -> None:
        if self.element.is_displayed():
            self.element.click()
        else:
            self.clickjs(**kwargs)

    def get_by_label(self, lab):
        locator = "//label[contains(text(),'" + lab + "')]"
        try:
            self.element = self.element.find_element("xpath", locator)
            return self
        except Exception as e:
            print(locator, str(e))
            raise Exception("Element not found!")

    def get_by_role(self, role, name):
        pass

    def nth(self, index=0):
        return self

    def evaluate(self, script: str, value=None, **kwargs):
        if not self.element:
            return None
        script = script.replace("node", 'arguments[0]')
        if value:
            return self._parent.execute_script("arguments[0].value = arguments[1]", self.element, value)
        return self._parent.execute_script(script, self.element)

    def clickjs(self, **kwargs):
        self._parent.execute_script('arguments[0].click()', self.element)

    def filljs(self, value):
        self._parent.execute_script(
            'arguments[0].value = arguments[1]', self.element, value)

    def wait_for(self, timeout=3000):
        if not self.element:
            raise Exception("Element not found!")

    def locator(self, locator, timeout=5):
        ba = "css selector"
        if locator.find("[") == -1 and locator.find(".") == -1 and locator.find("(") == -1 and locator.find("#") == -1:
            ba = "tag name"
        try:
            el = self.element.find_element(
                ba, locator)
        except Exception as e:
            print(locator, str(e))
            raise Exception("Element not found!")

        return LactorDriver(el)

    def press(self, text: str, **kwargs):
        if text.lower() == "enter":
            text = Keys.ENTER
        self.element.send_keys(text)

    def type(self, text, **kwargs):
        try:
            self.element.clear()
            self.element.send_keys(text)
        except:
            pass
        self.filljs(text)

    def is_disabled(self, **kwargs):
        if not self.element:
            return False
        return not self.element.is_enabled()

    def get_by_placeholder(self, text, **kwargs):
        locator = "[placeholder*=\""+text.strip()+"\"]"
        try:
            self.element = self.element.find_element("css selector", locator)
            return self
        except Exception as e:
            print(locator, str(e))
            raise Exception("Element not found!")

    def get_by_text(self, text, **kwargs):
        exact = kwargs.get("exact", False)
        el = None
        try:
            if not exact:
                locator = "//*[contains(text(),\""+text.strip()+"\")]"
                el = self.element.find_element(
                    "xpath", locator)
            else:
                locator = "//*[text()=\""+text.strip()+"\"]"
                el = self.element.find_element(
                    "xpath", locator)
        except Exception as e:
            print(locator, str(e))
            raise Exception("Element not found!")
        return LactorDriver(el)


class BaseDriver:

    def __init__(self):
        self.driver = None
        self.element = None
        self.solver = TwoCaptcha(os.getenv("TwoCaptcha_API_KEY"))

    class EventListeners(AbstractEventListener):

        def __init__(self, dr) -> None:
            self.dr = dr
            super().__init__()

        def before_navigate_to(self, url, driver):
            # self.get_scripts(driver)
            print("before_navigate_to %s" % url)

        def get_scripts(self, driver):
            script = open(os.getcwd()+"/script.js").read()
            self.dr.captcha(driver)
            # driver.execute_script(script)

        def after_navigate_to(self, url, driver):
            self.get_scripts(driver)
            print("after_navigate_to %s" % url)

        def before_click(self, element, driver):
            pass
            # print("before_click %s" % element)

        def after_click(self, element, driver):
            self.get_scripts(driver)
            # print("after_click %s" % element)

        def after_navigate_forward(self, driver):
            print("after_navigate_forward")

        def before_navigate_forward(self, driver):
            print("before_navigate_forward")

        def after_navigate_back(self, driver):
            print("after_navigate_back")

        def before_navigate_back(self, driver):
            print("before_navigate_back")

        def before_change_value_of(self, element, driver):
            pass

        def after_change_value_of(self, element, driver) -> None:
            self.get_scripts(driver)

            # print("before_change_value_of")

    def get_driver(self, user_data_dir=None, user_dir=None, **kwargs):
        if self.driver:
            return self
        # https://nopecha.com/f/chrome.zip
        # with open('chrome.zip', 'wb') as f:
        #     f.write(requests.get(
        #         'https://nopecha.com/f/chrome.zip').content)
        # with zipfile.ZipFile('chrome.zip', 'r') as f:
        #     f.extractall('nopecha')
        extension_dir = os.getcwd() + "/captcha"
        extension_dir += ","+os.getcwd() + "/CapSolver.Browser.Extension"
        self.driver = BaDriver(
            uc=True, user_data_dir=user_data_dir, incognito=True, extension_dir=extension_dir, **kwargs)
        self.driver = EventFiringWebDriver(
            self.driver, self.EventListeners(self))
        # #self.driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
        #                             'source': 'alert("This is an alert.")'})
        NOPECHA_KEY = "dl0rzmq6ileq7ah0"
        self.driver.maximize_window()
        # self.driver.get(f"https://nopecha.com/setup#{NOPECHA_KEY}")

        return self

    def captcha(self, driver=None, tys=0):
        try:
            el = self.locator("#captcha-widget", 3, show_error=False)
            if el.is_available():
                self.sleep(5)
                return
                js = json.loads(el.text_content())
                current_url = self.driver.current_url
                current_url = current_url.strip().split("?")[0]
                url = js.get("url", current_url)
                pageurl = js.get("pageurl", current_url)
                sitekey = js.get("sitekey", js.get("pkey"))
                sitekey = js.get("sitekey", js.get("pkey"))
                captchaType = js.get("captchaType")
                version = js.get("version", "v2")
                surl = js.get("surl", current_url)
                enterprise = js.get("enterprise", False)
                print(f"Solve {captchaType} for: {url} ..", sitekey)
                if captchaType == "recaptcha":
                    result = self.solver.recaptcha(
                        sitekey=sitekey, url=url, version=version, enterprise=enterprise)
                elif captchaType == "turnstile":
                    result = self.solver.turnstile(sitekey=sitekey,
                                                   url=pageurl, action=js["action"], data=js["data"], pagedata=js["pagedata"])
                else:
                    result = self.solver.funcaptcha(
                        sitekey=sitekey, url=url, surl=surl)

                result = result["code"]
                print("Solved! code:", result)
                el.fill(result)
                el.click()
                return result
        except Exception as e:
            print("Captcha error:", str(e))
            if tys < 3:
                return self.captcha(driver=driver, tys=tys + 1)
            return None

    def quit(self):
        self.close_driver()

    def sleep(self, sc):
        time.sleep(sc)

    def wait_for_url(self, url, timeout=20):
        url = url.strip().replace("*", "")
        for i in range(timeout):
            if self.driver.current_url.find(url) != -1:
                return True
            time.sleep(1)
        raise Exception("URL not found")

    def get_cookies(self, dic=False, convert=False):
        cookies = self.driver.get_cookies()
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

    def evaluate(self, script: str, *args):
        if not self.driver:
            return None
        return self.driver.execute_script(script, *args)

    def close_driver(self, Force=True):
        if self.driver is not None:
            self.driver.quit()
            self.driver = None

    def goto(self, url, trys=0):
        try:
            if self.driver is not None:
                self.driver.get(url)
        except Exception as e:
            self.sleep(1)
            if trys < 3:
                return self.goto(url, trys=trys + 1)
            raise Exception(str(e))

    def wait_for_timeout(self, timeout=3000):
        timeout = (timeout / 1000) if timeout > 100 else timeout
        time.sleep(timeout)

    def locator(self, locator, timeout=5, **kwargs):
        show_error = kwargs.get("show_error", True)
        if self.driver is not None:
            try:
                el = self.wait_for_element(
                    "css selector", locator, timeout=timeout)
                return el
            except Exception as e:
                m = str(e)
                m = m.replace("Message:", "").strip()
                if show_error:
                    print(m)
                return LactorDriver(None)

    def get_by_label(self, lab):
        try:
            return self.wait_for_element("xpath", "//label[contains(text(),'" + lab + "')]")
        except Exception as e:
            m = str(e)
            m = m.replace("Message:", "").strip()
            print(m)
            return LactorDriver()

    def is_visible(self, locator=None):
        return self.driver.is_element_visible(locator)

    def get_by_placeholder(self, text, **kwargs):
        timeout = kwargs.get("timeout", 10)
        if self.driver is not None:
            try:
                return self.wait_for_element("css selector", "[placeholder*=\""+text.strip()+"\"]", timeout=timeout)
            except Exception as e:
                m = str(e)
                m = m.replace("Message:", "").strip()
                print(m)
                return LactorDriver()

    def reload(self):
        if self.driver is not None:
            self.driver.refresh()

    def frame_locator(self, locator, timeout=10):
        if self.driver is not None:
            try:
                iframe = self.locator(locator)
                el = self.driver.switch_to.frame(iframe)
                print(el)
                return LactorDriver(el)
            except Exception as e:
                m = str(e)
                m = m.replace("Message:", "").strip()
                print(m)
                return LactorDriver(None)

    def default_content(self):
        self.driver.switch_to.default_content()

    def wait_for_element(self, by, locator, **kwargs):
        timeout = kwargs.get("timeout", 10)
        visiable = kwargs.get("visiable", False)
        element = None
        try:
            wait = WebDriverWait(self.driver, timeout, ignored_exceptions=None)
            if not visiable:
                element = wait.until(
                    EC.presence_of_element_located((by, locator)))
            else:
                element = wait.until(
                    EC.visibility_of_element_located((by, locator)))
        except:
            raise Exception(
                "Selector {%s} was not visible after %s seconds!"
                % (locator, timeout)
            )
        return LactorDriver(element)

    def get_by_text(self, text, **kwargs):
        timeout = kwargs.get("timeout", 10)
        exact = kwargs.get("exact", False)
        if self.driver is not None:
            try:
                if exact:
                    return self.wait_for_element("xpath", "//*[text()=\""+text.strip()+"\"]", timeout=timeout)
                else:
                    return self.wait_for_element("xpath", "//*[contains(text(),\""+text.strip()+"\")]", timeout=timeout)
            except Exception as e:
                m = str(e)
                m = m.replace("Message:", "").strip()
                print(m)
                return LactorDriver()


# print(LactorDriver(None))
