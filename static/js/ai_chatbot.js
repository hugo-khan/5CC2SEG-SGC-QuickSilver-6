/**
 * AI Chatbot JavaScript
 * 
 * Provides progressive enhancement for the AI Chef chatbot:
 * - Intercepts form submission for AJAX requests
 * - Updates chat transcript without full page reload
 * - Handles publish button click
 * - Falls back to normal form submission if JS fails
 * 
 * This file exports helper functions for testing when run in Node.js.
 */

(function() {
    'use strict';

    // Helper functions (exported for testing)

    /**
     * Escape HTML special characters to prevent XSS.
     * @param {string} text - The text to escape
     * @returns {string} - The escaped text
     */
    function escapeHtml(text) {
        if (typeof text !== 'string') {
            return '';
        }
        const htmlEntities = {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#39;'
        };
        return text.replace(/[&<>"']/g, function(char) {
            return htmlEntities[char];
        });
    }

    /**
     * Render assistant content while allowing limited, trusted HTML (anchors).
     * - Escapes HTML
     * - Re-hydrates safe <a> tags
     * - Applies minimal markdown (**bold**, *italic*)
     */
    function renderAssistantContent(text) {
        const escaped = escapeHtml(text || '');

        // Allow only safe <a href="..."> links (http, https, or relative)
        const withLinks = escaped
            // Handle escaped quotes (&quot;) as well as raw quotes
            .replace(/&lt;a\s+[^&]*href=&quot;([^"&]+)&quot;[^&]*&gt;(.*?)&lt;\/a&gt;/gi, function(_, href, linkText) {
                const safeHref = (href || '').trim();
                const lowerHref = safeHref.toLowerCase();

                // Block javascript or data URIs
                const isSafeProtocol = lowerHref.startsWith('http://') || lowerHref.startsWith('https://') || lowerHref.startsWith('/');
                if (!isSafeProtocol || lowerHref.startsWith('javascript:') || lowerHref.startsWith('data:')) {
                    return linkText; // drop the link, keep text
                }

                return `<a href="${escapeHtml(safeHref)}" class="fw-bold">${linkText}</a>`;
            })
            .replace(/&lt;a\s+[^&]*href="([^"]+)"[^&]*&gt;(.*?)&lt;\/a&gt;/gi, function(_, href, linkText) {
                const safeHref = (href || '').trim();
                const lowerHref = safeHref.toLowerCase();

                const isSafeProtocol = lowerHref.startsWith('http://') || lowerHref.startsWith('https://') || lowerHref.startsWith('/');
                if (!isSafeProtocol || lowerHref.startsWith('javascript:') || lowerHref.startsWith('data:')) {
                    return linkText;
                }

                return `<a href="${escapeHtml(safeHref)}" class="fw-bold">${linkText}</a>`;
            });

        // Bold: **text**
        let html = withLinks.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
        // Italic: *text* (simple, non-greedy)
        html = html.replace(/(^|[\s>_])\*([^*\n]+)\*/g, '$1<em>$2</em>');
        return html;
    }

    /**
     * Backward-compatible alias used by pre-rendered assistant messages.
     * Keeps legacy calls working after the safer renderer rename.
     */
    function renderMarkdownSafe(text) {
        return renderAssistantContent(text);
    }

    /**
     * Build HTML for a chat message.
     * @param {string} role - 'user' or 'assistant'
     * @param {string} content - The message content
     * @param {boolean} allowHtml - If true, allow HTML in content (only for trusted assistant messages)
     * @returns {string} - The HTML string
     */
    function buildMessageHTML(role, content, allowHtml) {
        const isUser = role === 'user';
        const bubbleClass = isUser ? 'bg-primary text-white' : 'bg-light';
        const alignClass = isUser ? 'justify-content-end' : '';
        const time = new Date().toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' });
        const timeClass = isUser ? 'text-white-50' : 'text-muted';
        
        let header = '';
        if (!isUser) {
            header = '<div class="fw-bold text-muted small mb-1"><span class="bi-robot"></span> AI Chef</div>';
        }
        
        // For assistant messages, allow limited HTML/markdown; user content is always escaped.
        const displayContent = (!isUser && allowHtml) ? renderAssistantContent(content) : escapeHtml(content);

        return `
            <div class="chat-message chat-message-${escapeHtml(role)} mb-3">
                <div class="d-flex ${alignClass}">
                    <div class="message-bubble ${bubbleClass} rounded-3 p-3" style="max-width: 80%;">
                        ${header}
                        <div class="message-content" style="white-space: pre-wrap;">${displayContent}</div>
                        <div class="${timeClass} small mt-1">${escapeHtml(time)}</div>
                    </div>
                </div>
            </div>
        `;
    }

    /**
     * Parse the response from the message endpoint.
     * @param {Object} data - The JSON response data
     * @returns {Object} - Parsed data with message and draft info
     */
    function parseDraftResponse(data) {
        if (!data || typeof data !== 'object') {
            return { success: false, error: 'Invalid response' };
        }
        
        if (data.error) {
            return { success: false, error: data.error };
        }
        
        return {
            success: true,
            message: data.message || null,
            draft: data.draft || null
        };
    }

    /**
     * Get CSRF token from cookies or form.
     * @returns {string|null} - The CSRF token or null if not found
     */
    function getCsrfToken() {
        // Check if we're in a browser environment
        if (typeof document === 'undefined') {
            return null;
        }
        
        // Try to get from cookie first
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.startsWith('csrftoken=')) {
                return cookie.substring('csrftoken='.length);
            }
        }
        
        // Fall back to hidden input
        const csrfInput = document.querySelector('input[name="csrfmiddlewaretoken"]');
        if (csrfInput) {
            return csrfInput.value;
        }
        
        return null;
    }

    /**
     * Build HTML for the publish section.
     * @param {Object} draft - Draft object with id, title, publish_url
     * @param {string} csrfToken - CSRF token for the form
     * @returns {string} - The HTML string
     */
    function buildPublishSectionHTML(draft, csrfToken) {
        if (!draft || !draft.id || !draft.publish_url) {
            return '';
        }
        
        const title = escapeHtml(draft.title || 'Your recipe');
        const publishUrl = escapeHtml(draft.publish_url);
        
        return `
            <div id="publish-section" class="alert alert-success d-flex justify-content-between align-items-center mb-4">
                <div>
                    <strong><span class="bi-check-circle"></span> Recipe Ready!</strong>
                    <span class="ms-2">${title} is ready to publish.</span>
                </div>
                <form method="post" action="${publishUrl}" id="publish-form" class="d-inline">
                    <input type="hidden" name="csrfmiddlewaretoken" value="${escapeHtml(csrfToken)}">
                    <button type="submit" class="btn btn-success" id="publish-btn">
                        <span class="bi-upload"></span> Publish Recipe
                    </button>
                </form>
            </div>
        `;
    }

    // Loading status updates

    var loadingStartTime = null;
    var loadingInterval = null;

    var loadingMessages = [
        { time: 0, text: "Searching for recipe ideas..." },
        { time: 2000, text: "Analyzing ingredients and techniques..." },
        { time: 5000, text: "Crafting your personalized recipe..." },
        { time: 8000, text: "Adding finishing touches..." },
        { time: 12000, text: "Almost there..." },
    ];

    function updateLoadingStatus() {
        loadingStartTime = Date.now();
        var statusEl = document.getElementById('loading-status');
        
        if (!statusEl) return;

        // Clear any existing interval
        if (loadingInterval) {
            clearInterval(loadingInterval);
        }

        loadingInterval = setInterval(function() {
            var elapsed = Date.now() - loadingStartTime;
            
            // Find the appropriate message
            var message = loadingMessages[0].text;
            for (var i = loadingMessages.length - 1; i >= 0; i--) {
                if (elapsed >= loadingMessages[i].time) {
                    message = loadingMessages[i].text;
                    break;
                }
            }
            
            statusEl.textContent = message;
        }, 500);
    }

    function stopLoadingStatus() {
        if (loadingInterval) {
            clearInterval(loadingInterval);
            loadingInterval = null;
        }
    }

    // DOM interaction (browser only)

    function initChatbot() {
        const chatForm = document.getElementById('chat-form');
        const chatTranscript = document.getElementById('chat-transcript');
        const loadingIndicator = document.getElementById('loading-indicator');
        const emptyState = document.getElementById('empty-state');
        const sendBtn = document.getElementById('send-btn');
        const promptInput = document.getElementById('prompt');
        const dietaryInput = document.getElementById('dietary_requirements');

        if (!chatForm || !chatTranscript) {
            return; // Elements not found, likely not on the chatbot page
        }

        // Apply markdown rendering to any pre-rendered assistant messages
        const existingAssistantMessages = document.querySelectorAll('.chat-message-assistant .message-content');
        existingAssistantMessages.forEach(function(el) {
            const html = el.innerHTML || '';
            // If server already rendered safe anchors, keep them as-is; otherwise, render markdown safely.
            if (html.includes('<a ')) {
                return; // preserve existing HTML (e.g., publish success link)
            }
            el.innerHTML = renderMarkdownSafe(el.textContent);
        });

        // Handle chat form submission
        chatForm.addEventListener('submit', function(e) {
            e.preventDefault();

            const prompt = promptInput.value.trim();
            const dietary = dietaryInput ? dietaryInput.value.trim() : '';

            if (!prompt) {
                return;
            }

            const csrfToken = getCsrfToken();
            if (!csrfToken) {
                // Fall back to normal form submission
                chatForm.submit();
                return;
            }

            // Hide empty state
            if (emptyState) {
                emptyState.classList.add('d-none');
            }

            // Add user message to transcript (never allow HTML in user content)
            const userContent = prompt + (dietary ? '\n\nDietary requirements: ' + dietary : '');
            chatTranscript.insertAdjacentHTML('beforeend', buildMessageHTML('user', userContent, false));

            // Show loading indicator with progress updates
            if (loadingIndicator) {
                loadingIndicator.classList.remove('d-none');
                // Start progress updates
                updateLoadingStatus();
            }

            // Disable form
            sendBtn.disabled = true;
            promptInput.disabled = true;
            if (dietaryInput) dietaryInput.disabled = true;

            // Scroll to bottom
            chatTranscript.scrollTop = chatTranscript.scrollHeight;

            // Send AJAX request
            fetch(chatForm.action, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken
                },
                body: JSON.stringify({
                    prompt: prompt,
                    dietary_requirements: dietary
                })
            })
            .then(function(response) {
                return response.json().then(function(data) {
                    return { ok: response.ok, data: data };
                });
            })
            .then(function(result) {
                // Hide loading indicator and stop status updates
                stopLoadingStatus();
                if (loadingIndicator) {
                    loadingIndicator.classList.add('d-none');
                }

                const parsed = parseDraftResponse(result.data);

                if (!parsed.success) {
                    // Add error message (no HTML needed)
                    chatTranscript.insertAdjacentHTML('beforeend', 
                        buildMessageHTML('assistant', 'Sorry, an error occurred: ' + (parsed.error || 'Unknown error'), false)
                    );
                } else {
                    // Add assistant message (recipe text, allow markdown formatting like **bold**)
                    if (parsed.message && parsed.message.content) {
                        chatTranscript.insertAdjacentHTML('beforeend', 
                            buildMessageHTML('assistant', parsed.message.content, true)
                        );
                    }

                    // Add/update publish section
                    if (parsed.draft) {
                        const existingPublish = document.getElementById('publish-section');
                        if (existingPublish) {
                            existingPublish.remove();
                        }
                        
                        const publishHTML = buildPublishSectionHTML(parsed.draft, csrfToken);
                        chatTranscript.insertAdjacentHTML('afterend', publishHTML);
                        
                        // Attach publish handler to new form
                        attachPublishHandler();
                    }
                }

                // Clear form and re-enable
                promptInput.value = '';
                if (dietaryInput) dietaryInput.value = '';
                sendBtn.disabled = false;
                promptInput.disabled = false;
                if (dietaryInput) dietaryInput.disabled = false;

                // Scroll to bottom
                chatTranscript.scrollTop = chatTranscript.scrollHeight;
            })
            .catch(function(error) {
                console.error('Chat request failed:', error);
                
                // Hide loading indicator and stop status updates
                stopLoadingStatus();
                if (loadingIndicator) {
                    loadingIndicator.classList.add('d-none');
                }

                // Re-enable form
                sendBtn.disabled = false;
                promptInput.disabled = false;
                if (dietaryInput) dietaryInput.disabled = false;

                // Fall back to normal form submission
                chatForm.submit();
            });
        });

        // Attach publish handler if publish form exists
        attachPublishHandler();
    }

    function attachPublishHandler() {
        const publishForm = document.getElementById('publish-form');
        if (!publishForm) {
            return;
        }

        publishForm.addEventListener('submit', function(e) {
            e.preventDefault();

            const publishBtn = document.getElementById('publish-btn');
            const csrfToken = getCsrfToken();

            if (!csrfToken) {
                publishForm.submit();
                return;
            }

            // Disable button
            if (publishBtn) {
                publishBtn.disabled = true;
                publishBtn.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Publishing...';
            }

            fetch(publishForm.action, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken
                },
                body: JSON.stringify({})
            })
            .then(function(response) {
                return response.json().then(function(data) {
                    return { ok: response.ok, data: data };
                });
            })
            .then(function(result) {
                if (result.ok && result.data.success) {
                    // Show success message with a guaranteed clickable hyperlink
                    const chatTranscript = document.getElementById('chat-transcript');
                    const wrapper = document.createElement('div');
                    wrapper.className = 'chat-message chat-message-assistant mb-3';

                    const outer = document.createElement('div');
                    outer.className = 'd-flex';

                    const bubble = document.createElement('div');
                    bubble.className = 'message-bubble bg-light rounded-3 p-3';
                    bubble.style.maxWidth = '80%';

                    const header = document.createElement('div');
                    header.className = 'fw-bold text-muted small mb-1';
                    header.innerHTML = '<span class="bi-robot"></span> AI Chef';

                    const body = document.createElement('div');
                    body.className = 'message-content';
                    body.style.whiteSpace = 'pre-wrap';
                    body.append('🎉 Recipe published successfully! View it ');
                    const link = document.createElement('a');
                    link.className = 'fw-bold';
                    link.href = result.data.recipe_url;
                    link.target = '_blank';
                    link.rel = 'noopener noreferrer';
                    link.textContent = 'here';
                    body.append(link);
                    body.append('.');

                    const time = document.createElement('div');
                    time.className = 'text-muted small mt-1';
                    time.textContent = new Date().toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' });

                    bubble.append(header, body, time);
                    outer.appendChild(bubble);
                    wrapper.appendChild(outer);

                    chatTranscript.appendChild(wrapper);
                    chatTranscript.scrollTop = chatTranscript.scrollHeight;

                    // Disable publish button now that it's done
                    if (publishBtn) {
                        publishBtn.disabled = true;
                        publishBtn.innerHTML = '<span class="bi-check-circle"></span> Published';
                    }
                } else {
                    // Show error
                    alert('Failed to publish: ' + (result.data.error || 'Unknown error'));
                    if (publishBtn) {
                        publishBtn.disabled = false;
                        publishBtn.innerHTML = '<span class="bi-upload"></span> Publish Recipe';
                    }
                }
            })
            .catch(function(error) {
                console.error('Publish request failed:', error);
                // Fall back to normal form submission
                publishForm.submit();
            });
        });
    }

    // Initialize when DOM is ready
    if (typeof document !== 'undefined') {
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', initChatbot);
        } else {
            initChatbot();
        }
    }

    // Module exports (for Node.js testing)

    if (typeof module !== 'undefined' && module.exports) {
        module.exports = {
            escapeHtml: escapeHtml,
            buildMessageHTML: buildMessageHTML,
            parseDraftResponse: parseDraftResponse,
            getCsrfToken: getCsrfToken,
            buildPublishSectionHTML: buildPublishSectionHTML
        };
    }

})();
