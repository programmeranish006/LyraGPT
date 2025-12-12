import json
from datetime import datetime
from functools import wraps
from flask import jsonify, request

def validate_request_json(*expected_fields):
    """Decorator to validate JSON request contains expected fields"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            data = request.get_json()
            if not data:
                return jsonify({
                    "status": "error",
                    "message": "Request body must be JSON"
                }), 400
            
            missing_fields = [field for field in expected_fields if field not in data]
            if missing_fields:
                return jsonify({
                    "status": "error",
                    "message": f"Missing required fields: {', '.join(missing_fields)}"
                }), 400
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def success_response(data=None, message="Success", code=200):
    """Create a standardized success response"""
    response = {
        "status": "success",
        "message": message
    }
    if data is not None:
        response["data"] = data
    return jsonify(response), code

def error_response(message="Error", code=400, details=None):
    """Create a standardized error response"""
    response = {
        "status": "error",
        "message": message
    }
    if details:
        response["details"] = details
    return jsonify(response), code

def paginate_list(items, limit=10, offset=0):
    """Paginate a list of items"""
    total = len(items)
    paginated = items[offset:offset + limit]
    
    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "count": len(paginated),
        "items": paginated
    }

def format_timestamp(dt=None):
    """Format timestamp as ISO string"""
    if dt is None:
        dt = datetime.now()
    return dt.isoformat()

def validate_email(email):
    """Basic email validation"""
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_name(name, min_length=2, max_length=100):
    """Validate name field"""
    if not name or not isinstance(name, str):
        return False
    name = name.strip()
    return min_length <= len(name) <= max_length

def validate_text_field(text, min_length=0, max_length=None):
    """Validate text field"""
    if not isinstance(text, str):
        return False
    if len(text) < min_length:
        return False
    if max_length and len(text) > max_length:
        return False
    return True
