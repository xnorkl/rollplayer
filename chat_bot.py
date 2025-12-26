#!/usr/bin/env python3
from __future__ import annotations

import json
import logging
import sys
import time
from dataclasses import dataclass
from enum import Enum
from typing import Optional, Callable, Dict, Any

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import JSONResponse
from bs4 import BeautifulSoup
import uvicorn

from config import WS_ADDRESS, WS_PORT, LOG_LEVEL
from gm_handler import GMHandler

# #region agent log
DEBUG_LOG_PATH = "/var/log/roll20_chatbot_debug.log"
# #endregion

LOG = logging.getLogger(__name__)

app = FastAPI()


@dataclass(frozen=True)
class Package:
    class Type(Enum):
        chat = "chat"

    type: Type
    data: str | dict  # Can be string (old format) or dict (new Roll20 API format)

    @classmethod
    def from_json(cls, json_data: str) -> Package:
        dct = json.loads(json_data)
        data = dct.get("data", "")
        # If data is a dict (new Roll20 API format), keep it as dict
        # If data is a string (old format), keep it as string
        return cls(type=Package.Type(dct["type"]), data=data)

    def to_chat_entry(self) -> ChatEntry:
        return ChatEntry.from_package(self)


@dataclass(frozen=True)
class ChatEntry:
    id: str
    message: str
    who: Optional[str] = None
    playerid: Optional[str] = None
    characterId: Optional[str] = None
    message_type: Optional[str] = None  # "command", "question", "rollresult"
    roll_data: Optional[dict] = None  # For rollresult messages

    @classmethod
    def from_package(cls, package: Package) -> ChatEntry:
        # Check if data is a dict (new Roll20 API format)
        if isinstance(package.data, dict):
            return cls.from_roll20_api(package.data)
        else:
            # Old format: HTML string
            return cls.from_html_str(package.data)

    @classmethod
    def from_roll20_api(cls, data: dict) -> ChatEntry:
        """Create ChatEntry from Roll20 API message format."""
        return cls(
            id=data.get("messageId", ""),
            message=data.get("message", ""),
            who=data.get("who"),
            playerid=data.get("playerid"),
            characterId=data.get("characterId"),
            message_type=data.get("type"),
            roll_data=data.get("rollData"),
        )

    @classmethod
    def from_html_str(cls, html: str) -> ChatEntry:
        """Create ChatEntry from old HTML format (backward compatibility)."""
        soup = BeautifulSoup(html, "html.parser")
        div = soup.find("div")
        if not div:
            return cls(id="", message="")

        attrs = div.attrs
        message_id = attrs.get("data-messageid", "")

        # Remove metadata elements (timestamp, sender, avatar, etc.)
        for element in div.find_all(
            ["span", "div"],
            class_=lambda x: x
            and any(
                c in str(x) for c in ["tstamp", "by", "avatar", "spacer", "flyout"]
            ),
        ):
            element.decompose()

        # Get the remaining text content (the actual message)
        message = div.get_text(strip=True, separator=" ")

        return cls(id=message_id, message=message)


@dataclass
class BotResponse:
    """Structured response from the bot."""

    type: str  # "text", "rollresult", "command"
    content: str  # Plain text or JSON string
    metadata: Optional[Dict[str, Any]] = None

    def to_json(self) -> str:
        """Convert to JSON string for WebSocket transmission."""
        return json.dumps(
            {"type": self.type, "content": self.content, **(self.metadata or {})}
        )


