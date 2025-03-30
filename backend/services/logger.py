# Logger service for handling WebSocket connections and log broadcasting

from flask import request, jsonify
from flask_socketio import SocketIO, emit
import time

# Initialize SocketIO instance to be imported by app.py
socketio = SocketIO(cors_allowed_origins="*")

# Store connected clients for broadcasting
connected_clients = set()

# WebSocket event handlers
@socketio.on('connect')
def handle_connect():
    """Handle new WebSocket connections"""
    connected_clients.add(request.sid)
    print(f"Client connected: {request.sid}. Total clients: {len(connected_clients)}")

@socketio.on('disconnect')
def handle_disconnect():
    """Handle WebSocket disconnections"""
    if request.sid in connected_clients:
        connected_clients.remove(request.sid)
    print(f"Client disconnected: {request.sid}. Total clients: {len(connected_clients)}")

# Log broadcasting function
def broadcast_log(log_type, message, summary=""):
    """
    Broadcast a log message to all connected WebSocket clients
    
    Args:
        log_type (str): Type of log ('system' or 'ai')
        message (str): Log message content
        summary (str, optional): Summary of the log message. Defaults to empty string.
    """
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    log_data = {
        "type": log_type,
        "message": message,
        "timestamp": timestamp,
        "summary": summary
    }
    
    # Emit to all connected clients
    socketio.emit('log', log_data)
    
    # Print to server console for debugging
    print(f"[{timestamp}] [{log_type}] {message}")
    
    return log_data

# HTTP route handler (to be registered in app.py)
def handle_log_post():
    """
    Handle HTTP POST requests to /api/log
    Expected request body: { "type": "system|ai", "message": "log content" }
    """
    data = request.get_json()
    
    if not data or 'type' not in data or 'message' not in data:
        return jsonify({"error": "Invalid request. Required fields: 'type', 'message'"}), 400
    
    log_type = data.get('type')
    message = data.get('message')
    
    # Validate log type
    if log_type not in ['system', 'ai']:
        return jsonify({"error": "Invalid log type. Must be 'system' or 'ai'"}), 400
    
    # Get summary if provided, otherwise default to empty string
    summary = data.get('summary', '')
    
    # Broadcast the log
    log_data = broadcast_log(log_type, message, summary)
    
    return jsonify(log_data), 200