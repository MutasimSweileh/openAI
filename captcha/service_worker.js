chrome.runtime.onMessage.addListener(function (request, sender, sendResponse) {
    chrome.tabs.query({ currentWindow: true }, function (tabs) {
        for (var i in tabs) {
            chrome.tabs.sendMessage(tabs[i].id, request);
        }
    });
});