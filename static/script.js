let searchResults = [];
let pdfLoaded = false;
let controller = null;

function autoResize(el) {
    el.style.height = 'auto';
    el.style.height = Math.min(el.scrollHeight, 120) + 'px';
}

function showMsg(id, text, type) {
    document.getElementById(id).innerHTML =
        `<div class="status-msg status-${type}">${text}</div>`;
}

async function searchPDFs() {
    const query = document.getElementById("searchInput").value.trim();

    if (query.length < 3) {
        showMsg("searchMsg", "Please enter at least 3 characters.", "error");
        return;
    }

    showMsg("searchMsg", "Searching...", "info");

    const res = await fetch("/search", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({query})
    });

    const data = await res.json();

    if (data.error) {
        showMsg("searchMsg", data.error, "error");
        document.getElementById("pdfList").innerHTML = "";
        document.getElementById("loadBtn").disabled = true;
        return;
    }

    searchResults = data.results;
    showMsg("searchMsg", `Found ${data.results.length} PDF(s).`, "success");

    document.getElementById("pdfList").innerHTML = data.results.map(pdf => `
        <div class="pdf-item">
            <input type="checkbox" id="pdf_${pdf.id}" value="${pdf.path}" checked />
            <label for="pdf_${pdf.id}" title="${pdf.name}">${pdf.name}</label>
        </div>
    `).join("");

    document.getElementById("loadBtn").disabled = false;
}

async function loadPDFs() {
    const checkboxes = document.querySelectorAll("#pdfList input[type='checkbox']:checked");
    const paths = Array.from(checkboxes).map(cb => cb.value);

    if (paths.length === 0) {
        showMsg("loadMsg", "Please select at least one PDF.", "error");
        return;
    }

    showMsg("loadMsg", "Loading PDFs... Please wait.", "info");
    document.getElementById("loadBtn").disabled = true;

    const res = await fetch("/load", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({paths})
    });

    const data = await res.json();

    if (data.error) {
        showMsg("loadMsg", data.error, "error");
        document.getElementById("loadBtn").disabled = false;
        return;
    }

    showMsg("loadMsg", data.message, "success");
    pdfLoaded = true;

    document.getElementById("lockedMsg").style.display = "none";
    document.getElementById("inputSection").style.display = "block";
    document.getElementById("welcomeScreen").style.display = "none";

    addMessage("assistant", "PDFs loaded successfully. You can now ask questions about the selected documents.");
}

async function askQuestion() {
    const input = document.getElementById("questionInput");
    const query = input.value.trim();

    if (!query || !pdfLoaded) return;

    addMessage("user", query);
    input.value = "";
    input.style.height = "auto";

    const typingId = addTyping();

    // Show stop button
    document.getElementById("stopBtn").style.display = "flex";
    document.getElementById("sendBtn").style.display = "none";

    controller = new AbortController();

    try {
        const res = await fetch("/ask", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({query}),
            signal: controller.signal
        });

        const data = await res.json();
        removeTyping(typingId);

        if (data.error) {
            addMessage("assistant", data.error);
            return;
        }

        let html = `<div>${escapeHTML(data.answer)}</div>`;

        if (data.sources && data.sources.length > 0) {
            const unique = [...new Map(
                data.sources.map(s => [`${s.pdf}-${s.page}`, s])
            ).values()];
            html += `<div class="sources">Sources: ` +
                unique.map(s => `<span>${s.pdf} - Page ${s.page}</span>`).join("") +
                `</div>`;
        }

        if (data.suggestions && data.suggestions.length > 0) {
            let sHTML = `<div class="suggestions"><strong>Answer not found. Try these folders:</strong>`;
            data.suggestions.forEach(s => {
                sHTML += `<div>${s.folder} (${s.similarity} match)<br>`;
                sHTML += s.pdfs.map(p => `&nbsp;&nbsp;- ${p}`).join("<br>");
                sHTML += `</div>`;
            });
            sHTML += `</div>`;
            html += sHTML;
        }

        addMessage("assistant", html, true);

    } catch (err) {
        removeTyping(typingId);
        if (err.name === "AbortError") {
            addMessage("assistant", "Generation stopped.");
        }
    } finally {
        document.getElementById("stopBtn").style.display = "none";
        document.getElementById("sendBtn").style.display = "flex";
        controller = null;
    }
}

function stopGeneration() {
    if (controller) {
        controller.abort();
    }
}

async function recordVoice() {
    const btn = document.getElementById("voiceBtn");
    btn.classList.add("recording");
    btn.innerHTML = "&#9210;";
    btn.disabled = true;

    const res = await fetch("/voice", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({duration: 10})
    });

    const data = await res.json();
    btn.classList.remove("recording");
    btn.innerHTML = "&#127897;";
    btn.disabled = false;

    if (data.text) {
        document.getElementById("questionInput").value = data.text;
        autoResize(document.getElementById("questionInput"));
    }
}

function addMessage(role, content, isHTML = false) {
    const container = document.getElementById("chatMessages");
    const div = document.createElement("div");
    div.className = `message ${role}`;

    const avatar = role === "user" ? "I" : "AI";
    const avatarClass = role === "user" ? "user-avatar" : "bot-avatar";

    div.innerHTML = `
        <div class="avatar ${avatarClass}">${avatar}</div>
        <div class="bubble">${isHTML ? content : escapeHTML(content)}</div>
    `;

    container.appendChild(div);
    container.scrollTop = container.scrollHeight;
    return div;
}

function addTyping() {
    const container = document.getElementById("chatMessages");
    const div = document.createElement("div");
    div.className = "message assistant";
    div.id = "typing-" + Date.now();
    div.innerHTML = `
        <div class="avatar bot-avatar">AI</div>
        <div class="bubble">
            <div class="typing">
                <span></span><span></span><span></span>
            </div>
        </div>
    `;
    container.appendChild(div);
    container.scrollTop = container.scrollHeight;
    return div.id;
}

function removeTyping(id) {
    const el = document.getElementById(id);
    if (el) el.remove();
}

function escapeHTML(str) {
    return str
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/\n/g, "<br>");
}