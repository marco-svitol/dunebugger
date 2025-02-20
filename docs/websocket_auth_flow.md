1. **Raspberry Pi Authentication**:
   - The Raspberry Pi uses provided credentials (e.g., username/password or client certificate) to authenticate with the backend hosted on an Azure Function.

2. **Fetch WSS URL**:
   - The Raspberry Pi makes an API request to the Azure Function. The Azure Function uses the connection string to generate a Client Access URL (WSS URL) with a token.

3. **Establish WebSocket Connection**:
   - The Raspberry Pi uses the WSS URL to establish a WebSocket connection with Azure Web PubSub. The token in the URL has a limited TTL (Time-To-Live).

4. **Frontend Authentication**:
   - A similar authentication flow occurs for the frontend (mobile app or browser). The frontend authenticates with the backend using credentials.

5. **Fetch WSS URL for Frontend**:
   - The frontend makes an API request to the Azure Function to fetch the WSS URL.

6. **Establish WebSocket Connection for Frontend**:
   - The frontend uses the WSS URL to establish a WebSocket connection with Azure Web PubSub.

7. **Message Communication**:
   - Both the Raspberry Pi and the frontend are now connected to Azure Web PubSub. They can send and receive messages through the WebSocket connections.

8. **Backend Logic**:
   - The Azure Function can also be connected to Azure Web PubSub to intercept and evaluate messages. It can act as a mediator, processing messages and performing necessary actions.

### Diagram of the Architecture

```plaintext
+-------------------+       +-------------------+       +-------------------+
|                   |       |                   |       |                   |
|   Raspberry Pi    |       |   Azure Function  |       |   Mobile App /    |
|                   |       |                   |       |   Browser         |
+--------+----------+       +--------+----------+       +--------+----------+
         |                           |                           |
         | 1. Authenticate           |                           |
         |-------------------------->|                           |
         |                           |                           |
         | 2. Fetch WSS URL          |                           |
         |-------------------------->|                           |
         |                           |                           |
         | 3. Use WSS URL to connect |                           |
         |<--------------------------|                           |
         |                           |                           |
         |                           | 4. Authenticate           |
         |                           |<--------------------------|
         |                           |                           |
         |                           | 5. Fetch WSS URL          |
         |                           |<--------------------------|
         |                           |                           |
         |                           | 6. Use WSS URL to connect |
         |                           |-------------------------->|
         |                           |                           |
```
