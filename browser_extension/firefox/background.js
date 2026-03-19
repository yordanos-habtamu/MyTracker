let currentTabId = null;
let startTime = null;
let currentTabData = {};

function sendToFlask(data) {
    fetch("http://localhost:5001/tab_update", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data)
    }).catch(err => console.log("Flask offline"));
}

function handleTabChange(newTabId) {
    const now = Date.now();

    // 1. If we were tracking a previous tab, finalize it and send data
    if (currentTabId !== null && startTime !== null) {
        const timeSpentSeconds = Math.round((now - startTime) / 1000);
        if (timeSpentSeconds > 0) {
            sendToFlask({
                ...currentTabData,
                duration: timeSpentSeconds,
                event: "tab_closed_or_switched"
            });
        }
    }

    // 2. Start tracking the new tab
    browser.tabs.get(newTabId).then(tab => {
        if (!tab.url || tab.url.startsWith('about:')) return;
        
        currentTabId = newTabId;
        startTime = Date.now();
        currentTabData = {
            app: "Firefox",
            title: tab.title,
            url: tab.url
        };
    });
}

// Listen for tab switches
browser.tabs.onActivated.addListener(activeInfo => {
    handleTabChange(activeInfo.tabId);
});

// Listen for URL changes in the same tab
browser.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
    if (changeInfo.status === "complete" && tab.active) {
        handleTabChange(tabId);
    }
});

// Handle tab closing
browser.tabs.onRemoved.addListener((tabId, removeInfo) => {
    if (tabId === currentTabId) {
        const now = Date.now();
        const timeSpentSeconds = Math.round((now - startTime) / 1000);
        if (timeSpentSeconds > 0) {
            sendToFlask({
                ...currentTabData,
                duration: timeSpentSeconds,
                event: "tab_closed"
            });
        }
        currentTabId = null;
        startTime = null;
        currentTabData = {};
    }
});