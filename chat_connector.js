// ==UserScript==   
// @name         Roll20 Chat Connector
// @namespace    https://github.com/xnorkl/roll20_shadowdark_GM
// @version      0.1
// @description  Connects the Roll20 chat to a WebSocket
// @author       Thomas Gordon (@xnorkl)
// @match        https://app.roll20.net/*
// @updateURL    https://raw.githubusercontent.com/xnorkl/roll20_shadowdark_GM/main/chat_connector.js
// @downloadURL  https://raw.githubusercontent.com/xnorkl/roll20_shadowdark_GM/main/chat_connector.js
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
            // #region agent log
            fetch('http://127.0.0.1:7242/ingest/f44cea64-0bc3-42f2-97f3-ae109d0be063',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'chat_connector.js:49',message:'WebSocket opened',data:{url:wsUrl,readyState:webSocket.readyState},timestamp:Date.now(),sessionId:'debug-session',runId:'run3',hypothesisId:'G'})}).catch(()=>{});
            // #endregion
            alert("ChatBot connected");
        };
        webSocket.onerror = function(event) {
            // #region agent log
            fetch('http://127.0.0.1:7242/ingest/f44cea64-0bc3-42f2-97f3-ae109d0be063',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'chat_connector.js:54',message:'WebSocket error',data:{readyState:webSocket.readyState,url:wsUrl},timestamp:Date.now(),sessionId:'debug-session',runId:'run3',hypothesisId:'G'})}).catch(()=>{});
            // #endregion
            console.error("WebSocket error:", event);
        };
        webSocket.onmessage = function (event) {
            console.log("<",event.data);
            // #region agent log
            fetch('http://127.0.0.1:7242/ingest/f44cea64-0bc3-42f2-97f3-ae109d0be063',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'chat_connector.js:52',message:'WebSocket message received',data:{messageLength:event.data.length},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'A'})}).catch(()=>{});
            // #endregion
            var textArea;
            var textareas = Array.from(document.getElementsByClassName("ui-autocomplete-input"));
            // #region agent log
            fetch('http://127.0.0.1:7242/ingest/f44cea64-0bc3-42f2-97f3-ae109d0be063',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'chat_connector.js:56',message:'Found textareas before manipulation',data:{count:textareas.length,types:textareas.map(e=>e.nodeName)},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'E'})}).catch(()=>{});
            // #endregion
            var textareaFound = false;
            textareas.forEach(
                function(element, index, array) {
                    if (element.nodeName === "TEXTAREA") {
                        textareaFound = true;
                        // #region agent log
                        var beforeProps = {hasControl:!!element.control,isFocused:document.activeElement===element,hasValue:element.value!==undefined,className:element.className,id:element.id||'no-id'};
                        fetch('http://127.0.0.1:7242/ingest/f44cea64-0bc3-42f2-97f3-ae109d0be063',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'chat_connector.js:64',message:'Textarea before manipulation',data:beforeProps,timestamp:Date.now(),sessionId:'debug-session',runId:'run2',hypothesisId:'F'})}).catch(()=>{});
                        // #endregion
                        // Blur the textarea first to avoid triggering focus handlers when clicking Send
                        if (document.activeElement === element) {
                            element.blur();
                            // #region agent log
                            fetch('http://127.0.0.1:7242/ingest/f44cea64-0bc3-42f2-97f3-ae109d0be063',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'chat_connector.js:69',message:'Blurred textarea before setting value',data:{},timestamp:Date.now(),sessionId:'debug-session',runId:'run2',hypothesisId:'F'})}).catch(()=>{});
                            // #endregion
                        }
                        element.value = event.data;
                        // #region agent log
                        var afterProps = {hasControl:!!element.control,isFocused:document.activeElement===element,valueLength:element.value.length};
                        fetch('http://127.0.0.1:7242/ingest/f44cea64-0bc3-42f2-97f3-ae109d0be063',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'chat_connector.js:74',message:'Textarea value set after blur',data:afterProps,timestamp:Date.now(),sessionId:'debug-session',runId:'run2',hypothesisId:'F'})}).catch(()=>{});
                        // #endregion
                    }
                }
            );
            // #region agent log
            if (!textareaFound) {
                fetch('http://127.0.0.1:7242/ingest/f44cea64-0bc3-42f2-97f3-ae109d0be063',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'chat_connector.js:79',message:'No textarea found',data:{textareasCount:textareas.length},timestamp:Date.now(),sessionId:'debug-session',runId:'run2',hypothesisId:'E'})}).catch(()=>{});
            }
            // #endregion
            var buttons = Array.from(document.getElementsByClassName("btn"));
            // #region agent log
            fetch('http://127.0.0.1:7242/ingest/f44cea64-0bc3-42f2-97f3-ae109d0be063',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'chat_connector.js:82',message:'Found buttons before click',data:{count:buttons.length,sendButtons:buttons.filter(b=>b.innerText==='Send').length,activeElement:document.activeElement?document.activeElement.tagName:'none'},timestamp:Date.now(),sessionId:'debug-session',runId:'run2',hypothesisId:'F'})}).catch(()=>{});
            // #endregion
            buttons.forEach(
                function(element, index, array) {
                    if (element.innerText === "Send") {
                        // #region agent log
                        fetch('http://127.0.0.1:7242/ingest/f44cea64-0bc3-42f2-97f3-ae109d0be063',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'chat_connector.js:87',message:'Clicking Send button',data:{},timestamp:Date.now(),sessionId:'debug-session',runId:'run2',hypothesisId:'F'})}).catch(()=>{});
                        // #endregion
                        element.click();
                    }
                }
            );
        }
        webSocket.onclose = function(event) {
            // #region agent log
            fetch('http://127.0.0.1:7242/ingest/f44cea64-0bc3-42f2-97f3-ae109d0be063',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'chat_connector.js:106',message:'WebSocket closed',data:{code:event.code,reason:event.reason,wasClean:event.wasClean,url:wsUrl},timestamp:Date.now(),sessionId:'debug-session',runId:'run3',hypothesisId:'G'})}).catch(()=>{});
            // #endregion
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
                // #region agent log
                fetch('http://127.0.0.1:7242/ingest/f44cea64-0bc3-42f2-97f3-ae109d0be063',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'chat_connector.js:104',message:'MutationObserver triggered',data:{addedNodes:mutation.addedNodes.length,removedNodes:mutation.removedNodes.length},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'B'})}).catch(()=>{});
                // #endregion
                mutation.addedNodes.forEach(function(node) {
                    // Only process if it's an element node with chat content
                    if (node.nodeType === 1 && (node.classList.contains('message') || node.querySelector('.message'))) {
                        // #region agent log
                        var nodeInfo = {nodeType:node.nodeType,className:node.className||'no-class',hasMessageClass:node.classList.contains('message'),hasQuerySelector:!!node.querySelector('.message')};
                        fetch('http://127.0.0.1:7242/ingest/f44cea64-0bc3-42f2-97f3-ae109d0be063',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'chat_connector.js:109',message:'Processing message node',data:nodeInfo,timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'B'})}).catch(()=>{});
                        // #endregion
                        var messageInfo = extractMessageInfo(node);
                        console.log("Sending message:", messageInfo);
                        // #region agent log
                        var wsState = webSocket.readyState;
                        var wsStates = {0:'CONNECTING',1:'OPEN',2:'CLOSING',3:'CLOSED'};
                        fetch('http://127.0.0.1:7242/ingest/f44cea64-0bc3-42f2-97f3-ae109d0be063',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'chat_connector.js:155',message:'About to send message',data:{readyState:wsState,readyStateName:wsStates[wsState],messageLength:messageInfo.message.length,sender:messageInfo.sender},timestamp:Date.now(),sessionId:'debug-session',runId:'run3',hypothesisId:'G'})}).catch(()=>{});
                        // #endregion
                        if (webSocket.readyState === WebSocket.OPEN) {
                            var messageJson = JSON.stringify({
                                type: "chat",
                                data: node.outerHTML,
                                sender: messageInfo.sender,
                                message: messageInfo.message
                            });
                            // #region agent log
                            fetch('http://127.0.0.1:7242/ingest/f44cea64-0bc3-42f2-97f3-ae109d0be063',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'chat_connector.js:165',message:'Sending WebSocket message',data:{jsonLength:messageJson.length,hasType:messageJson.includes('"type"'),hasData:messageJson.includes('"data"')},timestamp:Date.now(),sessionId:'debug-session',runId:'run3',hypothesisId:'G'})}).catch(()=>{});
                            // #endregion
                            try {
                                webSocket.send(messageJson);
                                // #region agent log
                                fetch('http://127.0.0.1:7242/ingest/f44cea64-0bc3-42f2-97f3-ae109d0be063',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'chat_connector.js:171',message:'WebSocket send() called successfully',data:{},timestamp:Date.now(),sessionId:'debug-session',runId:'run3',hypothesisId:'G'})}).catch(()=>{});
                                // #endregion
                            } catch (e) {
                                // #region agent log
                                fetch('http://127.0.0.1:7242/ingest/f44cea64-0bc3-42f2-97f3-ae109d0be063',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'chat_connector.js:175',message:'WebSocket send() error',data:{error:String(e),errorType:typeof e},timestamp:Date.now(),sessionId:'debug-session',runId:'run3',hypothesisId:'G'})}).catch(()=>{});
                                // #endregion
                                console.error("Error sending message:", e);
                            }
                        } else {
                            // #region agent log
                            fetch('http://127.0.0.1:7242/ingest/f44cea64-0bc3-42f2-97f3-ae109d0be063',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'chat_connector.js:180',message:'WebSocket not open, skipping send',data:{readyState:wsState,readyStateName:wsStates[wsState]},timestamp:Date.now(),sessionId:'debug-session',runId:'run3',hypothesisId:'G'})}).catch(()=>{});
                            // #endregion
                            console.warn("WebSocket not open, readyState:", wsState);
                        }
                    }
                });
            }
        });
    });

    observer.observe(targetNode, {
        childList: true, subtree: true
    });
})();