(() => {
    let recaptchaInstance;
    console.log("recaptchaInstance")
    Object.defineProperty(window, "grecaptcha", {
        configurable: true,
        get: function () {
            return recaptchaInstance;
        },
        set: function (e) {
            recaptchaInstance = e;
            manageRecaptchaObj(e);
            manageEnterpriseObj(e);
        },
    });

    let manageRecaptchaObj = function (obj) {
        if (window.___grecaptcha_cfg === undefined) return;
        let originalExecuteFunc;
        let originalResetFunc;

        if (obj.execute) originalExecuteFunc = obj.execute;
        if (obj.reset) originalResetFunc = obj.reset;

        Object.defineProperty(obj, "execute", {
            configurable: true,
            get: function () {
                return async function (sitekey, options) {
                    console.log("recaptchaInstance", sitekey, options);
                    if (!options) {
                        if (!isInvisible()) {
                            return await originalExecuteFunc(sitekey, options);
                        }
                    }

                    let config = { enabledForRecaptchaV3: true };

                    if (!config.enabledForRecaptchaV3) {
                        return await originalExecuteFunc(sitekey, options);
                    }

                    if (isBlacklisted(window.location.href, config)) {
                        return await originalExecuteFunc(sitekey, options);
                    }

                    let widgetId = addWidgetInfo(sitekey, options);

                    return await waitForResult(widgetId);
                };
            },
            set: function (e) {
                originalExecuteFunc = e;
            },
        });

        Object.defineProperty(obj, "reset", {
            configurable: true,
            get: function () {
                return function (widgetId) {
                    if (widgetId === undefined) {
                        let ids = Object.keys(___grecaptcha_cfg.clients)[0];
                        widgetId = ids.length ? ids[0] : 0;
                    }

                    resetCaptchaWidget("recaptcha", widgetId);

                    return originalResetFunc(widgetId);
                };
            },
            set: function (e) {
                originalResetFunc = e;
            },
        });
    };

    let manageEnterpriseObj = function (obj) {
        if (window.___grecaptcha_cfg === undefined) return;
        let originalEnterpriseObj;

        Object.defineProperty(obj, "enterprise", {
            configurable: true,
            get: function () {
                return originalEnterpriseObj;
            },
            set: function (ent) {
                originalEnterpriseObj = ent;

                let originalExecuteFunc;
                let originalResetFunc;

                Object.defineProperty(ent, "execute", {
                    configurable: true,
                    get: function () {
                        return async function (sitekey, options) {
                            if (!options) {
                                if (!isInvisible()) {
                                    return await originalExecuteFunc(sitekey, options);
                                }
                            }

                            let config = {};

                            if (!config.enabledForRecaptchaV3) {
                                return await originalExecuteFunc(sitekey, options);
                            }

                            if (isBlacklisted(window.location.href, config)) {
                                return await originalExecuteFunc(sitekey, options);
                            }

                            let widgetId = addWidgetInfo(sitekey, options, "1");

                            return await waitForResult(widgetId);
                        };
                    },
                    set: function (e) {
                        originalExecuteFunc = e;
                    },
                });

                Object.defineProperty(ent, "reset", {
                    configurable: true,
                    get: function () {
                        return function (widgetId) {
                            if (widgetId === undefined) {
                                let ids = Object.keys(___grecaptcha_cfg.clients)[0];
                                widgetId = ids.length ? ids[0] : 0;
                            }

                            resetCaptchaWidget("recaptcha", widgetId);

                            return originalResetFunc(widgetId);
                        };
                    },
                    set: function (e) {
                        originalResetFunc = e;
                    },
                });
            },
        });
    };
    let resetCaptchaWidget = function (captchaType, widgetId) {
        let widgets = widgetsList.children;

        for (let i = 0; i < widgets.length; i++) {
            let wd = widgets[i].dataset;

            if (wd.captchaType != captchaType) continue;
            if (wd.widgetId != widgetId) continue;

            wd.reset = true; break;
        }
    };

    let waitForResult = function (widgetId) {
        return new Promise(function (resolve, reject) {
            let interval = setInterval(function () {
                let button = getCaptchaWidgetButton("recaptcha", widgetId);

                if (button && button.dataset.response) {
                    resolve(button.dataset.response);
                    clearInterval(interval);
                }
            }, 500);
        });
    };

    let isInvisible = function () {
        let widgets = document.querySelectorAll('head captcha-widget');
        for (let i = 0; i < widgets.length; i++) {
            if (widgets[i].dataset.version == 'v2_invisible') {
                let badge = document.querySelector('.grecaptcha-badge');
                badge.id = "recaptcha-badge-" + widgets[i].dataset.widgetId;
                widgets[i].dataset.containerId = badge.id;
                return true;
            }
        }
        return false;
    };

    let isBlacklisted = function (url, config) {
        return false;
        let m = config.blackListDomain.split('\n').filter(function (entry) {
            return url.includes(entry);
        });
        return m.length > 0;
    };
    let widgetsList = document.querySelector('head > captcha-widgets');
    if (!widgetsList) {
        widgetsList = document.createElement("captcha-widgets");
        if (document.head)
            document.head.appendChild(widgetsList);
    }
    let isCaptchaWidgetRegistered = function (captchaType, widgetId) {
        let widgets = widgetsList.children;
        for (let i = 0; i < widgets.length; i++) {
            if (widgets[i].dataset.captchaType !== captchaType) continue;
            if (widgets[i].dataset.widgetId !== widgetId + '') continue;
            return true;
        }

        return false;
    };
    // let CAPTCHA_WIDGETS_LOOP = setInterval(function () {
    //     let input = document.querySelector("input[name='fc-token']");
    //     if (!input) return;
    //     if (!window.arkoselabs_callback_dse7f73ek) return;
    //     let widgetInfo = getArkoselabsWidgetInfo(input);
    //     registerCaptchaWidget(widgetInfo);
    // }, 2000);
    let getCaptchaWidgetButton = function (captchaType, widgetId) {
        return document.querySelector(".captcha-solver[data-captcha-type='" + captchaType + "'][data-widget-id='" + widgetId + "']");
    };
    let uad = setInterval(function () {
        if (window.___grecaptcha_cfg === undefined) return;
        if (___grecaptcha_cfg.clients === undefined) return;

        for (let widgetId in ___grecaptcha_cfg.clients) {
            let widget = ___grecaptcha_cfg.clients[widgetId];

            if (getCaptchaWidgetButton("recaptcha", widget.id)) continue;
            console.log("recaptcha widget: ", widget);
            let widgetInfo = getRecaptchaWidgetInfo(widget);

            registerCaptchaWidget(widgetInfo);
            clearInterval(uad);
        }
    }, 2000);
    let registerCaptchaWidget = function (widgetInfo) {
        console.log(widgetInfo)
        let button = createSolverButton(widgetInfo.captchaType, widgetInfo.widgetId, widgetInfo);
        let input = document.getElementById(widgetInfo.containerId);
        if (input) {
            input.after(button);
            let btn = document.createElement('button');
            btn.type = "button";
            btn.id = "captcha-widget";
            btn.dataset.json = JSON.stringify(widgetInfo);
            btn.innerText = JSON.stringify(widgetInfo);
            btn.style.display = "none";
            document.body.appendChild(btn);
            btn.addEventListener("click", (event) => {
                button.value = btn.value;
                button.click()
            });
        }
        //clearInterval(CAPTCHA_WIDGETS_LOOP)
    };
    function createElementFromHTML(htmlString) {
        var div = document.createElement('div');
        div.innerHTML = htmlString.trim();
        return div.firstChild;
    }
    function createSolverButton(captchaType, widgetId, widgetInfo) {
        let button = createElementFromHTML(`
            <button class="captcha-solver captcha-solver_inner" data-state="ready" type="button" data-captcha-type="${captchaType}" data-widget-id="${widgetId}">
                solveWith2Captcha
            </button>
        `);
        button.dataset.json = JSON.stringify(widgetInfo);
        button.addEventListener("click", (event) => {
            var data = event.target.dataset;
            console.log("button", data);
            console.log(event.target.getAttribute('data-state'));
            let code = event.target.value;
            if (code) {
                document.getElementById("g-recaptcha-response").value = code;
                document.getElementById("g-recaptcha-response").innerHTML = code;
                //document.getElementById(widgetInfo.inputId).value = code;
                let textarea = document.createElement('textarea');
                textarea.id = 'twocaptcha-callback-trigger2';
                textarea.setAttribute('data-function', widgetInfo.callback);
                textarea.value = code;
                document.body.appendChild(textarea);
            }
        });

        return button;
    }
    function findRecaptchaClients() {
        // eslint-disable-next-line camelcase
        if (typeof (___grecaptcha_cfg) !== 'undefined') {
            // eslint-disable-next-line camelcase, no-undef
            return Object.entries(___grecaptcha_cfg.clients).map(([cid, client]) => {
                const data = { id: cid, version: cid >= 10000 ? 'V3' : 'V2' };
                const objects = Object.entries(client).filter(([_, value]) => value && typeof value === 'object');

                objects.forEach(([toplevelKey, toplevel]) => {
                    const found = Object.entries(toplevel).find(([_, value]) => (
                        value && typeof value === 'object' && 'sitekey' in value && 'size' in value
                    ));

                    if (typeof toplevel === 'object' && toplevel instanceof HTMLElement && toplevel['tagName'] === 'DIV') {
                        data.pageurl = toplevel.baseURI;
                    }

                    if (found) {
                        const [sublevelKey, sublevel] = found;

                        data.sitekey = sublevel.sitekey;
                        const callbackKey = data.version === 'V2' ? 'callback' : 'promise-callback';
                        const callback = sublevel[callbackKey];
                        if (!callback) {
                            data.callback = null;
                            data.function = null;
                        } else {
                            data.function = callback;
                            const keys = [cid, toplevelKey, sublevelKey, callbackKey].map((key) => `['${key}']`).join('');
                            data.callback = `___grecaptcha_cfg.clients${keys}`;
                        }
                    }
                });
                return data;
            });
        }
        return [];
    }
    let getRecaptchaWidgetInfo2 = function (widget) {
        // let widgetId = parseInt(Date.now() / 1000);

        // let badge = document.querySelector(".grecaptcha-badge");
        // if (!badge.id) badge.id = "recaptcha-badge-" + widgetId;

        let info = {
            captchaType: "recaptcha",
            widgetId: widget.id,
            version: "v2",
            sitekey: null,
            action: null,
            s: null,
            callback: null,
            enterprise: grecaptcha.enterprise ? true : false,
            containerId: null,
            bindedButtonId: null,
        };

        /*
         * Check if is badge
         */
        let isBadge = false;

        mainLoop: for (let k1 in widget) {
            if (typeof widget[k1] !== "object") continue;

            for (let k2 in widget[k1]) {
                if (widget[k1][k2] && widget[k1][k2].classList && widget[k1][k2].classList.contains("grecaptcha-badge")) {
                    isBadge = true;
                    break mainLoop;
                }
            }
        }


        /*
         * 1. Look for version
         */
        if (isBadge) {
            info.version = "v3";

            for (let k1 in widget) {
                let obj = widget[k1];

                if (typeof obj !== "object") continue;

                for (let k2 in obj) {
                    if (typeof obj[k2] !== "string") continue;
                    if (obj[k2] == "fullscreen") info.version = "v2_invisible";
                }
            }
        }

        /*
         * 2. Look for containerId
         */
        let n1;
        for (let k in widget) {
            if (widget[k] && widget[k].nodeType) {
                if (widget[k].id) {
                    info.containerId = widget[k].id;
                } else if (widget[k].dataset.sitekey) {
                    widget[k].id = "recaptcha-container-" + Date.now();
                    info.containerId = widget[k].id;
                } else if (info.version == 'v2') {
                    if (!n1) {
                        n1 = widget[k];
                        continue;
                    }

                    if (widget[k].isSameNode(n1)) {
                        widget[k].id = "recaptcha-container-" + Date.now();
                        info.containerId = widget[k].id;
                        break;
                    }
                }
            }
        }
        let d = findRecaptchaClients();
        //console.log("findRecaptchaClients:", d[0]);
        info.sitekey = d[0].sitekey;
        info.pageurl = d[0].pageurl;
        info.callback = d[0].callback;
        info.action = d[0].function;
        info.function = d[0].function;
        info.version = d[0].version;

        /*
         * 4. Prepare callback
         */
        console.log("info: ", info);
        if (info.callback) {
            console.log("callback: ", info.callback);
            let callbackKey = "reCaptchaWidgetCallback" + widget.id;
            window[callbackKey] = info.callback;
            info.callback = callbackKey;
        }

        return info;
    };

    let getRecaptchaWidgetInfo = function (widget) {
        // let widgetId = parseInt(Date.now() / 1000);

        // let badge = document.querySelector(".grecaptcha-badge");
        // if (!badge.id) badge.id = "recaptcha-badge-" + widgetId;

        let info = {
            captchaType: "recaptcha",
            widgetId: widget.id,
            version: "v2",
            sitekey: null,
            action: null,
            s: null,
            callback: null,
            enterprise: grecaptcha.enterprise ? true : false,
            containerId: null,
            bindedButtonId: null,
        };

        /*
         * Check if is badge
         */
        let isBadge = false;

        mainLoop: for (let k1 in widget) {
            if (typeof widget[k1] !== "object") continue;

            for (let k2 in widget[k1]) {
                if (widget[k1][k2] && widget[k1][k2].classList && widget[k1][k2].classList.contains("grecaptcha-badge")) {
                    isBadge = true;
                    break mainLoop;
                }
            }
        }


        /*
         * 1. Look for version
         */
        if (isBadge) {
            info.version = "v3";

            for (let k1 in widget) {
                let obj = widget[k1];

                if (typeof obj !== "object") continue;

                for (let k2 in obj) {
                    if (typeof obj[k2] !== "string") continue;
                    if (obj[k2] == "fullscreen") info.version = "v2_invisible";
                }
            }
        }

        /*
         * 2. Look for containerId
         */
        let n1;
        for (let k in widget) {
            if (widget[k] && widget[k].nodeType) {
                if (widget[k].id) {
                    info.containerId = widget[k].id;
                } else if (widget[k].dataset.sitekey) {
                    widget[k].id = "recaptcha-container-" + Date.now();
                    info.containerId = widget[k].id;
                } else if (info.version == 'v2') {
                    if (!n1) {
                        n1 = widget[k];
                        continue;
                    }

                    if (widget[k].isSameNode(n1)) {
                        widget[k].id = "recaptcha-container-" + Date.now();
                        info.containerId = widget[k].id;
                        break;
                    }
                }
            }
        }

        /*
         * 3. Look for sitekey, action, s and callback
         */
        for (let k1 in widget) {
            let obj = widget[k1];

            if (typeof obj !== "object") continue;

            for (let k2 in obj) {
                if (obj[k2] === null) continue;
                if (typeof obj[k2] !== "object") continue;
                if (obj[k2].sitekey === undefined) continue;
                if (obj[k2].action === undefined) continue;

                for (let k3 in obj[k2]) {
                    if (k3 === "sitekey") info.sitekey = obj[k2][k3];
                    if (k3 === "action") info.action = obj[k2][k3];
                    if (k3 === "s") info.s = obj[k2][k3];
                    if (k3 === "callback") info.callback = obj[k2][k3];
                    if (k3 === "bind" && obj[k2][k3]) {
                        if (typeof obj[k2][k3] === "string") {
                            info.bindedButtonId = obj[k2][k3];
                        } else {
                            let button = obj[k2][k3];
                            if (button.id === undefined) {
                                button.id = "recaptchaBindedElement" + widget.id;
                            }
                            info.bindedButtonId = button.id;
                        }
                    }
                }
            }
        }

        /*
         * 4. Prepare callback
         */
        console.log("info: ", info);
        if (typeof info.callback === "function") {
            console.log("callback: ", info.callback);
            let callbackKey = "reCaptchaWidgetCallback" + widget.id;
            window[callbackKey] = info.callback;
            info.callback = callbackKey;
        }

        return info;
    };
    setInterval(function () {
        let textarea = document.querySelector('textarea[id=twocaptcha-callback-trigger2]');
        if (textarea) {
            let func = textarea.getAttribute('data-function');
            let data = textarea.value;
            textarea.remove();
            console.log(func);
            console.log(data);
            if (func) {
                window[func](data);
            }
        }
    }, 1000);
})()