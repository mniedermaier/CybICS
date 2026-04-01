/**
 * CybICS AI Chat Widget
 *
 * Self-contained chat widget with streaming SSE support, resize handles,
 * session persistence, and destructive action confirmation.
 *
 * Loaded with `defer` so the DOM is ready when this runs.
 */

/* ── Markdown rendering ── */

function safeMarkdown(content) {
    return DOMPurify.sanitize(marked.parse(content));
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

/* ── Session ── */

let chatSessionId = sessionStorage.getItem('cybics_session_id');
if (!chatSessionId) {
    chatSessionId = crypto.randomUUID();
    sessionStorage.setItem('cybics_session_id', chatSessionId);
}

/* ── Toggle / Status ── */

function toggleChat() {
    const chatWidget = document.getElementById('chatWidget');
    chatWidget.classList.toggle('expanded');

    if (chatWidget.classList.contains('expanded')) {
        document.getElementById('chatInput').focus();
        checkAgentStatus();
    } else {
        chatWidget.style.width = '';
        chatWidget.style.height = '';
    }
}

function checkAgentStatus() {
    fetch('/api/agent/status')
        .then(response => response.json())
        .then(data => {
            const statusDiv = document.getElementById('agentStatus');
            if (data.available && data.enabled) {
                statusDiv.innerHTML = `✅ Agent Ready (${data.model})`;
                statusDiv.style.color = '#4ade80';
            } else if (!data.enabled) {
                statusDiv.innerHTML = '❌ Agent Disabled';
                statusDiv.style.color = '#f87171';
            } else {
                statusDiv.innerHTML = '⚠️ Agent Unavailable';
                statusDiv.style.color = '#fbbf24';
            }
        })
        .catch(() => {
            const statusDiv = document.getElementById('agentStatus');
            statusDiv.innerHTML = '❌ Agent Offline';
            statusDiv.style.color = '#f87171';
        });
}

/* ── Typing indicator ── */

function showTyping() {
    const messages = document.getElementById('chatMessages');
    const typingDiv = document.createElement('div');
    typingDiv.className = 'chat-message agent-message typing-indicator';
    typingDiv.id = 'typingIndicator';
    typingDiv.innerHTML = `
        <span class="message-avatar">🤖</span>
        <span class="message-text">
            <span class="typing-dot"></span>
            <span class="typing-dot"></span>
            <span class="typing-dot"></span>
        </span>
    `;
    messages.appendChild(typingDiv);
    messages.scrollTop = messages.scrollHeight;
}

function hideTyping() {
    const typing = document.getElementById('typingIndicator');
    if (typing) typing.remove();
}

/* ── Message rendering ── */

function addMessageToChat(sender, message) {
    const messages = document.getElementById('chatMessages');
    const messageDiv = document.createElement('div');
    messageDiv.className = `chat-message ${sender}-message`;

    const avatar = sender === 'user' ? '👤' : '🤖';
    const messageContent = sender === 'agent'
        ? safeMarkdown(message)
        : escapeHtml(message);

    messageDiv.innerHTML = `
        <span class="message-avatar">${avatar}</span>
        <span class="message-text">${messageContent}</span>
    `;

    messages.appendChild(messageDiv);
    messages.scrollTop = messages.scrollHeight;
    saveChatHistory();
}

function createStreamingMessage() {
    const messages = document.getElementById('chatMessages');
    const messageDiv = document.createElement('div');
    messageDiv.className = 'chat-message agent-message';
    messageDiv.innerHTML = `
        <span class="message-avatar">🤖</span>
        <span class="message-text"></span>
    `;
    messages.appendChild(messageDiv);
    messages.scrollTop = messages.scrollHeight;
    return messageDiv;
}

function updateStreamingMessage(div, content) {
    const textSpan = div.querySelector('.message-text');
    textSpan.innerHTML = safeMarkdown(content);
    const messages = document.getElementById('chatMessages');
    messages.scrollTop = messages.scrollHeight;
}

/* ── Confirmation buttons ── */

function showConfirmationButtons(div, pendingAction) {
    const textSpan = div.querySelector('.message-text');
    const btnContainer = document.createElement('div');
    btnContainer.style.cssText = 'margin-top: 10px; display: flex; gap: 8px;';
    btnContainer.innerHTML = `
        <button onclick="confirmAction(this)" style="padding: 4px 16px; background: #22c55e; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 13px;">Yes</button>
        <button onclick="cancelAction(this)" style="padding: 4px 16px; background: #ef4444; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 13px;">No</button>
    `;
    textSpan.appendChild(btnContainer);
}

function confirmAction(btn) {
    const container = btn.parentElement;
    container.querySelectorAll('button').forEach(b => b.disabled = true);
    container.innerHTML = '<em>Confirmed, executing...</em>';
    sendMessage('__confirm__');
}

function cancelAction(btn) {
    const container = btn.parentElement;
    container.querySelectorAll('button').forEach(b => b.disabled = true);
    container.innerHTML = '<em>Action cancelled.</em>';
}

/* ── Chat history persistence ── */

function saveChatHistory() {
    const messages = document.getElementById('chatMessages');
    const history = [];
    messages.querySelectorAll('.chat-message').forEach(msg => {
        if (msg.id === 'typingIndicator') return;
        const isUser = msg.classList.contains('user-message');
        const text = msg.querySelector('.message-text').textContent;
        history.push({ sender: isUser ? 'user' : 'agent', message: text });
    });
    sessionStorage.setItem('cybics_chat_history', JSON.stringify(history));
}

function loadChatHistory() {
    const history = sessionStorage.getItem('cybics_chat_history');
    if (!history) return;

    const messages = JSON.parse(history);
    const messagesContainer = document.getElementById('chatMessages');
    messagesContainer.innerHTML = '';

    messages.forEach(msg => {
        const messageDiv = document.createElement('div');
        messageDiv.className = `chat-message ${msg.sender}-message`;
        const avatar = msg.sender === 'user' ? '👤' : '🤖';
        const messageContent = msg.sender === 'agent'
            ? safeMarkdown(msg.message)
            : escapeHtml(msg.message);

        messageDiv.innerHTML = `
            <span class="message-avatar">${avatar}</span>
            <span class="message-text">${messageContent}</span>
        `;
        messagesContainer.appendChild(messageDiv);
    });
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

function clearChatHistory() {
    if (!confirm('Are you sure you want to clear the chat history? This cannot be undone.')) {
        return;
    }

    sessionStorage.removeItem('cybics_chat_history');
    chatSessionId = crypto.randomUUID();
    sessionStorage.setItem('cybics_session_id', chatSessionId);

    const messagesContainer = document.getElementById('chatMessages');
    messagesContainer.innerHTML = `
        <div class="chat-message agent-message">
            <span class="message-avatar">🤖</span>
            <span class="message-text">Hi! I'm the CybICS AI Assistant. Ask me anything about CybICS!</span>
        </div>
    `;

    const statusDiv = document.getElementById('agentStatus');
    const originalStatus = statusDiv.innerHTML;
    statusDiv.innerHTML = '✅ Chat history cleared';
    statusDiv.style.color = '#4ade80';

    setTimeout(() => {
        statusDiv.innerHTML = originalStatus;
        statusDiv.style.color = '';
        checkAgentStatus();
    }, 2000);
}

/* ── Streaming SSE ── */

function handleStreamResponse(response) {
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let streamingDiv = null;
    let accumulatedContent = '';
    let buffer = '';

    hideTyping();

    function processLine(line) {
        if (!line.startsWith('data: ')) return;
        try {
            const data = JSON.parse(line.slice(6));

            if (data.type === 'session' && data.session_id) {
                chatSessionId = data.session_id;
                sessionStorage.setItem('cybics_session_id', chatSessionId);
            } else if (data.type === 'tool') {
                if (!streamingDiv) streamingDiv = createStreamingMessage();
                accumulatedContent += `*Using tool: ${data.tool}...*\n\n`;
                updateStreamingMessage(streamingDiv, accumulatedContent);
            } else if (data.type === 'token') {
                if (!streamingDiv) {
                    streamingDiv = createStreamingMessage();
                    accumulatedContent = '';
                }
                accumulatedContent += data.content;
                updateStreamingMessage(streamingDiv, accumulatedContent);
            } else if (data.type === 'content') {
                if (!streamingDiv) streamingDiv = createStreamingMessage();
                accumulatedContent = data.content;
                updateStreamingMessage(streamingDiv, accumulatedContent);
            } else if (data.type === 'done') {
                if (data.confirmation_required) {
                    showConfirmationButtons(streamingDiv, data.pending_action);
                }
                saveChatHistory();
            }
        } catch (e) {
            // Skip malformed JSON
        }
    }

    function read() {
        reader.read().then(({ done, value }) => {
            if (done) {
                if (buffer.trim()) processLine(buffer.trim());
                saveChatHistory();
                return;
            }

            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split('\n');
            buffer = lines.pop();

            for (const line of lines) {
                const trimmed = line.trim();
                if (trimmed) processLine(trimmed);
            }

            read();
        }).catch(() => {
            saveChatHistory();
        });
    }

    read();
}

/* ── Send message ── */

function sendMessage(overrideMessage) {
    const input = document.getElementById('chatInput');
    const message = overrideMessage || input.value.trim();
    if (!message) return;

    if (message !== '__confirm__') {
        addMessageToChat('user', message);
    }

    input.value = '';
    showTyping();

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 600000);

    fetch('/api/agent/chat/stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: message, session_id: chatSessionId }),
        signal: controller.signal
    })
    .then(response => {
        clearTimeout(timeoutId);
        if (!response.ok || !response.headers.get('content-type')?.includes('text/event-stream')) {
            return sendMessageNonStreaming(message);
        }
        return handleStreamResponse(response);
    })
    .catch(error => {
        clearTimeout(timeoutId);
        if (error.name === 'AbortError') {
            hideTyping();
            addMessageToChat('agent', 'Sorry, the request took too long. Please try again.');
        } else {
            sendMessageNonStreaming(message);
        }
    });
}

