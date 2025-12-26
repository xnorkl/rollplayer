# Client-Side Testing Guide

This guide explains how to test the `chat_connector.js` Tampermonkey userscript that connects Roll20 to the chatbot server.

## Overview

The client-side code (`chat_connector.js`) is a Tampermonkey userscript that:

- Monitors Roll20 chat for new messages
- Connects to a WebSocket server
- Sends chat messages to the server
- Receives responses and posts them back to Roll20 chat

## Testing Methods

### 1. Manual Testing in Roll20 (Recommended for Full Integration)

This is the most realistic way to test the client-side code:

1. **Start the chatbot server**:

   ```bash
   python3 chat_bot.py
   ```

2. **Install Tampermonkey**:

   - Install the [Tampermonkey extension](https://www.tampermonkey.net/) in your browser
   - Open Tampermonkey dashboard
   - Create a new script and paste the contents of `chat_connector.js`
   - Save the script

3. **Configure WebSocket URL** (if needed):

   - Open browser console (F12) on Roll20
   - Set the WebSocket URL:
     ```javascript
     localStorage.setItem("roll20_chatbot_ws_url", "ws://localhost:5678");
     ```
   - Refresh the page

4. **Test in Roll20**:

   - Open a Roll20 game
   - Open browser console (F12) to see connection logs
   - Send a test message in chat: `!roll 2d6`
   - Check console for:
     - Connection confirmation: `"connecting to: ws://localhost:5678"`
     - Message sending: `"Sending message: {...}"`
     - Server responses: `"< response text"`

5. **Verify functionality**:
   - Connection should show: `"ChatBot connected"` alert
   - Commands should trigger responses in chat
   - Check browser console for any errors

### 2. Standalone HTML Test Page

Use the provided `test_client.html` file to test the client code without Roll20:

1. **Start the chatbot server**:

   ```bash
   python3 chat_bot.py
   ```

2. **Open the test page**:

   ```bash
   # In a new terminal
   python3 -m http.server 8000
   ```

   Then open `http://localhost:8000/test_client.html` in your browser

3. **Test the connection**:
   - The page simulates Roll20's chat structure
   - Open browser console (F12) to see logs
   - Type messages in the chat input
   - Watch for WebSocket messages and responses

### 3. Browser Console Testing

Test individual functions directly in the browser console:

1. **Load the script in Roll20** (with Tampermonkey installed)

2. **Open browser console** (F12)

3. **Test WebSocket connection**:

   ```javascript
   // Check if WebSocket is connected
   console.log(webSocket?.readyState); // Should be 1 (OPEN)

   // Manually send a test message
   webSocket.send(
     JSON.stringify({
       type: "chat",
       data: "<div data-messageid='test123'>!roll 2d6</div>",
       sender: "TestUser",
       message: "!roll 2d6",
     })
   );
   ```

4. **Test message extraction**:

   ```javascript
   // Create a test message node
   const testNode = document.createElement("div");
   testNode.className = "message";
   testNode.innerHTML =
     '<span class="byline">TestUser</span><div class="message">!roll 2d6</div>';

   // Test extraction (if function is accessible)
   // Note: extractMessageInfo is not exposed globally, so this is for reference
   ```

### 4. Unit Testing with Node.js/Jest

For more structured testing, you can extract testable functions:

1. **Create a test file** (e.g., `test_client.js`):

   ```javascript
   // Mock DOM and WebSocket
   global.WebSocket = class MockWebSocket {
     constructor(url) {
       this.url = url;
     }
     send() {}
     close() {}
   };

   // Test message extraction logic
   // (Would need to extract functions from userscript)
   ```

2. **Run tests**:
   ```bash
   npm install --save-dev jest
   npm test
   ```

### 5. WebSocket Testing Tools

Use external tools to test the WebSocket connection:

1. **Using `wscat`** (WebSocket cat):

   ```bash
   npm install -g wscat
   wscat -c ws://localhost:5678
   ```

   Then send test messages:

   ```json
   {
     "type": "chat",
     "data": "<div>!roll 2d6</div>",
     "sender": "Test",
     "message": "!roll 2d6"
   }
   ```

2. **Using browser WebSocket client**:
   - Open browser console
   - Connect manually:
     ```javascript
     const ws = new WebSocket("ws://localhost:5678");
     ws.onopen = () => console.log("Connected");
     ws.onmessage = (e) => console.log("Received:", e.data);
     ws.send(
       JSON.stringify({
         type: "chat",
         data: "<div>!roll 2d6</div>",
         sender: "Test",
         message: "!roll 2d6",
       })
     );
     ```

## Testing Checklist

### Connection Testing

- [ ] WebSocket connects successfully
- [ ] Connection alert appears
- [ ] Reconnection works after disconnect
- [ ] Correct WebSocket URL is used (local vs production)

### Message Sending

- [ ] Chat messages are detected
- [ ] Messages are sent to server in correct format
- [ ] Duplicate messages are not sent
- [ ] Message extraction works (sender, message text)

### Response Handling

- [ ] Server responses are received
- [ ] Responses are posted to Roll20 chat
- [ ] Textarea is populated correctly
- [ ] Send button is clicked automatically

### Error Handling

- [ ] Connection errors are logged
- [ ] Reconnection attempts after disconnect
- [ ] Invalid messages don't crash the script
- [ ] Missing DOM elements are handled gracefully

## Debugging Tips

1. **Enable verbose logging**:

   - The script logs to browser console
   - Check for `"connecting to:"`, `"Sending message:"`, `"<"` (responses)

2. **Check WebSocket state**:

   ```javascript
   // In browser console
   webSocket?.readyState;
   // 0 = CONNECTING, 1 = OPEN, 2 = CLOSING, 3 = CLOSED
   ```

3. **Monitor network traffic**:

   - Open browser DevTools → Network tab
   - Filter by "WS" (WebSocket)
   - See messages sent/received

4. **Test with different configurations**:

   ```javascript
   // Test local
   localStorage.setItem("roll20_chatbot_ws_url", "ws://localhost:5678");

   // Test production
   localStorage.setItem(
     "roll20_chatbot_ws_url",
     "wss://roll20-chatbot.fly.dev"
   );

   // Clear and use default
   localStorage.removeItem("roll20_chatbot_ws_url");
   ```

## Common Issues

### Connection Fails

- **Check server is running**: `curl http://localhost:5678/health`
- **Check WebSocket URL**: Verify in browser console
- **Check firewall**: Ensure port 5678 is accessible
- **HTTPS pages**: Must use `wss://` (secure WebSocket)

### Messages Not Sending

- **Check WebSocket state**: Should be `OPEN` (1)
- **Check DOM structure**: Roll20 may have changed HTML structure
- **Check console errors**: Look for JavaScript errors

### Responses Not Appearing

- **Check server logs**: Verify server received and processed message
- **Check response format**: Should be plain text
- **Check DOM selectors**: Roll20 UI may have changed

## Automated Testing

For CI/CD, you can:

1. **Use headless browser** (Puppeteer/Playwright):

   ```javascript
   const puppeteer = require("puppeteer");
   // Load Roll20 page, inject script, test
   ```

2. **Mock Roll20 DOM**:

   - Create test HTML with Roll20-like structure
   - Inject userscript
   - Test message detection and sending

3. **WebSocket mock server**:
   - Use a simple WebSocket echo server
   - Test client connection and message handling

See `test_client.html` for a basic test page implementation.
