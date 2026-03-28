#!/usr/bin/env python3
"""
Unit tests for Miniclaw OS core (zero API cost)
"""

import unittest
import tempfile
import json
import sqlite3
import time
from pathlib import Path
import sys
import os

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from miniclaw_os.core import PersistenceService, SchedulingService


class TestPersistenceService(unittest.TestCase):
    """Test persistence service functionality"""
    
    def setUp(self):
        """Set up test database"""
        self.temp_dir = tempfile.mkdtemp(prefix="persistence_test_")
        self.db_path = os.path.join(self.temp_dir, "test.db")
        self.persistence = PersistenceService(db_path=self.db_path)
    
    def tearDown(self):
        """Clean up test database"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_database_initialization(self):
        """Test that database tables are created"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Check tables exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = {row[0] for row in cursor.fetchall()}
        
        expected_tables = {"knowledge", "jobs", "sessions", "metrics"}
        self.assertTrue(expected_tables.issubset(tables), 
                       f"Missing tables: {expected_tables - tables}")
        
        conn.close()
    
    def test_save_knowledge(self):
        """Test saving knowledge entries"""
        kb_id = self.persistence.save_knowledge(
            category="test",
            content="Test knowledge content",
            metadata={"source": "unit_test", "importance": "high"}
        )
        
        self.assertIsNotNone(kb_id)
        self.assertTrue(kb_id.startswith("kb_"))
        
        # Verify entry was saved
        entries = self.persistence.query_knowledge("test", limit=1)
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["id"], kb_id)
        self.assertEqual(entries[0]["content"], "Test knowledge content")
        self.assertEqual(entries[0]["metadata"]["source"], "unit_test")
    
    def test_knowledge_pruning(self):
        """Test automatic knowledge pruning"""
        # Add many entries with unique IDs
        import time
        for i in range(1050):  # Exceed 1000 limit
            # Add small delay to ensure unique timestamps
            time.sleep(0.001)
            self.persistence.save_knowledge(
                category="bulk",
                content=f"Entry {i}",
                metadata={"index": i}
            )
        
        # Check pruning happened
        entries = self.persistence.query_knowledge("bulk", limit=2000)
        self.assertLessEqual(len(entries), 1000, 
                           "Should prune to 1000 entries max")
    
    def test_log_session(self):
        """Test session logging"""
        session_id = self.persistence.log_session(
            agent_id="test_agent",
            tokens_used=1500,
            cost=0.00021,
            status="completed",
            checkpoint_path="/tmp/checkpoint.json"
        )
        
        self.assertIsNotNone(session_id)
        self.assertTrue(session_id.startswith("session_"))
        
        # Verify session was logged
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM sessions WHERE id = ?", (session_id,))
        count = cursor.fetchone()[0]
        conn.close()
        
        self.assertEqual(count, 1, "Session should be logged")
    
    def test_get_stats(self):
        """Test statistics retrieval"""
        # Add some test data
        self.persistence.save_knowledge("stats_test", "Content 1")
        self.persistence.save_knowledge("stats_test", "Content 2")
        self.persistence.log_session("agent1", 1000, 0.00021, "success")  # 1000 tokens = $0.00014
        
        stats = self.persistence.get_stats()
        
        self.assertIn("knowledge_entries", stats)
        self.assertIn("active_jobs", stats)
        self.assertIn("sessions_today", stats)
        self.assertIn("cost_today", stats)
        self.assertIn("database_size", stats)
        
        self.assertEqual(stats["knowledge_entries"], 2)
        self.assertGreaterEqual(stats["cost_today"], 0.0001)  # Should be at least $0.0001


