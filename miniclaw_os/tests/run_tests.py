#!/usr/bin/env python3
"""
Sustainable Test Runner with Cost Control
Zero API cost for unit tests, budget control for integration tests
"""

import unittest
import sys
import os
from pathlib import Path
import json
import time
from datetime import datetime

# Add workspace to path
workspace_path = Path(__file__).parent.parent.parent
sys.path.insert(0, str(workspace_path))


class SustainableTestRunner:
    """Test runner with cost tracking and budget control"""
    
    def __init__(self, daily_test_budget=0.10):  # $0.10/day for testing
        self.daily_test_budget = daily_test_budget
        self.test_results = []
        self.cost_tracker = {
            "unit_tests": {"calls": 0, "tokens": 0, "cost": 0.0},
            "integration_tests": {"calls": 0, "tokens": 0, "cost": 0.0},
            "total": {"calls": 0, "tokens": 0, "cost": 0.0}
        }
        
        # Load existing test costs
        self.cost_file = workspace_path / "test_costs.json"
        self.load_test_costs()
    
    def load_test_costs(self):
        """Load previous test costs"""
        if self.cost_file.exists():
            with open(self.cost_file, 'r') as f:
                self.historical_costs = json.load(f)
        else:
            self.historical_costs = {
                "daily": {},
                "weekly": {},
                "total": {"calls": 0, "tokens": 0, "cost": 0.0}
            }
    
    def save_test_costs(self):
        """Save test costs to file"""
        today = datetime.now().strftime("%Y-%m-%d")
        
        if today not in self.historical_costs["daily"]:
            self.historical_costs["daily"][today] = {
                "calls": 0,
                "tokens": 0,
                "cost": 0.0,
                "tests_run": 0
            }
        
        # Update today's costs
        daily = self.historical_costs["daily"][today]
        daily["calls"] += self.cost_tracker["total"]["calls"]
        daily["tokens"] += self.cost_tracker["total"]["tokens"]
        daily["cost"] += self.cost_tracker["total"]["cost"]
        daily["tests_run"] += len(self.test_results)
        
        # Update total
        self.historical_costs["total"]["calls"] += self.cost_tracker["total"]["calls"]
        self.historical_costs["total"]["tokens"] += self.cost_tracker["total"]["tokens"]
        self.historical_costs["total"]["cost"] += self.cost_tracker["total"]["cost"]
        
        # Save to file
        with open(self.cost_file, 'w') as f:
            json.dump(self.historical_costs, f, indent=2)
    
    def check_budget(self, estimated_cost=0.0):
        """Check if test budget allows running more tests"""
        today = datetime.now().strftime("%Y-%m-%d")
        daily_cost = self.historical_costs.get("daily", {}).get(today, {}).get("cost", 0.0)
        
        total_estimated = daily_cost + estimated_cost + self.cost_tracker["total"]["cost"]
        
        if total_estimated > self.daily_test_budget:
            print(f"🚨 TEST BUDGET EXCEEDED: ${total_estimated:.4f} > ${self.daily_test_budget:.2f}")
            return False
        
        return True
    
    def run_test_suite(self, test_suite, suite_name="unit"):
        """Run a test suite with cost tracking"""
        print(f"\n{'='*70}")
        print(f"🧪 RUNNING {suite_name.upper()} TESTS")
        print(f"{'='*70}")
        
        # Check budget before running
        if not self.check_budget():
            print(f"⚠️  Skipping {suite_name} tests due to budget constraints")
            return
        
        # Run tests
        runner = unittest.TextTestRunner(verbosity=2)
        start_time = time.time()
        result = runner.run(test_suite)
        elapsed = time.time() - start_time
        
        # Record results
        suite_result = {
            "suite": suite_name,
            "tests_run": result.testsRun,
            "failures": len(result.failures),
            "errors": len(result.errors),
            "skipped": len(result.skipped),
            "elapsed_seconds": round(elapsed, 2),
            "cost": self.cost_tracker[suite_name]["cost"]
        }
        
        self.test_results.append(suite_result)
        
        # Print summary
        print(f"\n📊 {suite_name.upper()} TEST SUMMARY:")
        print(f"   Tests run: {result.testsRun}")
        print(f"   Failures: {len(result.failures)}")
        print(f"   Errors: {len(result.errors)}")
        print(f"   Skipped: {len(result.skipped)}")
        print(f"   Time: {elapsed:.2f}s")
        print(f"   Cost: ${self.cost_tracker[suite_name]['cost']:.4f}")
        
        if result.failures:
            print(f"\n❌ FAILURES:")
            for test, traceback in result.failures:
                print(f"   {test}: {traceback.split(chr(10))[0]}")
        
        return result
    
    def print_final_report(self):
        """Print final test report"""
        print(f"\n{'='*70}")
        print("📈 SUSTAINABLE TESTING REPORT")
        print(f"{'='*70}")
        
        total_tests = sum(r["tests_run"] for r in self.test_results)
        total_failures = sum(r["failures"] for r in self.test_results)
        total_errors = sum(r["errors"] for r in self.test_results)
        total_cost = sum(r["cost"] for r in self.test_results)
        
        print(f"\n📊 OVERALL RESULTS:")
        print(f"   Total tests run: {total_tests}")
        print(f"   Total failures: {total_failures}")
        print(f"   Total errors: {total_errors}")
        print(f"   Total cost: ${total_cost:.4f}")
        
        print(f"\n💰 COST BREAKDOWN:")
        for suite in ["unit_tests", "integration_tests"]:
            cost = self.cost_tracker[suite]["cost"]
            if cost > 0:
                print(f"   {suite}: ${cost:.4f}")
        
        print(f"\n🎯 BUDGET STATUS:")
        today = datetime.now().strftime("%Y-%m-%d")
        daily_cost = self.historical_costs.get("daily", {}).get(today, {}).get("cost", 0.0)
        budget_used = (daily_cost / self.daily_test_budget * 100) if self.daily_test_budget > 0 else 0
        
        print(f"   Daily budget: ${self.daily_test_budget:.2f}")
        print(f"   Used today: ${daily_cost:.4f}")
        print(f"   Budget used: {budget_used:.1f}%")
        
        if total_failures == 0 and total_errors == 0:
            print(f"\n✅ ALL TESTS PASSED!")
        else:
            print(f"\n⚠️  {total_failures + total_errors} TESTS FAILED")
        
        # Save costs
        self.save_test_costs()
        
        print(f"\n📁 Test costs saved to: {self.cost_file}")
        print(f"{'='*70}")


