#!/usr/bin/env python3
"""
Mock services for sustainable development
Zero API cost during development
"""

import json
import time
from datetime import datetime
from typing import List, Dict, Any, Optional


class MockTelegram:
    """Mock Telegram service for development"""
    
    def __init__(self, chat_id: str = "7353765873"):
        self.chat_id = chat_id
        self.messages_sent = []
        self.messages_received = []
        
    def send_message(self, text: str, **kwargs) -> Dict[str, Any]:
        """Mock sending a Telegram message"""
        message = {
            "message_id": f"mock_{int(time.time())}",
            "chat_id": self.chat_id,
            "text": text,
            "timestamp": datetime.now().isoformat(),
            "mock": True
        }
        self.messages_sent.append(message)
        print(f"[MOCK Telegram] Sent: {text[:100]}...")
        return message
    
    def receive_message(self, text: str) -> Dict[str, Any]:
        """Mock receiving a Telegram message"""
        message = {
            "message_id": f"mock_recv_{int(time.time())}",
            "chat_id": self.chat_id,
            "text": text,
            "timestamp": datetime.now().isoformat(),
            "mock": True
        }
        self.messages_received.append(message)
        return message
    
    def get_history(self) -> Dict[str, List]:
        """Get message history"""
        return {
            "sent": self.messages_sent,
            "received": self.messages_received
        }


class MockLLM:
    """Mock LLM service for development"""
    
    def __init__(self, model: str = "deepseek/deepseek-chat"):
        self.model = model
        self.calls = 0
        self.total_tokens = 0
        
    def complete(self, prompt: str, system_message: str = "", **kwargs) -> str:
        """Mock LLM completion"""
        self.calls += 1
        tokens = len(prompt) // 4  # Rough token estimate
        self.total_tokens += tokens
        
        # Generate mock response based on prompt type
        if "research" in prompt.lower():
            response = f"""# MOCK Research Report

**Topic:** {prompt[:50]}...

## Key Findings (Mock):
1. This is a mock response for development
2. No API costs incurred
3. Real implementation will use DeepSeek API
4. Testing with mocks ensures cost control

## Analysis:
Mock analysis shows promising results. In production, this would be real research.

**Tokens used:** {tokens} (mock)
**Cost:** $0.00 (development mode)"""
        
        elif "analyze" in prompt.lower():
            response = f"""## MOCK Analysis

**Input:** {prompt[:100]}...

### Analysis Results:
- Mock analysis complete
- Development mode active
- No API calls made
- Ready for production testing

### Recommendations:
1. Test with real API when approved
2. Monitor costs in production
3. Use safeguards for rate limiting"""
        
        else:
            response = f"""MOCK RESPONSE

This is a development mock for: {prompt[:80]}...

[Development mode - no API costs]
[Real implementation available when approved]
[Token estimate: {tokens}]
[Model: {self.model}]"""
        
        print(f"[MOCK LLM] Call #{self.calls}: {tokens} tokens (mock)")
        return response
    
    def get_stats(self) -> Dict[str, Any]:
        """Get mock LLM statistics"""
        return {
            "calls": self.calls,
            "total_tokens": self.total_tokens,
            "estimated_cost": 0.0,
            "model": self.model,
            "mode": "mock"
        }


class MockOpenClaw:
    """Mock OpenClaw service for development"""
    
    def __init__(self):
        self.tool_calls = 0
        
    def web_search(self, query: str, count: int = 5) -> List[str]:
        """Mock web search"""
        self.tool_calls += 1
        results = [
            f"MOCK result 1 for: {query}",
            f"MOCK result 2: Information about {query}",
            f"MOCK result 3: {query} trends 2026",
            f"MOCK result 4: Research paper on {query}",
            f"MOCK result 5: Industry analysis of {query}"
        ][:count]
        
        print(f"[MOCK OpenClaw] Search: '{query}' -> {len(results)} results")
        return results
    
    def read_file(self, path: str) -> str:
        """Mock file reading"""
        self.tool_calls += 1
        content = f"MOCK file content for: {path}\n\nThis is a development mock.\nReal implementation will read actual files."
        print(f"[MOCK OpenClaw] Read file: {path}")
        return content
    
    def exec_command(self, command: str) -> Dict[str, Any]:
        """Mock command execution"""
        self.tool_calls += 1
        result = {
            "command": command,
            "output": f"MOCK output for: {command}",
            "exit_code": 0,
            "mock": True
        }
        print(f"[MOCK OpenClaw] Exec: {command}")
        return result
    
    def get_stats(self) -> Dict[str, Any]:
        """Get mock OpenClaw statistics"""
        return {
            "tool_calls": self.tool_calls,
            "mode": "mock"
        }


class MockSafeguard:
    """Mock safeguard for testing"""
    
    def __init__(self):
        self.checks = 0
        self.blocks = 0
        
    def before_action(self, action_type: str, estimated_tokens: int = 0) -> bool:
        """Mock pre-action check"""
        self.checks += 1
        print(f"[MOCK Safeguard] Check #{self.checks}: {action_type} ({estimated_tokens} tokens)")
        return True  # Always allow in mock mode
    
    def after_action(self, action_type: str, actual_tokens: int = 0, success: bool = True):
        """Mock post-action update"""
        print(f"[MOCK Safeguard] Action complete: {action_type}, success: {success}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get mock safeguard statistics"""
        return {
            "checks": self.checks,
            "blocks": self.blocks,
            "mode": "mock"
        }


# Global mock instances for easy import
mock_telegram = MockTelegram()
mock_llm = MockLLM()
mock_openclaw = MockOpenClaw()
mock_safeguard = MockSafeguard()


def get_mock_services() -> Dict[str, Any]:
    """Get all mock services"""
    return {
        "telegram": mock_telegram,
        "llm": mock_llm,
        "openclaw": mock_openclaw,
        "safeguard": mock_safeguard
    }


def print_mock_stats():
    """Print statistics for all mock services"""
    print("\n" + "="*60)
    print("MOCK SERVICES STATISTICS (Development Mode)")
    print("="*60)
    
    stats = {
        "Telegram": {
            "Messages Sent": len(mock_telegram.messages_sent),
            "Messages Received": len(mock_telegram.messages_received)
        },
        "LLM": mock_llm.get_stats(),
        "OpenClaw": mock_openclaw.get_stats(),
        "Safeguard": mock_safeguard.get_stats()
    }
    
    for service, data in stats.items():
        print(f"\n{service}:")
        for key, value in data.items():
            print(f"  {key}: {value}")
    
    print("\n" + "="*60)
    print("TOTAL API COST: $0.00 (Development Mode)")
    print("="*60)


if __name__ == "__main__":
    # Test the mock services
    print("🧪 Testing mock services...")
    
    # Test Telegram
    msg = mock_telegram.send_message("Hello from mock Telegram!")
    print(f"Telegram message sent: {msg['message_id']}")
    
    # Test LLM
    response = mock_llm.complete("Research AI agents in 2026")
    print(f"LLM response length: {len(response)} chars")
    
    # Test OpenClaw
    results = mock_openclaw.web_search("autonomous AI")
    print(f"OpenClaw search results: {len(results)}")
    
    # Test Safeguard
    if mock_safeguard.before_action("test_action", 1000):
        print("Safeguard check passed")
        mock_safeguard.after_action("test_action", 950, True)
    
    # Print statistics
    print_mock_stats()
    
    print("\n✅ Mock services test complete!")