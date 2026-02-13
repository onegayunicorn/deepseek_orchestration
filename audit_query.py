#!/usr/bin/env python3
"""
DeepSeek Orchestrator - Audit Query Tool
Query and analyze the audit database
"""

import sqlite3
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

class AuditQuery:
    """Query tool for the audit database"""
    
    def __init__(self, db_path="deepseek_audit.db"):
        self.db_path = db_path
        if not Path(db_path).exists():
            print(f"Warning: Database {db_path} does not exist yet")
    
    def query(self, sql, params=()):
        """Execute a SQL query"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(sql, params)
        results = cursor.fetchall()
        conn.close()
        return results
    
    def recent_events(self, limit=10):
        """Get recent events"""
        sql = """
            SELECT timestamp, event_type, trigger_source, 
                   suggested_command, approved, executed
            FROM audit_log 
            ORDER BY timestamp DESC 
            LIMIT ?
        """
        return self.query(sql, (limit,))
    
    def executed_commands(self, limit=20):
        """Get recently executed commands"""
        sql = """
            SELECT timestamp, trigger_source, deepseek_input, 
                   suggested_command, execution_result
            FROM audit_log 
            WHERE executed = 1
            ORDER BY timestamp DESC 
            LIMIT ?
        """
        return self.query(sql, (limit,))
    
    def rejected_commands(self, limit=20):
        """Get rejected commands"""
        sql = """
            SELECT timestamp, trigger_source, deepseek_input, 
                   suggested_command, execution_result
            FROM audit_log 
            WHERE approved = 0 OR (approved = 1 AND executed = 0)
            ORDER BY timestamp DESC 
            LIMIT ?
        """
        return self.query(sql, (limit,))
    
    def commands_by_source(self):
        """Get command counts by source"""
        sql = """
            SELECT trigger_source, 
                   COUNT(*) as total,
                   SUM(CASE WHEN executed = 1 THEN 1 ELSE 0 END) as executed,
                   SUM(CASE WHEN approved = 0 THEN 1 ELSE 0 END) as rejected
            FROM audit_log 
            GROUP BY trigger_source
            ORDER BY total DESC
        """
        return self.query(sql)
    
    def commands_by_type(self):
        """Get command counts by event type"""
        sql = """
            SELECT event_type, COUNT(*) as count
            FROM audit_log 
            GROUP BY event_type
            ORDER BY count DESC
        """
        return self.query(sql)
    
    def search_commands(self, keyword):
        """Search for commands containing a keyword"""
        sql = """
            SELECT timestamp, trigger_source, deepseek_input, 
                   suggested_command, executed
            FROM audit_log 
            WHERE suggested_command LIKE ? 
               OR deepseek_input LIKE ?
            ORDER BY timestamp DESC
        """
        pattern = f"%{keyword}%"
        return self.query(sql, (pattern, pattern))
    
    def time_range(self, hours=24):
        """Get events from the last N hours"""
        cutoff = (datetime.now() - timedelta(hours=hours)).isoformat()
        sql = """
            SELECT timestamp, event_type, trigger_source, 
                   suggested_command, executed
            FROM audit_log 
            WHERE timestamp > ?
            ORDER BY timestamp DESC
        """
        return self.query(sql, (cutoff,))
    
    def statistics(self):
        """Get overall statistics"""
        stats = {}
        
        # Total events
        result = self.query("SELECT COUNT(*) as count FROM audit_log")
        stats['total_events'] = result[0]['count'] if result else 0
        
        # Executed commands
        result = self.query("SELECT COUNT(*) as count FROM audit_log WHERE executed = 1")
        stats['executed_commands'] = result[0]['count'] if result else 0
        
        # Rejected commands
        result = self.query("SELECT COUNT(*) as count FROM audit_log WHERE approved = 0")
        stats['rejected_commands'] = result[0]['count'] if result else 0
        
        # Most common sources
        stats['top_sources'] = [dict(row) for row in self.commands_by_source()]
        
        # Event types
        stats['event_types'] = [dict(row) for row in self.commands_by_type()]
        
        return stats


def print_table(rows, columns):
    """Print results as a formatted table"""
    if not rows:
        print("No results found")
        return
    
    # Convert Row objects to dicts
    data = [dict(row) for row in rows]
    
    # Calculate column widths
    widths = {}
    for col in columns:
        widths[col] = max(len(str(col)), max(len(str(row.get(col, ''))) for row in data))
    
    # Print header
    header = " | ".join(str(col).ljust(widths[col]) for col in columns)
    print(header)
    print("-" * len(header))
    
    # Print rows
    for row in data:
        print(" | ".join(str(row.get(col, '')).ljust(widths[col]) for col in columns))


def main():
    """CLI interface for audit queries"""
    import argparse
    
    parser = argparse.ArgumentParser(description='DeepSeek Orchestrator Audit Query Tool')
    parser.add_argument('--db', default='deepseek_audit.db', help='Path to audit database')
    
    subparsers = parser.add_subparsers(dest='command', help='Query command')
    
    # Recent events
    recent_parser = subparsers.add_parser('recent', help='Show recent events')
    recent_parser.add_argument('--limit', type=int, default=10, help='Number of events to show')
    
    # Executed commands
    exec_parser = subparsers.add_parser('executed', help='Show executed commands')
    exec_parser.add_argument('--limit', type=int, default=20, help='Number of commands to show')
    
    # Rejected commands
    reject_parser = subparsers.add_parser('rejected', help='Show rejected commands')
    reject_parser.add_argument('--limit', type=int, default=20, help='Number of commands to show')
    
    # Statistics
    subparsers.add_parser('stats', help='Show statistics')
    
    # Search
    search_parser = subparsers.add_parser('search', help='Search for commands')
    search_parser.add_argument('keyword', help='Keyword to search for')
    
    # Time range
    time_parser = subparsers.add_parser('timerange', help='Show events from last N hours')
    time_parser.add_argument('--hours', type=int, default=24, help='Number of hours')
    
    # Sources
    subparsers.add_parser('sources', help='Show commands by source')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    aq = AuditQuery(args.db)
    
    if args.command == 'recent':
        results = aq.recent_events(args.limit)
        print(f"\n=== Recent Events (last {args.limit}) ===\n")
        print_table(results, ['timestamp', 'event_type', 'trigger_source', 'suggested_command', 'executed'])
    
    elif args.command == 'executed':
        results = aq.executed_commands(args.limit)
        print(f"\n=== Executed Commands (last {args.limit}) ===\n")
        print_table(results, ['timestamp', 'trigger_source', 'deepseek_input', 'suggested_command'])
    
    elif args.command == 'rejected':
        results = aq.rejected_commands(args.limit)
        print(f"\n=== Rejected Commands (last {args.limit}) ===\n")
        print_table(results, ['timestamp', 'trigger_source', 'deepseek_input', 'suggested_command'])
    
    elif args.command == 'stats':
        stats = aq.statistics()
        print("\n=== Audit Statistics ===\n")
        print(json.dumps(stats, indent=2))
    
    elif args.command == 'search':
        results = aq.search_commands(args.keyword)
        print(f"\n=== Search Results for '{args.keyword}' ===\n")
        print_table(results, ['timestamp', 'trigger_source', 'suggested_command', 'executed'])
    
    elif args.command == 'timerange':
        results = aq.time_range(args.hours)
        print(f"\n=== Events from last {args.hours} hours ===\n")
        print_table(results, ['timestamp', 'event_type', 'trigger_source', 'suggested_command', 'executed'])
    
    elif args.command == 'sources':
        results = aq.commands_by_source()
        print("\n=== Commands by Source ===\n")
        print_table(results, ['trigger_source', 'total', 'executed', 'rejected'])


if __name__ == '__main__':
    main()
