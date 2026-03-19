document.getElementById('check').addEventListener('click', () => {
    // Test connection to Flask server
    fetch("http://localhost:5001/", {
        method: "GET",
        headers: { "Content-Type": "application/json" }
    })
    .then(response => {
        if (response.ok) {
            alert("✅ Connection successful! Flask server is running on port 5001.");
        } else {
            alert("❌ Server responded but with error status: " + response.status);
        }
    })
    .catch(err => {
        alert("❌ Connection failed. Make sure the desktop tracker is running on port 5001.\n\nError: " + err.message);
    });
});

// Check connection status on popup open
window.addEventListener('load', () => {
    // Try to get current tab info to verify extension is working
    browser.tabs.query({active: true, currentWindow: true}).then(tabs => {
        if (tabs.length > 0 && tabs[0].url && !tabs[0].url.startsWith('about:')) {
            document.querySelector('.status').textContent = "🟢 Active on current tab";
        } else {
            document.querySelector('.status').textContent = "🟡 No active tab";
        }
    });
    
    // Test server connection
    fetch("http://localhost:5001/", {
        method: "GET",
        headers: { "Content-Type": "application/json" }
    })
    .then(response => {
        if (response.ok) {
            document.querySelector('.status').textContent = "🟢 Extension connected to server";
        }
    })
    .catch(err => {
        document.querySelector('.status').textContent = "🔴 Server connection failed";
    });
});
