// Roll20 API Script for Shadowdark RPG GM Chatbot
// This script replaces the Tampermonkey userscript for Roll20 integration
// It uses Roll20's native API for better integration with dice rolls and character sheets

// ============================================================================
// CONFIGURATION
// ============================================================================
// WebSocket server address
// For local development: "ws://localhost:5678"
// For Fly.io deployment: "wss://your-app-name.fly.dev"
const getWebSocketAddress = function() {
    // Try to get from script state (Roll20 API script settings)
    const state = getScriptState();
    if (state && state.wsUrl) {
        return state.wsUrl;
    }
    // Try localStorage (for backward compatibility)
    const stored = localStorage.getItem('roll20_chatbot_ws_url');
    if (stored) {
        return stored;
    }
    // Default: check if we're on HTTPS (use wss) or HTTP (use ws)
    if (window.location.protocol === 'https:') {
        return "wss://roll20-chatbot.fly.dev";
    } else {
        return "ws://localhost:5678";
    }
};

// Bot identifier to prevent feedback loops
const BOT_NAME = "GM Chatbot";
let botPlayerId = null;

// ============================================================================
// WEBSOCKET CONNECTION
// ============================================================================
let webSocket = null;
let reconnectTimeout = null;

function connectToBackend() {
    const wsUrl = getWebSocketAddress();
    logMessage(`Connecting to WebSocket: ${wsUrl}`);
    
    try {
        webSocket = new WebSocket(wsUrl);
        
        webSocket.onopen = function(event) {
            logMessage("WebSocket connected");
            sendChat("", `${BOT_NAME} connected`);
        };
        
        webSocket.onerror = function(event) {
            logMessage("WebSocket error: " + JSON.stringify(event));
        };
        
        webSocket.onmessage = function(event) {
            handleBackendResponse(event.data);
        };
        
        webSocket.onclose = function(event) {
            logMessage(`WebSocket closed: code=${event.code}, reason=${event.reason}`);
            // Reconnect after 5 seconds
            reconnectTimeout = setTimeout(connectToBackend, 5000);
        };
    } catch (e) {
        logMessage("Error creating WebSocket: " + e);
        reconnectTimeout = setTimeout(connectToBackend, 5000);
    }
}

// ============================================================================
// ROLL20 ROLL PARSING
// ============================================================================

/**
 * Parse a Roll20 rollresult message to extract dice data
 * @param {Object} msg - Roll20 chat:message event object
 * @returns {Object|null} Parsed roll data or null if not a roll
 */
function parseRoll20Roll(msg) {
    if (msg.type !== "rollresult" && msg.type !== "gmrollresult") {
        return null;
    }
    
    try {
        const rollData = JSON.parse(msg.content);
        if (!rollData.rolls || !Array.isArray(rollData.rolls) || rollData.rolls.length === 0) {
            return null;
        }
        
        // Extract dice values and modifiers from first roll
        const firstRoll = rollData.rolls[0];
        const dice = firstRoll.dice || [];
        const expr = firstRoll.expr || "";
        const mods = firstRoll.mods || [];
        
        // Calculate total modifier
        let modifier = 0;
        mods.forEach(function(mod) {
            if (mod.type === "add") {
                modifier += mod.value || 0;
            } else if (mod.type === "subtract") {
                modifier -= mod.value || 0;
            }
        });
        
        // Get total from results
        const total = rollData.results ? rollData.results.total : null;
        
        return {
            dice: dice,
            expr: expr,
            modifier: modifier,
            total: total,
            raw: rollData
        };
    } catch (e) {
        logMessage("Error parsing roll: " + e);
        return null;
    }
}

// ============================================================================
// CHARACTER SHEET INTEGRATION
// ============================================================================

/**
 * Get a character attribute value
 * @param {String} characterId - Character ID (e.g., "char:abc123")
 * @param {String} attribute - Attribute name (e.g., "strength", "strength_mod")
 * @returns {Number|null} Attribute value or null if not found
 */
function getCharacterAttribute(characterId, attribute) {
    if (!characterId || !attribute) {
        return null;
    }
    
    try {
        const character = getObj("character", characterId.replace("char:", ""));
        if (!character) {
            return null;
        }
        
        // Try to get attribute
        const attr = findObjs({
            _type: "attribute",
            _characterid: character.id,
            name: attribute
        })[0];
        
        if (attr) {
            const value = parseFloat(attr.get("current"));
            return isNaN(value) ? null : value;
        }
        
        return null;
    } catch (e) {
        logMessage("Error getting character attribute: " + e);
        return null;
    }
}

