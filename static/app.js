/* -------------------------------------------------------------
 * app.js
 * Chat Interaction Handlers & Markdown Parser
 * ------------------------------------------------------------- */

document.addEventListener("DOMContentLoaded", () => {
    const inputForm = document.getElementById("input-form");
    const chatInput = document.getElementById("chat-input");
    const chatViewport = document.getElementById("chat-viewport");
    const welcomeScreen = document.getElementById("welcome-screen");
    const clearChatBtn = document.getElementById("clear-chat-btn");

    // Configure marked options if available
    if (typeof marked !== "undefined") {
        marked.setOptions({
            breaks: true,
            sanitize: false, // Allows HTML entities or tags safely if desired
        });
    }

    // Handles form submission
    inputForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        
        const messageText = chatInput.value.trim();
        if (!messageText) return;

        // Clear input
        chatInput.value = "";

        // Hide welcome screen if showing
        if (welcomeScreen) {
            welcomeScreen.style.display = "none";
        }

        // 1. Add User Message
        appendMessage("user", messageText);

        // 2. Add Typing Indicator
        const typingIndicator = appendTypingIndicator();

        // 3. Request API response from Flask server
        try {
            const response = await fetch("/api/chat", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({ message: messageText }),
            });

            if (!response.ok) {
                throw new Error(`Server returned status ${response.status}`);
            }

            const data = await response.json();
            
            // Remove typing indicator
            typingIndicator.remove();

            // 4. Add Bot Message
            if (data.answer) {
                appendMessage("bot", data.answer);
            } else {
                appendMessage("bot", "No response content received from server.");
            }

        } catch (error) {
            console.error("Chat request failed:", error);
            typingIndicator.remove();
            appendMessage("bot", `⚠️ Error: Could not reach the server. Details: ${error.message}`);
            showToast("Connection failed", "error");
        }
    });

    // Clear chat handler
    clearChatBtn.addEventListener("click", () => {
        // Clear message DOM elements
        const messages = chatViewport.querySelectorAll(".message");
        messages.forEach(msg => msg.remove());
        
        // Restore welcome screen
        if (welcomeScreen) {
            welcomeScreen.style.display = "flex";
        }
        
        showToast("Conversation history cleared");
    });

    /**
     * Appends a message bubble to the viewport.
     * @param {string} sender - 'user' or 'bot'
     * @param {string} text - Message text (supports Markdown for bot)
     */
    function appendMessage(sender, text) {
        const messageContainer = document.createElement("div");
        messageContainer.classList.add("message", sender);

        const bubble = document.createElement("div");
        bubble.classList.add("message-bubble");

        // Parse markdown for bot, escape HTML for user
        if (sender === "bot" && typeof marked !== "undefined") {
            bubble.innerHTML = marked.parse(text);
        } else {
            bubble.textContent = text;
        }

        const meta = document.createElement("div");
        meta.classList.add("message-meta");
        const timeString = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        meta.textContent = `${sender === "user" ? "You" : "Assistant"} • ${timeString}`;

        messageContainer.appendChild(bubble);
        messageContainer.appendChild(meta);
        chatViewport.appendChild(messageContainer);

        // Auto scroll to bottom
        chatViewport.scrollTop = chatViewport.scrollHeight;
    }

    /**
     * Appends a loading/typing indicator to the viewport.
     * @returns {HTMLElement} - The created typing indicator element.
     */
    function appendTypingIndicator() {
        const container = document.createElement("div");
        container.classList.add("message", "bot");

        const bubble = document.createElement("div");
        bubble.classList.add("message-bubble");

        const indicator = document.createElement("div");
        indicator.classList.add("typing-indicator");
        indicator.innerHTML = `
            <span class="typing-dot"></span>
            <span class="typing-dot"></span>
            <span class="typing-dot"></span>
        `;

        bubble.appendChild(indicator);
        container.appendChild(bubble);
        chatViewport.appendChild(container);

        chatViewport.scrollTop = chatViewport.scrollHeight;
        return container;
    }

    /**
     * Shows a temporary toast notification in the UI.
     * @param {string} message - Notification text
     * @param {string} type - 'success' or 'error'
     */
    function showToast(message, type = "success") {
        const toast = document.getElementById("toast-notification");
        const toastMsg = document.getElementById("toast-message");
        const toastIcon = toast.querySelector(".toast-icon");

        toastMsg.textContent = message;
        toastIcon.textContent = type === "success" ? "✨" : "⚠️";
        
        toast.style.display = "flex";

        setTimeout(() => {
            toast.style.display = "none";
        }, 3000);
    }
});
