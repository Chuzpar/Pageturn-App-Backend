from functools import wraps
from flask import jsonify
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
from app.models.user import User


def admin_required(fn):
    """
    Decorator to protect admin-only endpoints.
    Verifies JWT token and checks if user has admin role.
    
    Returns:
        403 Forbidden if user is not an admin
        401 Unauthorized if no valid token
    """
    @wraps(fn)
    def wrapper(*args, **kwargs):
        # Verify JWT token is present and valid
        verify_jwt_in_request()
        
        # Get user from database
        user = User.query.get(int(get_jwt_identity()))
        
        # Check if user exists and has admin role
        if not user or user.role != "admin":
            return jsonify({"error": "Admin access required"}), 403
            
        return fn(*args, **kwargs)
    return wrapper


def current_user():
    """
    Helper function to get the currently authenticated user.
    Assumes JWT token has been verified.
    
    Returns:
        User object or None if not found
    """
    user = User.query.get(int(get_jwt_identity()))
    return user