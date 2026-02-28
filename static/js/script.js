document.addEventListener("DOMContentLoaded", () => {
    const menuItems = document.querySelectorAll(".menu-item[data-page]");
    const pages = document.querySelectorAll(".page");
    const sidebar = document.getElementById("sidebar");
    const menuToggle = document.getElementById("menuToggle");
    const currentDateTime = document.getElementById("currentDateTime");
    const notifyCount = document.getElementById("notifyCount");
    const notifyBtn = document.getElementById("notifyBtn");
    const chartCanvas = document.getElementById("weeklyChart");
    const applyPlanBtn = document.getElementById("applyPlanBtn");
    const monitorButtons = document.querySelectorAll(".monitor-btn");
    const monitorTimerDisplay = document.getElementById("monitorTimerDisplay");
    const startMonitoringQuick = document.getElementById("startMonitoringQuick");
    const navActionButtons = document.querySelectorAll(".nav-action-btn[data-target-page]");
    const monitorStatusPill = document.getElementById("monitorStatusPill");
    const monitorGameStateText = document.getElementById("monitorGameStateText");
    const gamePresenceText = document.getElementById("gamePresenceText");
    const totalPlayTimeMetric = document.getElementById("totalPlayTimeMetric");
    const sessionCountMetric = document.getElementById("sessionCountMetric");

    let previousGameDetected = null;

    const toastContainer = document.createElement("div");
    toastContainer.className = "toast-container";
    document.body.appendChild(toastContainer);

    function switchPage(pageId) {
        menuItems.forEach((item) => item.classList.toggle("active", item.dataset.page === pageId));
        pages.forEach((page) => page.classList.toggle("active", page.id === pageId));

        if (window.innerWidth <= 900 && sidebar) {
            sidebar.classList.remove("open");
        }
    }

    function showToast(message, type = "info") {
        const node = document.createElement("div");
        node.className = `toast ${type}`;
        node.textContent = message;
        toastContainer.appendChild(node);
        setTimeout(() => node.remove(), 3200);
    }

    async function pushBrowserNotification(message) {
        if (!("Notification" in window)) {
            return;
        }
        try {
            if (Notification.permission === "default") {
                await Notification.requestPermission();
            }
            if (Notification.permission === "granted") {
                new Notification("Game Addiction Monitor", { body: message });
            }
        } catch (e) {
            // Ignore notification permission errors.
        }
    }

    async function monitorCall(action) {
        const endpointMap = {
            start: "/api/monitor/start",
            pause: "/api/monitor/pause",
            stop: "/api/monitor/stop"
        };
        const endpoint = endpointMap[action];
        if (!endpoint) return;

        try {
            const res = await fetch(endpoint, { method: "POST" });
            const data = await res.json();
            if (!res.ok) {
                showToast(data.error || "Monitoring action failed.", "info");
                return;
            }
            if (monitorTimerDisplay && data.elapsed_display) {
                monitorTimerDisplay.textContent = data.elapsed_display;
            }
            if (action === "start") {
                setStatusPill("running");
            } else if (action === "pause" || action === "stop") {
                setStatusPill("paused");
            }
            applyGameState(data.game_detected, data.game_title, true);
            if (action === "stop") {
                if (totalPlayTimeMetric && data.total_play_time_display) {
                    totalPlayTimeMetric.textContent = data.total_play_time_display;
                }
                if (sessionCountMetric && typeof data.total_sessions !== "undefined") {
                    sessionCountMetric.textContent = String(data.total_sessions);
                }
            }
            showToast(data.message, "success");
            if (action === "start") {
                await pushBrowserNotification("Monitoring has started.");
            } else if (action === "stop") {
                await pushBrowserNotification("Monitoring has stopped.");
            }
        } catch (e) {
            showToast("Unable to contact monitor service.", "info");
        }
    }

    function setStatusPill(status) {
        if (!monitorStatusPill) return;
        monitorStatusPill.classList.remove("active", "inactive");
        if (status === "running") {
            monitorStatusPill.classList.add("active");
            monitorStatusPill.textContent = "Active";
        } else {
            monitorStatusPill.classList.add("inactive");
            monitorStatusPill.textContent = "Paused";
        }
    }

    function applyGameState(gameDetected, gameTitle, notifyOnChange = false) {
        const label = gameDetected ? `Playing: ${gameTitle}` : "No game detected";
        if (monitorGameStateText) {
            monitorGameStateText.textContent = label;
        }
        if (gamePresenceText) {
            gamePresenceText.textContent = label;
        }

        if (notifyOnChange) {
            if (previousGameDetected === null) {
                previousGameDetected = gameDetected;
                return;
            }
            if (previousGameDetected !== gameDetected) {
                if (gameDetected) {
                    showToast(`Game detected: ${gameTitle}`, "success");
                    pushBrowserNotification(`Game detected: ${gameTitle}`);
                } else {
                    showToast("No game detected now.", "info");
                    pushBrowserNotification("No game detected now.");
                }
                previousGameDetected = gameDetected;
            }
        } else {
            previousGameDetected = gameDetected;
        }
    }

    async function syncMonitorStatus() {
        try {
            const res = await fetch("/api/monitor/status");
            if (!res.ok) return;
            const data = await res.json();
            setStatusPill(data.status);
            if (monitorTimerDisplay && data.elapsed_display) {
                monitorTimerDisplay.textContent = data.elapsed_display;
            }
            if (totalPlayTimeMetric && data.total_play_time_display) {
                totalPlayTimeMetric.textContent = data.total_play_time_display;
            }
            if (sessionCountMetric && typeof data.total_sessions !== "undefined") {
                sessionCountMetric.textContent = String(data.total_sessions);
            }
            applyGameState(data.game_detected, data.game_title, true);
        } catch (e) {
            // Ignore sync failures.
        }
    }

    menuItems.forEach((item) => {
        item.addEventListener("click", () => switchPage(item.dataset.page));
    });

    navActionButtons.forEach((btn) => {
        btn.addEventListener("click", () => {
            const target = btn.dataset.targetPage;
            switchPage(target);
        });
    });

    if (menuToggle && sidebar) {
        menuToggle.addEventListener("click", () => sidebar.classList.toggle("open"));
    }

    document.addEventListener("click", (event) => {
        if (!sidebar || !menuToggle || window.innerWidth > 900) return;
        if (!sidebar.contains(event.target) && !menuToggle.contains(event.target)) {
            sidebar.classList.remove("open");
        }
    });

    function updateClock() {
        if (!currentDateTime) return;
        const now = new Date();
        currentDateTime.textContent = now.toLocaleString([], {
            weekday: "short",
            year: "numeric",
            month: "short",
            day: "numeric",
            hour: "2-digit",
            minute: "2-digit"
        });
    }

    updateClock();
    setInterval(updateClock, 30000);

    if (notifyBtn && notifyCount) {
        notifyBtn.addEventListener("click", () => {
            const next = Math.max(0, Number(notifyCount.textContent) - 1);
            notifyCount.textContent = String(next);
        });

        setInterval(() => {
            const current = Number(notifyCount.textContent);
            const increment = Math.random() < 0.35 ? 1 : 0;
            notifyCount.textContent = String(Math.min(12, current + increment));
        }, 7000);
    }

    if (applyPlanBtn) {
        applyPlanBtn.addEventListener("click", () => {
            switchPage("assessment");
            showToast("Plan applied. Continue with assessment.", "success");
        });
    }

    if (startMonitoringQuick) {
        startMonitoringQuick.addEventListener("click", async () => {
            switchPage("monitoring");
            await monitorCall("start");
        });
    }

    monitorButtons.forEach((btn) => {
        btn.addEventListener("click", async () => {
            const action = btn.dataset.monitorAction;
            await monitorCall(action);
        });
    });

    syncMonitorStatus();
    setInterval(syncMonitorStatus, 1000);

    // Demo weekly chart. Replace with backend API values from Flask.
    // Example: fetch('/weekly-data').then(...) and redraw.
    if (chartCanvas) {
        const values = [3.2, 4.1, 2.9, 5.6, 4.8, 6.2, 3.7];
        const labels = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];

        function drawChart() {
            const dpr = window.devicePixelRatio || 1;
            const width = chartCanvas.clientWidth;
            const height = 220;
            chartCanvas.width = Math.floor(width * dpr);
            chartCanvas.height = Math.floor(height * dpr);

            const ctx = chartCanvas.getContext("2d");
            ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
            ctx.clearRect(0, 0, width, height);

            const maxValue = Math.max(...values);
            const left = 16;
            const right = 12;
            const top = 16;
            const bottom = 28;
            const chartWidth = width - left - right;
            const chartHeight = height - top - bottom;
            const slot = chartWidth / values.length;
            const barWidth = Math.min(30, slot * 0.56);

            ctx.font = "12px Inter";
            ctx.textAlign = "center";

            values.forEach((value, index) => {
                const barHeight = (value / maxValue) * chartHeight;
                const x = left + slot * index + (slot - barWidth) / 2;
                const y = top + (chartHeight - barHeight);

                ctx.fillStyle = "#2563eb";
                ctx.fillRect(x, y, barWidth, barHeight);

                ctx.fillStyle = "#6b7280";
                ctx.fillText(labels[index], x + barWidth / 2, height - 10);
            });
        }

        drawChart();
        window.addEventListener("resize", drawChart);
    }

    // Game History
    const gameHistoryList = document.getElementById("gameHistoryList");
    const refreshGameHistoryBtn = document.getElementById("refreshGameHistoryBtn");

    async function loadGameHistory() {
        if (!gameHistoryList) return;
        try {
            const response = await fetch("/api/monitor/game-history");
            const data = await response.json();
            if (data.history && data.history.length > 0) {
                let html = '<table style="width:100%;border-collapse:collapse;margin-top:12px;">';
                html += '<tr style="text-align:left;border-bottom:1px solid var(--border);"><th style="padding:8px;">Game</th><th style="padding:8px;">Play Time</th><th style="padding:8px;">Date</th></tr>';
                data.history.forEach(function(item) {
                    html += '<tr style="border-bottom:1px solid var(--border);"><td style="padding:8px;">' + item.game_name + '</td><td style="padding:8px;">' + item.play_time + '</td><td style="padding:8px;">' + item.played_at + '</td></tr>';
                });
                html += '</table>';
                gameHistoryList.innerHTML = html;
            } else {
                gameHistoryList.innerHTML = '<p class="muted">No game history yet.</p>';
            }
        } catch (error) {
            console.error("Error loading game history:", error);
        }
    }

    if (refreshGameHistoryBtn) {
        refreshGameHistoryBtn.addEventListener("click", loadGameHistory);
    }

    loadGameHistory();

    // ==========================
    // ALERT SYSTEM JAVASCRIPT
    // ==========================
    
    const testAlertBtn = document.getElementById("testAlertBtn");
    const refreshAlertsBtn = document.getElementById("refreshAlertsBtn");
    const alertsHistoryList = document.getElementById("alertsHistoryList");

    // Load alert history
    async function loadAlertHistory() {
        if (!alertsHistoryList) return;
        
        try {
            const response = await fetch("/api/alerts/log");
            const data = await response.json();
            
            if (data.alerts && data.alerts.length > 0) {
                let html = "";
                data.alerts.forEach(function(alert) {
                    html += '<div class="alert-history-item">';
                    html += '<div class="alert-type">' + alert.alert_type + '</div>';
                    html += '<div class="alert-message">' + alert.message + '</div>';
                    html += '<div class="alert-meta">';
                    if (alert.sent_via) html += 'Via: ' + alert.sent_via + ' | ';
                    html += 'Time: ' + alert.sent_at;
                    html += '</div>';
                    html += '</div>';
                });
                alertsHistoryList.innerHTML = html;
            } else {
                alertsHistoryList.innerHTML = '<p class="muted">No alerts yet.</p>';
            }
        } catch (error) {
            console.error("Error loading alert history:", error);
            alertsHistoryList.innerHTML = '<p class="muted">Error loading alerts.</p>';
        }
    }

    // Send test alert
    async function sendTestAlert() {
        if (!testAlertBtn) return;
        
        testAlertBtn.disabled = true;
        testAlertBtn.textContent = "Sending...";
        
        try {
            const response = await fetch("/api/alerts/test", {
                method: "POST"
            });
            
            const data = await response.json();
            
            if (response.ok) {
                showToast("Test alert sent!", "success");
                loadAlertHistory();
            } else {
                showToast("Failed to send test alert.", "error");
            }
        } catch (error) {
            console.error("Error sending test alert:", error);
            showToast("Error sending test alert.", "error");
        } finally {
            if (testAlertBtn) {
                testAlertBtn.disabled = false;
                testAlertBtn.textContent = "Send Test Alert";
            }
        }
    }

    // Event listeners for alert system
    if (testAlertBtn) {
        testAlertBtn.addEventListener("click", sendTestAlert);
    }

    if (refreshAlertsBtn) {
        refreshAlertsBtn.addEventListener("click", loadAlertHistory);
    }

    // Initial load of alert history
    loadAlertHistory();

    // ==========================
    // EMAIL CONFIGURATION SYSTEM
    // ==========================
    
    const emailStatusCard = document.getElementById("emailStatusCard");
    const emailStatusIcon = document.getElementById("emailStatusIcon");
    const emailStatusText = document.getElementById("emailStatusText");
    const configureEmailBtn = document.getElementById("configureEmailBtn");
    const testEmailConnectionBtn = document.getElementById("testEmailConnectionBtn");
    const emailConfigForm = document.getElementById("emailConfigForm");
    const gmailEmailInput = document.getElementById("gmailEmail");
    const gmailAppPasswordInput = document.getElementById("gmailAppPassword");
    const saveEmailConfigBtn = document.getElementById("saveEmailConfigBtn");
    const cancelEmailConfigBtn = document.getElementById("cancelEmailConfigBtn");

    // Load email configuration status
    async function loadEmailStatus() {
        try {
            const response = await fetch("/api/alerts/email-status");
            const data = await response.json();
            
            if (data.configured) {
                if (emailStatusCard) {
                    emailStatusCard.classList.remove("not-configured");
                    emailStatusCard.classList.add("configured");
                }
                if (emailStatusIcon) emailStatusIcon.textContent = "✅";
                if (emailStatusText) emailStatusText.textContent = "Email configured: " + data.email;
                if (testEmailConnectionBtn) testEmailConnectionBtn.style.display = "inline-block";
            } else {
                if (emailStatusCard) {
                    emailStatusCard.classList.remove("configured");
                    emailStatusCard.classList.add("not-configured");
                }
                if (emailStatusIcon) emailStatusIcon.textContent = "⚠️";
                if (emailStatusText) emailStatusText.textContent = "Email is not configured. Configure your Gmail to receive alerts.";
                if (testEmailConnectionBtn) testEmailConnectionBtn.style.display = "none";
            }
        } catch (error) {
            console.error("Error loading email status:", error);
        }
    }

    // Show email configuration form
    if (configureEmailBtn) {
        configureEmailBtn.addEventListener("click", function() {
            if (emailConfigForm) {
                emailConfigForm.classList.toggle("show");
            }
        });
    }

    // Cancel email configuration
    if (cancelEmailConfigBtn) {
        cancelEmailConfigBtn.addEventListener("click", function() {
            if (emailConfigForm) {
                emailConfigForm.classList.remove("show");
            }
            if (gmailEmailInput) gmailEmailInput.value = "";
            if (gmailAppPasswordInput) gmailAppPasswordInput.value = "";
        });
    }

    // Save email configuration
    if (saveEmailConfigBtn) {
        saveEmailConfigBtn.addEventListener("click", async function() {
            const email = gmailEmailInput ? gmailEmailInput.value.trim() : "";
            const appPassword = gmailAppPasswordInput ? gmailAppPasswordInput.value.trim() : "";
            
            if (!email || !appPassword) {
                showToast("Please enter both email and app password", "error");
                return;
            }
            
            saveEmailConfigBtn.disabled = true;
            saveEmailConfigBtn.textContent = "Saving...";
            
            try {
                const response = await fetch("/api/alerts/email-config", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json"
                    },
                    body: JSON.stringify({
                        email: email,
                        app_password: appPassword
                    })
                });
                
                const data = await response.json();
                
                if (response.ok) {
                    showToast(data.message, "success");
                    if (emailConfigForm) emailConfigForm.classList.remove("show");
                    if (gmailEmailInput) gmailEmailInput.value = "";
                    if (gmailAppPasswordInput) gmailAppPasswordInput.value = "";
                    loadEmailStatus();
                    loadAlertHistory();
                } else {
                    showToast(data.error || "Failed to configure email", "error");
                }
            } catch (error) {
                console.error("Error saving email config:", error);
                showToast("Error configuring email", "error");
            } finally {
                saveEmailConfigBtn.disabled = false;
                saveEmailConfigBtn.textContent = "Save Configuration";
            }
        });
    }

    // Test email connection
    if (testEmailConnectionBtn) {
        testEmailConnectionBtn.addEventListener("click", async function() {
            testEmailConnectionBtn.disabled = true;
            testEmailConnectionBtn.textContent = "Testing...";
            
            try {
                const response = await fetch("/api/alerts/test-email-connection", {
                    method: "POST"
                });
                
                const data = await response.json();
                
                if (response.ok) {
                    showToast(data.message, "success");
                    loadAlertHistory();
                } else {
                    showToast(data.error || "Failed to test connection", "error");
                }
            } catch (error) {
                console.error("Error testing email connection:", error);
                showToast("Error testing email connection", "error");
            } finally {
                testEmailConnectionBtn.disabled = false;
                testEmailConnectionBtn.textContent = "Test Connection";
            }
        });
    }

    // Initial load of email status
    loadEmailStatus();
});
