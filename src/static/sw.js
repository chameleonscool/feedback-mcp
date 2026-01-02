self.addEventListener('notificationclick', function (event) {
    const taskId = event.notification.tag;
    event.notification.close();

    // Deep link URL
    const url = '/#' + taskId;

    // This looks for an existing window and focuses it
    event.waitUntil(
        clients.matchAll({ type: 'window', includeUncontrolled: true }).then(function (clientList) {
            for (let i = 0; i < clientList.length; i++) {
                const client = clientList[i];
                // Check if the client is already matching our app (roughly)
                if (client.url.indexOf(location.origin) === 0 && 'focus' in client) {
                    client.postMessage({ type: 'SELECT_TASK', id: taskId });
                    return client.focus();
                }
            }
            // If no window is open, open a new one
            if (clients.openWindow) {
                return clients.openWindow(url);
            }
        })
    );
});
