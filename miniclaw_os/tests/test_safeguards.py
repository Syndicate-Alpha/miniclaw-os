#!/usr/bin/env python3
"""
Unit tests for safeguards (zero API cost)
"""

import unittest
import tempfile
import json
import os
from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from safeguards import MemorySafeguard


class TestMemorySafeguard(unittest.TestCase):
    """Test memory safeguard functionality"""
    
    def setUp(self):
        """Set up test environment"""
        # Create temporary workspace
        self.temp_dir = tempfile.mkdtemp(prefix="miniclaw_test_")
        self.safeguard = MemorySafeguard(workspace_path=self.temp_dir)
        
    def tearDown(self):
        """Clean up test environment"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_on_wakeup_creates_files(self):
        """Test that wakeup creates necessary files"""
        result = self.safeguard.on_wakeup()
        
        # Check memory directory exists
        memory_dir = Path(self.temp_dir) / "memory"
        self.assertTrue(memory_dir.exists(), "Memory directory should exist")
        
        # Check today's file exists
        from datetime import datetime
        today = datetime.utcnow().strftime("%Y-%m-%d")
        today_file = memory_dir / f"{today}.md"
        self.assertTrue(today_file.exists(), "Today's memory file should exist")
        
        # Check API usage file exists
        api_file = Path(self.temp_dir) / "api_usage.json"
        self.assertTrue(api_file.exists(), "API usage file should exist")
        
        self.assertTrue(result["memory_ok"], "Wakeup should succeed")
    
    def test_before_action_cost_calculation(self):
        """Test cost calculation before action"""
        # Load API usage first
        self.safeguard.on_wakeup()
        
        # Test with 1000 tokens
        result = self.safeguard.before_action("test_action", 1000)
        
        self.assertTrue(result, "Action should be allowed")
        
        # Check cost was calculated
        estimated_cost = (1000 / 1_000_000) * 0.14
        self.assertAlmostEqual(
            self.safeguard.api_usage['deepseek']['daily_cost_usd'],
            estimated_cost,
            places=6,
            msg="Cost should be calculated correctly"
        )
    
    def test_before_action_rate_limiting(self):
        """Test rate limiting (3 actions per hour)"""
        self.safeguard.on_wakeup()
        
        # Mock the actions tracking to simulate 3 actions already taken
        import time
        current_hour = int(time.time() // 3600)
        self.safeguard.actions_this_hour = {'hour': current_hour, 'count': 3}
        
        # Fourth action should be blocked
        result = self.safeguard.before_action("test_action_4", 100)
        self.assertFalse(result, "Fourth action should be blocked (3 per hour limit)")
    
    def test_after_action_checkpoint(self):
        """Test checkpoint creation after action"""
        self.safeguard.on_wakeup()
        
        # Run an action
        if self.safeguard.before_action("test_action", 500):
            self.safeguard.after_action("test_action", 450, success=True)
        
        # Check checkpoint was created
        checkpoint_dir = Path(self.temp_dir) / "session_checkpoints"
        self.assertTrue(checkpoint_dir.exists(), "Checkpoint directory should exist")
        
        checkpoints = list(checkpoint_dir.glob("*.json"))
        self.assertGreater(len(checkpoints), 0, "At least one checkpoint should exist")
        
        # Verify checkpoint content
        with open(checkpoints[0], 'r') as f:
            checkpoint = json.load(f)
        
        self.assertEqual(checkpoint["action"], "test_action")
        self.assertEqual(checkpoint["tokens"], 450)
        self.assertTrue(checkpoint["success"])
    
    def test_memory_flush(self):
        """Test memory flush procedure"""
        from datetime import datetime
        
        self.safeguard.on_wakeup()
        
        # Create some memory content
        memory_dir = Path(self.temp_dir) / "memory"
        today = datetime.utcnow().strftime("%Y-%m-%d")
        today_file = memory_dir / f"{today}.md"
        
        with open(today_file, 'w') as f:
            f.write("# Test Memory\n\nSome test content for flushing.\n")
        
        # Flush memory
        self.safeguard.memory_flush()
        
        # Check MEMORY.md was updated
        memory_file = Path(self.temp_dir) / "MEMORY.md"
        self.assertTrue(memory_file.exists(), "MEMORY.md should exist")
        
        content = memory_file.read_text()
        self.assertIn("Test Memory", content, "Flushed content should be in MEMORY.md")
        self.assertIn("Flush:", content, "Should have flush timestamp")
    
    def test_get_status(self):
        """Test status retrieval"""
        self.safeguard.on_wakeup()
        
        status = self.safeguard.get_status()
        
        self.assertIn("memory", status)
        self.assertIn("api", status)
        self.assertIn("timestamp", status)
        
        # Check memory status
        self.assertTrue(status["memory"]["mem_dir_exists"])
        self.assertIsInstance(status["memory"]["mem_files"], int)
        self.assertIsInstance(status["memory"]["checkpoints"], int)
        
        # Check API status
        if status["api"]:
            self.assertIn("daily_calls", status["api"])
            self.assertIn("daily_cost_usd", status["api"])
            self.assertIn("projected_runway_days", status["api"])


class TestSustainableVelocity(unittest.TestCase):
    """Test sustainable velocity safeguards"""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="velocity_test_")
        self.safeguard = MemorySafeguard(workspace_path=self.temp_dir)
        self.safeguard.on_wakeup()
    
    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_velocity_limit_reset(self):
        """Test that velocity limit resets after hour change"""
        import time
        
        # Mock actions_this_hour to simulate previous hour
        # Use a hour that's definitely different from current
        previous_hour = (int(time.time() // 3600) - 1) % 24
        self.safeguard.actions_this_hour = {'hour': previous_hour, 'count': 3}
        
        # Action should be allowed in new hour (count resets)
        result = self.safeguard.before_action("test_new_hour", 100)
        self.assertTrue(result, "Action should be allowed in new hour")
        
        # Count should be 1 (this action)
        self.assertEqual(self.safeguard.actions_this_hour['count'], 1)
    
    def test_failure_tracking(self):
        """Test API failure tracking and cooldown"""
        import time
        
        # Record 2 failures
        self.safeguard.recent_failures = [
            time.time() - 60,  # 1 minute ago
            time.time() - 30   # 30 seconds ago
        ]
        
        # Third action should be blocked (2 failures in 5 minutes)
        result = self.safeguard.before_action("test_with_failures", 100)
        self.assertFalse(result, "Action should be blocked after 2 recent failures")
        
        # Wait for failures to expire (mock)
        self.safeguard.recent_failures = [time.time() - 400]  # 400 seconds ago
        
        # Action should be allowed again
        result = self.safeguard.before_action("test_after_cooldown", 100)
        self.assertTrue(result, "Action should be allowed after failures expire")


if __name__ == "__main__":
    # Import here to avoid circular imports
    import time
    from datetime import datetime
    
    # Run tests
    unittest.main(verbosity=2)