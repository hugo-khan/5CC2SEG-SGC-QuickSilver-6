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

    // =============================================================================
    // Helper Functions (exported for testing)
    // =============================================================================

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
     * Build HTML for a chat message.
     * @param {string} role - 'user' or 'assistant'
     * @param {string} content - The message content
     * @returns {string} - The HTML string
     */
    function buildMessageHTML(role, content) {
        const isUser = role === 'user';
        const bubbleClass = isUser ? 'bg-primary text-white' : 'bg-light';
        const alignClass = isUser ? 'justify-content-end' : '';
        const time = new Date().toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' });
        const timeClass = isUser ? 'text-white-50' : 'text-muted';
        
        let header = '';
        if (!isUser) {
            header = '<div class="fw-bold text-muted small mb-1"><span class="bi-robot"></span> AI Chef</div>';
        }

        return `
            <div class="chat-message chat-message-${escapeHtml(role)} mb-3">
                <div class="d-flex ${alignClass}">
                    <div class="message-bubble ${bubbleClass} rounded-3 p-3" style="max-width: 80%;">
                        ${header}
                        <div class="message-content" style="white-space: pre-wrap;">${escapeHtml(content)}</div>
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

    // =============================================================================
    // DOM Interaction (only runs in browser)
    // =============================================================================

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

            // Add user message to transcript
            const userContent = prompt + (dietary ? '\n\nDietary requirements: ' + dietary : '');
            chatTranscript.insertAdjacentHTML('beforeend', buildMessageHTML('user', userContent));

            // Show loading indicator
            if (loadingIndicator) {
                loadingIndicator.classList.remove('d-none');
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
                // Hide loading indicator
                if (loadingIndicator) {
                    loadingIndicator.classList.add('d-none');
                }

                const parsed = parseDraftResponse(result.data);

                if (!parsed.success) {
                    // Add error message
                    chatTranscript.insertAdjacentHTML('beforeend', 
                        buildMessageHTML('assistant', 'Sorry, an error occurred: ' + (parsed.error || 'Unknown error'))
                    );
                } else {
                    // Add assistant message
                    if (parsed.message && parsed.message.content) {
                        chatTranscript.insertAdjacentHTML('beforeend', 
                            buildMessageHTML('assistant', parsed.message.content)
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
                
                // Hide loading indicator
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
                    // Redirect to the published recipe
                    window.location.href = result.data.recipe_url;
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

    // =============================================================================
    // Module Exports (for Node.js testing)
    // =============================================================================

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

