"""
OAuth Service for social login integration.
Supports Google, Facebook, and GitHub authentication.
"""

from typing import Dict, Any, Optional
import httpx
from authlib.integrations.starlette_client import OAuth
from authlib.integrations.base_client import OAuthError
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.config.settings import settings
from app.models.database import User
from app.core.auth import get_password_hash, create_access_token
from datetime import timedelta


class OAuthService:
    """Service for handling OAuth authentication."""
    
    def __init__(self):
        self.oauth = OAuth()
        self._setup_providers()
    
    def _setup_providers(self):
        """Setup OAuth providers."""
        
        # Google OAuth
        if settings.google_client_id and settings.google_client_secret:
            self.oauth.register(
                name='google',
                client_id=settings.google_client_id,
                client_secret=settings.google_client_secret,
                server_metadata_url='https://accounts.google.com/.well-known/openid_configuration',
                client_kwargs={
                    'scope': 'openid email profile'
                }
            )
        
        # GitHub OAuth
        if settings.github_client_id and settings.github_client_secret:
            self.oauth.register(
                name='github',
                client_id=settings.github_client_id,
                client_secret=settings.github_client_secret,
                access_token_url='https://github.com/login/oauth/access_token',
                authorize_url='https://github.com/login/oauth/authorize',
                api_base_url='https://api.github.com/',
                client_kwargs={'scope': 'user:email'},
            )
        
        # Facebook OAuth
        if settings.facebook_client_id and settings.facebook_client_secret:
            self.oauth.register(
                name='facebook',
                client_id=settings.facebook_client_id,
                client_secret=settings.facebook_client_secret,
                access_token_url='https://graph.facebook.com/oauth/access_token',
                authorize_url='https://www.facebook.com/dialog/oauth',
                api_base_url='https://graph.facebook.com/',
                client_kwargs={'scope': 'email'},
            )
    
    async def get_google_user_info(self, access_token: str) -> Dict[str, Any]:
        """Get user info from Google."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                'https://www.googleapis.com/oauth2/v2/userinfo',
                headers={'Authorization': f'Bearer {access_token}'}
            )
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Failed to get user info from Google"
                )
            
            return response.json()
    
    async def get_github_user_info(self, access_token: str) -> Dict[str, Any]:
        """Get user info from GitHub."""
        async with httpx.AsyncClient() as client:
            # Get user profile
            user_response = await client.get(
                'https://api.github.com/user',
                headers={'Authorization': f'token {access_token}'}
            )
            
            if user_response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Failed to get user info from GitHub"
                )
            
            user_data = user_response.json()
            
            # Get user email (might be private)
            email_response = await client.get(
                'https://api.github.com/user/emails',
                headers={'Authorization': f'token {access_token}'}
            )
            
            if email_response.status_code == 200:
                emails = email_response.json()
                # Find primary email
                primary_email = next((email['email'] for email in emails if email['primary']), None)
                if primary_email:
                    user_data['email'] = primary_email
            
            return user_data
    
    async def get_facebook_user_info(self, access_token: str) -> Dict[str, Any]:
        """Get user info from Facebook."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                'https://graph.facebook.com/me',
                params={
                    'fields': 'id,name,email,picture',
                    'access_token': access_token
                }
            )
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Failed to get user info from Facebook"
                )
            
            return response.json()
    
    async def create_or_get_oauth_user(
        self, 
        provider: str, 
        user_info: Dict[str, Any], 
        db: Session
    ) -> Dict[str, Any]:
        """Create or get user from OAuth provider info."""
        
        # Extract email from different providers
        email = None
        name = None
        provider_id = None
        
        if provider == 'google':
            email = user_info.get('email')
            name = user_info.get('name')
            provider_id = user_info.get('id')
        elif provider == 'github':
            email = user_info.get('email')
            name = user_info.get('name') or user_info.get('login')
            provider_id = str(user_info.get('id'))
        elif provider == 'facebook':
            email = user_info.get('email')
            name = user_info.get('name')
            provider_id = user_info.get('id')
        
        if not email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Email not provided by {provider}"
            )
        
        # Normalize email
        email = email.lower().strip()
        
        # Check if user already exists
        existing_user = db.query(User).filter(User.email == email).first()
        
        if existing_user:
            # Update OAuth info if needed
            if not existing_user.oauth_provider:
                existing_user.oauth_provider = provider
                existing_user.oauth_id = provider_id
                db.commit()
            
            user = existing_user
        else:
            # Create new user
            user = User(
                email=email,
                hashed_password=get_password_hash("oauth_user_no_password"),  # Placeholder
                is_active=True,
                is_admin=False,
                oauth_provider=provider,
                oauth_id=provider_id,
                full_name=name
            )
            
            db.add(user)
            db.commit()
            db.refresh(user)
        
        # Create access token
        access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
        access_token = create_access_token(
            data={"sub": user.email, "user_id": user.id},
            expires_delta=access_token_expires
        )
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "email": user.email,
                "full_name": user.full_name,
                "oauth_provider": user.oauth_provider
            }
        }
    
    def get_authorization_url(self, provider: str, redirect_uri: str) -> str:
        """Get authorization URL for OAuth provider."""
        if provider not in ['google', 'github', 'facebook']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unsupported OAuth provider"
            )
        
        client = getattr(self.oauth, provider, None)
        if not client:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"{provider} OAuth not configured"
            )
        
        # Generate authorization URL
        if provider == 'google':
            return f"https://accounts.google.com/oauth2/auth?client_id={settings.google_client_id}&redirect_uri={redirect_uri}&scope=openid email profile&response_type=code"
        elif provider == 'github':
            return f"https://github.com/login/oauth/authorize?client_id={settings.github_client_id}&redirect_uri={redirect_uri}&scope=user:email"
        elif provider == 'facebook':
            return f"https://www.facebook.com/dialog/oauth?client_id={settings.facebook_client_id}&redirect_uri={redirect_uri}&scope=email"
    
    async def exchange_code_for_token(self, provider: str, code: str, redirect_uri: str) -> str:
        """Exchange authorization code for access token."""
        
        if provider == 'google':
            return await self._exchange_google_code(code, redirect_uri)
        elif provider == 'github':
            return await self._exchange_github_code(code, redirect_uri)
        elif provider == 'facebook':
            return await self._exchange_facebook_code(code, redirect_uri)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unsupported OAuth provider"
            )
    
    async def _exchange_google_code(self, code: str, redirect_uri: str) -> str:
        """Exchange Google authorization code for access token."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                'https://oauth2.googleapis.com/token',
                data={
                    'client_id': settings.google_client_id,
                    'client_secret': settings.google_client_secret,
                    'code': code,
                    'grant_type': 'authorization_code',
                    'redirect_uri': redirect_uri,
                }
            )
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Failed to exchange code for token"
                )
            
            token_data = response.json()
            return token_data.get('access_token')
    
    async def _exchange_github_code(self, code: str, redirect_uri: str) -> str:
        """Exchange GitHub authorization code for access token."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                'https://github.com/login/oauth/access_token',
                data={
                    'client_id': settings.github_client_id,
                    'client_secret': settings.github_client_secret,
                    'code': code,
                    'redirect_uri': redirect_uri,
                },
                headers={'Accept': 'application/json'}
            )
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Failed to exchange code for token"
                )
            
            token_data = response.json()
            return token_data.get('access_token')
    
    async def _exchange_facebook_code(self, code: str, redirect_uri: str) -> str:
        """Exchange Facebook authorization code for access token."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                'https://graph.facebook.com/oauth/access_token',
                params={
                    'client_id': settings.facebook_client_id,
                    'client_secret': settings.facebook_client_secret,
                    'code': code,
                    'redirect_uri': redirect_uri,
                }
            )
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Failed to exchange code for token"
                )
            
            token_data = response.json()
            return token_data.get('access_token')