def discover_tests():
    """Discover all test modules"""
    test_dir = Path(__file__).parent
    
    # Unit tests (zero API cost)
    unit_loader = unittest.TestLoader()
    unit_suite = unittest.TestSuite()
    
    # Add safeguard tests
    unit_suite.addTests(unit_loader.loadTestsFromName("test_safeguards"))
    
    # Add miniclaw core tests  
    unit_suite.addTests(unit_loader.loadTestsFromName("test_miniclaw_core"))
    
    # Integration tests (would have API cost, but we use mocks)
    integration_suite = unittest.TestSuite()
    # Future: Add integration tests here when we have real API tests
    
    return {
        "unit_tests": unit_suite,
        "integration_tests": integration_suite
    }


def main():
    """Main test runner"""
    print("="*70)
    print("🧪 SUSTAINABLE TEST RUNNER - Miniclaw OS")
    print("="*70)
    print("Mode: DEVELOPMENT (Zero API Cost)")
    print("Budget: $0.10/day for testing")
    print("Founder: King K (Ideas + Vision)")
    print("Engineer: Elon AI (Execution + Safeguards)")
    print("="*70)
    
    # Initialize test runner
    runner = SustainableTestRunner(daily_test_budget=0.10)
    
    # Discover tests
    test_suites = discover_tests()
    
    # Run unit tests (zero cost)
    runner.run_test_suite(test_suites["unit_tests"], "unit_tests")
    
    # Run integration tests (would have cost with real API)
    if test_suites["integration_tests"].countTestCases() > 0:
        runner.run_test_suite(test_suites["integration_tests"], "integration_tests")
    else:
        print("\n⚠️  No integration tests defined (using mocks for development)")
        print("   Real API tests will be added with founder approval")
    
    # Print final report
    runner.print_final_report()
    
    # Return exit code based on test results
    total_failures = sum(r["failures"] for r in runner.test_results)
    total_errors = sum(r["errors"] for r in runner.test_results)
    
    if total_failures == 0 and total_errors == 0:
        print("\n🎉 READY FOR FOUNDER APPROVAL AND PRODUCTION TESTING")
        return 0
    else:
        print(f"\n⚠️  NEEDS FIXING: {total_failures + total_errors} test failures")
        return 1


if __name__ == "__main__":
    sys.exit(main())