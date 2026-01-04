"""Chat/GM router."""

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, status

from ...api.dependencies import get_campaign_service
from ...api.exceptions import APIError, ErrorCodes
from ...models.chat import APIResponse, ChatMessage
from ...services.campaign_service import CampaignService

router = APIRouter()


@router.post("/campaigns/{campaign_id}/chat", response_model=APIResponse[dict])
async def send_message(
    campaign_id: str,
    message: ChatMessage,
    service: CampaignService = Depends(get_campaign_service),
):
    """Send message to GM chatbot."""
    try:
        # Verify campaign exists
        await service.get_campaign(campaign_id)

        # TODO: Integrate with GM service when implemented
        response_text = f"Echo: {message.message}"

        return APIResponse(
            success=True,
            data={"response": response_text},
        )
    except FileNotFoundError:
        raise APIError(
            ErrorCodes.CAMPAIGN_NOT_FOUND,
            f"Campaign {campaign_id} not found",
            status_code=status.HTTP_404_NOT_FOUND,
        )
    except Exception as e:
        raise APIError(
            ErrorCodes.INTERNAL_ERROR,
            f"Failed to process message: {str(e)}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        ) from e


@router.get("/campaigns/{campaign_id}/chat/history")
async def get_chat_history(
    campaign_id: str,
    service: CampaignService = Depends(get_campaign_service),
):
    """Get chat history for a campaign."""
    try:
        await service.get_campaign(campaign_id)
        # TODO: Implement chat history storage
        return APIResponse(success=True, data={"messages": []})
    except FileNotFoundError:
        raise APIError(
            ErrorCodes.CAMPAIGN_NOT_FOUND,
            f"Campaign {campaign_id} not found",
            status_code=status.HTTP_404_NOT_FOUND,
        )
    except Exception as e:
        raise APIError(
            ErrorCodes.INTERNAL_ERROR,
            f"Failed to get chat history: {str(e)}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        ) from e


@router.websocket("/ws/campaigns/{campaign_id}/chat")
async def websocket_chat(
    websocket: WebSocket,
    campaign_id: str,
    service: CampaignService = Depends(get_campaign_service),
):
    """WebSocket endpoint for real-time chat."""
    await websocket.accept()
    try:
        # Verify campaign exists
        await service.get_campaign(campaign_id)

        while True:
            data = await websocket.receive_text()
            # TODO: Process message with GM service
            response = {"type": "text", "content": f"Echo: {data}"}
            await websocket.send_json(response)
    except WebSocketDisconnect:
        pass
    except Exception as e:
        await websocket.close(code=1011, reason=str(e))
