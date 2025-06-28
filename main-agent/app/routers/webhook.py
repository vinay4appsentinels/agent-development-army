import logging
from typing import Dict, Any
from fastapi import APIRouter, Request, HTTPException, Header
from fastapi.responses import JSONResponse

from app.config import settings
from app.utils.github import verify_webhook_signature
from app.utils.parser import parse_github_event

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
        
        # Check if it's a supported event type
        supported_events = ["issues", "issue_comment", "pull_request"]
        if x_github_event not in supported_events:
            logger.info(f"Ignoring unsupported event: {x_github_event}")
            return JSONResponse(
                status_code=200,
                content={
                    "status": "ignored",
                    "message": f"Event type '{x_github_event}' is not supported"
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
        
        # Parse the GitHub event
        parsed_event = parse_github_event(x_github_event, payload)
        if not parsed_event:
            logger.error(f"Failed to parse {x_github_event} event")
            return JSONResponse(
                status_code=400,
                content={
                    "status": "error",
                    "message": f"Failed to parse {x_github_event} event"
                }
            )
        
        # Log parsed event details
        action = parsed_event.get("action", "")
        mentions = parsed_event.get("mentions", [])
        attention = parsed_event.get("attention", {})
        
        logger.info(
            f"Processing {x_github_event} event - Action: {action}, "
            f"Repository: {repo_full_name}, "
            f"Mentions: {mentions}, "
            f"Attention Required: {attention.get('requires_attention', False)}, "
            f"Priority: {attention.get('priority', 'normal')}"
        )
        
        # Log attention details if mentions are found
        if mentions:
            logger.info(f"🔔 Attention required for users: @{', @'.join(mentions)}")
            logger.info(f"📋 Attention reasons: {', '.join(attention.get('attention_reason', []))}")
        
        # Log event-specific details
        if x_github_event == "issues":
            issue_info = parsed_event.get("issue", {})
            logger.info(
                f"Issue: #{issue_info.get('number')} - '{issue_info.get('title')}' "
                f"by @{issue_info.get('author')} [{issue_info.get('state')}]"
            )
            if issue_info.get("labels"):
                logger.info(f"Labels: {', '.join(issue_info.get('labels', []))}")
                
        elif x_github_event == "issue_comment":
            issue_info = parsed_event.get("issue", {})
            comment_info = parsed_event.get("comment", {})
            logger.info(
                f"Comment on Issue #{issue_info.get('number')} by @{comment_info.get('author')}"
            )
            logger.info(f"Comment preview: {comment_info.get('body', '')[:100]}...")
            
        elif x_github_event == "pull_request":
            pr_info = parsed_event.get("pull_request", {})
            logger.info(
                f"PR: #{pr_info.get('number')} - '{pr_info.get('title')}' "
                f"by @{pr_info.get('author')} [{pr_info.get('state')}] "
                f"({pr_info.get('head_branch')} → {pr_info.get('base_branch')})"
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
                "mentions": mentions,
                "attention_required": attention.get("requires_attention", False),
                "priority": attention.get("priority", "normal"),
                "parsed_data": parsed_event
            }
        )
        
    except ValueError as e:
        logger.error(f"Failed to parse webhook payload: {e}")
        raise HTTPException(status_code=400, detail="Invalid JSON payload")
    
    except Exception as e:
        logger.error(f"Error processing webhook: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")