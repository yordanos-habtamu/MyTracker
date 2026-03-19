function sendTabInfo(tab) {
    fetch("http://localhost:5001/tab_update", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({
            app: "Chrome",
            title: tab.title,
            url: tab.url
        })
    });
}

chrome.tabs.onActivated.addListener(activeInfo => {
    chrome.tabs.get(activeInfo.tabId, sendTabInfo);
});

chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
    if (changeInfo.status === "complete") sendTabInfo(tab);
});