import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import os

class Report:
    def __init__(self, report_type: str, device_hostname: str, timestamp: datetime, results: str,
                 device_info: Dict = None):
        self.report_type = report_type
        self.device_hostname = device_hostname
        self.timestamp = timestamp
        self.results = results
        self.device_info = device_info or {}

    @classmethod
    def from_dict(cls, data: Dict):
        return cls(
            report_type=data['report_type'],
            device_hostname=data['device_hostname'],
            timestamp=datetime.fromisoformat(data['timestamp']),
            results=data['results'],
            device_info=data.get('device_info', {})
        )

    def to_dict(self) -> Dict:
        return {
            'report_type': self.report_type,
            'device_hostname': self.device_hostname,
            'timestamp': self.timestamp.isoformat(),
            'results': self.results,
            'device_info': self.device_info
        }

class ReportManager:
    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent
        self.reports_dir = self.project_root / 'reports'
        self.reports_dir.mkdir(exist_ok=True)

    def save_report(self, report: Report):
        """Save a report to file"""
        # Create directory for report type if it doesn't exist
        report_type_dir = self.reports_dir / report.report_type
        report_type_dir.mkdir(exist_ok=True)

        # Create filename with timestamp and hostname
        filename = f"{report.timestamp.strftime('%Y%m%d_%H%M%S')}_{report.device_hostname}.json"
        filepath = report_type_dir / filename

        # Save report to file
        with open(filepath, 'w') as f:
            json.dump(report.to_dict(), f, indent=2)

    def get_reports(self, report_type: Optional[str] = None) -> List[Report]:
        """Get all reports, optionally filtered by type"""
        reports = []
        
        # Determine which directories to search
        if report_type:
            dirs = [self.reports_dir / report_type]
        else:
            dirs = [d for d in self.reports_dir.iterdir() if d.is_dir()]

        # Collect reports from directories
        for directory in dirs:
            if directory.exists():
                for file in directory.glob('*.json'):
                    try:
                        with open(file, 'r') as f:
                            data = json.load(f)
                            reports.append(Report.from_dict(data))
                    except Exception as e:
                        print(f"Error loading report {file}: {e}")

        # Sort reports by timestamp, newest first
        return sorted(reports, key=lambda x: x.timestamp, reverse=True)

    def delete_report(self, report_type: str, filename: str):
        """Delete a specific report"""
        filepath = self.reports_dir / report_type / filename
        if filepath.exists():
            filepath.unlink() 