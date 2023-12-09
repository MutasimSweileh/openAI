(() => {
    let originalFunCaptcha;
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
    //console.log("handleArkoselabsInit")
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

})()


let scripts = [
    //["content/injected.js"],
    ["content/recaptcha_interceptor.js"],
    ["content/zon_interceptor.js"],
    //["content/funcaptcha_object_inteceptor.js"]
];

scripts.forEach(s => {
    if (s.length > 1 && !s[1]) return;
    let script = document.createElement('script');
    script.src = chrome.runtime.getURL(s[0]);
    (document.head || document.documentElement).prepend(script);
});