/**
 * Get ability modifier for a character
 * @param {String} characterId - Character ID
 * @param {String} abilityName - Ability name (e.g., "strength", "dex")
 * @returns {Number} Ability modifier (defaults to 0)
 */
function getAbilityModifier(characterId, abilityName) {
    if (!characterId) {
        return 0;
    }
    
    // Normalize ability name
    const abilityMap = {
        "str": "strength",
        "strength": "strength",
        "dex": "dexterity",
        "dexterity": "dexterity",
        "con": "constitution",
        "constitution": "constitution",
        "int": "intelligence",
        "intelligence": "intelligence",
        "wis": "wisdom",
        "wisdom": "wisdom",
        "cha": "charisma",
        "charisma": "charisma"
    };
    
    const normalized = abilityMap[abilityName.toLowerCase()];
    if (!normalized) {
        return 0;
    }
    
    // Try modifier attribute first
    const modAttr = getCharacterAttribute(characterId, normalized + "_mod");
    if (modAttr !== null) {
        return modAttr;
    }
    
    // Fall back to calculating from ability score
    const abilityScore = getCharacterAttribute(characterId, normalized);
    if (abilityScore !== null) {
        // Shadowdark modifier calculation
        if (abilityScore <= 2) return -5;
        if (abilityScore <= 4) return -4;
        if (abilityScore <= 6) return -3;
        if (abilityScore <= 8) return -2;
        if (abilityScore <= 10) return -1;
        if (abilityScore <= 12) return 0;
        if (abilityScore <= 14) return 1;
        if (abilityScore <= 16) return 2;
        if (abilityScore <= 18) return 3;
        return 4; // 19-20
    }
    
    return 0;
}

/**
 * Get the active character for a player
 * @param {String} playerId - Player ID
 * @returns {String|null} Character ID or null
 */
function getPlayerCharacter(playerId) {
    try {
        const player = getObj("player", playerId);
        if (!player) {
            return null;
        }
        
        // Get controlled characters
        const controlled = findObjs({
            _type: "character",
            controlledby: playerId
        });
        
        if (controlled.length > 0) {
            return "char:" + controlled[0].id;
        }
        
        return null;
    } catch (e) {
        logMessage("Error getting player character: " + e);
        return null;
    }
}

// ============================================================================
// FORMATTED ROLL SENDING
// ============================================================================

/**
 * Send a formatted rollresult to chat
 * @param {String} diceExpr - Dice expression (e.g., "2d6", "1d20")
 * @param {Number} modifier - Modifier to add
 * @param {String} description - Description text
 */
function sendRollResult(diceExpr, modifier, description) {
    // Parse dice expression
    const match = diceExpr.match(/(\d*)d(\d+)/);
    if (!match) {
        sendChat("", description || "Invalid dice expression");
        return;
    }
    
    const numDice = parseInt(match[1]) || 1;
    const dieSize = parseInt(match[2]);
    
    // Build rollresult structure
    const rollresult = {
        type: "rollresult",
        rolls: [{
            dice: [], // Will be filled by Roll20
            expr: diceExpr,
            mods: modifier !== 0 ? [{type: "add", value: modifier}] : []
        }],
        results: {}
    };
    
    // Use Roll20's inline roll syntax to actually roll the dice
    const rollText = modifier !== 0 
        ? `[[${diceExpr}${modifier >= 0 ? '+' : ''}${modifier}]]`
        : `[[${diceExpr}]]`;
    
    const fullText = description ? `${description}: ${rollText}` : rollText;
    
    sendChat("", fullText);
}

// ============================================================================
// BACKEND RESPONSE HANDLING
// ============================================================================

/**
 * Handle response from backend WebSocket
 * @param {String} data - Response data (JSON string)
 */
