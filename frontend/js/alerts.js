window.onload = function () {
    loadAlerts();

    document.getElementById("clearBtn").addEventListener("click", function () {
        if (!confirm("Are you sure you want to clear all violation alerts?")) return;

        fetch("http://127.0.0.1:5000/api/alerts/clear", {
            method: "DELETE"
        })
        .then(res => res.json())
        .then(data => {
            alert(data.message);
            loadAlerts();
        })
        .catch(err => {
            console.error("Error clearing alerts:", err);
            alert("Failed to clear alerts");
        });
    });
};

function formatDateTime(utcString) {
    const d = new Date(utcString); // auto converts UTC → local
    return d.toLocaleString("en-IN", {
        year: "numeric",
        month: "2-digit",
        day: "2-digit",
        hour: "2-digit",
        minute: "2-digit",
        second: "2-digit",
        hour12: true
    });
}

function loadAlerts() {
    fetch("http://127.0.0.1:5000/api/alerts")
        .then(res => res.json())
        .then(data => {
            const tableBody = document.querySelector("#violationTable tbody");
            tableBody.innerHTML = "";

            if (!data.violations || data.violations.length === 0) {
                tableBody.innerHTML = `
                    <tr>
                        <td colspan="5" style="text-align:center;">
                            No violations detected
                        </td>
                    </tr>
                `;
                return;
            }

            data.violations.forEach(v => {
                const row = document.createElement("tr");
                row.innerHTML = `
                    <td>${v.original_file}</td>
                    <td>${v.matched_source}</td>
                    <td>${v.similarity}%</td>
                    <td>${formatDateTime(v.date)}</td>
                    <td>${v.status}</td>
                `;
                tableBody.appendChild(row);
            });
        })
        .catch(err => {
            console.error("Error loading alerts:", err);
        });
}
