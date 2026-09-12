document.addEventListener("DOMContentLoaded", () => {
    // DOM Elements
    const fileInput = document.getElementById("pdfFileInput");
    const selectedFileName = document.getElementById("selectedFileName");
    const selectedFileInfo = document.getElementById("selectedFileInfo");
    const clearFileBtn = document.getElementById("clearFileBtn");
    const processBtn = document.getElementById("processBtn");
    const dropZone = document.getElementById("dropZone");
    const resetBtn = document.getElementById("resetBtn");
    const mainUploadCard = document.getElementById("mainUploadCard");
    const cursorGlow = document.getElementById("cursorGlow");
    
    // Status & HUD Elements
    const statusContainer = document.getElementById("statusContainer");
    const statusTitle = document.getElementById("statusTitle");
    const statusSubtext = document.getElementById("statusSubtext");
    const statusTimeElapsed = document.getElementById("statusTimeElapsed");
    const hudProgressBar = document.getElementById("hudProgressBar");
    const progressPercentage = document.getElementById("progressPercentage");
    const progressPhaseName = document.getElementById("progressPhaseName");
    const step1 = document.getElementById("step1");
    const step2 = document.getElementById("step2");
    const step3 = document.getElementById("step3");
    
    // Download & Results
    const downloadContainer = document.getElementById("downloadContainer");
    const extractedRowsBadge = document.getElementById("extractedRowsBadge");
    const extractionModeBadge = document.getElementById("extractionModeBadge");
    const pageCountBadge = document.getElementById("pageCountBadge");
    const downloadExcelBtn = document.getElementById("downloadExcelBtn");
    
    // Errors & Preview
    const errorBanner = document.getElementById("errorBanner");
    const errorMessage = document.getElementById("errorMessage");
    const previewSection = document.getElementById("previewSection");
    const companyHeading = document.getElementById("companyHeading");
    const companyAddress = document.getElementById("companyAddress");
    const companyContacts = document.getElementById("companyContacts");
    const invoiceMetaGrid = document.getElementById("invoiceMetaGrid");
    const tableBody = document.getElementById("tableBody");
    const tableSearchInput = document.getElementById("tableSearchInput");
    const copyTableBtn = document.getElementById("copyTableBtn");
    const totalWeightCell = document.getElementById("totalWeightCell");
    const totalAmountCell = document.getElementById("totalAmountCell");

    // Toast
    const actionToastEl = document.getElementById("actionToast");
    const toastMessage = document.getElementById("toastMessage");
    const toastIcon = document.getElementById("toastIcon");
    const actionToast = actionToastEl ? new bootstrap.Toast(actionToastEl, { delay: 2800 }) : null;

    let currentFile = null;
    let extractedDataCache = null;
    let timerInterval = null;
    let hudProgressTimer = null;

    /* ==========================================================================
       1. INTERACTIVE MOTION CANVAS BACKGROUND (Particles & Neural Constellation)
       ========================================================================== */
    const canvas = document.getElementById("motionCanvas");
    if (canvas) {
        const ctx = canvas.getContext("2d");
        let width = canvas.width = window.innerWidth;
        let height = canvas.height = window.innerHeight;
        
        const particles = [];
        const numParticles = Math.min(Math.floor((width * height) / 18000), 75);
        let mouseX = width / 2;
        let mouseY = height / 2;
        let isMouseActive = false;

        class Particle {
            constructor() {
                this.reset();
            }

            reset() {
                this.x = Math.random() * width;
                this.y = Math.random() * height;
                this.vx = (Math.random() - 0.5) * 0.6;
                this.vy = (Math.random() - 0.5) * 0.6;
                this.radius = Math.random() * 2 + 1;
                this.color = Math.random() > 0.4 ? "rgba(6, 182, 212, " : "rgba(99, 102, 241, ";
                this.alpha = Math.random() * 0.5 + 0.2;
                this.baseAlpha = this.alpha;
            }

            update() {
                this.x += this.vx;
                this.y += this.vy;

                if (this.x < 0 || this.x > width) this.vx *= -1;
                if (this.y < 0 || this.y > height) this.vy *= -1;

                // Mouse interaction
                if (isMouseActive) {
                    const dx = mouseX - this.x;
                    const dy = mouseY - this.y;
                    const dist = Math.sqrt(dx * dx + dy * dy);
                    if (dist < 140) {
                        this.x += (dx / dist) * 0.8;
                        this.y += (dy / dist) * 0.8;
                        this.alpha = Math.min(this.baseAlpha * 2, 1);
                    } else {
                        this.alpha = this.baseAlpha;
                    }
                }
            }

            draw() {
                ctx.beginPath();
                ctx.arc(this.x, this.y, this.radius, 0, Math.PI * 2);
                ctx.fillStyle = `${this.color}${this.alpha})`;
                ctx.shadowColor = "#06b6d4";
                ctx.shadowBlur = 8;
                ctx.fill();
                ctx.shadowBlur = 0;
            }
        }

        for (let i = 0; i < numParticles; i++) {
            particles.push(new Particle());
        }

        function animateCanvas() {
            ctx.clearRect(0, 0, width, height);

            // Draw connections
            for (let i = 0; i < particles.length; i++) {
                for (let j = i + 1; j < particles.length; j++) {
                    const dx = particles[i].x - particles[j].x;
                    const dy = particles[i].y - particles[j].y;
                    const dist = Math.sqrt(dx * dx + dy * dy);

                    if (dist < 130) {
                        const lineAlpha = (1 - dist / 130) * 0.22;
                        ctx.beginPath();
                        ctx.moveTo(particles[i].x, particles[i].y);
                        ctx.lineTo(particles[j].x, particles[j].y);
                        ctx.strokeStyle = `rgba(6, 182, 212, ${lineAlpha})`;
                        ctx.lineWidth = 0.8;
                        ctx.stroke();
                    }
                }
            }

            // Update & Draw particles
            particles.forEach(p => {
                p.update();
                p.draw();
            });

            requestAnimationFrame(animateCanvas);
        }

        animateCanvas();

        window.addEventListener("resize", () => {
            width = canvas.width = window.innerWidth;
            height = canvas.height = window.innerHeight;
        });

        window.addEventListener("mousemove", (e) => {
            mouseX = e.clientX;
            mouseY = e.clientY;
            isMouseActive = true;
            
            // Cursor spotlight follow
            if (cursorGlow) {
                cursorGlow.style.left = `${e.clientX}px`;
                cursorGlow.style.top = `${e.clientY}px`;
            }
        });
    }

    /* ==========================================================================
       2. INTERACTIVE 3D PERSPECTIVE TILT ON UPLOAD CARD
       ========================================================================== */
    if (mainUploadCard) {
        mainUploadCard.addEventListener("mousemove", (e) => {
            const rect = mainUploadCard.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;
            const centerX = rect.width / 2;
            const centerY = rect.height / 2;
            
            const rotateX = ((y - centerY) / centerY) * -3;
            const rotateY = ((x - centerX) / centerX) * 3;
            
            mainUploadCard.style.transform = `perspective(1000px) rotateX(${rotateX}deg) rotateY(${rotateY}deg)`;
        });

        mainUploadCard.addEventListener("mouseleave", () => {
            mainUploadCard.style.transform = "perspective(1000px) rotateX(0deg) rotateY(0deg)";
        });
    }

    /* ==========================================================================
       3. FILE SELECTION & DRAG-AND-DROP
       ========================================================================== */
    function handleFileSelection(file) {
        if (!file) return;
        
        if (!file.name.toLowerCase().endsWith(".pdf")) {
            showError("Invalid file type. Please upload a standard PDF (.pdf) file.");
            return;
        }

        currentFile = file;
        selectedFileName.textContent = file.name;
        if (clearFileBtn) clearFileBtn.classList.remove("hidden");
        
        processBtn.disabled = false;
        dropZone.classList.add("scanning");
        hideError();
        hideResults();
        
        showToast("PDF document staged for neural extraction.", "bi-file-earmark-check-fill");
    }

    fileInput.addEventListener("change", (e) => {
        if (e.target.files && e.target.files.length > 0) {
            handleFileSelection(e.target.files[0]);
        }
    });

    if (clearFileBtn) {
        clearFileBtn.addEventListener("click", (e) => {
            e.stopPropagation();
            resetUploadState();
        });
    }

    if (resetBtn) {
        resetBtn.addEventListener("click", () => {
            resetUploadState();
            window.scrollTo({ top: 0, behavior: "smooth" });
        });
    }

    function resetUploadState() {
        currentFile = null;
        fileInput.value = "";
        selectedFileName.textContent = "No file selected";
        if (clearFileBtn) clearFileBtn.classList.add("hidden");
        processBtn.disabled = true;
        dropZone.classList.remove("scanning");
        hideError();
        hideResults();
    }

    // Drag and Drop
    dropZone.addEventListener("dragover", (e) => {
        e.preventDefault();
        dropZone.classList.add("dragover");
    });

    dropZone.addEventListener("dragleave", (e) => {
        e.preventDefault();
        dropZone.classList.remove("dragover");
    });

    dropZone.addEventListener("drop", (e) => {
        e.preventDefault();
        dropZone.classList.remove("dragover");
        if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
            handleFileSelection(e.dataTransfer.files[0]);
        }
    });

    /* ==========================================================================
       4. HIGH-TECH HUD PROCESSING TELEMETRY ANIMATION
       ========================================================================== */
    function startHudTelemetry() {
        statusContainer.classList.remove("hidden");
        let startTime = Date.now();
        let currentProgress = 5;
        
        // Step classes
        step1.className = "hud-step-item active";
        step2.className = "hud-step-item";
        step3.className = "hud-step-item";
        
        hudProgressBar.style.width = "5%";
        progressPercentage.textContent = "5%";
        progressPhaseName.textContent = "PHASE 1/3";
        statusTitle.textContent = "Analyzing Document Geometry";
        statusSubtext.textContent = "Parsing vector paths, text boxes, and stream blocks...";

        // Timer
        clearInterval(timerInterval);
        timerInterval = setInterval(() => {
            const elapsed = ((Date.now() - startTime) / 1000).toFixed(1);
            statusTimeElapsed.textContent = `${elapsed}s`;
        }, 100);

        // Smooth progress stepping
        clearInterval(hudProgressTimer);
        hudProgressTimer = setInterval(() => {
            if (currentProgress < 35) {
                currentProgress += 5;
                step1.className = "hud-step-item active";
            } else if (currentProgress < 75) {
                currentProgress += 3;
                step1.className = "hud-step-item completed";
                step2.className = "hud-step-item active";
                progressPhaseName.textContent = "PHASE 2/3";
                statusTitle.textContent = "Neural Spatial Clustering";
                statusSubtext.textContent = "Clustering line-item tokens and detecting table grid columns...";
            } else if (currentProgress < 92) {
                currentProgress += 1;
                step2.className = "hud-step-item completed";
                step3.className = "hud-step-item active";
                progressPhaseName.textContent = "PHASE 3/3";
                statusTitle.textContent = "Compiling Excel Workbook";
                statusSubtext.textContent = "Injecting OpenPyXL formulas, sum totals, and header formats...";
            }
            
            hudProgressBar.style.width = `${currentProgress}%`;
            progressPercentage.textContent = `${Math.floor(currentProgress)}%`;
        }, 150);
    }

    function completeHudTelemetry() {
        clearInterval(timerInterval);
        clearInterval(hudProgressTimer);
        
        hudProgressBar.style.width = "100%";
        progressPercentage.textContent = "100%";
        progressPhaseName.textContent = "DONE";
        step1.className = "hud-step-item completed";
        step2.className = "hud-step-item completed";
        step3.className = "hud-step-item completed";
        statusTitle.textContent = "Extraction Completed Successfully";
        statusSubtext.textContent = "Spreadsheet generated and ready for instant download.";
    }

    /* ==========================================================================
       5. PROCESS PDF ACTION & API COMMUNICATION
       ========================================================================== */
    processBtn.addEventListener("click", async () => {
        if (!currentFile) {
            showError("No PDF selected. Please choose a valid invoice file first.");
            return;
        }

        hideError();
        hideResults();
        processBtn.disabled = true;
        startHudTelemetry();

        const formData = new FormData();
        formData.append("file", currentFile);

        try {
            const response = await fetch("/api/process", {
                method: "POST",
                body: formData
            });

            const data = await response.json();

            if (!response.ok || !data.success) {
                clearInterval(timerInterval);
                clearInterval(hudProgressTimer);
                const errDetail = data.detail || data.error || "An error occurred during PDF processing.";
                showError(errDetail);
                statusContainer.classList.add("hidden");
                processBtn.disabled = false;
                return;
            }

            // Success
            completeHudTelemetry();
            extractedDataCache = data;

            setTimeout(() => {
                downloadContainer.classList.remove("hidden");
                animateCounter(extractedRowsBadge, `Extracted rows: `, data.row_count || 0);
                extractionModeBadge.innerHTML = `<i class="bi bi-gear-wide-connected me-1"></i>Engine: ${data.mode || 'AUTO'}`;
                if (pageCountBadge) {
                    pageCountBadge.innerHTML = `<i class="bi bi-files me-1"></i>Pages: ${data.pages_count || 1}`;
                }
                
                downloadExcelBtn.href = data.download_url;
                downloadExcelBtn.setAttribute("download", `Invoice_Data_${data.file_id}.xlsx`);

                // Render Header and Animated Table
                renderInvoiceData(data);
                processBtn.disabled = false;

                // Trigger Cyber Confetti Blast
                triggerCelebrationConfetti();
                
                showToast("Invoice spreadsheet generated successfully!", "bi-check-circle-fill");
            }, 400);

        } catch (err) {
            console.error(err);
            clearInterval(timerInterval);
            clearInterval(hudProgressTimer);
            showError("Network or server connection failed. Please ensure the backend is running.");
            statusContainer.classList.add("hidden");
            processBtn.disabled = false;
        }
    });

    /* ==========================================================================
       6. RENDER INVOICE DATA & ANIMATED TABLE
       ========================================================================== */
    function renderInvoiceData(data) {
        const header = data.header || {};
        const rows = data.rows || [];

        // Company title & address
        companyHeading.textContent = header.Company || "INVOICE";
        companyAddress.textContent = header.Address || "";
        
        const contacts = [];
        if (header.Phone) contacts.push(`Phone: ${header.Phone}`);
        if (header.Email) contacts.push(`Email: ${header.Email}`);
        if (header["SAC Code"]) contacts.push(`SAC Code: ${header["SAC Code"]}`);
        if (header["Type Of Service"]) contacts.push(`Service: ${header["Type Of Service"]}`);
        companyContacts.textContent = contacts.join(" | ");

        // Meta Grid
        invoiceMetaGrid.innerHTML = "";
        const metaFields = [
            { label: "Invoice No", val: header["Invoice No"] },
            { label: "Date", val: header["Date"] },
            { label: "Bill", val: header["Bill"] },
            { label: "Customer", val: header["Customer"] },
            { label: "PAN", val: header["PAN"] },
            { label: "CIN", val: header["CIN"] },
            { label: "Location", val: header["Location"] }
        ];

        metaFields.forEach(f => {
            if (f.val) {
                const div = document.createElement("div");
                div.className = "meta-item";
                div.innerHTML = `<span class="meta-label">${escapeHtml(f.label)}:</span> <span class="meta-val">${escapeHtml(f.val)}</span>`;
                invoiceMetaGrid.appendChild(div);
            }
        });

        // Render Table Rows with Staggered Animation
        renderTableRows(rows);

        previewSection.classList.remove("hidden");
        previewSection.scrollIntoView({ behavior: "smooth", block: "start" });
    }

    function renderTableRows(rows, filterQuery = "") {
        tableBody.innerHTML = "";
        let totalWeight = 0;
        let totalAmount = 0;

        const filtered = rows.filter(row => {
            if (!filterQuery) return true;
            const q = filterQuery.toLowerCase();
            return Object.values(row).some(val => String(val || "").toLowerCase().includes(q));
        });

        if (filtered.length === 0) {
            const tr = document.createElement("tr");
            tr.innerHTML = `<td colspan="9" class="text-center py-4 text-muted font-mono">No matching records found</td>`;
            tableBody.appendChild(tr);
            totalWeightCell.textContent = "-";
            totalAmountCell.textContent = "-";
            return;
        }

        filtered.forEach((row, index) => {
            const tr = document.createElement("tr");
            tr.className = "table-row-animate";
            tr.style.animationDelay = `${Math.min(index * 25, 400)}ms`;

            // Accumulate numeric totals
            const wVal = parseFloat(String(row["Weight"] || "").replace(/[^0-9.]/g, ""));
            if (!isNaN(wVal)) totalWeight += wVal;

            const aVal = parseFloat(String(row["Amount"] || "").replace(/[^0-9.]/g, ""));
            if (!isNaN(aVal)) totalAmount += aVal;

            tr.innerHTML = `
                <td class="col-sr">${escapeHtml(row["Sr No"] || String(index + 1))}</td>
                <td class="col-doc">${highlightText(row["Doc No"] || "", filterQuery)}</td>
                <td class="col-date">${highlightText(row["Date"] || "", filterQuery)}</td>
                <td class="col-dest">${highlightText(row["Dest. City"] || "", filterQuery)}</td>
                <td class="col-mode">${highlightText(row["Mode"] || "", filterQuery)}</td>
                <td class="col-i">${highlightText(row["I"] || "", filterQuery)}</td>
                <td class="col-pc">${highlightText(row["PC"] || "", filterQuery)}</td>
                <td class="col-weight text-end font-mono">${highlightText(row["Weight"] || "", filterQuery)}</td>
                <td class="col-amount text-end font-mono">${highlightText(row["Amount"] || "", filterQuery)}</td>
            `;
            tableBody.appendChild(tr);
        });

        // Update Footers
        totalWeightCell.textContent = totalWeight > 0 ? totalWeight.toFixed(2) : "-";
        totalAmountCell.textContent = totalAmount > 0 ? `₹${totalAmount.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}` : "-";
    }

    /* ==========================================================================
       7. LIVE SEARCH FILTER & CSV COPY
       ========================================================================== */
    if (tableSearchInput) {
        tableSearchInput.addEventListener("input", (e) => {
            if (extractedDataCache && extractedDataCache.rows) {
                renderTableRows(extractedDataCache.rows, e.target.value.trim());
            }
        });
    }

    if (copyTableBtn) {
        copyTableBtn.addEventListener("click", () => {
            if (!extractedDataCache || !extractedDataCache.rows || extractedDataCache.rows.length === 0) {
                showToast("No table data available to copy.", "bi-exclamation-circle");
                return;
            }

            const headers = ["Sr No", "Doc No", "Date", "Dest. City", "Mode", "I", "PC", "Weight", "Amount"];
            const csvRows = [headers.join(",")];

            extractedDataCache.rows.forEach(r => {
                const values = headers.map(h => `"${String(r[h] || '').replace(/"/g, '""')}"`);
                csvRows.push(values.join(","));
            });

            navigator.clipboard.writeText(csvRows.join("\n")).then(() => {
                showToast("Spreadsheet copied to clipboard as CSV!", "bi-clipboard-check-fill");
            }).catch(() => {
                showToast("Failed to copy data.", "bi-x-circle");
            });
        });
    }

    /* ==========================================================================
       8. UTILITY & VISUAL FX (Confetti, Counters, Toasts)
       ========================================================================== */
    function triggerCelebrationConfetti() {
        if (typeof confetti === "function") {
            confetti({
                particleCount: 50,
                spread: 70,
                origin: { y: 0.65 },
                colors: ['#06b6d4', '#22d3ee', '#6366f1', '#10b981', '#ffffff']
            });
        }
    }

    function animateCounter(el, prefix, targetNum) {
        let current = 0;
        const step = Math.max(1, Math.floor(targetNum / 20));
        const interval = setInterval(() => {
            current += step;
            if (current >= targetNum) {
                current = targetNum;
                clearInterval(interval);
            }
            el.innerHTML = `<i class="bi bi-table me-1"></i>${prefix}${current}`;
        }, 20);
    }

    function showToast(msg, iconClass = "bi-check-circle-fill") {
        if (actionToast && toastMessage && toastIcon) {
            toastMessage.textContent = msg;
            toastIcon.className = `bi ${iconClass} text-cyan fs-5`;
            actionToast.show();
        }
    }

    function showError(msg) {
        errorMessage.textContent = msg;
        errorBanner.classList.remove("hidden");
    }

    function hideError() {
        errorBanner.classList.add("hidden");
    }

    function hideResults() {
        statusContainer.classList.add("hidden");
        downloadContainer.classList.add("hidden");
        previewSection.classList.add("hidden");
    }

    function escapeHtml(text) {
        const div = document.createElement("div");
        div.textContent = text;
        return div.innerHTML;
    }

    function highlightText(text, query) {
        if (!query) return escapeHtml(text);
        const safeText = escapeHtml(text);
        const regex = new RegExp(`(${query.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`, 'gi');
        return safeText.replace(regex, `<mark class="bg-cyan-subtle text-white px-1 rounded">$1</mark>`);
    }
});