class ChatBot:
    def __init__(
        self,
        msg_handler_func: Callable[[Package], Optional[str | BotResponse]],
    ):
        self._msg_handler_func = msg_handler_func
        self._handled_messages = set()

    async def handle_websocket(self, websocket: WebSocket):
        """Handle WebSocket connections."""
        # #region agent log
        try:
            log_data = {
                "sessionId": "debug-session",
                "runId": "post-fix",
                "location": "chat_bot.py:78",
                "message": "WebSocket handle() called",
                "data": {
                    "path": websocket.url.path,
                    "remote": str(websocket.client) if websocket.client else None,
                },
                "timestamp": int(time.time() * 1000),
                "hypothesisId": "FIX",
            }
            LOG.info(f"[DEBUG] {json.dumps(log_data)}")
        except:
            pass
        # #endregion
        await websocket.accept()
        try:
            LOG.debug(f"Opened a new WebSocket connection")
            while True:
                try:
                    msg = await websocket.receive_text()
                    # #region agent log
                    try:
                        import json as json_module

                        log_data = {
                            "sessionId": "debug-session",
                            "runId": "run3",
                            "location": "chat_bot.py:95",
                            "message": "WebSocket message received",
                            "data": {
                                "msgLength": len(msg),
                                "msgPreview": msg[:100] if len(msg) > 100 else msg,
                                "isJson": True,
                            },
                            "timestamp": int(time.time() * 1000),
                            "hypothesisId": "G",
                        }
                        try:
                            parsed = json_module.loads(msg)
                            log_data["data"]["hasType"] = "type" in parsed
                            log_data["data"]["type"] = parsed.get("type", "none")
                        except:
                            log_data["data"]["isJson"] = False
                        LOG.info(f"[DEBUG] {json.dumps(log_data)}")
                    except:
                        pass
                    # #endregion
                    hashed_msg = hash(msg)
                    # #region agent log
                    try:
                        log_data = {
                            "sessionId": "debug-session",
                            "runId": "run3",
                            "location": "chat_bot.py:97",
                            "message": "Message hash check",
                            "data": {
                                "hash": hashed_msg,
                                "isDuplicate": hashed_msg in self._handled_messages,
                                "handledCount": len(self._handled_messages),
                            },
                            "timestamp": int(time.time() * 1000),
                            "hypothesisId": "G",
                        }
                        LOG.info(f"[DEBUG] {json.dumps(log_data)}")
                    except:
                        pass
                    # #endregion
                    if hashed_msg not in self._handled_messages:
                        self._handled_messages.add(hashed_msg)
                        # #region agent log
                        try:
                            log_data = {
                                "sessionId": "debug-session",
                                "runId": "run3",
                                "location": "chat_bot.py:99",
                                "message": "Parsing package",
                                "data": {},
                                "timestamp": int(time.time() * 1000),
                                "hypothesisId": "G",
                            }
                            LOG.info(f"[DEBUG] {json.dumps(log_data)}")
                        except:
                            pass
                        # #endregion
                        try:
                            p = Package.from_json(msg)
                        except Exception as parse_error:
                            # #region agent log
                            try:
                                log_data = {
                                    "sessionId": "debug-session",
                                    "runId": "run3",
                                    "location": "chat_bot.py:99",
                                    "message": "Package parsing error",
                                    "data": {
                                        "error": str(parse_error),
                                        "errorType": type(parse_error).__name__,
                                    },
                                    "timestamp": int(time.time() * 1000),
                                    "hypothesisId": "G",
                                }
                                LOG.error(f"[DEBUG] {json.dumps(log_data)}")
                            except:
                                pass
                            # #endregion
                            raise
                        # #region agent log
                        try:
                            log_data = {
                                "sessionId": "debug-session",
                                "runId": "run3",
                                "location": "chat_bot.py:100",
                                "message": "Package parsed successfully",
                                "data": {
                                    "type": (
                                        p.type.value
                                        if hasattr(p.type, "value")
                                        else str(p.type)
                                    ),
                                    "dataLength": len(p.data),
                                },
                                "timestamp": int(time.time() * 1000),
                                "hypothesisId": "G",
                            }
                            LOG.info(f"[DEBUG] {json.dumps(log_data)}")
                        except:
                            pass
                        # #endregion
                        LOG.debug(f"Received the following new message: {p}")
                        try:
                            if answer := self._msg_handler_func(p):
                                # #region agent log
                                try:
                                    answer_length = (
                                        len(answer)
                                        if isinstance(answer, str)
                                        else len(str(answer))
                                    )
                                    log_data = {
                                        "sessionId": "debug-session",
                                        "runId": "run3",
                                        "location": "chat_bot.py:102",
                                        "message": "Handler returned answer",
                                        "data": {
                                            "answerLength": answer_length,
                                            "answerType": type(answer).__name__,
                                        },
                                        "timestamp": int(time.time() * 1000),
                                        "hypothesisId": "G",
                                    }
                                    LOG.info(f"[DEBUG] {json.dumps(log_data)}")
                                except:
                                    pass
                                # #endregion
                                LOG.debug(f"Sending the following answer: {answer}")

                                # Handle both string (old format) and BotResponse (new format)
                                if isinstance(answer, BotResponse):
                                    await websocket.send_text(answer.to_json())
                                else:
                                    # Backward compatibility: plain text
                                    await websocket.send_text(answer)
                            else:
                                # #region agent log
                                try:
                                    log_data = {
                                        "sessionId": "debug-session",
                                        "runId": "run3",
                                        "location": "chat_bot.py:106",
                                        "message": "Handler returned no answer",
                                        "data": {},
                                        "timestamp": int(time.time() * 1000),
                                        "hypothesisId": "G",
                                    }
                                    LOG.info(f"[DEBUG] {json.dumps(log_data)}")
                                except:
                                    pass
                                # #endregion
                                LOG.debug("Sending no answer")
                        except Exception as e:
                            # #region agent log
                            try:
                                log_data = {
                                    "sessionId": "debug-session",
                                    "runId": "run3",
                                    "location": "chat_bot.py:107",
                                    "message": "Handler exception",
                                    "data": {
                                        "error": str(e),
                                        "errorType": type(e).__name__,
                                    },
                                    "timestamp": int(time.time() * 1000),
                                    "hypothesisId": "G",
                                }
                                LOG.error(f"[DEBUG] {json.dumps(log_data)}")
                            except:
                                pass
                            # #endregion
                            LOG.warning(
                                f"While handling the message the following exception occurred: {e}"
                            )
                    else:
                        # #region agent log
                        try:
                            log_data = {
                                "sessionId": "debug-session",
                                "runId": "run3",
                                "location": "chat_bot.py:112",
                                "message": "Duplicate message detected",
                                "data": {"hash": hashed_msg},
                                "timestamp": int(time.time() * 1000),
                                "hypothesisId": "G",
                            }
                            LOG.info(f"[DEBUG] {json.dumps(log_data)}")
                        except:
                            pass
                        # #endregion
                        LOG.debug(f"Already received the following message: '{msg}'")
                except WebSocketDisconnect:
                    LOG.debug("WebSocket connection closed")
                    break
                except Exception as e:
                    LOG.error(f"Unexpected error in handle loop: {e}")
                    break
        except Exception as e:
            # #region agent log
            try:
                log_data = {
                    "sessionId": "debug-session",
                    "runId": "post-fix",
                    "location": "chat_bot.py:120",
                    "message": "Exception in handle()",
                    "data": {"error": str(e), "type": type(e).__name__},
                    "timestamp": int(time.time() * 1000),
                    "hypothesisId": "FIX",
                }
                LOG.error(f"[DEBUG] {json.dumps(log_data)}")
            except:
                pass
            # #endregion
            LOG.error(f"Error in handle(): {e}")
            raise


