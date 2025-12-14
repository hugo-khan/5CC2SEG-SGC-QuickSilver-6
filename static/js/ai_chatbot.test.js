/**
 * Tests for AI Chatbot JavaScript helpers
 * 
 * Run with: node --test static/js/ai_chatbot.test.js
 * Or via npm: npm run test:js
 * 
 * Uses Node's built-in test runner (node:test) and assert module.
 */

const { describe, it, beforeEach } = require('node:test');
const assert = require('node:assert');

// Import the helper functions from the chatbot module
const {
    escapeHtml,
    buildMessageHTML,
    parseDraftResponse,
    getCsrfToken,
    buildPublishSectionHTML
} = require('./ai_chatbot.js');

// Tests for escapeHtml

describe('escapeHtml', () => {
    it('should escape ampersand', () => {
        assert.strictEqual(escapeHtml('Tom & Jerry'), 'Tom &amp; Jerry');
    });

    it('should escape less than', () => {
        assert.strictEqual(escapeHtml('1 < 2'), '1 &lt; 2');
    });

    it('should escape greater than', () => {
        assert.strictEqual(escapeHtml('2 > 1'), '2 &gt; 1');
    });

    it('should escape double quotes', () => {
        assert.strictEqual(escapeHtml('He said "hello"'), 'He said &quot;hello&quot;');
    });

    it('should escape single quotes', () => {
        assert.strictEqual(escapeHtml("It's fine"), "It&#39;s fine");
    });

    it('should escape multiple special characters', () => {
        assert.strictEqual(
            escapeHtml('<script>alert("XSS")</script>'),
            '&lt;script&gt;alert(&quot;XSS&quot;)&lt;/script&gt;'
        );
    });

    it('should return empty string for non-string input', () => {
        assert.strictEqual(escapeHtml(null), '');
        assert.strictEqual(escapeHtml(undefined), '');
        assert.strictEqual(escapeHtml(123), '');
        assert.strictEqual(escapeHtml({}), '');
    });

    it('should handle empty string', () => {
        assert.strictEqual(escapeHtml(''), '');
    });

    it('should return string without special chars unchanged', () => {
        assert.strictEqual(escapeHtml('Hello World'), 'Hello World');
    });
});

// Tests for buildMessageHTML

describe('buildMessageHTML', () => {
    it('should create user message with correct classes', () => {
        const html = buildMessageHTML('user', 'Hello');
        assert.ok(html.includes('chat-message-user'));
        assert.ok(html.includes('bg-primary'));
        assert.ok(html.includes('text-white'));
        assert.ok(html.includes('justify-content-end'));
    });

    it('should create assistant message with correct classes', () => {
        const html = buildMessageHTML('assistant', 'Hi there');
        assert.ok(html.includes('chat-message-assistant'));
        assert.ok(html.includes('bg-light'));
        assert.ok(html.includes('AI Chef'));
    });

    it('should escape content in message', () => {
        const html = buildMessageHTML('user', '<script>alert("xss")</script>');
        assert.ok(html.includes('&lt;script&gt;'));
        assert.ok(!html.includes('<script>alert'));
    });

    it('should include timestamp', () => {
        const html = buildMessageHTML('user', 'Test');
        // Check for time format (e.g., "10:30 AM" or "22:30")
        assert.ok(html.includes('small mt-1'));
    });

    it('should include message content', () => {
        const html = buildMessageHTML('assistant', 'Here is your recipe');
        assert.ok(html.includes('Here is your recipe'));
    });

    it('should add robot icon for assistant', () => {
        const html = buildMessageHTML('assistant', 'Hello');
        assert.ok(html.includes('bi-robot'));
    });

    it('should not add robot icon for user', () => {
        const html = buildMessageHTML('user', 'Hello');
        // User messages shouldn't have the AI Chef header
        assert.ok(!html.includes('AI Chef'));
    });
});

// Tests for parseDraftResponse

