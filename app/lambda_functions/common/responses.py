import json
import logging
from typing import Any, Dict, Optional

logger = logging.getLogger()


def success_response(data: Any, status_code: int = 200,
                     message: Optional[str] = None) -> Dict:
    """Build successful API response"""
    body = {'success': True, 'data': data}

    if message:
        body['message'] = message

    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',  # CORS support
            'Access-Control-Allow-Headers': 'Content-Type,X-Api-Key',
            'Access-Control-Allow-Methods': 'GET,POST,DELETE,OPTIONS'
        },
        'body': json.dumps(body)
    }


def error_response(message: str, status_code: int = 500,
                   error_code: Optional[str] = None,
                   details: Optional[Dict] = None) -> Dict:
    """Build error API response"""
    body = {'success': False, 'error': {'message': message}}

    if error_code:
        body['error']['code'] = error_code
    if details:
        body['error']['details'] = details

    logger.error(f"Error response: {status_code} - {message}")

    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type,X-Api-Key',
            'Access-Control-Allow-Methods': 'GET,POST,DELETE,OPTIONS'
        },
        'body': json.dumps(body)
    }


def validation_error_response(message: str, details: Optional[Dict] = None) -> Dict:
    """Build validation error response (400)"""
    return error_response(message=message, status_code=400,
                          error_code='VALIDATION_ERROR', details=details)


def not_found_response(resource: str, resource_id: str) -> Dict:
    """Build not found response (404)"""
    return error_response(
        message=f"{resource} not found: {resource_id}",
        status_code=404,
        error_code='NOT_FOUND'
    )


def internal_error_response(exception: Exception) -> Dict:
    logger.exception("Internal server error", exc_info=exception)

    return error_response(
        message='An internal server error occurred',
        status_code=500,
        error_code='INTERNAL_ERROR',
        details={'type': type(exception).__name__}
    )
