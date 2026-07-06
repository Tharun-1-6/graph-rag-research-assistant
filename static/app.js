/* -------------------------------------------------------------
 * app.js
 * Chat Interaction Handlers & Interactive Knowledge Graph View
 * ------------------------------------------------------------- */

document.addEventListener("DOMContentLoaded", () => {
    const inputForm = document.getElementById("input-form");
    const chatInput = document.getElementById("chat-input");
    const chatViewport = document.getElementById("chat-viewport");
    const welcomeScreen = document.getElementById("welcome-screen");
    const clearChatBtn = document.getElementById("clear-chat-btn");
    const modelSelect = document.getElementById("model-select");

    // Tab toggling DOM references
    const tabChat = document.getElementById("tab-chat");
    const tabGraph = document.getElementById("tab-graph");
    const panelChat = document.getElementById("panel-chat");
    const panelGraph = document.getElementById("panel-graph");

    // Vis.js Graph properties
    let network = null;
    let nodesDataSet = null;
    let edgesDataSet = null;
    let fullGraphData = null; // Cache full network response
    let activeHighlightPath = null; // Store active query response path metadata

    // Configure marked options if available
    if (typeof marked !== "undefined") {
        marked.setOptions({
            breaks: true,
            sanitize: false,
        });
    }

    // Tab Switching Click Handlers
    tabChat.addEventListener("click", () => {
        tabGraph.classList.remove("active");
        tabChat.classList.add("active");
        panelGraph.style.display = "none";
        panelChat.style.display = "flex";
    });

    tabGraph.addEventListener("click", () => {
        tabChat.classList.remove("active");
        tabGraph.classList.add("active");
        panelChat.style.display = "none";
        panelGraph.style.display = "flex";
        
        // Lazy-load overall network structure if not initialized
        if (!network) {
            initializeGlobalGraph();
        } else {
            // Resize canvas context on visibility change
            network.setSize("100%", "100%");
            network.fit();
        }
    });

    // Handles form submission
    inputForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        
        const messageText = chatInput.value.trim();
        if (!messageText) return;

        chatInput.value = "";

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
                body: JSON.stringify({ 
                    message: messageText,
                    model: modelSelect.value
                }),
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

            // 5. If query returned a sub-graph trace, store it for visualization highlight
            if (data.path_nodes && data.path_nodes.length > 0) {
                activeHighlightPath = {
                    nodes: data.path_nodes,
                    edges: data.path_edges || []
                };
                
                // Show clear highlights button
                document.getElementById("btn-clear-highlights").style.display = "inline-block";
                
                // Prompt user visually
                showToast("Graph path retrieved! Switch to Graph Explorer tab to view path trace.");
                
                // If graph is already loaded, apply highlights immediately
                if (network) {
                    highlightGraphSearchPath();
                }
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
        const messages = chatViewport.querySelectorAll(".message");
        messages.forEach(msg => msg.remove());
        
        if (welcomeScreen) {
            welcomeScreen.style.display = "flex";
        }
        
        showToast("Conversation history cleared");
    });

    /**
     * Appends a message bubble to the viewport.
     */
    function appendMessage(sender, text) {
        const messageContainer = document.createElement("div");
        messageContainer.classList.add("message", sender);

        const bubble = document.createElement("div");
        bubble.classList.add("message-bubble");

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

        chatViewport.scrollTop = chatViewport.scrollHeight;
    }

    /**
     * Appends a loading/typing indicator to the viewport.
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
        }, 4000);
    }

    // Node Group Colors configuration
    const NODE_COLORS = {
        "Paper": "#f87171",       // Soft Neon Red
        "Author": "#60a5fa",      // Soft Neon Blue
        "Method": "#34d399",      // Soft Neon Green
        "Dataset": "#c084fc",     // Soft Neon Purple
        "Institution": "#fbbf24", // Yellow
        "Metric": "#2dd4bf",      // Teal
        "Task": "#fb923c",        // Orange
        "Topic": "#9ca3af",       // Gray
    };

    /**
     * Fetch, map and render the full NetworkX knowledge graph on Vis.js Network Canvas.
     */
    async function initializeGlobalGraph() {
        const canvasContainer = document.getElementById("graph-canvas-container");
        canvasContainer.innerHTML = `<div style="display:flex;justify-content:center;align-items:center;height:100%;color:var(--text-secondary);font-size:0.95rem;">🕸️ Rendering knowledge graph structure...</div>`;
        
        try {
            const response = await fetch("/api/graph/data");
            if (!response.ok) throw new Error("Failed to load global graph dataset.");
            fullGraphData = await response.json();
            
            canvasContainer.innerHTML = ""; // Clear loader
            
            // Transform node properties for VisJS formatting
            const visNodes = fullGraphData.nodes.map(node => {
                const groupColor = NODE_COLORS[node.type] || "#a3a3a3";
                const size = 15 + Math.min(node.degree * 2.5, 45);
                
                // Add HTML hover tooltips like the reference graph.html
                const hoverTooltip = `
                <div style="font-family: Arial, sans-serif; font-size: 13px; color: white; background: #222; padding: 10px; border-radius: 5px; border: 1px solid #444;">
                    <b>ID:</b> ${node.id}<br/>
                    <b>Name:</b> ${node.label}<br/>
                    <b>Type:</b> ${node.type}<br/>
                    <b>Connections:</b> ${node.degree}<br/>
                    <b>Description:</b> ${node.description || "No description available."}
                </div>
                `;
                
                return {
                    id: node.id,
                    label: node.label,
                    type: node.type,
                    description: node.description,
                    degree: node.degree,
                    size: size,
                    title: hoverTooltip,
                    shape: "dot",
                    font: { color: "white", size: 12, face: "Inter" },
                    color: {
                        background: "#111827",
                        border: groupColor,
                        highlight: {
                            background: groupColor,
                            border: "#ffffff"
                        }
                    },
                    borderWidth: 2,
                    borderWidthSelected: 4
                };
            });

            // Transform edges for VisJS formatting
            const visEdges = fullGraphData.edges.map((edge, idx) => {
                return {
                    id: `edge_${idx}`,
                    from: edge.from,
                    to: edge.to,
                    label: edge.relationship,
                    title: `Relationship: ${edge.relationship} (Confidence: ${edge.confidence || 1.0})`,
                    font: { color: "#9ca3af", size: 9, align: "middle", face: "Inter" },
                    color: { color: "rgba(99, 102, 241, 0.25)", highlight: "#6366f1" },
                    arrows: { to: { enabled: true, scaleFactor: 0.5 } },
                    smooth: { type: "continuous" }
                };
            });

            nodesDataSet = new vis.DataSet(visNodes);
            edgesDataSet = new vis.DataSet(visEdges);

            const data = {
                nodes: nodesDataSet,
                edges: edgesDataSet
            };

            const options = {
                physics: {
                    solver: "forceAtlas2Based",
                    forceAtlas2Based: {
                        gravitationalConstant: -180,
                        centralGravity: 0.005,
                        springLength: 180,
                        springConstant: 0.05,
                        damping: 0.4,
                        avoidOverlap: 1.0
                    },
                    stabilization: { 
                        enabled: true,
                        fit: true,
                        iterations: 1000, 
                        updateInterval: 50 
                    }
                },
                nodes: {
                    scaling: {
                        min: 15,
                        max: 60
                    }
                },
                edges: {
                    scaling: {
                        min: 1,
                        max: 5
                    },
                    smooth: {
                        enabled: true,
                        type: "dynamic",
                        roundness: 0.5
                    }
                },
                interaction: {
                    hover: true,
                    dragNodes: true,
                    dragView: true,
                    zoomView: true
                }
            };

            network = new vis.Network(canvasContainer, data, options);

            // Click handling - update details sidebar and center camera view on selected node
            network.on("click", (params) => {
                if (params.nodes.length > 0) {
                    const selectedId = params.nodes[0];
                    const selectedNode = visNodes.find(n => String(n.id) === String(selectedId));
                    if (selectedNode) {
                        displayNodeDetails(selectedNode);
                        
                        // Pin clicked node location temporarily to prevent physics drift displacement
                        nodesDataSet.update({ id: selectedId, fixed: { x: true, y: true } });

                        // Center and zoom viewport onto clicked node smoothly, offsetting slightly left to clear the 320px sidebar
                        network.focus(selectedId, {
                            scale: 0.85,
                            offset: { x: -80, y: 0 },
                            animation: {
                                duration: 800,
                                easingFunction: "easeInOutQuad"
                            }
                        });
                    }
                } else {
                    // Unpin all nodes when clicking empty canvas space to restore elastic physics
                    if (nodesDataSet) {
                        const allNodes = nodesDataSet.get();
                        const unpinned = allNodes.map(node => ({ id: node.id, fixed: { x: false, y: false } }));
                        nodesDataSet.update(unpinned);
                    }

                    resetNodeDetails();
                    
                    // Smoothly fit whole graph layout back into viewport
                    network.fit({
                        animation: {
                            duration: 800,
                            easingFunction: "easeInOutQuad"
                        }
                    });
                }
            });

            // If a search trace was retrieved while we were on chat tab, highlight it now
            if (activeHighlightPath) {
                highlightGraphSearchPath();
            }

            // Register toolbar controls
            document.getElementById("btn-fit-graph").onclick = () => network.fit();
            
            let physicsEnabled = true;
            document.getElementById("btn-toggle-physics").onclick = () => {
                physicsEnabled = !physicsEnabled;
                network.setOptions({ physics: physicsEnabled });
                document.getElementById("btn-toggle-physics").textContent = physicsEnabled ? "Freeze Physics" : "Resume Physics";
                showToast(physicsEnabled ? "Physics simulation active" : "Physics simulation suspended");
            };

            document.getElementById("btn-clear-highlights").onclick = () => {
                resetGraphHighlights();
            };

            // Implement type filtering logic
            document.getElementById("graph-type-filter").onchange = (e) => {
                const selectedType = e.target.value;
                if (!nodesDataSet) return;

                const allNodes = nodesDataSet.get();
                const updatedNodes = allNodes.map(node => {
                    const isMatched = (selectedType === "all" || node.type === selectedType);
                    const baseColor = NODE_COLORS[node.type] || "#a3a3a3";

                    return {
                        id: node.id,
                        color: {
                            background: isMatched ? "#111827" : "rgba(17, 24, 39, 0.1)",
                            border: isMatched ? baseColor : "rgba(255, 255, 255, 0.05)"
                        },
                        font: {
                            color: isMatched ? "#f3f4f6" : "rgba(255, 255, 255, 0.15)"
                        }
                    };
                });

                nodesDataSet.update(updatedNodes);
                showToast(selectedType === "all" ? "Showing all node types" : `Filtering for ${selectedType} nodes`);
            };

        } catch (err) {
            console.error(err);
            canvasContainer.innerHTML = `<div style="display:flex;justify-content:center;align-items:center;height:100%;color:#ef4444;font-size:0.95rem;">⚠️ Failed to load Knowledge Graph visualization: ${err.message}</div>`;
        }
    }

    /**
     * Highlights only the nodes and edges traversed during the last query execution.
     * Grays out everything else to focus on search lineage.
     */
    function highlightGraphSearchPath() {
        if (!network || !nodesDataSet || !edgesDataSet || !activeHighlightPath) return;

        const pathNodeIds = new Set(activeHighlightPath.nodes.map(n => n.id));
        
        // Vis edges don't always have ID mapped direct from backend, search matching from/to pairs
        const pathEdges = activeHighlightPath.edges;

        // 1. Update node appearances
        const allNodes = nodesDataSet.get();
        const updatedNodes = allNodes.map(node => {
            const isHighlighted = pathNodeIds.has(node.id);
            const baseColor = NODE_COLORS[node.type] || "#a3a3a3";
            
            return {
                id: node.id,
                color: {
                    background: isHighlighted ? baseColor : "#0d111d",
                    border: isHighlighted ? "#ffffff" : "rgba(255, 255, 255, 0.05)",
                },
                font: {
                    color: isHighlighted ? "#ffffff" : "rgba(255,255,255,0.15)"
                },
                shadow: isHighlighted ? { enabled: true, color: baseColor, size: 10 } : { enabled: false }
            };
        });
        nodesDataSet.update(updatedNodes);

        // 2. Update edge appearances
        const allEdges = edgesDataSet.get();
        const updatedEdges = allEdges.map(edge => {
            // Check if this edge is in path
            const isInPath = pathEdges.some(pe => 
                (pe.source === edge.from && pe.target === edge.to) ||
                (pe.source === edge.to && pe.target === edge.from)
            );

            return {
                id: edge.id,
                color: {
                    color: isInPath ? "#6366f1" : "rgba(255, 255, 255, 0.02)",
                },
                font: {
                    color: isInPath ? "#818cf8" : "rgba(255, 255, 255, 0.02)"
                },
                width: isInPath ? 3 : 1
            };
        });
        edgesDataSet.update(updatedEdges);

        // Focus camera on first seed node in path
        if (activeHighlightPath.nodes.length > 0) {
            network.focus(activeHighlightPath.nodes[0].id, {
                scale: 0.9,
                animation: { duration: 1000, easingFunction: "easeInOutQuad" }
            });
        }
    }

    /**
     * Restore original visualization look.
     */
    function resetGraphHighlights() {
        if (!network || !nodesDataSet || !edgesDataSet) return;

        const allNodes = nodesDataSet.get();
        const updatedNodes = allNodes.map(node => {
            const baseColor = NODE_COLORS[node.type] || "#a3a3a3";
            return {
                id: node.id,
                color: {
                    background: "#111827",
                    border: baseColor
                },
                font: {
                    color: "#f3f4f6"
                },
                shadow: { enabled: false }
            };
        });
        nodesDataSet.update(updatedNodes);

        const allEdges = edgesDataSet.get();
        const updatedEdges = allEdges.map(edge => {
            return {
                id: edge.id,
                color: {
                    color: "rgba(99, 102, 241, 0.2)"
                },
                font: {
                    color: "#9ca3af"
                },
                width: 1
            };
        });
        edgesDataSet.update(updatedEdges);

        activeHighlightPath = null;
        document.getElementById("btn-clear-highlights").style.display = "none";
        showToast("Search highlights cleared. Displaying full graph.");
        network.fit();
    }

    let currentSelectedNode = null;

    /**
     * Populate side pane with attributes of selected node.
     */
    function displayNodeDetails(node) {
        currentSelectedNode = node;
        document.getElementById("sidebar-empty-state").style.display = "none";
        
        const detailsContent = document.getElementById("sidebar-node-content");
        detailsContent.style.display = "block";

        document.getElementById("detail-node-name").textContent = node.label;
        
        const badge = document.getElementById("detail-node-type");
        badge.textContent = node.type;
        badge.style.borderColor = NODE_COLORS[node.type] || "#a3a3a3";
        badge.style.color = NODE_COLORS[node.type] || "#a3a3a3";

        document.getElementById("detail-node-connections").textContent = node.degree;
        
        const descField = document.getElementById("detail-node-desc");
        
        // Auto-trigger generation if description is a default placeholder
        const isPlaceholder = !node.description || 
                             node.description.startsWith("Entity Node of type") || 
                             node.description === "No description available.";
                             
        if (isPlaceholder) {
            descField.innerHTML = `<i>🪄 Auto-generating summary details...</i>`;
            autoGenerateNodeDescription(node, descField);
        } else {
            descField.textContent = node.description;
        }

        // Reset and prime sidebar chat workspace
        const sViewport = document.getElementById("sidebar-chat-viewport");
        sViewport.innerHTML = `<div class="sidebar-chat-msg system">Ask a question about ${node.label}</div>`;
    }

    /**
     * Call the backend generator API to write node descriptions.
     */
    async function autoGenerateNodeDescription(node, descField) {
        try {
            const response = await fetch("/api/graph/generate_description", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    node_id: node.id,
                    type: node.type,
                    label: node.label
                })
            });
            
            if (!response.ok) throw new Error("Metadata generation failed.");
            
            const data = await response.json();
            if (data.description) {
                descField.textContent = data.description;
                node.description = data.description;
                
                // Update properties in VisJS dataset in-memory cache
                if (nodesDataSet) {
                    nodesDataSet.update({
                        id: node.id,
                        description: data.description
                    });
                }
            } else {
                throw new Error("No description returned.");
            }
        } catch (err) {
            console.error(err);
            descField.textContent = `Entity Node of type ${node.type}`;
            showToast("Failed to auto-generate description", "error");
        }
    }

    // Sidebar Chat Submit Handler
    const sidebarChatForm = document.getElementById("sidebar-chat-form");
    const sidebarChatInput = document.getElementById("sidebar-chat-input");
    const sidebarChatViewport = document.getElementById("sidebar-chat-viewport");
    const sidebarModelSelect = document.getElementById("sidebar-model-select");

    sidebarChatForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        if (!currentSelectedNode) return;

        const queryText = sidebarChatInput.value.trim();
        if (!queryText) return;

        sidebarChatInput.value = "";

        // Append user query bubble
        appendSidebarMessage("user", queryText);

        // Add loading state
        const loadingIndicator = document.createElement("div");
        loadingIndicator.classList.add("sidebar-chat-msg", "bot");
        loadingIndicator.innerHTML = `<i>Thinking...</i>`;
        sidebarChatViewport.appendChild(loadingIndicator);
        sidebarChatViewport.scrollTop = sidebarChatViewport.scrollHeight;

        try {
            const response = await fetch("/api/graph/chat", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    node_id: currentSelectedNode.id,
                    type: currentSelectedNode.type,
                    label: currentSelectedNode.label,
                    message: queryText,
                    model: sidebarModelSelect.value
                })
            });

            loadingIndicator.remove();

            const data = await response.json();
            if (!response.ok) {
                throw new Error(data.error || "Graph query failed.");
            }

            if (data.answer) {
                appendSidebarMessage("bot", data.answer);
            } else {
                appendSidebarMessage("bot", "No response content received.");
            }
        } catch (err) {
            if (typeof loadingIndicator !== 'undefined' && loadingIndicator.parentNode) {
                loadingIndicator.remove();
            }
            appendSidebarMessage("bot", `⚠️ Error: ${err.message}`);
            showToast("Sidebar query failed", "error");
        }
    });

    function appendSidebarMessage(sender, text) {
        const msgDiv = document.createElement("div");
        msgDiv.classList.add("sidebar-chat-msg", sender);
        msgDiv.textContent = text;
        sidebarChatViewport.appendChild(msgDiv);
        sidebarChatViewport.scrollTop = sidebarChatViewport.scrollHeight;
    }

    /**
     * Revert side pane state when background is clicked.
     */
    function resetNodeDetails() {
        currentSelectedNode = null;
        document.getElementById("sidebar-node-content").style.display = "none";
        document.getElementById("sidebar-empty-state").style.display = "flex";
    }
});