# Global ChatBot instance
_chatbot: Optional[ChatBot] = None


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    # #region agent log
    try:
        log_data = {
            "sessionId": "debug-session",
            "runId": "post-fix",
            "location": "chat_bot.py:145",
            "message": "Health check endpoint called",
            "data": {},
            "timestamp": int(time.time() * 1000),
            "hypothesisId": "FIX",
        }
        LOG.info(f"[DEBUG] {json.dumps(log_data)}")
    except:
        pass
    # #endregion
    return JSONResponse(
        content={"status": "healthy", "service": "websocket"},
        status_code=200,
    )


@app.get("/")
async def root():
    """Root endpoint - health check."""
    return await health_check()


@app.websocket("/")
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for chat messages."""
    if _chatbot is None:
        raise HTTPException(status_code=500, detail="ChatBot not initialized")
    await _chatbot.handle_websocket(websocket)


def run_forever(
    msg_handler_func: Callable[[Package], Optional[str]],
    address: str = "0.0.0.0",
    port: int = 5678,
):
    """Run the FastAPI server forever."""
    global _chatbot
    _chatbot = ChatBot(msg_handler_func)

    LOG.info(f"Starting FastAPI server at: '{address}:{port}'")
    LOG.info("Server will handle both WebSocket and HTTP requests")

    # #region agent log
    try:
        log_data = {
            "sessionId": "debug-session",
            "runId": "post-fix",
            "location": "chat_bot.py:180",
            "message": "Starting FastAPI server",
            "data": {"address": address, "port": port},
            "timestamp": int(time.time() * 1000),
            "hypothesisId": "FIX",
        }
        LOG.info(f"[DEBUG] {json.dumps(log_data)}")
    except:
        pass
    # #endregion

    uvicorn.run(app, host=address, port=port, log_level=LOG_LEVEL.lower())


if __name__ == "__main__":
    # Initialize GM handler
    gm_handler = GMHandler()

    def gm_message_handler(p: Package) -> Optional[str]:
        """Handle messages using the GM handler"""
        if p.type == Package.Type.chat:
            chat_msg = p.to_chat_entry()
            # #region agent log
            try:
                log_data = {
                    "sessionId": "debug-session",
                    "runId": "run3",
                    "location": "chat_bot.py:220",
                    "message": "Extracted chat message",
                    "data": {
                        "messageId": chat_msg.id,
                        "messageText": chat_msg.message,
                        "messageLength": len(chat_msg.message),
                        "messagePreview": (
                            chat_msg.message[:100]
                            if len(chat_msg.message) > 100
                            else chat_msg.message
                        ),
                    },
                    "timestamp": int(time.time() * 1000),
                    "hypothesisId": "H",
                }
                LOG.info(f"[DEBUG] {json.dumps(log_data)}")
            except:
                pass
            # #endregion
            LOG.debug(f"Received chat message: {chat_msg.message}")
            # #region agent log
            try:
                log_data = {
                    "sessionId": "debug-session",
                    "runId": "run3",
                    "location": "chat_bot.py:235",
                    "message": "Calling handler",
                    "data": {
                        "startsWithExclamation": chat_msg.message.strip().startswith(
                            "!"
                        ),
                        "isQuestion": (
                            gm_handler.ai_handler.is_question(chat_msg.message)
                            if hasattr(gm_handler, "ai_handler")
                            else None
                        ),
                    },
                    "timestamp": int(time.time() * 1000),
                    "hypothesisId": "H",
                }
                LOG.info(f"[DEBUG] {json.dumps(log_data)}")
            except Exception as e:
                try:
                    log_data = {
                        "sessionId": "debug-session",
                        "runId": "run3",
                        "location": "chat_bot.py:235",
                        "message": "Error checking handler conditions",
                        "data": {"error": str(e)},
                        "timestamp": int(time.time() * 1000),
                        "hypothesisId": "H",
                    }
                    LOG.error(f"[DEBUG] {json.dumps(log_data)}")
                except:
                    pass
            # #endregion
            # Pass full ChatEntry for context (characterId, playerid, etc.)
            response = gm_handler.handle_message(chat_msg)
            # #region agent log
            try:
                log_data = {
                    "sessionId": "debug-session",
                    "runId": "run3",
                    "location": "chat_bot.py:252",
                    "message": "Handler response",
                    "data": {
                        "hasResponse": response is not None,
                        "responseLength": len(response) if response else 0,
                        "responsePreview": (
                            response[:100]
                            if response and len(response) > 100
                            else response
                        ),
                    },
                    "timestamp": int(time.time() * 1000),
                    "hypothesisId": "H",
                }
                LOG.info(f"[DEBUG] {json.dumps(log_data)}")
            except:
                pass
            # #endregion
            if response:
                LOG.debug(f"GM handler response: {response}")
            return response
        return None

    # Configure logging
    log_level = getattr(logging, LOG_LEVEL.upper(), logging.INFO)
    logging.basicConfig(
        stream=sys.stdout,
        format="[%(asctime)s] [%(filename)s:%(lineno)d] %(levelname)s - %(message)s",
        level=log_level,
    )
    LOG.setLevel(log_level)

    # Start the bot
    LOG.info("Starting GM Chatbot for Shadowdark RPG...")
    LOG.info(f"Configuration: WS_ADDRESS={WS_ADDRESS}, WS_PORT={WS_PORT}")

    if WS_ADDRESS != "0.0.0.0":
        LOG.warning(
            f"WS_ADDRESS is '{WS_ADDRESS}' but should be '0.0.0.0' for Fly.io deployment!"
        )

    run_forever(gm_message_handler, address=WS_ADDRESS, port=WS_PORT)
