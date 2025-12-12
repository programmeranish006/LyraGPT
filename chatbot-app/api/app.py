from flask import Flask, jsonify, request
from flask_cors import CORS
from api.awt_components import awt_bp
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# Enable CORS for all routes
CORS(app)

# Configuration
app.config['JSON_SORT_KEYS'] = False
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = True

# Register blueprints
app.register_blueprint(awt_bp)

# ==================== GENERAL ROUTES ====================

@app.route('/', methods=['GET'])
def home():
    """API home endpoint"""
    return jsonify({
        "status": "success",
        "name": "AWT Components API",
        "version": "1.0.0",
        "description": "Backend API for AWT Components Showcase Application",
        "endpoints": {
            "components": {
                "GET /api/awt/components": "Get all AWT components",
                "GET /api/awt/components/<category>": "Get components by category",
                "GET /api/awt/components/<category>/<name>": "Get specific component details"
            },
            "form": {
                "POST /api/awt/form/submit": "Submit form data",
                "GET /api/awt/form/submissions": "Get all submissions",
                "GET /api/awt/form/submissions/<id>": "Get specific submission",
                "DELETE /api/awt/form/submissions/<id>": "Delete submission",
                "POST /api/awt/form/validate": "Validate form data"
            },
            "examples": {
                "GET /api/awt/examples": "Get all code examples",
                "GET /api/awt/examples/<component>": "Get example for component"
            },
            "statistics": {
                "GET /api/awt/stats": "Get submission statistics"
            },
            "health": {
                "GET /api/awt/health": "Health check"
            }
        }
    }), 200

@app.route('/api', methods=['GET'])
def api_info():
    """API information endpoint"""
    return jsonify({
        "status": "success",
        "message": "Welcome to AWT Components API",
        "base_url": request.base_url,
        "documentation": "See / endpoint for available endpoints"
    }), 200

# ==================== ERROR HANDLERS ====================

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({
        "status": "error",
        "code": 404,
        "message": "Endpoint not found"
    }), 404

@app.errorhandler(405)
def method_not_allowed(error):
    """Handle 405 errors"""
    return jsonify({
        "status": "error",
        "code": 405,
        "message": "Method not allowed"
    }), 405

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    return jsonify({
        "status": "error",
        "code": 500,
        "message": "Internal server error"
    }), 500

# ==================== REQUEST/RESPONSE LOGGING ====================

@app.before_request
def log_request():
    """Log incoming requests"""
    from flask import request
    print(f"[{datetime.now().isoformat()}] {request.method} {request.path}")

@app.after_request
def log_response(response):
    """Log outgoing responses"""
    print(f"Response Status: {response.status_code}")
    return response

# ==================== MAIN ====================

if __name__ == '__main__':
    debug_mode = os.getenv('DEBUG', 'True') == 'True'
    port = int(os.getenv('PORT', 5000))
    
    print("=" * 50)
    print("AWT Components API Server")
    print("=" * 50)
    print(f"Starting server on port {port}")
    print(f"Debug mode: {debug_mode}")
    print("=" * 50)
    
    app.run(debug=debug_mode, port=port, host='0.0.0.0')
