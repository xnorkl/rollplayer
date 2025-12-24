// ==UserScript==
// @name         Roll20 Chat Connector
// @namespace    https://github.com/Griesbacher/roll20_chatbot
// @version      0.1
// @description  Connects the Roll20 chat to a WebSocket
// @author       Philip Griesbacher
// @match        https://app.roll20.net/*
// @updateURL    https://raw.githubusercontent.com/Griesbacher/roll20_chat_bot/master/chat_connector.js
// @downloadURL  https://raw.githubusercontent.com/Griesbacher/roll20_chat_bot/master/chat_connector.js
// ==/UserScript==
(function() {
    'use strict';

    // ============================================================================
    // CONFIGURATION
    // ============================================================================
    // WebSocket server address
    // For local development: "ws://localhost:5678"
    // For Fly.io deployment: "wss://your-app-name.fly.dev"
    // Use "ws://" for unencrypted, "wss://" for encrypted (required for HTTPS pages)
    const webSocketAddress = (function() {
        // Try to get from localStorage (allows runtime configuration)
        const stored = localStorage.getItem('roll20_chatbot_ws_url');
        if (stored) {
            return stored;
        }
        // Default: check if we're on HTTPS (use wss) or HTTP (use ws)
        // For local development, default to localhost
        if (window.location.protocol === 'https:') {
            // HTTPS page - use secure WebSocket (wss://)
            // Change this to your Fly.io app URL
            return "wss://roll20-chatbot.fly.dev";
        } else {
            // HTTP page - use unencrypted WebSocket (ws://)
            return "ws://localhost:5678";
        }
    })();
    
    // ============================================================================
    // END CONFIGURATION
    // ============================================================================

    const targetNode = document.getElementById('textchat');
    var webSocket;
    function connectToBackend(){
        const wsUrl = localStorage.getItem('roll20_chatbot_ws_url') || webSocketAddress;
        console.log("connecting to:", wsUrl);
        webSocket = new WebSocket(wsUrl)
        webSocket.onopen = function(event) {
            alert("ChatBot connected");
        };
        webSocket.onmessage = function (event) {
            console.log("<",event.data);
            var textArea;
            Array.from(document.getElementsByClassName("ui-autocomplete-input")).forEach(
                function(element, index, array) {
                    if (element.nodeName === "TEXTAREA") {
                        element.value = event.data;;
                    }
                }
            );
            Array.from(document.getElementsByClassName("btn")).forEach(
                function(element, index, array) {
                    if (element.innerText === "Send") {
                        element.click();
                    }
                }
            );
        }
        webSocket.onclose = function(event) {
            console.log(`[close] Connection closed code=${event.code} reason=${event.reason} clean=${event.wasClean}`);
            setTimeout(connectToBackend, 5000);
        };
    }
    connectToBackend();

    function extractMessageInfo(node) {
        // Try to extract sender name and message text
        var senderName = "Unknown";
        var messageText = "";
        
        // Look for sender name in various possible locations
        var senderElement = node.querySelector('.byline, .sendername, [data-sender]');
        if (senderElement) {
            senderName = senderElement.textContent.trim() || senderElement.getAttribute('data-sender') || "Unknown";
        }
        
        // Extract message text
        var messageElement = node.querySelector('.message, .msg, [data-message]');
        if (messageElement) {
            messageText = messageElement.textContent.trim();
        } else {
            // Fallback: get all text content
            messageText = node.textContent.trim();
        }
        
        return {
            sender: senderName,
            message: messageText,
            html: node.outerHTML
        };
    }

    var observer = new MutationObserver(function(mutations) {
        mutations.forEach(function(mutation) {
            if (webSocket.readyState === WebSocket.OPEN){
                mutation.addedNodes.forEach(function(node) {
                    // Only process if it's an element node with chat content
                    if (node.nodeType === 1 && (node.classList.contains('message') || node.querySelector('.message'))) {
                        var messageInfo = extractMessageInfo(node);
                        console.log("Sending message:", messageInfo);
                        webSocket.send(JSON.stringify({
                            type: "chat",
                            data: node.outerHTML,
                            sender: messageInfo.sender,
                            message: messageInfo.message
                        }));
                    }
                });
            }
        });
    });

    observer.observe(targetNode, {
        childList: true, subtree: true
    });
})();