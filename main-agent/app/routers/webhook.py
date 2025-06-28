import logging
from typing import Dict, Any
from fastapi import APIRouter, Request, HTTPException, Header
from fastapi.responses import JSONResponse

from app.config import settings
from app.utils.github import verify_webhook_signature

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/github")
async def handle_github_webhook(
    request: Request,
    x_github_event: str = Header(None, alias="X-GitHub-Event"),
    x_github_delivery: str = Header(None, alias="X-GitHub-Delivery"),
    x_hub_signature_256: str = Header(None, alias="X-Hub-Signature-256")
) -> JSONResponse:
    """
    Handle incoming GitHub webhook events.
    
    Args:
        request: FastAPI request object
        x_github_event: GitHub event type header
        x_github_delivery: Unique delivery ID from GitHub
        x_hub_signature_256: HMAC signature for payload verification
    
    Returns:
        JSONResponse with status and message
    """
    try:
        # Get raw payload
        payload_bytes = await request.body()
        
        # Verify webhook signature
        if not verify_webhook_signature(
            payload_bytes, 
            x_hub_signature_256, 
            settings.github_webhook_secret
        ):
            logger.warning(f"Invalid webhook signature for delivery: {x_github_delivery}")
            raise HTTPException(status_code=401, detail="Invalid signature")
        
        # Parse JSON payload
        payload = await request.json()
        
        # Log the event
        logger.info(f"Received GitHub webhook event: {x_github_event}, delivery: {x_github_delivery}")
        logger.debug(f"Payload: {payload}")
        
        # Check if it's an issue event
        if x_github_event != "issues":
            logger.info(f"Ignoring non-issue event: {x_github_event}")
            return JSONResponse(
                status_code=200,
                content={
                    "status": "ignored",
                    "message": f"Event type '{x_github_event}' is not processed"
                }
            )
        
        # Extract repository information
        repository = payload.get("repository", {})
        repo_full_name = repository.get("full_name", "")
        
        # Check repository whitelist
        if settings.repository_whitelist and repo_full_name not in settings.repository_whitelist:
            logger.info(f"Repository '{repo_full_name}' not in whitelist, ignoring event")
            return JSONResponse(
                status_code=200,
                content={
                    "status": "ignored",
                    "message": f"Repository '{repo_full_name}' not in whitelist"
                }
            )
        
        # Extract issue information
        action = payload.get("action", "")
        issue = payload.get("issue", {})
        issue_id = issue.get("id")
        issue_number = issue.get("number")
        issue_title = issue.get("title", "")
        issue_labels = [label.get("name", "") for label in issue.get("labels", [])]
        
        logger.info(
            f"Processing issue event - Action: {action}, "
            f"Repository: {repo_full_name}, "
            f"Issue: #{issue_number} ({issue_id}), "
            f"Title: '{issue_title}', "
            f"Labels: {issue_labels}"
        )
        
        # TODO: In Stage 2, this is where we'll implement tag matching and command execution
        
        return JSONResponse(
            status_code=200,
            content={
                "status": "accepted",
                "message": "Webhook processed successfully",
                "delivery_id": x_github_delivery,
                "event": x_github_event,
                "action": action,
                "repository": repo_full_name,
                "issue_number": issue_number
            }
        )
        
    except ValueError as e:
        logger.error(f"Failed to parse webhook payload: {e}")
        raise HTTPException(status_code=400, detail="Invalid JSON payload")
    
    except Exception as e:
        logger.error(f"Error processing webhook: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")