function handleBackendResponse(data) {
    try {
        const response = JSON.parse(data);
        
        if (response.type === "rollresult") {
            // Handle structured roll response
            const metadata = response.metadata || {};
            const dice = metadata.dice || "1d20";
            const modifier = metadata.modifier || 0;
            const description = metadata.description || "";
            
            // Check if we need to look up character attributes
            if (metadata.character_id && metadata.ability) {
                // Look up ability modifier from character sheet
                const abilityMod = getAbilityModifier(metadata.character_id, metadata.ability);
                const finalModifier = modifier + abilityMod;
                
                sendRollResult(dice, finalModifier, description);
            } else if (metadata.character_id && metadata.initiative) {
                // Initiative roll - look up dex modifier
                const dexMod = getAbilityModifier(metadata.character_id, "dex");
                const finalModifier = modifier + dexMod;
                
                sendRollResult(dice, finalModifier, description);
            } else {
                // Regular roll
                sendRollResult(dice, modifier, description);
            }
        } else if (response.type === "text") {
            // Send plain text message
            sendChat("", response.content || data);
        } else {
            // Fallback: treat as plain text
            sendChat("", data);
        }
    } catch (e) {
        // Not JSON, send as plain text
        sendChat("", data);
    }
}

// ============================================================================
// MESSAGE HANDLING
// ============================================================================

/**
 * Send message to backend via WebSocket
 * @param {Object} msgData - Message data object
 */
function sendToBackend(msgData) {
    if (!webSocket || webSocket.readyState !== WebSocket.OPEN) {
        logMessage("WebSocket not connected, cannot send message");
        return;
    }
    
    try {
        const payload = JSON.stringify({
            type: "chat",
            data: msgData
        });
        webSocket.send(payload);
    } catch (e) {
        logMessage("Error sending to backend: " + e);
    }
}

// ============================================================================
// ROLL20 API EVENT HANDLERS
// ============================================================================

on("ready", function() {
    logMessage("Roll20 API Script loaded");
    
    // Get bot player ID (if script is run by a player)
    const players = findObjs({_type: "player"});
    players.forEach(function(player) {
        if (player.get("displayname") === BOT_NAME || player.get("displayname").includes("Chatbot")) {
            botPlayerId = player.id;
        }
    });
    
    // Connect to backend
    connectToBackend();
});

on("chat:message", function(msg) {
    // Ignore messages from the bot itself
    if (botPlayerId && msg.playerid === botPlayerId) {
        return;
    }
    
    // Filter by message type
    if (msg.type === "api") {
        // Commands starting with ! are type "api" and hidden from users
        // Extract the command from content
        const command = msg.content.trim();
        if (command.startsWith("!")) {
            handleCommand(msg, command);
        }
    } else if (msg.type === "rollresult" || msg.type === "gmrollresult") {
        // Handle dice rolls - parse and potentially use for commands
        handleRollResult(msg);
    } else if (msg.type === "general") {
        // Regular chat messages - check if it's a question
        handleGeneralMessage(msg);
    }
    // Ignore other message types
});

/**
 * Handle command messages (type "api")
 */
function handleCommand(msg, command) {
    const msgData = {
        message: command,
        who: msg.who || "Unknown",
        playerid: msg.playerid || null,
        characterId: getPlayerCharacter(msg.playerid) || null,
        type: "command"
    };
    
    sendToBackend(msgData);
}

/**
 * Handle roll result messages
 */
function handleRollResult(msg) {
    const rollData = parseRoll20Roll(msg);
    if (!rollData) {
        return;
    }
    
    logMessage("Roll detected: " + JSON.stringify(rollData));
    
    // Send roll data to backend for potential use
    // The backend can use this for commands that were waiting for a roll
    const msgData = {
        message: "", // No text message
        who: msg.who || "Unknown",
        playerid: msg.playerid || null,
        characterId: getPlayerCharacter(msg.playerid) || null,
        type: "rollresult",
        rollData: rollData
    };
    
    sendToBackend(msgData);
}

/**
 * Handle general chat messages (questions)
 */
function handleGeneralMessage(msg) {
    const content = msg.content || "";
    const trimmed = content.trim();
    
    // Check if it looks like a question (basic heuristic)
    if (trimmed.endsWith("?") || 
        /^(what|how|when|where|why|who|which|can|could|should|would|will|is|are|does|do|did|was|were|explain|describe|tell|show|help)/i.test(trimmed)) {
        
        const msgData = {
            message: trimmed,
            who: msg.who || "Unknown",
            playerid: msg.playerid || null,
            characterId: getPlayerCharacter(msg.playerid) || null,
            type: "question"
        };
        
        sendToBackend(msgData);
    }
}

// ============================================================================
// UTILITY FUNCTIONS
// ============================================================================

function logMessage(message) {
    log(`[GM Chatbot] ${message}`);
}

