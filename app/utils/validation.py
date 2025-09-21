"""
Authentication and input validation utilities.
"""

import re
from typing import Dict, List, Optional
from pydantic import BaseModel, validator


class ValidationError(Exception):
    """Custom validation error."""
    def __init__(self, message: str, field: str = None):
        self.message = message
        self.field = field
        super().__init__(self.message)


class PasswordRequirements:
    """Password strength requirements."""
    MIN_LENGTH = 8
    MAX_LENGTH = 128
    REQUIRE_UPPERCASE = True
    REQUIRE_LOWERCASE = True
    REQUIRE_DIGIT = True
    REQUIRE_SPECIAL = True
    SPECIAL_CHARACTERS = "!@#$%^&*()_+-=[]{}|;:,.<>?"


def validate_email(email: str) -> bool:
    """
    Validate email format using regex.
    
    Args:
        email: Email address to validate
        
    Returns:
        bool: True if email is valid, False otherwise
    """
    if not email or not isinstance(email, str):
        return False
    
    # RFC 5322 compliant email regex (simplified)
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    # Additional checks
    if len(email) > 254:  # RFC 5321 limit
        return False
    
    if '..' in email:  # No consecutive dots
        return False
    
    if email.startswith('.') or email.endswith('.'):  # No leading/trailing dots
        return False
    
    return bool(re.match(email_pattern, email))


def validate_password(password: str) -> Dict[str, any]:
    """
    Validate password strength against requirements.
    
    Args:
        password: Password to validate
        
    Returns:
        Dict containing validation result and details
    """
    if not password or not isinstance(password, str):
        return {
            "valid": False,
            "message": "Password is required",
            "requirements_met": []
        }
    
    requirements_met = []
    errors = []
    
    # Length check
    if len(password) >= PasswordRequirements.MIN_LENGTH:
        requirements_met.append("minimum_length")
    else:
        errors.append(f"Password must be at least {PasswordRequirements.MIN_LENGTH} characters long")
    
    if len(password) <= PasswordRequirements.MAX_LENGTH:
        requirements_met.append("maximum_length")
    else:
        errors.append(f"Password must be no more than {PasswordRequirements.MAX_LENGTH} characters long")
    
    # Uppercase check
    if PasswordRequirements.REQUIRE_UPPERCASE:
        if re.search(r'[A-Z]', password):
            requirements_met.append("uppercase")
        else:
            errors.append("Password must contain at least one uppercase letter")
    
    # Lowercase check
    if PasswordRequirements.REQUIRE_LOWERCASE:
        if re.search(r'[a-z]', password):
            requirements_met.append("lowercase")
        else:
            errors.append("Password must contain at least one lowercase letter")
    
    # Digit check
    if PasswordRequirements.REQUIRE_DIGIT:
        if re.search(r'\d', password):
            requirements_met.append("digit")
        else:
            errors.append("Password must contain at least one digit")
    
    # Special character check
    if PasswordRequirements.REQUIRE_SPECIAL:
        special_chars_escaped = re.escape(PasswordRequirements.SPECIAL_CHARACTERS)
        if re.search(f'[{special_chars_escaped}]', password):
            requirements_met.append("special_character")
        else:
            errors.append(f"Password must contain at least one special character ({PasswordRequirements.SPECIAL_CHARACTERS})")
    
    # Common password checks
    common_passwords = [
        "password", "123456", "123456789", "qwerty", "abc123", 
        "password123", "admin", "letmein", "welcome", "monkey"
    ]
    
    if password.lower() in common_passwords:
        errors.append("Password is too common. Please choose a more secure password")
    
    is_valid = len(errors) == 0
    
    return {
        "valid": is_valid,
        "message": "Password meets all requirements" if is_valid else "; ".join(errors),
        "requirements_met": requirements_met,
        "errors": errors
    }


def get_password_strength_score(password: str) -> Dict[str, any]:
    """
    Calculate password strength score (0-100).
    
    Args:
        password: Password to evaluate
        
    Returns:
        Dict containing strength score and level
    """
    if not password:
        return {"score": 0, "level": "Very Weak", "feedback": []}
    
    score = 0
    feedback = []
    
    # Length scoring
    length = len(password)
    if length >= 8:
        score += 25
    elif length >= 6:
        score += 15
        feedback.append("Consider using a longer password")
    else:
        feedback.append("Password is too short")
    
    # Character variety scoring
    has_lower = bool(re.search(r'[a-z]', password))
    has_upper = bool(re.search(r'[A-Z]', password))
    has_digit = bool(re.search(r'\d', password))
    has_special = bool(re.search(r'[!@#$%^&*()_+\-=\[\]{}|;:,.<>?]', password))
    
    char_types = sum([has_lower, has_upper, has_digit, has_special])
    score += char_types * 15
    
    # Bonus for good practices
    if length >= 12:
        score += 10
        feedback.append("Great length!")
    
    if char_types >= 3:
        feedback.append("Good character variety!")
    
    # Penalties
    if re.search(r'(.)\1{2,}', password):  # Repeated characters
        score -= 10
        feedback.append("Avoid repeating characters")
    
    if re.search(r'(012|123|234|345|456|567|678|789|890|abc|bcd|cde)', password.lower()):
        score -= 15
        feedback.append("Avoid sequential characters")
    
    # Determine strength level
    if score >= 80:
        level = "Very Strong"
    elif score >= 60:
        level = "Strong"
    elif score >= 40:
        level = "Moderate"
    elif score >= 20:
        level = "Weak"
    else:
        level = "Very Weak"
    
    return {
        "score": max(0, min(100, score)),
        "level": level,
        "feedback": feedback
    }


def validate_user_registration(email: str, password: str, confirm_password: str = None) -> Dict[str, any]:
    """
    Comprehensive validation for user registration.
    
    Args:
        email: Email address
        password: Password
        confirm_password: Password confirmation (optional)
        
    Returns:
        Dict containing validation results
    """
    errors = []
    
    # Email validation
    if not validate_email(email):
        errors.append("Please enter a valid email address")
    
    # Password validation
    password_result = validate_password(password)
    if not password_result["valid"]:
        errors.extend(password_result["errors"])
    
    # Password confirmation
    if confirm_password is not None and password != confirm_password:
        errors.append("Passwords do not match")
    
    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "email_valid": validate_email(email),
        "password_result": password_result
    }


class UserRegistrationRequest(BaseModel):
    """Pydantic model for user registration with validation."""
    email: str
    password: str
    confirm_password: Optional[str] = None
    
    @validator('email')
    def validate_email_format(cls, v):
        if not validate_email(v):
            raise ValueError('Please enter a valid email address')
        return v.lower().strip()
    
    @validator('password')
    def validate_password_strength(cls, v):
        result = validate_password(v)
        if not result["valid"]:
            raise ValueError(result["message"])
        return v
    
    @validator('confirm_password')
    def passwords_match(cls, v, values):
        if 'password' in values and v != values['password']:
            raise ValueError('Passwords do not match')
        return v


class UserLoginRequest(BaseModel):
    """Pydantic model for user login with validation."""
    email: str
    password: str
    
    @validator('email')
    def validate_email_format(cls, v):
        if not validate_email(v):
            raise ValueError('Please enter a valid email address')
        return v.lower().strip()
    
    @validator('password')
    def validate_password_not_empty(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('Password is required')
        return v
