from datetime import timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from pydantic import ValidationError

from app.core.auth import (
    authenticate_user,
    create_access_token,
    get_password_hash,
    get_current_active_user,
)
from app.core.database import get_db
from app.models.database import User
from app.models.schemas import Token, UserCreate, UserResponse
from app.config.settings import settings
from app.utils.validation import (
    UserRegistrationRequest,
    UserLoginRequest,
    validate_user_registration,
    validate_email,
    get_password_strength_score
)

router = APIRouter()


@router.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
) -> Any:
    """
    OAuth2 compatible token login, get an access token for future requests.
    """
    # Validate email format
    if not validate_email(form_data.username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please enter a valid email address",
        )
    
    # Validate password is not empty
    if not form_data.password or len(form_data.password.strip()) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password is required",
        )
    
    user = authenticate_user(db, form_data.username.lower().strip(), form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": user.email, "user_id": user.id},
        expires_delta=access_token_expires,
    )
    
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/register", response_model=UserResponse)
async def register_user(
    user_in: UserCreate,
    db: Session = Depends(get_db),
) -> Any:
    """
    Register a new user with enhanced validation.
    """
    # Comprehensive validation
    validation_result = validate_user_registration(
        email=user_in.email,
        password=user_in.password
    )
    
    if not validation_result["valid"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="; ".join(validation_result["errors"]),
        )
    
    # Normalize email
    normalized_email = user_in.email.lower().strip()
    
    # Check if user already exists
    db_user = db.query(User).filter(User.email == normalized_email).first()
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )
    
    # Create new user
    hashed_password = get_password_hash(user_in.password)
    db_user = User(
        email=normalized_email,
        hashed_password=hashed_password,
        is_active=True,
        is_admin=False,
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return db_user


@router.post("/validate-password")
async def validate_password_strength(
    request: dict,
) -> Any:
    """
    Validate password strength and return feedback.
    """
    try:
        password = request.get("password", "")
        
        strength_result = get_password_strength_score(password)
        validation_result = validate_user_registration("test@example.com", password)
        
        return {
            "strength": strength_result,
            "validation": {
                "valid": validation_result["password_result"]["valid"],
                "errors": validation_result["password_result"]["errors"],
                "requirements_met": validation_result["password_result"]["requirements_met"]
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get("/me", response_model=UserResponse)
async def read_users_me(
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Get current user.
    """
    return current_user


