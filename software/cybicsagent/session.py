"""CybICS AI Agent - Session manager for conversation history"""
import time
import uuid
import logging
from collections import OrderedDict
from threading import RLock

from config import MAX_SESSIONS, get_max_history

logger = logging.getLogger(__name__)


class SessionManager:
    """Thread-safe conversation session manager with message history and pending actions."""

    def __init__(self, max_sessions=None):
        self._sessions = OrderedDict()
        self._max_sessions = max_sessions or MAX_SESSIONS
        self._lock = RLock()

    def get_or_create(self, session_id=None):
        """Get an existing session or create a new one."""
        with self._lock:
            if session_id and session_id in self._sessions:
                session = self._sessions[session_id]
                # Move to end (most recently used)
                self._sessions.move_to_end(session_id)
                return session

            # Create new session
            if not session_id:
                session_id = str(uuid.uuid4())

            # Evict oldest if at capacity
            while len(self._sessions) >= self._max_sessions:
                evicted_id, _ = self._sessions.popitem(last=False)
                logger.debug(f"Evicted session {evicted_id}")

            session = {
                'id': session_id,
                'messages': [],
                'created_at': time.time(),
                'pending_action': None,
            }
            self._sessions[session_id] = session
            return session

    def add_message(self, session_id, role, content):
        """Add a message to a session's history."""
        with self._lock:
            session = self._sessions.get(session_id)
            if not session:
                return

            session['messages'].append({
                'role': role,
                'content': content,
            })

    def get_messages(self, session_id, model_name='phi3:mini'):
        """Get conversation messages for a session, trimmed to model's limit."""
        with self._lock:
            session = self._sessions.get(session_id)
            if not session:
                return []

            max_history = get_max_history(model_name)
            messages = session['messages']

            # Keep only the most recent messages within limit
            if len(messages) > max_history:
                return list(messages[-max_history:])
            return list(messages)

    def set_pending_action(self, session_id, tool_name, parameters):
        """Store a pending destructive action awaiting confirmation."""
        with self._lock:
            session = self._sessions.get(session_id)
            if session:
                session['pending_action'] = {
                    'tool': tool_name,
                    'parameters': parameters,
                }

    def pop_pending_action(self, session_id):
        """Retrieve and clear a pending action."""
        with self._lock:
            session = self._sessions.get(session_id)
            if session and session['pending_action']:
                action = session['pending_action']
                session['pending_action'] = None
                return action
            return None


# Global session manager instance
session_manager = SessionManager()
