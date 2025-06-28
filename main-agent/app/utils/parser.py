import re
import logging
from typing import Dict, List, Optional, Any, Set

logger = logging.getLogger(__name__)


def extract_mentions(text: str) -> List[str]:
    """
    Extract @mentions from text.
    
    Args:
        text: Text content to parse
    
    Returns:
        List of mentioned usernames (without @)
    """
    if not text:
        return []
    
    # Pattern to match @username mentions
    mention_pattern = r'@([a-zA-Z0-9][a-zA-Z0-9-]*[a-zA-Z0-9]|[a-zA-Z0-9])'
    matches = re.findall(mention_pattern, text)
    
    # Remove duplicates while preserving order
    seen = set()
    unique_mentions = []
    for mention in matches:
        if mention.lower() not in seen:
            seen.add(mention.lower())
            unique_mentions.append(mention)
    
    return unique_mentions


def extract_hashtags(text: str) -> List[str]:
    """
    Extract #hashtags from text.
    
    Args:
        text: Text content to parse
    
    Returns:
        List of hashtags (without #)
    """
    if not text:
        return []
    
    # Pattern to match #hashtag
    hashtag_pattern = r'#([a-zA-Z0-9_-]+)'
    matches = re.findall(hashtag_pattern, text)
    
    # Remove duplicates while preserving order
    seen = set()
    unique_hashtags = []
    for hashtag in matches:
        if hashtag.lower() not in seen:
            seen.add(hashtag.lower())
            unique_hashtags.append(hashtag)
    
    return unique_hashtags