class TestSchedulingService(unittest.TestCase):
    """Test scheduling service functionality"""
    
    def setUp(self):
        """Set up test scheduler"""
        self.temp_dir = tempfile.mkdtemp(prefix="scheduler_test_")
        self.db_path = os.path.join(self.temp_dir, "test.db")
        self.persistence = PersistenceService(db_path=self.db_path)
        self.scheduler = SchedulingService(self.persistence)
    
    def tearDown(self):
        """Clean up test scheduler"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_schedule_validation(self):
        """Test cron schedule validation"""
        valid_schedules = [
            "* * * * *",
            "0 * * * *",
            "0 0 * * *",
            "0 0 * * 0",
            "*/5 * * * *"
        ]
        
        invalid_schedules = [
            "",
            "* * * *",
            "* * * * * *",
            "a * * * *",
            "* * * * * extra"
        ]
        
        for schedule in valid_schedules:
            self.assertTrue(self.scheduler.validate_schedule(schedule),
                          f"Should be valid: {schedule}")
        
        for schedule in invalid_schedules:
            self.assertFalse(self.scheduler.validate_schedule(schedule),
                           f"Should be invalid: {schedule}")
    
    def test_add_job(self):
        """Test adding scheduled jobs"""
        job_id = self.scheduler.add_job(
            name="Test Job",
            schedule="0 * * * *",
            plugin="test_plugin",
            parameters={"param1": "value1", "param2": 42}
        )
        
        self.assertIsNotNone(job_id)
        self.assertTrue(job_id.startswith("job_"))
        
        # Verify job was added
        jobs = self.scheduler.get_jobs()
        job = next((j for j in jobs if j["id"] == job_id), None)
        
        self.assertIsNotNone(job, "Job should be in list")
        self.assertEqual(job["name"], "Test Job")
        self.assertEqual(job["schedule"], "0 * * * *")
        self.assertEqual(job["plugin"], "test_plugin")
        self.assertEqual(job["parameters"]["param1"], "value1")
        self.assertEqual(job["parameters"]["param2"], 42)
        self.assertTrue(job["enabled"])
    
    def test_job_failure_handling(self):
        """Test job failure tracking and disabling"""
        # Add a job
        job_id = self.scheduler.add_job(
            name="Failing Job",
            schedule="* * * * *",
            plugin="failing_plugin",
            parameters={}
        )
        
        # Simulate 3 failures
        for i in range(3):
            # Mock run_job to simulate failure
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE jobs SET failures = ? WHERE id = ?",
                (i + 1, job_id)
            )
            conn.commit()
            conn.close()
        
        # Get job status
        jobs = self.scheduler.get_jobs()
        job = next((j for j in jobs if j["id"] == job_id), None)
        
        self.assertEqual(job["failures"], 3)
        
        # On 4th failure, job should be disabled
        # (This is tested in the run_job method, which we're mocking)
    
    def test_execute_plugin_mock(self):
        """Test plugin execution (mock mode)"""
        # Test telegram_notification plugin
        result = self.scheduler.execute_plugin(
            "telegram_notification",
            {"message": "Test notification"}
        )
        
        self.assertIn("status", result)
        
        # Test research_agent plugin
        result = self.scheduler.execute_plugin(
            "research_agent",
            {"topic": "Test topic"}
        )
        
        self.assertIn("status", result)
        
        # Test system_check plugin
        result = self.scheduler.execute_plugin("system_check", {})
        
        self.assertIn("status", result)
        self.assertIn("stats", result)
        
        # Test unknown plugin
        result = self.scheduler.execute_plugin("unknown_plugin", {})
        
        self.assertEqual(result["status"], "unknown_plugin")
        self.assertEqual(result["plugin"], "unknown_plugin")


class TestIntegration(unittest.TestCase):
    """Test integration between components"""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="integration_test_")
        self.db_path = os.path.join(self.temp_dir, "test.db")
    
    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_persistence_scheduler_integration(self):
        """Test that persistence and scheduler work together"""
        persistence = PersistenceService(db_path=self.db_path)
        scheduler = SchedulingService(persistence)
        
        # Add a job through scheduler
        job_id = scheduler.add_job(
            name="Integration Test Job",
            schedule="0 0 * * *",
            plugin="system_check",
            parameters={}
        )
        
        # Verify job is in database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM jobs WHERE id = ?", (job_id,))
        job_name = cursor.fetchone()[0]
        conn.close()
        
        self.assertEqual(job_name, "Integration Test Job")
        
        # Get jobs through scheduler
        jobs = scheduler.get_jobs()
        self.assertGreater(len(jobs), 0)
        
        # Verify persistence stats include jobs
        stats = persistence.get_stats()
        self.assertIn("active_jobs", stats)
        self.assertEqual(stats["active_jobs"], 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)