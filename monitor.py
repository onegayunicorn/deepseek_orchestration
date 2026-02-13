#!/usr/bin/env python3
"""
DeepSeek Orchestrator - System Monitor
Monitors orchestrator health and performance
"""

import os
import sys
import time
import json
import sqlite3
from pathlib import Path
from datetime import datetime, timedelta

class OrchestratorMonitor:
    """Monitor for orchestrator health and performance"""
    
    def __init__(self, config_path="config.json"):
        with open(config_path, 'r') as f:
            self.config = json.load(f)
        
        self.db_path = self.config.get('audit_log', 'deepseek_audit.db')
        self.triggers_dir = Path(self.config.get('file_watch', {}).get('watch_dir', './triggers'))
    
    def get_queue_status(self):
        """Get current queue status"""
        pending_tasks = list(self.triggers_dir.glob("*.task"))
        completed_results = list(self.triggers_dir.glob("*.result"))
        
        return {
            'pending_tasks': len(pending_tasks),
            'completed_results': len(completed_results),
            'oldest_pending': self._get_oldest_file(pending_tasks),
            'newest_result': self._get_newest_file(completed_results)
        }
    
    def _get_oldest_file(self, files):
        """Get the oldest file from a list"""
        if not files:
            return None
        oldest = min(files, key=lambda f: f.stat().st_mtime)
        age = time.time() - oldest.stat().st_mtime
        return {
            'file': oldest.name,
            'age_seconds': int(age)
        }
    
    def _get_newest_file(self, files):
        """Get the newest file from a list"""
        if not files:
            return None
        newest = max(files, key=lambda f: f.stat().st_mtime)
        age = time.time() - newest.stat().st_mtime
        return {
            'file': newest.name,
            'age_seconds': int(age)
        }
    
    def get_audit_stats(self, hours=24):
        """Get audit statistics for the last N hours"""
        if not Path(self.db_path).exists():
            return None
        
        cutoff = (datetime.now() - timedelta(hours=hours)).isoformat()
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Total events
        cursor.execute("SELECT COUNT(*) FROM audit_log WHERE timestamp > ?", (cutoff,))
        total = cursor.fetchone()[0]
        
        # Executed commands
        cursor.execute("SELECT COUNT(*) FROM audit_log WHERE timestamp > ? AND executed = 1", (cutoff,))
        executed = cursor.fetchone()[0]
        
        # Rejected commands
        cursor.execute("SELECT COUNT(*) FROM audit_log WHERE timestamp > ? AND approved = 0", (cutoff,))
        rejected = cursor.fetchone()[0]
        
        # Failed executions
        cursor.execute("""
            SELECT COUNT(*) FROM audit_log 
            WHERE timestamp > ? AND executed = 1 
            AND execution_result LIKE '%"success": false%'
        """, (cutoff,))
        failed = cursor.fetchone()[0]
        
        # Commands by source
        cursor.execute("""
            SELECT trigger_source, COUNT(*) as count
            FROM audit_log 
            WHERE timestamp > ?
            GROUP BY trigger_source
            ORDER BY count DESC
        """, (cutoff,))
        by_source = {row[0]: row[1] for row in cursor.fetchall()}
        
        conn.close()
        
        return {
            'period_hours': hours,
            'total_events': total,
            'executed': executed,
            'rejected': rejected,
            'failed': failed,
            'success_rate': round(((executed - failed) / executed * 100) if executed > 0 else 0, 2),
            'by_source': by_source
        }
    
    def check_health(self):
        """Perform health check"""
        issues = []
        warnings = []
        
        # Check if database exists
        if not Path(self.db_path).exists():
            warnings.append("Audit database does not exist yet")
        
        # Check if triggers directory exists
        if not self.triggers_dir.exists():
            issues.append(f"Triggers directory does not exist: {self.triggers_dir}")
        
        # Check for stale tasks (older than 5 minutes)
        queue = self.get_queue_status()
        if queue['oldest_pending'] and queue['oldest_pending']['age_seconds'] > 300:
            warnings.append(f"Stale task detected: {queue['oldest_pending']['file']} ({queue['oldest_pending']['age_seconds']}s old)")
        
        # Check for too many pending tasks
        if queue['pending_tasks'] > 10:
            warnings.append(f"High number of pending tasks: {queue['pending_tasks']}")
        
        return {
            'healthy': len(issues) == 0,
            'issues': issues,
            'warnings': warnings,
            'timestamp': datetime.now().isoformat()
        }
    
    def get_full_status(self):
        """Get complete status report"""
        return {
            'timestamp': datetime.now().isoformat(),
            'health': self.check_health(),
            'queue': self.get_queue_status(),
            'audit_24h': self.get_audit_stats(24),
            'audit_1h': self.get_audit_stats(1)
        }
    
    def watch_mode(self, interval=10):
        """Continuously monitor and display status"""
        print("DeepSeek Orchestrator Monitor")
        print("=" * 60)
        print("Press Ctrl+C to stop\n")
        
        try:
            while True:
                os.system('clear' if os.name == 'posix' else 'cls')
                
                print(f"DeepSeek Orchestrator Monitor - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                print("=" * 60)
                
                status = self.get_full_status()
                
                # Health status
                health = status['health']
                health_icon = "✓" if health['healthy'] else "✗"
                print(f"\n{health_icon} Health: {'Healthy' if health['healthy'] else 'Issues Detected'}")
                
                if health['issues']:
                    print("\n  Issues:")
                    for issue in health['issues']:
                        print(f"    ✗ {issue}")
                
                if health['warnings']:
                    print("\n  Warnings:")
                    for warning in health['warnings']:
                        print(f"    ⚠ {warning}")
                
                # Queue status
                queue = status['queue']
                print(f"\nQueue Status:")
                print(f"  Pending tasks: {queue['pending_tasks']}")
                print(f"  Completed results: {queue['completed_results']}")
                
                if queue['oldest_pending']:
                    print(f"  Oldest pending: {queue['oldest_pending']['file']} ({queue['oldest_pending']['age_seconds']}s)")
                
                # Audit stats (last hour)
                if status['audit_1h']:
                    stats_1h = status['audit_1h']
                    print(f"\nLast Hour:")
                    print(f"  Total events: {stats_1h['total_events']}")
                    print(f"  Executed: {stats_1h['executed']}")
                    print(f"  Rejected: {stats_1h['rejected']}")
                    print(f"  Failed: {stats_1h['failed']}")
                    print(f"  Success rate: {stats_1h['success_rate']}%")
                
                # Audit stats (last 24 hours)
                if status['audit_24h']:
                    stats_24h = status['audit_24h']
                    print(f"\nLast 24 Hours:")
                    print(f"  Total events: {stats_24h['total_events']}")
                    print(f"  Executed: {stats_24h['executed']}")
                    print(f"  Success rate: {stats_24h['success_rate']}%")
                    
                    if stats_24h['by_source']:
                        print(f"\n  By source:")
                        for source, count in list(stats_24h['by_source'].items())[:5]:
                            print(f"    {source}: {count}")
                
                print(f"\n{'=' * 60}")
                print(f"Refreshing in {interval}s...")
                
                time.sleep(interval)
        
        except KeyboardInterrupt:
            print("\n\nMonitor stopped")


def main():
    """CLI interface for the monitor"""
    import argparse
    
    parser = argparse.ArgumentParser(description='DeepSeek Orchestrator Monitor')
    parser.add_argument('--config', default='config.json', help='Path to configuration file')
    parser.add_argument('--watch', action='store_true', help='Continuous monitoring mode')
    parser.add_argument('--interval', type=int, default=10, help='Refresh interval for watch mode')
    parser.add_argument('--json', action='store_true', help='Output as JSON')
    
    args = parser.parse_args()
    
    monitor = OrchestratorMonitor(args.config)
    
    if args.watch:
        monitor.watch_mode(interval=args.interval)
    else:
        status = monitor.get_full_status()
        
        if args.json:
            print(json.dumps(status, indent=2))
        else:
            print("DeepSeek Orchestrator Status")
            print("=" * 60)
            print(json.dumps(status, indent=2))


if __name__ == '__main__':
    main()