def parse_issue_event(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Parse GitHub issue event payload.
    
    Args:
        payload: GitHub webhook payload
    
    Returns:
        Parsed issue event data
    """
    action = payload.get("action", "")
    issue = payload.get("issue", {})
    repository = payload.get("repository", {})
    sender = payload.get("sender", {})
    
    # Extract issue content
    issue_body = issue.get("body", "")
    issue_title = issue.get("title", "")
    
    # Extract mentions from title and body
    title_mentions = extract_mentions(issue_title)
    body_mentions = extract_mentions(issue_body)
    all_mentions = list(set(title_mentions + body_mentions))
    
    # Extract hashtags
    title_hashtags = extract_hashtags(issue_title)
    body_hashtags = extract_hashtags(issue_body)
    all_hashtags = list(set(title_hashtags + body_hashtags))
    
    return {
        "event_type": "issues",
        "action": action,
        "repository": {
            "name": repository.get("name", ""),
            "full_name": repository.get("full_name", ""),
            "owner": repository.get("owner", {}).get("login", "")
        },
        "issue": {
            "id": issue.get("id"),
            "number": issue.get("number"),
            "title": issue_title,
            "body": issue_body,
            "state": issue.get("state", ""),
            "labels": [label.get("name", "") for label in issue.get("labels", [])],
            "assignees": [assignee.get("login", "") for assignee in issue.get("assignees", [])],
            "author": issue.get("user", {}).get("login", ""),
            "created_at": issue.get("created_at", ""),
            "updated_at": issue.get("updated_at", ""),
            "html_url": issue.get("html_url", "")
        },
        "mentions": all_mentions,
        "hashtags": all_hashtags,
        "sender": {
            "login": sender.get("login", ""),
            "type": sender.get("type", "")
        }
    }


def parse_issue_comment_event(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Parse GitHub issue comment event payload.
    
    Args:
        payload: GitHub webhook payload
    
    Returns:
        Parsed issue comment event data
    """
    action = payload.get("action", "")
    issue = payload.get("issue", {})
    comment = payload.get("comment", {})
    repository = payload.get("repository", {})
    sender = payload.get("sender", {})
    
    # Extract comment content
    comment_body = comment.get("body", "")
    
    # Extract mentions from comment
    comment_mentions = extract_mentions(comment_body)
    
    # Extract hashtags from comment
    comment_hashtags = extract_hashtags(comment_body)
    
    return {
        "event_type": "issue_comment",
        "action": action,
        "repository": {
            "name": repository.get("name", ""),
            "full_name": repository.get("full_name", ""),
            "owner": repository.get("owner", {}).get("login", "")
        },
        "issue": {
            "id": issue.get("id"),
            "number": issue.get("number"),
            "title": issue.get("title", ""),
            "state": issue.get("state", ""),
            "labels": [label.get("name", "") for label in issue.get("labels", [])],
            "author": issue.get("user", {}).get("login", ""),
            "html_url": issue.get("html_url", "")
        },
        "comment": {
            "id": comment.get("id"),
            "body": comment_body,
            "author": comment.get("user", {}).get("login", ""),
            "created_at": comment.get("created_at", ""),
            "updated_at": comment.get("updated_at", ""),
            "html_url": comment.get("html_url", "")
        },
        "mentions": comment_mentions,
        "hashtags": comment_hashtags,
        "sender": {
            "login": sender.get("login", ""),
            "type": sender.get("type", "")
        }
    }


def parse_pull_request_event(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Parse GitHub pull request event payload.
    
    Args:
        payload: GitHub webhook payload
    
    Returns:
        Parsed pull request event data
    """
    action = payload.get("action", "")
    pull_request = payload.get("pull_request", {})
    repository = payload.get("repository", {})
    sender = payload.get("sender", {})
    
    # Extract PR content
    pr_body = pull_request.get("body", "")
    pr_title = pull_request.get("title", "")
    
    # Extract mentions from title and body
    title_mentions = extract_mentions(pr_title)
    body_mentions = extract_mentions(pr_body)
    all_mentions = list(set(title_mentions + body_mentions))
    
    # Extract hashtags
    title_hashtags = extract_hashtags(pr_title)
    body_hashtags = extract_hashtags(pr_body)
    all_hashtags = list(set(title_hashtags + body_hashtags))
    
    return {
        "event_type": "pull_request",
        "action": action,
        "repository": {
            "name": repository.get("name", ""),
            "full_name": repository.get("full_name", ""),
            "owner": repository.get("owner", {}).get("login", "")
        },
        "pull_request": {
            "id": pull_request.get("id"),
            "number": pull_request.get("number"),
            "title": pr_title,
            "body": pr_body,
            "state": pull_request.get("state", ""),
            "author": pull_request.get("user", {}).get("login", ""),
            "created_at": pull_request.get("created_at", ""),
            "updated_at": pull_request.get("updated_at", ""),
            "html_url": pull_request.get("html_url", ""),
            "head_branch": pull_request.get("head", {}).get("ref", ""),
            "base_branch": pull_request.get("base", {}).get("ref", "")
        },
        "mentions": all_mentions,
        "hashtags": all_hashtags,
        "sender": {
            "login": sender.get("login", ""),
            "type": sender.get("type", "")
        }
    }


def determine_attention_required(parsed_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Determine whose attention is required based on mentions and event context.
    
    Args:
        parsed_data: Parsed event data
    
    Returns:
        Dictionary with attention analysis
    """
    mentions = parsed_data.get("mentions", [])
    event_type = parsed_data.get("event_type", "")
    action = parsed_data.get("action", "")
    sender_login = parsed_data.get("sender", {}).get("login", "")
    
    attention_required = {
        "direct_mentions": mentions,
        "requires_attention": len(mentions) > 0,
        "attention_reason": [],
        "priority": "normal"
    }
    
    # Determine attention reasons
    if mentions:
        attention_required["attention_reason"].append(f"Direct mentions: @{', @'.join(mentions)}")
    
    # High priority scenarios
    if event_type == "issue_comment" and mentions:
        attention_required["priority"] = "high"
        attention_required["attention_reason"].append("Comment with mentions requires immediate attention")
    
    if event_type == "issues" and action == "opened" and mentions:
        attention_required["priority"] = "high"
        attention_required["attention_reason"].append("New issue with mentions")
    
    # Add context-based attention
    if event_type == "issues":
        issue_labels = parsed_data.get("issue", {}).get("labels", [])
        urgent_labels = ["urgent", "critical", "bug", "security", "high-priority"]
        if any(label.lower() in urgent_labels for label in issue_labels):
            attention_required["requires_attention"] = True
            attention_required["priority"] = "high"
            attention_required["attention_reason"].append(f"Issue has urgent labels: {', '.join(issue_labels)}")
    
    return attention_required


def parse_github_event(event_type: str, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Parse GitHub webhook event based on event type.
    
    Args:
        event_type: GitHub event type (e.g., 'issues', 'issue_comment', 'pull_request')
        payload: GitHub webhook payload
    
    Returns:
        Parsed event data with mentions and attention analysis
    """
    try:
        if event_type == "issues":
            parsed_data = parse_issue_event(payload)
        elif event_type == "issue_comment":
            parsed_data = parse_issue_comment_event(payload)
        elif event_type == "pull_request":
            parsed_data = parse_pull_request_event(payload)
        else:
            logger.info(f"Unsupported event type: {event_type}")
            return None
        
        # Add attention analysis
        attention_analysis = determine_attention_required(parsed_data)
        parsed_data["attention"] = attention_analysis
        
        return parsed_data
        
    except Exception as e:
        logger.error(f"Error parsing {event_type} event: {e}", exc_info=True)
        return None