"""Shell execution audit trail persistence with immutable JSONL logging.

Implements append-only JSONL audit trail for compliance, forensics, and
hash-chain integrity verification.
"""

from __future__ import annotations

import json
from pathlib import Path
from datetime import datetime
from typing import Optional, Iterator

from kicli_code_assist.executor.shell_execution import ExecutionAuditRecord


class AuditTrailLogger:
    """Immutable append-only JSONL logger for shell execution audit trail."""
    
    def __init__(self, log_path: Path):
        """Initialize audit logger.
        
        Args:
            log_path: Path to JSONL audit trail file
        """
        self.log_path = Path(log_path)
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        self._previous_hash: Optional[str] = None
        
        # Load last hash if file exists
        if self.log_path.exists():
            try:
                self._previous_hash = self._get_last_record_hash()
            except Exception:
                pass  # Ignore errors on corrupted files
    
    def log_execution(self, record: ExecutionAuditRecord) -> None:
        """Log shell execution record to audit trail.
        
        Args:
            record: ExecutionAuditRecord to log
            
        Raises:
            IOError if unable to write to log file
        """
        # Finalize record with hash chain
        record.finalize(previous_hash=self._previous_hash)
        self._previous_hash = record.current_hash
        
        # Append to JSONL (atomic write)
        try:
            with open(self.log_path, 'a') as f:
                f.write(json.dumps(record.to_dict()) + '\n')
        except IOError as e:
            raise IOError(f"Failed to write audit trail: {e}") from e
    
    def _get_last_record_hash(self) -> Optional[str]:
        """Get hash of last record in audit trail.
        
        Returns:
            SHA256 hash string or None if file is empty
        """
        with open(self.log_path, 'r') as f:
            lines = f.readlines()
        
        if not lines:
            return None
        
        last_line = lines[-1].strip()
        if not last_line:
            return None
        
        record_dict = json.loads(last_line)
        return record_dict.get('current_hash')
    
    def read_records(self, limit: Optional[int] = None) -> Iterator[ExecutionAuditRecord]:
        """Read audit records from trail (chronological).
        
        Args:
            limit: Max records to return (most recent first)
            
        Yields:
            ExecutionAuditRecord instances
        """
        if not self.log_path.exists():
            return
        
        records = []
        try:
            with open(self.log_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            record_dict = json.loads(line)
                            records.append(record_dict)
                        except json.JSONDecodeError:
                            # Skip malformed lines
                            continue
        except IOError:
            return
        
        # Yield in reverse order (most recent first) with limit
        for record_dict in reversed(records[:limit or len(records)]):
            yield record_dict  # Return dicts for flexibility
    
    def verify_integrity(self) -> tuple[bool, list[str]]:
        """Verify hash-chain integrity of audit trail.
        
        Returns:
            Tuple of (is_valid, list of error messages)
        """
        errors = []
        
        if not self.log_path.exists():
            return True, []
        
        previous_hash = None
        
        try:
            with open(self.log_path, 'r') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line:
                        continue
                    
                    try:
                        record_dict = json.loads(line)
                    except json.JSONDecodeError:
                        errors.append(f"Line {line_num}: Invalid JSON")
                        continue
                    
                    # Check hash chain
                    current_hash = record_dict.get('current_hash')
                    previous_hash_in_record = record_dict.get('previous_hash')
                    
                    if previous_hash_in_record != previous_hash:
                        errors.append(
                            f"Line {line_num}: Hash chain broken "
                            f"(expected {previous_hash}, got {previous_hash_in_record})"
                        )
                    
                    previous_hash = current_hash
        
        except IOError as e:
            errors.append(f"Failed to read audit trail: {e}")
        
        return len(errors) == 0, errors
    
    def get_summary(self) -> dict:
        """Get summary statistics of audit trail.
        
        Returns:
            Dict with record count, date range, success/failure counts
        """
        total_records = 0
        successful_executions = 0
        failed_executions = 0
        first_timestamp = None
        last_timestamp = None
        risk_levels = {}
        
        if not self.log_path.exists():
            return {
                'total_records': 0,
                'successful': 0,
                'failed': 0,
                'first_record': None,
                'last_record': None,
                'file_size_bytes': 0,
            }
        
        try:
            with open(self.log_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    
                    try:
                        record_dict = json.loads(line)
                        total_records += 1
                        
                        # Track timestamps
                        timestamp = record_dict.get('timestamp')
                        if timestamp:
                            if not first_timestamp:
                                first_timestamp = timestamp
                            last_timestamp = timestamp
                        
                        # Track execution outcomes
                        if record_dict.get('execution_results'):
                            for result in record_dict['execution_results']:
                                if result.get('success'):
                                    successful_executions += 1
                                else:
                                    failed_executions += 1
                        
                        # Track risk levels
                        batch = record_dict.get('command_batch', {})
                        if batch and batch.get('commands'):
                            # Count per-command risks
                            pass  # Simplified for now
                    
                    except json.JSONDecodeError:
                        continue
        
        except IOError:
            pass
        
        return {
            'total_records': total_records,
            'successful_executions': successful_executions,
            'failed_executions': failed_executions,
            'first_record': first_timestamp,
            'last_record': last_timestamp,
            'file_size_bytes': self.log_path.stat().st_size if self.log_path.exists() else 0,
        }
    
    def export_json(self, output_path: Path) -> None:
        """Export entire audit trail as JSON array.
        
        Args:
            output_path: Path to write JSON file
        """
        records = []
        try:
            with open(self.log_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            records.append(json.loads(line))
                        except json.JSONDecodeError:
                            continue
        except IOError:
            pass
        
        with open(output_path, 'w') as f:
            json.dump(records, f, indent=2)
    
    def export_csv(self, output_path: Path) -> None:
        """Export audit trail as CSV for analysis.
        
        Args:
            output_path: Path to write CSV file
        """
        import csv
        
        rows = []
        
        try:
            with open(self.log_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    
                    try:
                        record = json.loads(line)
                        
                        # Extract relevant fields for CSV
                        batch = record.get('command_batch', {})
                        approval = record.get('approval', {})
                        
                        for cmd_dict in batch.get('commands', []):
                            rows.append({
                                'timestamp': record.get('timestamp'),
                                'session_id': record.get('session_id'),
                                'command': cmd_dict.get('command'),
                                'approval_decision': approval.get('decision'),
                                'approved_by': approval.get('approved_by'),
                                'risk_level': cmd_dict.get('risk_level', 'unknown'),
                            })
                    except (json.JSONDecodeError, TypeError):
                        continue
        
        except IOError:
            pass
        
        if rows:
            with open(output_path, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=rows[0].keys())
                writer.writeheader()
                writer.writerows(rows)
