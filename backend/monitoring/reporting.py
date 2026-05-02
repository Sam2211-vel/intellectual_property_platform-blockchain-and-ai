import os
from datetime import datetime

REPORT_DIR = "monitoring/reports"
SCREENSHOT_DIR = "monitoring/screenshots"

os.makedirs(REPORT_DIR, exist_ok=True)
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

def generate_report(violations):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = os.path.join(REPORT_DIR, f"violation_report_{timestamp}.txt")

    with open(report_path, "w") as report:
        report.write("SMART IP GUARD – VIOLATION REPORT\n")
        report.write("="*40 + "\n\n")

        if not violations:
            report.write("No violations detected.\n")
        else:
            for v in violations:
                report.write(f"File: {v['file']}\n")
                report.write(f"Hash: {v['hash']}\n")
                report.write(f"Status: {v['status']}\n")
                report.write("-"*30 + "\n")

    return report_path


if __name__ == "__main__":
    sample_violations = [{
        "file": "content_1.txt",
        "hash": "dummy_hash",
        "status": "VIOLATION DETECTED"
    }]

    report = generate_report(sample_violations)
    print("Report generated at:", report)
