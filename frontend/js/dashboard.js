window.onload = function () {
    fetch("/api/dashboard")
        .then(response => response.json())
        .then(data => {
            const tableBody = document.querySelector("#assetTable tbody");
            tableBody.innerHTML = "";

            data.assets.forEach(asset => {
                const row = document.createElement("tr");
                row.innerHTML = `
                    <td>${asset.file_name}</td>
                    <td>${asset.owner}</td>
                    <td>${asset.file_hash}</td>
                    <td>${asset.cid}</td>
                    <td>${asset.tx_hash}</td>
                    <td>${asset.timestamp}</td>
                `;
                tableBody.appendChild(row);
            });
        })
        .catch(err => console.error("Dashboard load error:", err));
};
