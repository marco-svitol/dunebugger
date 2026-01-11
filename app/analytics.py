"""
Analytics module for parsing dunebugger logs and providing simple metrics.
"""

import re
import subprocess
from datetime import datetime
from typing import List, Dict, Optional, Tuple
import os


class LogAnalytics:
    """
    Class for analyzing dunebugger logs to extract metrics about start button presses.
    
    Supports two log sources:
    1. Production (systemd): via journalctl -u dunebugger.service
    2. Development: from log files
    """
    
    # Regular expression patterns for parsing log entries
    # Pattern for systemd logs: "Jan 10 17:46:19 rpi4bDB2025 python[596]: INFO - 10/01/2026 17:46:19 : Start button pressed"
    SYSTEMD_PATTERN = re.compile(
        r'python\[\d+\]:\s+(?:INFO|DEBUG|WARNING|ERROR)\s+-\s+(\d{2}/\d{2}/\d{4}\s+\d{2}:\d{2}:\d{2})\s+:\s+Start button pressed'
    )
    
    # Pattern for file logs: "INFO - 05/01/2026 15:40:38 : Start button pressed"
    FILE_PATTERN = re.compile(
        r'(?:INFO|DEBUG|WARNING|ERROR)\s+-\s+(\d{2}/\d{2}/\d{4}\s+\d{2}:\d{2}:\d{2})\s+:\s+Start button pressed'
    )
    
    TIMESTAMP_FORMAT = "%m/%d/%Y %H:%M:%S"
    
    def __init__(self, systemd_service_name: str = "dunebugger.service", log_file_path: Optional[str] = None):
        """
        Initialize the LogAnalytics class.
        
        Args:
            systemd_service_name: Name of the systemd service for production logs
            log_file_path: Path to the log file for development logs
        """
        self.systemd_service_name = systemd_service_name
        self.log_file_path = log_file_path
    
    def is_running_as_systemd(self) -> bool:
        """
        Check if the application is running as a systemd service.
        
        Returns:
            True if running as systemd service, False otherwise
        """
        try:
            result = subprocess.run(
                ['systemctl', 'is-active', self.systemd_service_name],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except (subprocess.SubprocessError, FileNotFoundError):
            return False
    
    def get_systemd_logs(self, since: Optional[str] = None) -> List[str]:
        """
        Fetch logs from systemd journal.
        
        Args:
            since: Optional time filter (e.g., "today", "1 week ago", "2025-01-01")
        
        Returns:
            List of log lines
        """
        cmd = ['journalctl', '-u', self.systemd_service_name, '--no-pager']
        
        if since:
            cmd.extend(['--since', since])
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                return result.stdout.splitlines()
            else:
                raise RuntimeError(f"journalctl command failed with code {result.returncode}: {result.stderr}")
        
        except subprocess.TimeoutExpired:
            raise RuntimeError("journalctl command timed out")
        except FileNotFoundError:
            raise RuntimeError("journalctl command not found")
    
    def get_file_logs(self) -> List[str]:
        """
        Read logs from file.
        
        Returns:
            List of log lines
        """
        if not self.log_file_path:
            raise ValueError("Log file path not configured")
        
        if not os.path.exists(self.log_file_path):
            raise FileNotFoundError(f"Log file not found: {self.log_file_path}")
        
        with open(self.log_file_path, 'r', encoding='utf-8') as f:
            return f.readlines()
    
    def parse_start_button_events(self, log_lines: List[str], use_systemd_pattern: bool = False) -> List[str]:
        """
        Parse log lines to extract start button press timestamps.
        
        Args:
            log_lines: List of log lines to parse
            use_systemd_pattern: If True, use systemd log pattern; otherwise use file pattern
        
        Returns:
            List of timestamp strings in format "MM/DD/YYYY HH:MM:SS"
        """
        pattern = self.SYSTEMD_PATTERN if use_systemd_pattern else self.FILE_PATTERN
        timestamps = []
        
        for line in log_lines:
            match = pattern.search(line)
            if match:
                timestamp_str = match.group(1)
                try:
                    # Validate the timestamp format by parsing it
                    datetime.strptime(timestamp_str, self.TIMESTAMP_FORMAT)
                    # Keep it as string for JSON serialization
                    timestamps.append(timestamp_str)
                except ValueError as e:
                    # Skip lines with invalid timestamp format
                    continue
        
        return timestamps
    
    def get_start_button_events_from_systemd(self, since: Optional[str] = None) -> List[str]:
        """
        Get start button press events from systemd journal.
        
        Args:
            since: Optional time filter (e.g., "today", "1 week ago", "2025-01-01")
        
        Returns:
            List of timestamp strings for each start button press
        """
        log_lines = self.get_systemd_logs(since=since)
        return self.parse_start_button_events(log_lines, use_systemd_pattern=True)
    
    def get_start_button_events_from_file(self) -> List[str]:
        """
        Get start button press events from log file.
        
        Returns:
            List of timestamp strings for each start button press
        """
        log_lines = self.get_file_logs()
        return self.parse_start_button_events(log_lines, use_systemd_pattern=False)
    
    def get_start_button_events(self, since: Optional[str] = None) -> List[str]:
        """
        Get start button press events, automatically detecting the log source.
        
        Args:
            since: Optional time filter for systemd logs (e.g., "today", "1 week ago")
        
        Returns:
            List of timestamp strings for each start button press
        """
        if self.is_running_as_systemd():
            return self.get_start_button_events_from_systemd(since=since)
        else:
            return self.get_start_button_events_from_file()
    
    def get_metrics(self, since: Optional[str] = None) -> Dict[str, any]:
        """
        Get analytics metrics for start button presses.
        
        Args:
            since: Optional time filter for systemd logs
        
        Returns:
            Dictionary containing:
                - count: Total number of start button presses
                - timestamps: List of timestamp strings
                - first_press: First press timestamp string (or None)
                - last_press: Last press timestamp string (or None)
                - log_source: Source of logs ("systemd" or "file")
        """
        is_systemd = self.is_running_as_systemd()
        timestamps = self.get_start_button_events(since=since)
        
        metrics = {
            "count": len(timestamps),
            "timestamps": timestamps,
            "first_press": timestamps[0] if timestamps else None,
            "last_press": timestamps[-1] if timestamps else None,
            "log_source": "systemd" if is_systemd else "file"
        }
        
        return metrics
    
    def format_metrics_summary(self, metrics: Dict[str, any]) -> str:
        """
        Format metrics into a human-readable summary.
        
        Args:
            metrics: Metrics dictionary from get_metrics()
        
        Returns:
            Formatted string summary
        """
        lines = []
        lines.append(f"Log Source: {metrics['log_source']}")
        lines.append(f"Total Start Button Presses: {metrics['count']}")
        
        if metrics['first_press']:
            lines.append(f"First Press: {metrics['first_press']}")
        
        if metrics['last_press']:
            lines.append(f"Last Press: {metrics['last_press']}")
        
        if metrics['count'] > 0:
            lines.append("\nAll Press Timestamps:")
            for i, ts in enumerate(metrics['timestamps'], 1):
                lines.append(f"  {i}. {ts}")
        
        return "\n".join(lines)

    def execute_metrics_command(self, args: Optional[List[str]] = None) -> str:
        """
        Execute the metrics command to get start button press analytics.
        
        Args:
            args: Command arguments (currently unused)
        
        Returns:
            Formatted metrics summary string
        """
        metrics = self.get_metrics()
        return self.format_metrics_summary(metrics)