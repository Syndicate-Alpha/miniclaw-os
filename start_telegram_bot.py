#!/usr/bin/env python3
"""
Start Telegram bot for AI Empire control
Run this to start the founder control panel
"""

import os
import sys
import json
from pathlib import Path

def check_dependencies():
    """Check if required dependencies are installed"""
    try:
        import telegram
        print(f"✅ python-telegram-bot: {telegram.__version__}")
        return True
    except ImportError:
        print("❌ python-telegram-bot not installed")
        print("   Install with: pip install python-telegram-bot>=20.0")
        return False

def load_config():
    """Load Telegram configuration"""
    config_path = Path("telegram_config.json")
    if not config_path.exists():
        print("❌ telegram_config.json not found")
        return None
    
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        print("✅ Configuration loaded")
        return config
    except Exception as e:
        print(f"❌ Error loading config: {e}")
        return None

def start_bot_demo():
    """Start bot in demo mode"""
    print("\n" + "="*60)
    print("🧪 Starting Telegram Bot in DEMO MODE")
    print("="*60)
    
    from telegram_integration import main
    
    # Run in demo mode
    sys.argv = ["telegram_integration.py", "--demo"]
    main()

def start_bot_full():
    """Start bot with full integration"""
    print("\n" + "="*60)
    print("🤖 Starting Telegram Bot with FULL INTEGRATION")
    print("="*60)
    
    config = load_config()
    if not config:
        print("⚠️  Falling back to demo mode")
        start_bot_demo()
        return
    
    bot_token = config["telegram"]["bot_token"]
    channel_id = config["telegram"].get("channel_id")
    
    if not channel_id:
        print("⚠️  Channel ID not configured")
        print("   Please add channel ID to telegram_config.json")
        print("   Falling back to demo mode")
        start_bot_demo()
        return
    
    from telegram_integration import main
    
    # Run with full config
    sys.argv = [
        "telegram_integration.py",
        "--token", bot_token,
        "--channel", channel_id
    ]
    
    print(f"   Bot: {config['telegram']['bot_username']}")
    print(f"   Channel: {config['telegram']['channel_url']}")
    print(f"   Status: {config['telegram']['channel_status']}")
    print("\n✅ Bot starting...")
    
    try:
        main()
    except KeyboardInterrupt:
        print("\n🛑 Bot stopped by user")
    except Exception as e:
        print(f"❌ Error starting bot: {e}")
        print("⚠️  Falling back to demo mode")
        start_bot_demo()

def show_status():
    """Show current Telegram integration status"""
    config = load_config()
    
    print("\n" + "="*60)
    print("📊 TELEGRAM INTEGRATION STATUS")
    print("="*60)
    
    if config:
        telegram_cfg = config["telegram"]
        print(f"🤖 Bot: {telegram_cfg['bot_username']}")
        print(f"📢 Channel: {telegram_cfg['channel_url']}")
        print(f"🔒 Status: {telegram_cfg['channel_status'].upper()}")
        print(f"⚙️ Integration: {telegram_cfg['integration_status'].replace('_', ' ').title()}")
        
        if telegram_cfg["integration_status"] == "pending_channel_id":
            print("\n🚨 ACTION REQUIRED:")
            print("1. Add @AI_Empire2026_Bot as channel admin")
            print("2. Get numeric channel ID (e.g., -100xxxxxxxxxx)")
            print("3. Update telegram_config.json with channel_id")
    
    # Check dependencies
    deps_ok = check_dependencies()
    
    print("\n" + "="*60)
    print("Available commands:")
    print("  python start_telegram_bot.py status   - Show current status")
    print("  python start_telegram_bot.py demo     - Start in demo mode")
    print("  python start_telegram_bot.py start    - Start bot (if configured)")
    print("="*60)

def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        show_status()
        return
    
    command = sys.argv[1].lower()
    
    if command == "status":
        show_status()
    elif command == "demo":
        start_bot_demo()
    elif command == "start":
        if check_dependencies():
            start_bot_full()
        else:
            print("⚠️  Dependencies missing. Running demo mode instead.")
            start_bot_demo()
    else:
        print(f"❌ Unknown command: {command}")
        print("Available commands: status, demo, start")
        sys.exit(1)

if __name__ == "__main__":
    main()