function sendMessageNonStreaming(message) {
    hideTyping();
    showTyping();

    fetch('/api/agent/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: message, session_id: chatSessionId }),
    })
    .then(response => response.json())
    .then(data => {
        hideTyping();
        if (data.session_id) {
            chatSessionId = data.session_id;
            sessionStorage.setItem('cybics_session_id', chatSessionId);
        }
        if (data.error) {
            addMessageToChat('agent', `Error: ${data.error}`);
        } else if (data.confirmation_required) {
            const div = createStreamingMessage();
            updateStreamingMessage(div, data.response);
            showConfirmationButtons(div, data.pending_action);
        } else {
            addMessageToChat('agent', data.response);
        }
    })
    .catch(error => {
        hideTyping();
        addMessageToChat('agent', `Sorry, I encountered an error: ${error.message}`);
    });
}

/* ── Resize handles ── */

(function initResize() {
    const chatWidget = document.getElementById('chatWidget');
    const topHandle = document.getElementById('chatResizeHandle');
    const leftHandle = document.getElementById('chatResizeLeft');
    const cornerHandle = document.getElementById('chatResizeCorner');
    if (!chatWidget) return;

    let resizeMode = null;
    let startX, startY, startWidth, startHeight;

    function startResize(mode, cursor, e) {
        if (!chatWidget.classList.contains('expanded')) return;
        resizeMode = mode;
        startX = e.clientX;
        startY = e.clientY;
        startWidth = chatWidget.offsetWidth;
        startHeight = chatWidget.offsetHeight;
        chatWidget.classList.add('resizing');
        document.body.style.userSelect = 'none';
        document.body.style.cursor = cursor;
        e.preventDefault();
        e.stopPropagation();
    }

    function bindHandle(el, mode, cursor) {
        if (!el) return;
        el.addEventListener('mousedown', function(e) { startResize(mode, cursor, e); });
        el.addEventListener('click', function(e) { e.stopPropagation(); });
    }

    bindHandle(topHandle, 'top', 'n-resize');
    bindHandle(leftHandle, 'left', 'w-resize');
    bindHandle(cornerHandle, 'corner', 'nw-resize');

    document.addEventListener('mousemove', function(e) {
        if (!resizeMode) return;
        if (resizeMode === 'top' || resizeMode === 'corner') {
            const h = Math.max(300, Math.min(startHeight + (startY - e.clientY), window.innerHeight - 50));
            chatWidget.style.height = h + 'px';
        }
        if (resizeMode === 'left' || resizeMode === 'corner') {
            const w = Math.max(300, Math.min(startWidth + (startX - e.clientX), window.innerWidth - 50));
            chatWidget.style.width = w + 'px';
        }
    });

    document.addEventListener('mouseup', function() {
        if (resizeMode) {
            resizeMode = null;
            chatWidget.classList.remove('resizing');
            document.body.style.userSelect = '';
            document.body.style.cursor = '';
        }
    });
})();

/* ── Init ── */

// Enter key to send
const chatInput = document.getElementById('chatInput');
if (chatInput) {
    chatInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') sendMessage();
    });
}

// Restore previous chat
loadChatHistory();
