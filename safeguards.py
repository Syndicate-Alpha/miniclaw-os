#!/usr/bin/env python3
"""
AI Empire Safeguards Module
Memory continuity, API rate limits, cost control, session recovery
"""

import json
import os
import time
from datetime import datetime, timedelta
from pathlib import Path
import sys

class MemorySafeguard:
    """Memory continuity and session recovery safeguards"""
    
    def __init__(self, workspace_path="/root/.openclaw/workspace"):
        self.workspace = Path(workspace_path)
        self.memory_dir = self.workspace / "memory"
        self.api_usage_file = self.workspace / "api_usage.json"
        self.checkpoints_dir = self.workspace / "session_checkpoints"
        
        # Ensure directories exist
        self.memory_dir.mkdir(exist_ok=True)
        self.checkpoints_dir.mkdir(exist_ok=True)
        
    def on_wakeup(self):
        """MANDATORY: Check memory continuity on every wakeup"""
        print("🔍 Memory Safeguard: Wakeup sequence starting...")
        
        # 1. Check MEMORY.md exists
        memory_file = self.workspace / "MEMORY.md"
        if not memory_file.exists():
            print("⚠️  WARNING: MEMORY.md not found! Creating empty...")
            memory_file.write_text("# 🧠 MEMORY.md - Long-Term Memory\n\n## Created: " + 
                                  datetime.utcnow().isoformat() + "\n")
        
        # 2. Check today's memory file
        today = datetime.utcnow().strftime("%Y-%m-%d")
        today_file = self.memory_dir / f"{today}.md"
        if not today_file.exists():
            print(f"📝 Creating today's memory file: {today}.md")
            today_file.write_text(f"# Memory: {today}\n\n")
        
        # 3. Check yesterday's memory file
        yesterday = (datetime.utcnow() - timedelta(days=1)).strftime("%Y-%m-%d")
        yesterday_file = self.memory_dir / f"{yesterday}.md"
        
        # 4. Load API usage tracking
        self.load_api_usage()
        
        # 5. Check for orphaned sessions
        self.check_orphaned_sessions()
        
        print("✅ Memory Safeguard: Wakeup sequence complete")
        return {
            "memory_ok": True,
            "today_file": str(today_file),
            "yesterday_exists": yesterday_file.exists(),
            "api_usage_loaded": hasattr(self, 'api_usage')
        }
    
    def load_api_usage(self):
        """Load and validate API usage tracking"""
        if not self.api_usage_file.exists():
            print("⚠️  API usage file not found, creating default...")
            self.api_usage = {
                "deepseek": {
                    "last_checked": datetime.utcnow().isoformat(),
                    "daily_calls": 0,
                    "daily_tokens": 0,
                    "daily_cost_usd": 0.0,
                    "monthly_budget_usd": 100.0,
                    "burn_rate_usd_per_day": 0.0,
                    "projected_runway_days": "infinite",
                    "alerts": []
                }
            }
            self.save_api_usage()
        else:
            with open(self.api_usage_file, 'r') as f:
                self.api_usage = json.load(f)
            print(f"📊 API usage loaded: {self.api_usage['deepseek']['daily_calls']} calls today")
    
    def save_api_usage(self):
        """Save API usage tracking"""
        with open(self.api_usage_file, 'w') as f:
            json.dump(self.api_usage, f, indent=2)
    
    def check_orphaned_sessions(self):
        """Check for orphaned session files and recover if possible"""
        # Look for checkpoint files without completion markers
        checkpoint_files = list(self.checkpoints_dir.glob("*.json"))
        if checkpoint_files:
            latest = max(checkpoint_files, key=os.path.getctime)
            print(f"🔍 Found {len(checkpoint_files)} checkpoint files")
            print(f"   Latest: {latest.name}")
            
            # Check if latest is recent (< 1 hour)
            file_age = time.time() - os.path.getctime(latest)
            if file_age < 3600:
                print("⚠️  Recent checkpoint found - possible orphaned session")
                return latest
        return None
    
    def before_action(self, action_type, estimated_tokens=0):
        """Check before taking action (API call, tool use, etc.)"""
        print(f"🔒 Safeguard: Pre-action check for {action_type}")
        
        # **SUSTAINABLE VELOCITY RULE:** Max 3 major actions per hour
        current_hour = datetime.utcnow().hour
        if hasattr(self, 'actions_this_hour'):
            if self.actions_this_hour.get('hour') == current_hour:
                if self.actions_this_hour.get('count', 0) >= 3:
                    print(f"🚨 SUSTAINABILITY: Already {self.actions_this_hour['count']} actions this hour (max 3)")
                    print(f"   Pausing for sustainable velocity - resume next hour")
                    return False
            else:
                self.actions_this_hour = {'hour': current_hour, 'count': 0}
        else:
            self.actions_this_hour = {'hour': current_hour, 'count': 0}
        
        # Estimate cost
        estimated_cost = (estimated_tokens / 1_000_000) * 0.14  # DeepSeek input cost
        
        # Check daily limits
        daily_cost = self.api_usage['deepseek']['daily_cost_usd'] + estimated_cost
        if daily_cost > 5.0:
            print(f"🚨 EMERGENCY: Estimated cost ${estimated_cost:.4f} would exceed daily $5.00 limit!")
            print(f"   Current daily: ${self.api_usage['deepseek']['daily_cost_usd']:.4f}")
            return False
        
        if daily_cost > 4.5:
            print(f"⚠️  CRITICAL: Estimated cost would bring daily to ${daily_cost:.4f} (>90% limit)")
        
        # **API ERROR PREVENTION:** Check for recent failures
        if hasattr(self, 'recent_failures'):
            failure_window = [f for f in self.recent_failures if time.time() - f < 300]  # Last 5 minutes
            if len(failure_window) >= 2:
                print(f"🚨 API ERROR PREVENTION: {len(failure_window)} failures in last 5 minutes")
                print(f"   Cooling down for 10 minutes to avoid rate limits")
                return False
        
        # Update tracking
        self.api_usage['deepseek']['daily_calls'] += 1
        self.api_usage['deepseek']['daily_tokens'] += estimated_tokens
        self.api_usage['deepseek']['daily_cost_usd'] = daily_cost
        
        # Calculate burn rate
        hours_since_midnight = datetime.utcnow().hour + datetime.utcnow().minute / 60
        if hours_since_midnight > 0:
            self.api_usage['deepseek']['burn_rate_usd_per_day'] = daily_cost / (hours_since_midnight / 24)
            runway = 100.0 / self.api_usage['deepseek']['burn_rate_usd_per_day'] if self.api_usage['deepseek']['burn_rate_usd_per_day'] > 0 else 9999
            self.api_usage['deepseek']['projected_runway_days'] = round(runway, 1)
        
        self.api_usage['deepseek']['last_checked'] = datetime.utcnow().isoformat()
        self.save_api_usage()
        
        print(f"   Estimated: {estimated_tokens} tokens, ${estimated_cost:.4f}")
        print(f"   Daily total: ${daily_cost:.4f}/$5.00, Runway: {self.api_usage['deepseek']['projected_runway_days']} days")
        return True
    
    def after_action(self, action_type, actual_tokens=0, success=True):
        """Update after action completion"""
        print(f"🔒 Safeguard: Post-action update for {action_type}")
        
        # Track actions per hour for sustainable velocity
        if hasattr(self, 'actions_this_hour'):
            self.actions_this_hour['count'] = self.actions_this_hour.get('count', 0) + 1
        
        # Track API failures for error prevention
        if not success:
            if not hasattr(self, 'recent_failures'):
                self.recent_failures = []
            self.recent_failures.append(time.time())
            # Keep only last hour of failures
            self.recent_failures = [f for f in self.recent_failures if time.time() - f < 3600]
            print(f"⚠️  API failure recorded ({len(self.recent_failures)} in last hour)")
        
        # Create checkpoint
        checkpoint = {
            "timestamp": datetime.utcnow().isoformat(),
            "action": action_type,
            "tokens": actual_tokens,
            "success": success,
            "memory_files": [str(f) for f in list(self.memory_dir.glob("*.md"))],
            "velocity_metrics": {
                "actions_this_hour": self.actions_this_hour.get('count', 0) if hasattr(self, 'actions_this_hour') else 0,
                "recent_failures": len(self.recent_failures) if hasattr(self, 'recent_failures') else 0
            }
        }
        
        checkpoint_file = self.checkpoints_dir / f"checkpoint_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
        with open(checkpoint_file, 'w') as f:
            json.dump(checkpoint, f, indent=2)
        
        print(f"   Checkpoint saved: {checkpoint_file.name}")
        
        # Clean old checkpoints (keep last 10)
        checkpoints = sorted(self.checkpoints_dir.glob("*.json"), key=os.path.getctime)
        if len(checkpoints) > 10:
            for old in checkpoints[:-10]:
                old.unlink()
                print(f"   Cleaned old checkpoint: {old.name}")
    
    def memory_flush(self):
        """Flush recent memory to long-term storage"""
        print("🧹 Memory Safeguard: Flushing recent memory...")
        
        # Read today's memory
        today = datetime.utcnow().strftime("%Y-%m-%d")
        today_file = self.memory_dir / f"{today}.md"
        
        if today_file.exists():
            content = today_file.read_text()
            
            # Append to MEMORY.md with timestamp
            memory_file = self.workspace / "MEMORY.md"
            with open(memory_file, 'a') as f:
                f.write(f"\n## Flush: {datetime.utcnow().isoformat()}\n")
                f.write(content[:1000] + "\n...\n")  # First 1000 chars
            
            print(f"✅ Flushed {len(content)} chars to MEMORY.md")
        else:
            print("⚠️  No today's memory file to flush")
    
    def get_status(self):
        """Get current safeguard status"""
        return {
            "memory": {
                "mem_dir_exists": self.memory_dir.exists(),
                "mem_files": len(list(self.memory_dir.glob("*.md"))),
                "checkpoints": len(list(self.checkpoints_dir.glob("*.json")))
            },
            "api": self.api_usage['deepseek'] if hasattr(self, 'api_usage') else None,
            "timestamp": datetime.utcnow().isoformat()
        }


# Global instance for easy import
safeguard = MemorySafeguard()

if __name__ == "__main__":
    # Test the safeguards
    print("🧪 Testing AI Empire Safeguards...")
    
    # Wakeup sequence
    status = safeguard.on_wakeup()
    print(f"Wakeup status: {status}")
    
    # Pre-action check
    if safeguard.before_action("test_call", estimated_tokens=1000):
        print("Pre-action check passed")
        
        # Simulate action
        time.sleep(0.5)
        
        # Post-action update
        safeguard.after_action("test_call", actual_tokens=950, success=True)
    
    # Get final status
    final = safeguard.get_status()
    print(f"Final status: {json.dumps(final, indent=2)}")
    
    print("✅ Safeguards test complete")