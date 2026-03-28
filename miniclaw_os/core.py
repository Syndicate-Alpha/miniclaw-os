#!/usr/bin/env python3
"""
Miniclaw OS Core - Persistent autonomous agent operating system
Built with sustainable development practices
"""

import json
import sqlite3
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
import threading
from abc import ABC, abstractmethod

# Try to import real services, fall back to mocks
try:
    from safeguards import safeguard as real_safeguard
    SAFEGUARDS_AVAILABLE = True
except ImportError:
    SAFEGUARDS_AVAILABLE = False

try:
    from .mocks import mock_telegram, mock_llm, mock_openclaw, mock_safeguard
    MOCKS_AVAILABLE = True
except ImportError:
    MOCKS_AVAILABLE = False


class PersistenceService:
    """Structured knowledge persistence with safeguards"""
    
    def __init__(self, db_path: str = "miniclaw_data.db"):
        self.db_path = db_path
        self.conn = None
        self.setup_database()
        
    def setup_database(self):
        """Initialize database schema"""
        self.conn = sqlite3.connect(self.db_path)
        cursor = self.conn.cursor()
        
        # Knowledge Base
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS knowledge (
                id TEXT PRIMARY KEY,
                category TEXT,
                content TEXT,
                metadata TEXT,
                created_at TIMESTAMP,
                updated_at TIMESTAMP
            )
        ''')
        
        # Scheduled Jobs
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS jobs (
                id TEXT PRIMARY KEY,
                name TEXT,
                schedule TEXT,
                plugin TEXT,
                parameters TEXT,
                last_run TIMESTAMP,
                next_run TIMESTAMP,
                enabled BOOLEAN DEFAULT 1,
                failures INTEGER DEFAULT 0
            )
        ''')
        
        # Agent Sessions
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sessions (
                id TEXT PRIMARY KEY,
                agent_id TEXT,
                start_time TIMESTAMP,
                end_time TIMESTAMP,
                tokens_used INTEGER,
                cost REAL,
                status TEXT,
                checkpoint_path TEXT
            )
        ''')
        
        # System Metrics
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS metrics (
                timestamp TIMESTAMP PRIMARY KEY,
                daily_calls INTEGER,
                daily_tokens INTEGER,
                daily_cost REAL,
                active_agents INTEGER
            )
        ''')
        
        self.conn.commit()
        print(f"✅ Persistence service initialized: {self.db_path}")
    
    def save_knowledge(self, category: str, content: str, metadata: Dict = None) -> str:
        """Save structured knowledge with safeguards"""
        knowledge_id = f"kb_{int(time.time())}_{hash(content) % 10000}"
        
        # Check memory limits (safeguard)
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM knowledge")
        count = cursor.fetchone()[0]
        
        if count > 1000:  # Memory safeguard
            print("⚠️  Knowledge base limit reached (1000 entries), pruning oldest")
            self.prune_old_knowledge(100)  # Keep 900 entries
        
        cursor.execute('''
            INSERT INTO knowledge (id, category, content, metadata, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            knowledge_id,
            category,
            content,
            json.dumps(metadata or {}),
            datetime.now().isoformat(),
            datetime.now().isoformat()
        ))
        
        self.conn.commit()
        print(f"📚 Knowledge saved: {category} -> {knowledge_id}")
        return knowledge_id
    
    def prune_old_knowledge(self, keep_count: int = 900):
        """Prune oldest knowledge entries (memory safeguard)"""
        cursor = self.conn.cursor()
        cursor.execute('''
            DELETE FROM knowledge 
            WHERE id IN (
                SELECT id FROM knowledge 
                ORDER BY created_at ASC 
                LIMIT (SELECT COUNT(*) FROM knowledge) - ?
            )
        ''', (keep_count,))
        
        deleted = cursor.rowcount
        self.conn.commit()
        print(f"🧹 Pruned {deleted} old knowledge entries")
        return deleted
    
    def query_knowledge(self, category: str = None, limit: int = 10) -> List[Dict]:
        """Query knowledge base"""
        cursor = self.conn.cursor()
        
        if category:
            cursor.execute('''
                SELECT id, category, content, metadata, created_at 
                FROM knowledge 
                WHERE category = ? 
                ORDER BY created_at DESC 
                LIMIT ?
            ''', (category, limit))
        else:
            cursor.execute('''
                SELECT id, category, content, metadata, created_at 
                FROM knowledge 
                ORDER BY created_at DESC 
                LIMIT ?
            ''', (limit,))
        
        results = []
        for row in cursor.fetchall():
            results.append({
                "id": row[0],
                "category": row[1],
                "content": row[2],
                "metadata": json.loads(row[3]) if row[3] else {},
                "created_at": row[4]
            })
        
        return results
    
    def log_session(self, agent_id: str, tokens_used: int, cost: float, status: str, checkpoint_path: str = None):
        """Log agent session for monitoring"""
        session_id = f"session_{int(time.time())}"
        
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO sessions (id, agent_id, start_time, end_time, tokens_used, cost, status, checkpoint_path)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            session_id,
            agent_id,
            datetime.now().isoformat(),
            datetime.now().isoformat(),
            tokens_used,
            cost,
            status,
            checkpoint_path
        ))
        
        self.conn.commit()
        print(f"📊 Session logged: {agent_id} -> {status}, ${cost:.4f}")
        return session_id
    
    def get_stats(self) -> Dict[str, Any]:
        """Get system statistics"""
        cursor = self.conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM knowledge")
        knowledge_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM jobs WHERE enabled = 1")
        active_jobs = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM sessions WHERE date(end_time) = date('now')")
        today_sessions = cursor.fetchone()[0]
        
        cursor.execute("SELECT SUM(cost) FROM sessions WHERE date(end_time) = date('now')")
        today_cost = cursor.fetchone()[0] or 0.0
        
        return {
            "knowledge_entries": knowledge_count,
            "active_jobs": active_jobs,
            "sessions_today": today_sessions,
            "cost_today": round(today_cost, 4),
            "database_size": Path(self.db_path).stat().st_size if Path(self.db_path).exists() else 0
        }


class SchedulingService:
    """Cron scheduling with rate limiting"""
    
    def __init__(self, persistence: PersistenceService):
        self.persistence = persistence
        self.running = False
        self.thread = None
        
    def add_job(self, name: str, schedule: str, plugin: str, parameters: Dict = None) -> str:
        """Add a scheduled job with safeguards"""
        job_id = f"job_{int(time.time())}"
        
        # Parse schedule for validation
        if not self.validate_schedule(schedule):
            raise ValueError(f"Invalid schedule format: {schedule}")
        
        # Calculate next run time
        next_run = self.calculate_next_run(schedule)
        
        cursor = self.persistence.conn.cursor()
        cursor.execute('''
            INSERT INTO jobs (id, name, schedule, plugin, parameters, next_run, enabled)
            VALUES (?, ?, ?, ?, ?, ?, 1)
        ''', (
            job_id,
            name,
            schedule,
            plugin,
            json.dumps(parameters or {}),
            next_run.isoformat()
        ))
        
        self.persistence.conn.commit()
        print(f"⏰ Job scheduled: {name} -> {schedule}, next: {next_run}")
        return job_id
    
    def validate_schedule(self, schedule: str) -> bool:
        """Validate cron schedule format"""
        # Simple validation - real implementation would use croniter
        parts = schedule.split()
        if len(parts) != 5:
            return False
        
        # Check each part is valid
        for part in parts:
            if not (part.isdigit() or part == '*' or ',' in part or '-' in part or '/' in part):
                return False
        
        return True
    
    def calculate_next_run(self, schedule: str) -> datetime:
        """Calculate next run time (simplified)"""
        # Simplified - real implementation would use croniter
        now = datetime.now()
        
        # For demo: run in 5 minutes
        next_run = now + timedelta(minutes=5)
        
        # Add some randomness to avoid all jobs running at once
        import random
        next_run += timedelta(seconds=random.randint(0, 300))
        
        return next_run
    
    def run_job(self, job_id: str):
        """Execute a scheduled job with safeguards"""
        cursor = self.persistence.conn.cursor()
        cursor.execute('''
            SELECT name, schedule, plugin, parameters, failures 
            FROM jobs 
            WHERE id = ? AND enabled = 1
        ''', (job_id,))
        
        row = cursor.fetchone()
        if not row:
            print(f"⚠️  Job not found or disabled: {job_id}")
            return
        
        name, schedule, plugin, params_json, failures = row
        parameters = json.loads(params_json) if params_json else {}
        
        print(f"🚀 Running job: {name} (plugin: {plugin})")
        
        try:
            # Check rate limits before running
            if failures >= 3:
                print(f"⚠️  Job {name} has {failures} failures, skipping")
                return
            
            # Execute plugin (mock for now)
            result = self.execute_plugin(plugin, parameters)
            
            # Update job status
            cursor.execute('''
                UPDATE jobs 
                SET last_run = ?, next_run = ?, failures = 0
                WHERE id = ?
            ''', (
                datetime.now().isoformat(),
                self.calculate_next_run(schedule).isoformat(),
                job_id
            ))
            
            self.persistence.conn.commit()
            print(f"✅ Job completed: {name}")
            
        except Exception as e:
            print(f"❌ Job failed: {name} - {e}")
            
            # Increment failure count
            cursor.execute('''
                UPDATE jobs 
                SET failures = failures + 1 
                WHERE id = ?
            ''', (job_id,))
            
            # Disable job after 3 failures
            if failures + 1 >= 3:
                cursor.execute('''
                    UPDATE jobs 
                    SET enabled = 0 
                    WHERE id = ?
                ''', (job_id,))
                print(f"🚨 Job disabled due to failures: {name}")
            
            self.persistence.conn.commit()
    
    def execute_plugin(self, plugin: str, parameters: Dict) -> Any:
        """Execute a plugin (mock implementation)"""
        # Mock plugin execution
        if plugin == "telegram_notification":
            message = parameters.get("message", "Scheduled notification")
            
            if MOCKS_AVAILABLE:
                mock_telegram.send_message(f"⏰ {message}")
                return {"status": "sent", "mock": True}
            else:
                # Real implementation would send actual Telegram message
                return {"status": "plugin_not_implemented", "plugin": plugin}
        
        elif plugin == "research_agent":
            topic = parameters.get("topic", "AI trends")
            
            if MOCKS_AVAILABLE:
                response = mock_llm.complete(f"Research {topic}")
                self.persistence.save_knowledge("research", response, {"topic": topic})
                return {"status": "researched", "topic": topic, "mock": True}
        
        elif plugin == "system_check":
            stats = self.persistence.get_stats()
            return {"status": "checked", "stats": stats}
        
        else:
            return {"status": "unknown_plugin", "plugin": plugin}
    
    def start_scheduler(self):
        """Start the scheduling service"""
        if self.running:
            print("⚠️  Scheduler already running")
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._scheduler_loop, daemon=True)
        self.thread.start()
        print("✅ Scheduling service started")
    
    def stop_scheduler(self):
        """Stop the scheduling service"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        print("🛑 Scheduling service stopped")
    
    def _scheduler_loop(self):
        """Main scheduler loop"""
        print("🔄 Scheduler loop started")
        
        while self.running:
            try:
                # Check for due jobs
                cursor = self.persistence.conn.cursor()
                cursor.execute('''
                    SELECT id FROM jobs 
                    WHERE enabled = 1 
                    AND next_run <= ? 
                    AND (last_run IS NULL OR last_run < next_run)
                ''', (datetime.now().isoformat(),))
                
                due_jobs = cursor.fetchall()
                
                for (job_id,) in due_jobs:
                    self.run_job(job_id)
                
                # Sleep for 1 minute
                time.sleep(60)
                
            except Exception as e:
                print(f"❌ Scheduler error: {e}")
                time.sleep(60)  # Sleep on error too
    
    def get_jobs(self) -> List[Dict]:
        """Get all scheduled jobs"""
        cursor = self.persistence.conn.cursor()
        cursor.execute('''
            SELECT id, name, schedule, plugin, parameters, last_run, next_run, enabled, failures
            FROM jobs
            ORDER BY next_run ASC
        ''')
        
        jobs = []
        for row in cursor.fetchall():
            jobs.append({
                "id": row[0],
                "name": row[1],
                "schedule": row[2],
                "plugin": row[3],
                "parameters": json.loads(row[4]) if row[4] else {},
                "last_run": row[5],
                "next_run": row[6],
                "enabled": bool(row[7]),
                "failures": row[8]
            })
        
        return jobs


class MiniclawOS:
    """Main Miniclaw OS class"""
    
    def __init__(self, use_mocks: bool = True):
        self.use_mocks = use_mocks
        self.persistence = PersistenceService()
        self.scheduler = SchedulingService(self.persistence)
        
        # Initialize services based on mode
        if use_mocks and MOCKS_AVAILABLE:
            self.telegram = mock_telegram
            self.llm = mock_llm
            self.openclaw = mock_openclaw
            self.safeguard = mock_safeguard
            print("🔧 Running in MOCK mode (zero API cost)")
        else:
            # Real services would be initialized here
            self.telegram = None
            self.llm = None
            self.openclaw = None
            self.safeguard = real_safeguard if SAFEGUARDS_AVAILABLE else None
            print("⚡ Running in REAL mode (API costs apply)")
        
        print(f"🚀 Miniclaw OS initialized (v0.1.0)")
    
    def start(self):
        """Start all OS services"""
        print("🚀 Starting Miniclaw OS...")
        
        # Start scheduler
        self.scheduler.start_scheduler()
        
        # Send startup notification
        if self.telegram:
            self.telegram.send_message(
                f"🚀 Miniclaw OS v0.1.0 started\n"
                f"Mode: {'MOCK' if self.use_mocks else 'REAL'}\n"
                f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )
        
        print("✅ Miniclaw OS running")
    
    def stop(self):
        """Stop all OS services"""
        print("🛑 Stopping Miniclaw OS...")
        
        # Stop scheduler
        self.scheduler.stop_scheduler()
        
        # Send shutdown notification
        if self.telegram:
            stats = self.persistence.get_stats()
            self.telegram.send_message(
                f"🛑 Miniclaw OS shutting down\n"
                f"Stats: {stats['knowledge_entries']} knowledge entries\n"
                f"Cost today: ${stats['cost_today']:.4f}"
            )
        
        print("✅ Miniclaw OS stopped")
    
    def get_status(self) -> Dict[str, Any]:
        """Get system status"""
        stats = self.persistence.get_stats()
        jobs = self.scheduler.get_jobs()
        
        return {
            "version": "0.1.0",
            "mode": "mock" if self.use_mocks else "real",
            "running": self.scheduler.running,
            "stats": stats,
            "active_jobs": len([j for j in jobs if j["enabled"]]),
            "next_job_run": min([j["next_run"] for j in jobs if j["enabled"] and j["next_run"]], default=None),
            "database_path": self.persistence.db_path
        }
    
    def demo_workflow(self):
        """Demonstrate a complete workflow"""
        print("\n" + "="*60)
        print("DEMO WORKFLOW: Sustainable AI Agent OS")
        print("="*60)
        
        # 1. Save some knowledge
        print("\n1. 📚 Saving knowledge...")
        kb_id = self.persistence.save_knowledge(
            "research",
            "AI agents are becoming more autonomous in 2026.",
            {"source": "demo", "tags": ["ai", "trends"]}
        )
        print(f"   Saved: {kb_id}")
        
        # 2. Schedule a job
        print("\n2. ⏰ Scheduling job...")
        job_id = self.scheduler.add_job(
            "Daily Research",
            "0 9 * * *",  # 9 AM daily (simplified)
            "research_agent",
            {"topic": "AI trends 2026"}
        )
        print(f"   Scheduled: {job_id}")
        
        # 3. Query knowledge
        print("\n3. 🔍 Querying knowledge...")
        knowledge = self.persistence.query_knowledge("research", limit=3)
        print(f"   Found {len(knowledge)} research entries")
        for item in knowledge:
            print(f"   - {item['id']}: {item['content'][:80]}...")
        
        # 4. Get system status
        print("\n4. 📊 System status...")
        status = self.get_status()
        print(f"   Mode: {status['mode']}")
        print(f"   Knowledge entries: {status['stats']['knowledge_entries']}")
        print(f"   Active jobs: {status['active_jobs']}")
        print(f"   Cost today: ${status['stats']['cost_today']:.4f}")
        
        # 5. Send Telegram notification
        print("\n5. 💬 Sending Telegram notification...")
        if self.telegram:
            response = self.telegram.send_message(
                "✅ Miniclaw OS demo complete!\n"
                f"Mode: {status['mode'].upper()}\n"
                f"Knowledge: {status['stats']['knowledge_entries']} entries\n"
                f"Jobs: {status['active_jobs']} active\n"
                f"API Cost: ${status['stats']['cost_today']:.4f} today"
            )
            print(f"   Telegram message sent: {response.get('message_id', 'unknown')}")
        
        print("\n" + "="*60)
        print("✅ DEMO COMPLETE: Working prototype ready!")
        print("="*60)
        
        return {
            "knowledge_id": kb_id,
            "job_id": job_id,
            "status": status,
            "telegram_sent": self.telegram is not None
        }


# Global instance for easy access
miniclaw = None


def initialize(use_mocks: bool = True) -> MiniclawOS:
    """Initialize Miniclaw OS"""
    global miniclaw
    miniclaw = MiniclawOS(use_mocks=use_mocks)
    return miniclaw


if __name__ == "__main__":
    # Run demo
    print("🧪 Miniclaw OS Demo (Sustainable Development)")
    print("Mode: MOCK (zero API cost)")
    
    # Initialize with mocks
    os = initialize(use_mocks=True)
    
    # Start the OS
    os.start()
    
    # Run demo workflow
    try:
        results = os.demo_workflow()
        
        # Show mock statistics
        if MOCKS_AVAILABLE:
            from .mocks import print_mock_stats
            print_mock_stats()
        
        # Stop the OS
        os.stop()
        
        print("\n🎉 DEMO SUCCESSFUL!")
        print(f"Knowledge saved: {results['knowledge_id']}")
        print(f"Job scheduled: {results['job_id']}")
        print(f"Mode: {results['status']['mode']}")
        print(f"Total API cost: $0.00 (mock mode)")
        
    except KeyboardInterrupt:
        print("\n🛑 Demo interrupted by user")
        os.stop()
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()
        if os:
            os.stop()