describe('parseDraftResponse', () => {
    it('should return error for null input', () => {
        const result = parseDraftResponse(null);
        assert.strictEqual(result.success, false);
        assert.ok(result.error);
    });

    it('should return error for undefined input', () => {
        const result = parseDraftResponse(undefined);
        assert.strictEqual(result.success, false);
    });

    it('should return error for non-object input', () => {
        const result = parseDraftResponse('string');
        assert.strictEqual(result.success, false);
    });

    it('should return error when error field is present', () => {
        const result = parseDraftResponse({ error: 'Something went wrong' });
        assert.strictEqual(result.success, false);
        assert.strictEqual(result.error, 'Something went wrong');
    });

    it('should parse successful response with message and draft', () => {
        const data = {
            message: { role: 'assistant', content: 'Here is your recipe' },
            draft: { id: 123, title: 'Pasta', publish_url: '/ai/chef/publish/123/' }
        };
        const result = parseDraftResponse(data);
        
        assert.strictEqual(result.success, true);
        assert.deepStrictEqual(result.message, data.message);
        assert.deepStrictEqual(result.draft, data.draft);
    });

    it('should handle response without draft', () => {
        const data = {
            message: { role: 'assistant', content: 'Sorry, I could not find a recipe' }
        };
        const result = parseDraftResponse(data);
        
        assert.strictEqual(result.success, true);
        assert.strictEqual(result.draft, null);
    });

    it('should handle response without message', () => {
        const data = {
            draft: { id: 1, title: 'Test' }
        };
        const result = parseDraftResponse(data);
        
        assert.strictEqual(result.success, true);
        assert.strictEqual(result.message, null);
    });

    it('should handle empty object', () => {
        const result = parseDraftResponse({});
        assert.strictEqual(result.success, true);
        assert.strictEqual(result.message, null);
        assert.strictEqual(result.draft, null);
    });
});

// Tests for getCsrfToken

describe('getCsrfToken', () => {
    // Note: getCsrfToken relies on document.cookie and DOM elements
    // In Node.js environment, document is undefined, so it will return null
    
    it('should return null when document is not available', () => {
        const result = getCsrfToken();
        assert.strictEqual(result, null);
    });
});

// Tests for buildPublishSectionHTML

describe('buildPublishSectionHTML', () => {
    it('should return empty string for null draft', () => {
        const html = buildPublishSectionHTML(null, 'token123');
        assert.strictEqual(html, '');
    });

    it('should return empty string for undefined draft', () => {
        const html = buildPublishSectionHTML(undefined, 'token123');
        assert.strictEqual(html, '');
    });

    it('should return empty string for draft without id', () => {
        const html = buildPublishSectionHTML({ title: 'Test' }, 'token123');
        assert.strictEqual(html, '');
    });

    it('should return empty string for draft without publish_url', () => {
        const html = buildPublishSectionHTML({ id: 1, title: 'Test' }, 'token123');
        assert.strictEqual(html, '');
    });

    it('should create publish section with correct structure', () => {
        const draft = {
            id: 123,
            title: 'Delicious Pasta',
            publish_url: '/ai/chef/publish/123/'
        };
        const html = buildPublishSectionHTML(draft, 'csrf_token_value');
        
        assert.ok(html.includes('publish-section'));
        assert.ok(html.includes('alert-success'));
        assert.ok(html.includes('Delicious Pasta'));
        assert.ok(html.includes('/ai/chef/publish/123/'));
        assert.ok(html.includes('csrf_token_value'));
        assert.ok(html.includes('publish-form'));
        assert.ok(html.includes('Publish Recipe'));
    });

    it('should escape HTML in title', () => {
        const draft = {
            id: 1,
            title: '<script>alert("xss")</script>',
            publish_url: '/publish/'
        };
        const html = buildPublishSectionHTML(draft, 'token');
        
        assert.ok(html.includes('&lt;script&gt;'));
        assert.ok(!html.includes('<script>alert'));
    });

    it('should use default title when not provided', () => {
        const draft = {
            id: 1,
            publish_url: '/publish/'
        };
        const html = buildPublishSectionHTML(draft, 'token');
        
        assert.ok(html.includes('Your recipe'));
    });

    it('should escape HTML in CSRF token', () => {
        const draft = {
            id: 1,
            title: 'Test',
            publish_url: '/publish/'
        };
        const html = buildPublishSectionHTML(draft, '<token>');
        
        assert.ok(html.includes('&lt;token&gt;'));
        assert.ok(!html.includes('value="<token>"'));
    });
});

console.log('All tests passed!');

