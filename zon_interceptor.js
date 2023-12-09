(() => {
    let originalFunCaptcha;
    console.log("handleArkoselabsInit")
    Object.defineProperty(window, "FunCaptcha", {

        get: function () {
            return function (e) {
                handleArkoselabsInit(e);
                return originalFunCaptcha(e);
            };
        },

        set: function (e) {
            window.ArkoseEnforcement = new Proxy(window.ArkoseEnforcement, {
                construct: function (target, args) {
                    handleArkoselabsInit(args[0]);
                    return new target(...args);
                },
            });

            originalFunCaptcha = e;
        },

    });

    let handleArkoselabsInit = function (params) {
        let dataKey = "arkoselabs_data_dse7f73ek";
        let callbackKey = "arkoselabs_callback_dse7f73ek";
        console.log(params)
        window[callbackKey] = params.callback;

        if (params.data) {
            window[dataKey] = encodeURIComponent(JSON.stringify(params.data));
        }
        //console.log(window)
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
    //captcha-solver_inner
    let yua2 = setInterval(() => {
        let solver_inner = document.querySelector(".captcha-solver_inner");
        let cf = document.querySelector('input[name="cf-turnstile-response"]');
        if (cf && !solver_inner) {
            console.log("interceptorFunc2");
            interceptorFunc();
            window.location.reload();
            //clearInterval(yua2);
        }
    }, 2000);
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
        fixHeightIframe();
        let input = document.querySelector("input[name='fc-token']");
        if (!input) return;
        console.log(input)
        if (!window.arkoselabs_callback_dse7f73ek) return;
        console.log(window.arkoselabs_callback_dse7f73ek)
        let widgetInfo = getArkoselabsWidgetInfo(input);
        registerCaptchaWidget(widgetInfo);
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
        let button = createSolverButton(widgetInfo.captchaType, widgetInfo.widgetId, widgetInfo);
        let input = document.getElementById(widgetInfo.inputId);
        input.after(button);
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

        return {
            captchaType: "arkoselabs",
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
                document.querySelector('input[name="cf-turnstile-response"]').value = code;
                document.querySelector('input[name="g-recaptcha-response"]').value = code;
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
})()