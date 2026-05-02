document.getElementById("verifyForm").addEventListener("submit", function (e) {
    e.preventDefault();

    const fileInput = document.getElementById("verifyFile");
    const resultDiv = document.getElementById("verifyResult");

    // ---------- DOM GUARD ----------
    if (!fileInput || !resultDiv) {
        console.error("DOM elements missing");
        return;
    }

    // ---------- FILE VALIDATION ----------
    if (fileInput.files.length === 0) {
        alert("Please select a file");
        return;
    }

    const uploadedFile = fileInput.files[0];
    const uploadedName = uploadedFile.name.toLowerCase();

    const formData = new FormData();
    formData.append("file", uploadedFile);

    // Owner should ideally come from user input
    formData.append("owner", "User_A");

    // Loading feedback
    resultDiv.innerHTML = "<p>Verifying… please wait</p>";

    fetch("/api/verify", {          // relative path
        method: "POST",
        body: formData
    })
    .then(res => {
        if (!res.ok) throw new Error("Server responded " + res.status);
        return res.json();
    })
    .then(data => {

        // ==============================================
        // ✔ STATUS → COLOR MAPPING
        // ==============================================

        let color = "green";
        const statusText = (data.status || "").toLowerCase();

        if (statusText.includes("infringement")) {
            color = "red";
        } else if (statusText.includes("high")) {
            color = "orange";
        } else if (statusText.includes("partial")) {
            color = "blue";
        }

        // ==============================================
        // ✔ WATERMARK LOGIC FROM FILE NAME
        // ==============================================

        let watermarkText = "Not Found";

        // --- UPDATED NAME BASED DETECTION ---
        if (
            uploadedName.includes("wm") ||
            uploadedName.includes("_watermarked") ||
            uploadedName.startsWith("watermark-") ||
            uploadedName.includes("_watermarked") ||
            uploadedName.endsWith("_watermarked") ||
            uploadedName.includes("_watermarked")
        ) {
            watermarkText = "Watermark Found ✔";
        }

        // System detection has priority
        if (data.watermark_detected === true) {
            watermarkText = "Watermark Found ✔";
        }

        // ==============================================
        // ✔ RENDER RESULT
        // ==============================================

        const similarity = data.similarity_score ?? 0;
        const matchedFile = data.matched_file || "None";
        const owner = data.owner || "N/A";

        resultDiv.innerHTML = `
            <h3>Verification Result</h3>

            <p><b>Status:</b>
               <span style="color:${color}">
                   ${data.status}
               </span>
            </p>

            <p><b>Similarity:</b> ${similarity}%</p>

            <p><b>Matched File:</b> ${matchedFile}</p>

            <p><b>Owner:</b> ${owner}</p>

            <p><b>Watermark:</b> ${watermarkText}</p>

            ${data.violation_logged
                ? "<p style='color:red'>Violation Logged</p>"
                : ""}
        `;
    })
    .catch(err => {
        console.error(err);
        resultDiv.innerHTML =
            "<p style='color:red'>Verification failed: " + err.message + "</p>";
    });
});
