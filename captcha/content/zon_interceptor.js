(() => {

    let originalFunCaptcha;
    // console.log("handleArkoselabsInit")
    // Object.defineProperty(window, "FunCaptcha", {

    //     get: function () {
    //         return function (e) {
    //             handleArkoselabsInit(e);
    //             return originalFunCaptcha(e);
    //         };
    //     },

    //     set: function (e) {
    //         window.ArkoseEnforcement = new Proxy(window.ArkoseEnforcement, {
    //             construct: function (target, args) {
    //                 handleArkoselabsInit(args[0]);
    //                 return new target(...args);
    //             },
    //         });

    //         originalFunCaptcha = e;
    //     },

    // });
    // let yua2 = setInterval(() => {
    //     if (window.FunCaptcha) {
    //         console.log("interceptorFunc2")
    //         console.log(window.FunCaptcha)
    //         //interceptorFunc2();
    //         clearInterval(yua2);
    //     }
    // }, 1);
    // function interceptorFunc2() {
    //     window.ArkoseEnforcement = new Proxy(window.ArkoseEnforcement, {
    //         construct: function (target, args) {
    //             handleArkoselabsInit(args[0]);
    //             return new target(...args);
    //         },
    //     });
    // }
    // let handleArkoselabsInit = function (params) {
    //     let dataKey = "arkoselabs_data_dse7f73ek";
    //     let callbackKey = "arkoselabs_callback_dse7f73ek";
    //     console.log(params)
    //     window[callbackKey] = params.callback;
    //     if (params.data) {
    //         window[dataKey] = encodeURIComponent(JSON.stringify(params.data));
    //     }
    //     //console.log(window)
    // };
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
    //captcha-solver_inner
    // let yua2 = setInterval(() => {
    //     let solver_inner = document.querySelector(".captcha-solver_inner");
    //     let cf = document.querySelector('input[name="cf-turnstile-response"]');
    //     if (cf && !solver_inner) {
    //         console.log("interceptorFunc2");
    //         interceptorFunc();
    //         window.location.reload();
    //         //clearInterval(yua2);
    //     }
    // }, 2000);
    function as_callback(token) {
        console.log("Token: ", token)
        window.parent.postMessage(JSON.stringify({
            eventId: "challenge-complete",
            publicKey: window["arkoselabs_data_dse7f73ek"],
            payload: {
                sessionToken: token
            }
        }), "*")
    }
    let yua2 = setInterval(() => {
        let cf = document.querySelector('input[name=fc-token]:not([anticaptured])');
        if (cf) {
            var pk = cf.value.replace(/.*\|pk=([^\|]+)\|.*/, "$1");
            var surl = cf.value.replace(/.*\|surl=([^\|]+)\|.*/, "$1");
            console.log(pk, surl);
            let dataKey = "arkoselabs_data_dse7f73ek";
            let callbackKey = "arkoselabs_callback_dse7f73ek";
            window[callbackKey] = as_callback;
            window[dataKey] = pk;
            // if (params.data) {
            //     window[dataKey] = encodeURIComponent(JSON.stringify(params.data));
            // }
            clearInterval(yua2);
        }
    }, 1)

    let yua = setInterval(() => {
        if (window.turnstile) {
            console.log("interceptorFunc")
            interceptorFunc();
            clearInterval(yua);
        }
    }, 1)
    const interceptorFunc = function () {
        const initCaptcha = ([div, params]) => {
            const input = div.parentElement;
            let callbackKey = "arkoselabs_callback_dse7f73ek";
            let dataKey = "arkoselabs_data_dse7f73ek";
            if (!input.id) {
                input.id = "turnstile-input-" + params.sitekey;
            }
            window[callbackKey] = params.callback;
            window.tsCallback = params.callback;
            registerCaptchaWidget({
                captchaType: "turnstile",
                widgetId: params.sitekey,
                sitekey: params.sitekey,
                pageurl: window.location.href,
                data: params.cData,
                pagedata: params.chlPageData,
                action: params.action,
                callbackKey: params.callback,
                callback: callbackKey,
                inputId: input.id
            });
        }
        window.turnstile = new Proxy(window.turnstile, {
            get: function (target, prop) {
                if (prop === 'render') {
                    return new Proxy(target[prop], {
                        apply: (target, thisArg, argumentsList) => {
                            initCaptcha(argumentsList);
                            const obj = Reflect.apply(target, thisArg, argumentsList);
                            return obj;
                        }
                    });
                }
                return target[prop];
            }
        });
    }


    let CAPTCHA_WIDGETS_LOOP = setInterval(function () {
        //fixHeightIframe();
        let input = document.querySelector("input[name='fc-token']");
        if (!input) return;
        //console.log(input)
        if (!window.arkoselabs_callback_dse7f73ek) return;
        //console.log(window.arkoselabs_callback_dse7f73ek)
        let widgetInfo = getArkoselabsWidgetInfo(input);
        registerCaptchaWidget(widgetInfo);
        clearInterval(CAPTCHA_WIDGETS_LOOP);
    }, 2000);
    let fixHeightIframe = function () {
        const iframes = document.querySelectorAll('iframe');
        if (iframes) {
            iframes.forEach(function (iframe) {
                if (iframe.getAttribute('data-e2e') === 'enforcement-frame') {
                    if (!iframe.hasAttribute('data-height') || iframe.offsetHeight < 200) {
                        iframe.setAttribute('data-height', iframe.offsetHeight);
                    }
                    iframe.style.height = (+iframe.getAttribute('data-height') + 100) + 'px';
                }
            })
        }
    }
    let registerCaptchaWidget = function (widgetInfo) {
        console.log(widgetInfo)
        let input = document.getElementById(widgetInfo.inputId);
        let button = createSolverButton(widgetInfo.captchaType, widgetInfo.widgetId, widgetInfo);
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
            //console.log(event)
        });
        window.parent.postMessage({ type: "addbtn", value: widgetInfo }, "*");
        clearInterval(CAPTCHA_WIDGETS_LOOP)
    };
    let getArkoselabsWidgetInfo = function (input) {
        if (!input.id) {
            input.id = "arkoselab-input-0";
        }

        let params = {};

        input.value.split('|').forEach(pair => {
            let p = pair.split('=');
            params[p[0]] = unescape(p[1]);
        });
        var t = document.createElement("a");
        t.href = window.location.href;
        return {
            captchaType: "funcaptcha",
            widgetId: 0,
            pkey: params.pk,
            surl: params.surl,
            inputId: input.id,
            callback: "arkoselabs_callback_dse7f73ek",
            data: window["arkoselabs_data_dse7f73ek"] || null,
        };
    };
    function createElementFromHTML(htmlString) {
        var div = document.createElement('div');
        div.innerHTML = htmlString.trim();
        return div.firstChild;
    }
    function createSolverButton(captchaType, widgetId, widgetInfo) {
        let button = createElementFromHTML('<button class="captcha-solver captcha-solver_inner" data-state="ready" type="button" data-captcha-type="' + captchaType + '" data-widget-id="' + widgetId + '">solveWith2Captcha </button>');
        button.dataset.json = JSON.stringify(widgetInfo);
        button.addEventListener("click", (event) => {
            var data = event.target.dataset;
            console.log("button", data);
            console.log(event.target.getAttribute('data-state'));
            let code = event.target.value;
            if (code) {

                document.getElementById(widgetInfo.inputId).value = code;
                //$("#" + widgetInfo.inputId).val(code);
                let cf = document.querySelector('input[name="cf-turnstile-response"]');
                if (cf)
                    cf.value = code;
                let recaptcha = document.querySelector('input[name="g-recaptcha-response"]');
                if (recaptcha)
                    recaptcha.value = code;
                let textarea = document.createElement('textarea');
                textarea.id = 'twocaptcha-callback-trigger';
                textarea.setAttribute('data-function', widgetInfo.callback);
                textarea.value = code;
                document.body.appendChild(textarea);
            }
        });

        return button;
    }
    setInterval(function () {
        let textarea = document.querySelector('textarea[id=twocaptcha-callback-trigger]');
        if (textarea) {
            let func = textarea.getAttribute('data-function');
            let data = textarea.value;
            textarea.remove();
            window[func](data);
        }
    }, 1000);
    if (chrome && chrome.extension)
        chrome.extension.onMessage.addListener(function (
            request,
            sender,
            sendResponse
        ) {
            console.log(request);
        });
})()
function inIframe() {
    try {
        return window.self !== window.top;
    } catch (e) {
        return true;
    }
}
window.addEventListener("message", function (e) {
    if (!e.data || typeof e.data === "object") return;
    try {
        var a = JSON.parse(e.data);
        switch (a.eventId) {
            case "challenge-complete":
                console.log(a);
                let btn = document.getElementById("captcha-widget");
                if (btn)
                    btn.remove();
                window.parent.postMessage({ type: "rmbtn" }, "*");
                break;
        }
    } catch (x) {
    }
});
window.addEventListener("message", function (e) {
    if (inIframe()) {
        if (e.data.type == "addbtn")
            window.parent.postMessage(e.data, "*");
        else if (e.data.type == "click" || e.data.type == "rmbtn") {
            let btn = document.getElementById("captcha-widget");
            if (btn) {
                if (e.data.type == "rmbtn")
                    btn.remove();
                else {
                    btn.value = e.data.value;
                    btn.click();
                }
            } else {
                console.log(e);
                if (e.data.type == "rmbtn") {
                    window.parent.postMessage(e.data, "*");
                }
                document.querySelector("iframe").contentWindow.postMessage(e.data, "*");
            }
        }
    } else if (e.data.type == "addbtn") {
        console.log(e);
        let btn = document.createElement('button');
        btn.type = "button";
        btn.id = "captcha-widget";
        btn.dataset.json = JSON.stringify(e.data.value);
        btn.innerText = JSON.stringify(e.data.value);
        btn.style.display = "none";
        document.body.appendChild(btn);
        btn.addEventListener("click", (event) => {
            document.querySelector("iframe[src*='" + e.origin + "']").contentWindow.postMessage({ type: "click", value: event.target.value }, "*");
            console.log(event)
        });
    } else if (e.data.type == "rmbtn") {
        let btn = document.getElementById("captcha-widget");
        if (btn)
            btn.remove();
    }
});