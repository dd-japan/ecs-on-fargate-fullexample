from flask import Flask, request, jsonify
import json
import logging
from datetime import datetime
import os
import uuid
import sys

# Initialize Flask app
app = Flask(__name__)

# Force unbuffered output for better response handling
sys.stdout.flush()
sys.stderr.flush()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# In-memory storage for demonstration (in production, use a database)
data_store = []

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for ECS health checks"""
    logger.info("Health check requested")
    return jsonify({
        'status': 'healthy',
        'service': 'python-api',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0'
    }), 200

@app.route('/', methods=['GET'])
def root():
    """Root endpoint with API information"""
    logger.info("Root endpoint accessed")
    return jsonify({
        'message': 'Python API for ECS Fargate',
        'service': 'python-api',
        'version': '1.0.0',
        'endpoints': {
            'GET /': 'API information',
            'GET /health': 'Health check',
            'GET /api/data': 'Get all data items',
            'POST /api/data': 'Create new data item',
            'GET /api/data/<id>': 'Get specific data item',
            'GET /api/status': 'Service status'
        },
        'timestamp': datetime.now().isoformat()
    }), 200

@app.route('/api/data', methods=['GET'])
def get_data():
    """GET endpoint - retrieve all data"""
    logger.info(f"GET /api/data - Retrieved {len(data_store)} items")
    
    response = jsonify({
        'success': True,
        'data': data_store,
        'count': len(data_store),
        'timestamp': datetime.now().isoformat()
    })
    
    # Add headers to prevent caching and ensure proper content type
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    response.headers['Content-Type'] = 'application/json'
    
    return response, 200

@app.route('/api/data', methods=['POST'])
def create_data():
    """POST endpoint - create new data item"""
    try:
        # Get JSON data from request
        if not request.is_json:
            return jsonify({
                'success': False,
                'error': 'Content-Type must be application/json'
            }), 400
        
        request_data = request.get_json()
        
        if not request_data:
            return jsonify({
                'success': False,
                'error': 'Request body cannot be empty'
            }), 400
        
        # Create new item with metadata
        new_item = {
            'id': str(uuid.uuid4()),
            'data': request_data,
            'created_at': datetime.now().isoformat(),
            'created_by': request.remote_addr
        }
        
        # Store the item
        data_store.append(new_item)
        
        logger.info(f"POST /api/data - Created new item with ID: {new_item['id']}")
        
        response = jsonify({
            'success': True,
            'message': 'Data created successfully',
            'item': new_item,
            'total_items': len(data_store)
        })
        
        # Add headers to ensure proper response handling
        response.headers['Content-Type'] = 'application/json'
        response.headers['Cache-Control'] = 'no-cache'
        
        return response, 201
        
    except Exception as e:
        logger.error(f"Error creating data: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Internal server error',
            'details': str(e)
        }), 500

@app.route('/api/data/<item_id>', methods=['GET'])
def get_data_by_id(item_id):
    """GET endpoint - retrieve specific data item by ID"""
    logger.info(f"GET /api/data/{item_id}")
    
    # Find item by ID
    item = next((item for item in data_store if item['id'] == item_id), None)
    
    if not item:
        return jsonify({
            'success': False,
            'error': f'Item with ID {item_id} not found'
        }), 404
    
    return jsonify({
        'success': True,
        'item': item,
        'timestamp': datetime.now().isoformat()
    }), 200

@app.route('/api/status', methods=['GET'])
def get_status():
    """GET endpoint - service status and statistics"""
    logger.info("Status endpoint accessed")
    
    return jsonify({
        'service': 'python-api',
        'status': 'running',
        'version': '1.0.0',
        'environment': os.environ.get('ENVIRONMENT', 'development'),
        'statistics': {
            'total_items': len(data_store),
            'uptime': 'running',
            'last_activity': datetime.now().isoformat()
        },
        'system_info': {
            'python_version': os.sys.version,
            'platform': os.name
        }
    }), 200

@app.route('/api/data', methods=['DELETE'])
def clear_data():
    """DELETE endpoint - clear all data (for testing)"""
    global data_store
    items_count = len(data_store)
    data_store = []
    
    logger.info(f"DELETE /api/data - Cleared {items_count} items")
    
    return jsonify({
        'success': True,
        'message': f'Cleared {items_count} items',
        'timestamp': datetime.now().isoformat()
    }), 200

# Error handlers
@app.errorhandler(404)
def not_found(error):
    logger.warning(f"404 error for: {request.url}")
    return jsonify({
        'success': False,
        'error': 'Endpoint not found',
        'requested_path': request.path
    }), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"500 error: {str(error)}")
    return jsonify({
        'success': False,
        'error': 'Internal server error'
    }), 500

# Production deployment uses Gunicorn, not Flask dev server
# if __name__ == '__main__':
#     port = int(os.environ.get('PORT', 8000))
#     logger.info(f"Starting Python API on port {port}")
#     app.run(host='0.0.0.0', port=port, debug=False)
