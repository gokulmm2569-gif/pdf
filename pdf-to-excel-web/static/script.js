document.addEventListener("DOMContentLoaded", () => {
    const fileInput = document.getElementById("pdfFileInput");
    const selectedFileName = document.getElementById("selectedFileName");
    const processBtn = document.getElementById("processBtn");
    const dropZone = document.getElementById("dropZone");
    
    const statusContainer = document.getElementById("statusContainer");
    const statusSpinner = document.getElementById("statusSpinner");
    const statusText = document.getElementById("statusText");
    const statusSubtext = document.getElementById("statusSubtext");
    
    const downloadContainer = document.getElementById("downloadContainer");
    const extractedRowsBadge = document.getElementById("extractedRowsBadge");
    const extractionModeBadge = document.getElementById("extractionModeBadge");
    const downloadExcelBtn = document.getElementById("downloadExcelBtn");
    
    const errorBanner = document.getElementById("errorBanner");
    const errorMessage = document.getElementById("errorMessage");
    
    const previewSection = document.getElementById("previewSection");
    const companyHeading = document.getElementById("companyHeading");
    const companyAddress = document.getElementById("companyAddress");
    const companyContacts = document.getElementById("companyContacts");
    const invoiceMetaGrid = document.getElementById("invoiceMetaGrid");
    const tableBody = document.getElementById("tableBody");

    let currentFile = null;

    // File selection handler
    function handleFileSelection(file) {
        if (!file) return;
        
        if (!file.name.toLowerCase().endsWith(".pdf")) {
            showError("Please select a valid .pdf file.");
            return;
        }

        currentFile = file;
        selectedFileName.textContent = file.name;
        processBtn.disabled = false;
        hideError();
        hideResults();
    }

    fileInput.addEventListener("change", (e) => {
        if (e.target.files && e.target.files.length > 0) {
            handleFileSelection(e.target.files[0]);
        }
    });

    // Drag and Drop
    dropZone.addEventListener("dragover", (e) => {
        e.preventDefault();
        dropZone.style.borderColor = "#1e3a8a";
        dropZone.style.backgroundColor = "#eff6ff";
    });

    dropZone.addEventListener("dragleave", (e) => {
        e.preventDefault();
        dropZone.style.borderColor = "#94a3b8";
        dropZone.style.backgroundColor = "#f8fafc";
    });

    dropZone.addEventListener("drop", (e) => {
        e.preventDefault();
        dropZone.style.borderColor = "#94a3b8";
        dropZone.style.backgroundColor = "#f8fafc";
        if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
            handleFileSelection(e.dataTransfer.files[0]);
        }
    });

    // Process PDF action
    processBtn.addEventListener("click", async () => {
        if (!currentFile) {
            showError("No PDF selected. Please choose a file first.");
            return;
        }

        hideError();
        hideResults();
        
        // Show processing status
        statusContainer.classList.remove("hidden");
        statusSpinner.classList.remove("hidden");
        statusText.textContent = "Status: Processing PDF...";
        statusSubtext.textContent = "Extracting text, analyzing invoice geometry and table line-items...";
        processBtn.disabled = true;

        const formData = new FormData();
        formData.append("file", currentFile);

        try {
            const response = await fetch("/api/process", {
                method: "POST",
                body: formData
            });

            const data = await response.json();

            if (!response.ok || !data.success) {
                const errDetail = data.detail || data.error || "An error occurred during PDF processing.";
                showError(errDetail);
                statusContainer.classList.add("hidden");
                processBtn.disabled = false;
                return;
            }

            // Success
            statusSpinner.classList.add("hidden");
            statusText.textContent = "Status: Complete";
            statusSubtext.textContent = `Extracted ${data.row_count} records across ${data.pages_count} page(s).`;

            // Download container
            downloadContainer.classList.remove("hidden");
            extractedRowsBadge.textContent = `Extracted rows: ${data.row_count}`;
            extractionModeBadge.textContent = `Engine: ${data.mode}`;
            downloadExcelBtn.href = data.download_url;
            downloadExcelBtn.setAttribute("download", `Invoice_Data_${data.file_id}.xlsx`);

            // Render Header and Table
            renderInvoiceData(data);

            processBtn.disabled = false;
        } catch (err) {
            console.error(err);
            showError("Network or server connection failed. Please check your connection.");
            statusContainer.classList.add("hidden");
            processBtn.disabled = false;
        }
    });

    function renderInvoiceData(data) {
        const header = data.header || {};
        const rows = data.rows || [];

        // Company title & contact
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

        // Table Rows
        tableBody.innerHTML = "";
        rows.forEach(row => {
            const tr = document.createElement("tr");
            tr.innerHTML = `
                <td class="col-sr">${escapeHtml(row["Sr No"] || "")}</td>
                <td class="col-doc">${escapeHtml(row["Doc No"] || "")}</td>
                <td class="col-date">${escapeHtml(row["Date"] || "")}</td>
                <td class="col-dest">${escapeHtml(row["Dest. City"] || "")}</td>
                <td class="col-mode">${escapeHtml(row["Mode"] || "")}</td>
                <td class="col-i">${escapeHtml(row["I"] || "")}</td>
                <td class="col-pc">${escapeHtml(row["PC"] || "")}</td>
                <td class="col-weight">${escapeHtml(row["Weight"] || "")}</td>
                <td class="col-amount">${escapeHtml(row["Amount"] || "")}</td>
            `;
            tableBody.appendChild(tr);
        });

        previewSection.classList.remove("hidden");
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
});
