/* Toggle Profile Menu */
function toggleMenu() {
    let menu = document.getElementById("profileMenu");
    menu.style.display = (menu.style.display === "block") ? "none" : "block";
}

/* Request Notification Permission */
document.addEventListener("DOMContentLoaded", function() {
    if ("Notification" in window && Notification.permission !== "granted") {
        Notification.requestPermission();
    }
});

/* Show Browser Notification */
function showNotification(title) {
    if (Notification.permission === "granted") {
        new Notification("Task Reminder", {
            body: title,
            icon: "https://cdn-icons-png.flaticon.com/512/1827/1827379.png"
        });
    }
}

/* Poll Backend Every 30 Seconds */
async function checkTaskNotification() {
    try {
        let response = await fetch("/tasks_due");
        let tasks = await response.json();
        tasks.forEach(task => {
            showNotification(task.title);
        });
    } catch (err) {
        console.log(err);
    }
}

/* Start Interval */
setInterval(checkTaskNotification, 30000);