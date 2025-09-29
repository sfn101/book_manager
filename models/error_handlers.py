import logging
import os
from flask import jsonify, current_app

# Set up logging
logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)

def handle_database_error(e, operation="database operation"):
    """Handle database errors with appropriate logging and response"""
    # Log the full error details
    logger.error(f"Database error during {operation}: {str(e)}", exc_info=True)
    
    # In development, return detailed error; in production, return generic message
    if current_app.debug or os.getenv('FLASK_ENV') == 'development':
        return jsonify({
            'error': f'Database error during {operation}',
            'details': str(e)
        }), 500
    else:
        return jsonify({'error': 'Internal server error occurred'}), 500

def handle_validation_error(message, status_code=400):
    """Handle validation errors"""
    logger.warning(f"Validation error: {message}")
    return jsonify({'error': message}), status_code

def handle_not_found_error(resource="Resource"):
    """Handle not found errors"""
    return jsonify({'error': f'{resource} not found'}), 404

def handle_conflict_error(message, conflicting_id=None):
    """Handle conflict errors (409)"""
    response = {'error': message}
    if conflicting_id:
        response['conflicting_id'] = conflicting_id
    return jsonify(response), 409