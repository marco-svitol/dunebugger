Here's a JavaScript code example for the frontend that you can store in a static web app. This code will handle authentication with Auth0, establish a WebSocket connection with Azure Web PubSub, show the status of the remote Raspberry Pi, send messages to the Raspberry Pi, and receive messages from the Raspberry Pi.

### HTML File (`index.html`)
```html
<!DOCTYPE html>
<html>
<head>
    <title>Raspberry Pi Control Panel</title>
    <script src="https://cdn.auth0.com/js/auth0-spa-js/1.19/auth0-spa-js.production.js"></script>
    <script src="app.js"></script>
</head>
<body>
    <h1>Raspberry Pi Control Panel</h1>
    <div id="status">Connecting...</div>
    <button onclick="sendMessage('toggle')">Toggle GPIO</button>
    <div id="log"></div>
</body>
</html>
```

### JavaScript File (`app.js`)
```javascript
const auth0Domain = 'your-auth0-domain';
const clientId = 'your-client-id';
const audience = 'your-audience';
const raspberryClientId = 'raspberry-client-id';

let auth0 = null;
let websocket = null;

window.onload = async () => {
    await configureClient();
    await login();
    const wssUrl = await getWssUrl();
    connectWebSocket(wssUrl);
};

const configureClient = async () => {
    auth0 = await createAuth0Client({
        domain: auth0Domain,
        client_id: clientId,
        audience: audience
    });
};

const login = async () => {
    await auth0.loginWithPopup();
    const user = await auth0.getUser();
    document.getElementById('status').innerText = `Logged in as ${user.name}`;
};

const getWssUrl = async () => {
    const token = await auth0.getTokenSilently();
    const response = await fetch('https://your-backend-url/get-wss-url', {
        headers: {
            Authorization: `Bearer ${token}`
        }
    });
    const data = await response.json();
    return data.url;
};

const connectWebSocket = (url) => {
    websocket = new WebSocket(url);

    websocket.onopen = () => {
        document.getElementById('status').innerText = 'Connected to WebSocket';
        sendMessage(JSON.stringify({ action: 'status', clientId: raspberryClientId }));
    };

    websocket.onmessage = (event) => {
        const log = document.getElementById('log');
        const message = JSON.parse(event.data);
        log.innerHTML += `<p>${message}</p>`;
    };

    websocket.onclose = () => {
        document.getElementById('status').innerText = 'WebSocket connection closed';
    };
};

const sendMessage = (message) => {
    if (websocket && websocket.readyState === WebSocket.OPEN) {
        websocket.send(message);
        console.log(`Sent: ${message}`);
    } else {
        console.log('WebSocket is not connected');
    }
};
```

### Explanation
1. **HTML File**: Basic structure with a status display, a button to send a message, and a log box to show received messages.
2. **JavaScript File**:
   - **Auth0 Configuration**: Initializes the Auth0 client and handles user login.
   - **Get WSS URL**: Fetches the WebSocket URL from the backend using the Auth0 token.
   - **WebSocket Connection**: Establishes a WebSocket connection, sends a status request to the Raspberry Pi, and handles incoming messages.
   - **Send Message**: Sends messages to the Raspberry Pi through the WebSocket connection.

### Usage
- Replace the placeholders (`your-auth0-domain`, `your-client-id`, etc.) with your actual Auth0 and Web PubSub details.
- Deploy the HTML and JavaScript files to your static web app hosting service.

This setup ensures that your frontend can authenticate with Auth0, establish a WebSocket connection with Azure Web PubSub, and communicate with the Raspberry Pi.
