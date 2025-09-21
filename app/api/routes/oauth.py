"""
OAuth Authentication Routes

Handles social login with Google, Facebook, and GitHub.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Any, Optional

from app.core.database import get_db
from app.core.auth import get_current_active_user
from app.services.oauth_service import OAuthService
from app.config.settings import settings


router = APIRouter()


@router.get("/auth/{provider}")
async def oauth_login(
    provider: str,
    redirect_uri: Optional[str] = Query(None)
) -> Any:
    """
    Initiate OAuth login with specified provider.
    
    Args:
        provider: OAuth provider (google, github)
        redirect_uri: Optional custom redirect URI
        
    Returns:
        Authorization URL for the OAuth provider
    """
    if provider not in ['google', 'github']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported OAuth provider. Supported: google, github"
        )
    
    # Use default redirect URI if not provided
    if not redirect_uri:
        redirect_uri = settings.oauth_redirect_uri
    
    oauth_service = OAuthService()
    
    try:
        auth_url = oauth_service.get_authorization_url(provider, redirect_uri)
        return {
            "authorization_url": auth_url,
            "provider": provider,
            "redirect_uri": redirect_uri
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate authorization URL: {str(e)}"
        )


@router.get("/callback/{provider}")
async def oauth_callback(
    provider: str,
    code: str = Query(...),
    redirect_uri: Optional[str] = Query(None),
    db: Session = Depends(get_db)
) -> Any:
    """
    Handle OAuth callback and create/login user.
    
    Args:
        provider: OAuth provider (google, github)
        code: Authorization code from OAuth provider
        redirect_uri: Redirect URI used in authorization
        db: Database session
        
    Returns:
        Access token and user information
    """
    if provider not in ['google', 'github']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported OAuth provider. Supported: google, github"
        )
    
    if not redirect_uri:
        redirect_uri = settings.oauth_redirect_uri
    
    oauth_service = OAuthService()
    
    try:
        # Exchange code for access token
        access_token = await oauth_service.exchange_code_for_token(
            provider, code, redirect_uri
        )
        
        if not access_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to obtain access token"
            )
        
        # Get user info from provider
        if provider == 'google':
            user_info = await oauth_service.get_google_user_info(access_token)
        elif provider == 'github':
            user_info = await oauth_service.get_github_user_info(access_token)
        
        # Create or get user
        result = await oauth_service.create_or_get_oauth_user(
            provider, user_info, db
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"OAuth authentication failed: {str(e)}"
        )


@router.get("/providers")
async def get_available_providers() -> Any:
    """
    Get list of available OAuth providers.
    
    Returns:
        List of configured OAuth providers
    """
    providers = []
    
    if settings.google_client_id and settings.google_client_secret:
        providers.append({
            "name": "google",
            "display_name": "Google",
            "icon": "🔍",
            "color": "#4285f4"
        })
    
    if settings.github_client_id and settings.github_client_secret:
        providers.append({
            "name": "github",
            "display_name": "GitHub",
            "icon": "🐙",
            "color": "#333333"
        })
    
    
    return {
        "providers": providers,
        "total": len(providers)
    }


@router.post("/unlink/{provider}")
async def unlink_oauth_provider(
    provider: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
) -> Any:
    """
    Unlink OAuth provider from user account.
    
    Args:
        provider: OAuth provider to unlink
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Success message
    """
    if provider not in ['google', 'github']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported OAuth provider. Supported: google, github"
        )
    
    if current_user.oauth_provider != provider:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"User is not linked to {provider}"
        )
    
    # Check if user has a password (can't unlink if it's the only auth method)
    if not current_user.hashed_password or current_user.hashed_password == "oauth_user_no_password":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot unlink OAuth provider without setting a password first"
        )
    
    # Unlink the provider
    current_user.oauth_provider = None
    current_user.oauth_id = None
    db.commit()
    
    return {
        "message": f"Successfully unlinked {provider} from your account",
        "provider": provider
    }
