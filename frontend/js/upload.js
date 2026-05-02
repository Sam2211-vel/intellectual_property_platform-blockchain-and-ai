document.getElementById("uploadForm").addEventListener("submit", function (e) {
    e.preventDefault();

    const fileInput = document.getElementById("fileInput");
    const ownerInput = document.getElementById("ownerId");
    const assetType = document.getElementById("assetType").value;
    const resultDiv = document.getElementById("uploadResult");

    // ---------- FILE VALIDATION ----------
    if (!fileInput.files.length) {
        alert("Please select a file");
        return;
    }

    const file = fileInput.files[0];
    const formData = new FormData();

    formData.append("file", file);
    formData.append("owner", ownerInput.value);
    formData.append("file_type", assetType);

    // ==============================================
    // ✔ LOADING FEEDBACK – ADDED AS REQUESTED
    // ==============================================
    if (resultDiv) {
        resultDiv.innerHTML = "<p>uploading… please wait</p>";
    }

    // ---------- API CALL ----------
    fetch("/api/upload", {
        method: "POST",
        body: formData
    })
    .then(res => res.json().then(data => ({ status: res.status, data })))
    .then(({ status, data }) => {

        // ---------- DUPLICATE / SIMILAR FILE CASE ----------
        if (status === 409) {
            resultDiv.innerHTML = `
                <h4 style="color:red;">Upload Blocked</h4>
                <p><b>Similarity:</b> ${data.similarity}%</p>
            `;
            return;
        }

        // ---------- GENERAL FAILURE ----------
        if (!data.success) {
            alert("Upload failed");
            return;
        }

        // ---------- SUCCESS TEMPLATE ----------
        resultDiv.innerHTML = `
            <h4 style="color:green;">Upload Successful</h4>
            <p><b>Hash:</b> ${data.file_hash}</p>
            <p><b>IPFS CID:</b> ${data.cid}</p>
            <p><b>Blockchain Tx:</b> ${data.tx_hash}</p>
        `;
    })
    .catch(err => {
        console.error(err);
        alert("Upload error");
    });
});
