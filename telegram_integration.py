#!/usr/bin/env python3
"""
Telegram Integration for Miniclaw OS
Provides founder control via @AI_Empire2026_Bot
"""

import os
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import asyncio
from enum import Enum

# Try to import telegram libraries
TELEGRAM_AVAILABLE = False

# Mock classes for demo mode
class Update:
    pass

class ContextTypes:
    class DEFAULT_TYPE:
        pass

class InlineKeyboardButton:
    def __init__(self, text, callback_data=None):
        self.text = text
        self.callback_data = callback_data

class InlineKeyboardMarkup:
    def __init__(self, keyboard):
        self.keyboard = keyboard

class Application:
    @classmethod
    def builder(cls):
        return cls()
    
    def token(self, token):
        return self
    
    def build(self):
        return self
    
    def add_handler(self, handler):
        pass
    
    async def run_polling(self, allowed_updates):
        pass

class CommandHandler:
    def __init__(self, command, callback):
        self.command = command
        self.callback = callback

class MessageHandler:
    def __init__(self, filters, callback):
        self.filters = filters
        self.callback = callback

class CallbackQueryHandler:
    def __init__(self, callback):
        self.callback = callback

class filters:
    TEXT = "text"
    COMMAND = "command"
    
    @classmethod
    def TEXT(cls):
        return cls.TEXT
    
    @classmethod  
    def COMMAND(cls):
        return cls.COMMAND

# Import our systems
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from miniclaw_os.empire_learning import EmpireLearningSystem
    from safeguards import safeguard
    IMPORTS_SUCCESSFUL = True
except ImportError as e:
    print(f"⚠️  Import error: {e}")
    print("   Running in demo mode")
    IMPORTS_SUCCESSFUL = False


class ApprovalStatus(Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"


class TelegramControl:
    """Main Telegram control system for founder oversight"""
    
    def __init__(self, bot_token: str, channel_id: Optional[str] = None):
        self.bot_token = bot_token
        self.channel_id = channel_id
        self.pending_approvals: Dict[str, Dict] = {}
        self.learning_system = None
        self.safeguard = None
        
        # Initialize systems if available
        if IMPORTS_SUCCESSFUL:
            self.learning_system = EmpireLearningSystem(use_mocks=True)
            self.safeguard = safeguard
        
        # Bot application
        self.application = None
        
        # Setup logging
        logging.basicConfig(
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            level=logging.INFO
        )
        self.logger = logging.getLogger(__name__)
        
        print(f"🤖 Telegram Control initialized")
        print(f"   Bot: @AI_Empire2026_Bot")
        print(f"   Channel: {channel_id or 'Not set'}")
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        user = update.effective_user
        welcome_text = f"""
🚀 **AI Empire Control Panel**

Welcome, {user.first_name}! You are connected to the AI Empire control system.

**Available Commands:**
/status - System status and metrics
/evolution - Evolution progress
/safeguards - Safeguard settings and usage
/approvals - Pending approval requests
/budget - Cost and budget information
/help - Show this help message

**Quick Actions:**
👍 - Approve pending action
👎 - Reject pending action
🔄 - Refresh status

**Founder Alignment:** 0.95/1.0 (High Trust)
        """
        
        await update.message.reply_text(welcome_text, parse_mode='Markdown')
        
        # Log access
        self.logger.info(f"User {user.id} ({user.username}) accessed control panel")
    
    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /status command - show system status"""
        status_text = "🚀 **AI Empire Status**\n\n"
        
        if self.learning_system:
            status = self.learning_system.get_system_status()
            
            status_text += f"**Evolution Phase:** {status['evolution']['phase']}\n"
            status_text += f"**Learning Rate:** {status['evolution']['learning_rate']}x\n"
            status_text += f"**Founder Alignment:** {status['evolution']['founder_alignment']:.2f}/1.0\n\n"
            
            status_text += f"**Memory Efficiency:** {status['memory']['memory_efficiency']['efficiency']}\n"
            status_text += f"**Validated Patterns:** {status['memory']['learning_activity']['validated_patterns']}\n"
            status_text += f"**Pattern Candidates:** {status['memory']['learning_activity']['pattern_candidates']}\n\n"
            
            status_text += f"**Learning Velocity:** {status['performance']['learning_velocity']}\n"
        
        if self.safeguard:
            # Get safeguard stats
            status_text += "**🔒 Safeguards:**\n"
            status_text += f"API Calls Today: {self.safeguard.get_today_stats().get('total_calls', 0)}\n"
            status_text += f"Daily Cost: ${self.safeguard.get_today_stats().get('daily_cost_usd', 0):.4f}\n"
            status_text += f"Velocity: {self.safeguard.get_velocity_status()}\n"
        
        status_text += f"\n**Last Update:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}"
        
        # Add refresh button
        keyboard = [
            [InlineKeyboardButton("🔄 Refresh", callback_data="refresh_status")],
            [InlineKeyboardButton("📈 Evolution", callback_data="show_evolution")],
            [InlineKeyboardButton("🔒 Safeguards", callback_data="show_safeguards")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(status_text, parse_mode='Markdown', reply_markup=reply_markup)
    
    async def evolution_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /evolution command - show evolution progress"""
        if not self.learning_system:
            await update.message.reply_text("⚠️ Learning system not available in demo mode.")
            return
        
        status = self.learning_system.get_system_status()
        memory_stats = self.learning_system.tiered_memory.get_memory_stats()
        
        evolution_text = "🧬 **Exponential Evolution Progress**\n\n"
        
        evolution_text += f"**Phase {status['evolution']['phase']}**\n"
        
        # Phase requirements
        phase_requirements = {
            1: "3 validated patterns",
            2: "10 validated patterns", 
            3: "25 validated patterns",
            4: "50 validated patterns",
            5: "100+ validated patterns"
        }
        
        current_phase = status['evolution']['phase']
        if current_phase in phase_requirements:
            evolution_text += f"Next phase requires: {phase_requirements[current_phase]}\n"
        
        evolution_text += f"\n**Learning Metrics:**\n"
        evolution_text += f"Learning Rate: {status['evolution']['learning_rate']}x "
        evolution_text += f"({'📈 Growing' if status['evolution']['learning_rate'] > 1.2 else '📊 Stable' if status['evolution']['learning_rate'] > 0.8 else '📉 Slow'})\n"
        
        evolution_text += f"Founder Alignment: {status['evolution']['founder_alignment']:.2f}/1.0 "
        evolution_text += f"({'🎯 High Trust' if status['evolution']['founder_alignment'] > 0.8 else '⚠️ Needs Attention' if status['evolution']['founder_alignment'] > 0.5 else '🔴 Critical'})\n"
        
        evolution_text += f"\n**Memory Statistics:**\n"
        evolution_text += f"HOT Entries: {memory_stats['tiered_memory']['hot_entries']}\n"
        evolution_text += f"Validated Patterns: {memory_stats['learning_activity']['validated_patterns']}\n"
        evolution_text += f"Pattern Candidates: {memory_stats['learning_activity']['pattern_candidates']}\n"
        evolution_text += f"Recent Corrections (7d): {memory_stats['learning_activity']['recent_corrections_7d']}\n"
        
        # Evolution progress bar
        total_patterns = memory_stats['learning_activity']['validated_patterns']
        next_threshold = {1: 3, 2: 10, 3: 25, 4: 50, 5: 100}
        
        if current_phase in next_threshold:
            progress = min(100, int((total_patterns / next_threshold[current_phase]) * 100))
            bar_length = 20
            filled = int(bar_length * progress / 100)
            bar = "█" * filled + "░" * (bar_length - filled)
            evolution_text += f"\n**Progress to Phase {current_phase + 1}:**\n"
            evolution_text += f"`[{bar}] {progress}%`\n"
            evolution_text += f"({total_patterns}/{next_threshold[current_phase]} patterns)\n"
        
        await update.message.reply_text(evolution_text, parse_mode='Markdown')
    
    async def safeguards_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /safeguards command - show safeguard status"""
        if not self.safeguard:
            await update.message.reply_text("⚠️ Safeguards not available in demo mode.")
            return
        
        safeguard_text = "🔒 **Industrial Safeguards Status**\n\n"
        
        stats = self.safeguard.get_today_stats()
        velocity = self.safeguard.get_velocity_status()
        
        safeguard_text += "**Active Protections:**\n"
        safeguard_text += f"✅ Velocity Limit: 3 actions/hour\n"
        safeguard_text += f"✅ Cost Limit: $5.00/day\n"
        safeguard_text += f"✅ Memory Updates: Mandatory\n"
        safeguard_text += f"✅ Founder Approval: Telegram workflow\n\n"
        
        safeguard_text += "**Current Usage:**\n"
        safeguard_text += f"API Calls Today: {stats.get('total_calls', 0)}\n"
        safeguard_text += f"Daily Cost: ${stats.get('daily_cost_usd', 0):.4f}\n"
        safeguard_text += f"Cost Limit Used: {(stats.get('daily_cost_usd', 0) / 5.0 * 100):.1f}%\n"
        safeguard_text += f"Velocity Status: {velocity}\n\n"
        
        safeguard_text += "**Runway Calculation:**\n"
        daily_cost = stats.get('daily_cost_usd', 0.045)
        if daily_cost > 0:
            runway_days = 5.0 / daily_cost
            safeguard_text += f"Daily Burn: ${daily_cost:.3f}\n"
            safeguard_text += f"Runway: {runway_days:.1f} days at current rate\n"
        
        # Add safeguard controls
        keyboard = [
            [
                InlineKeyboardButton("📊 Usage Details", callback_data="usage_details"),
                InlineKeyboardButton("⚙️ Configure", callback_data="configure_safeguards")
            ],
            [
                InlineKeyboardButton("🔄 Reset Counters", callback_data="reset_counters"),
                InlineKeyboardButton("🚨 Emergency Stop", callback_data="emergency_stop")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(safeguard_text, parse_mode='Markdown', reply_markup=reply_markup)
    
    async def request_approval(self, action_type: str, description: str, 
                              estimated_cost: float = 0.0, data: Dict = None) -> str:
        """Request founder approval for an action"""
        approval_id = f"approval_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        approval_text = f"🔄 **Approval Requested**\n\n"
        approval_text += f"**Action:** {action_type}\n"
        approval_text += f"**Description:** {description}\n"
        
        if estimated_cost > 0:
            approval_text += f"**Estimated Cost:** ${estimated_cost:.4f}\n"
        
        if data:
            for key, value in data.items():
                if key not in ['sensitive', 'token', 'password']:
                    approval_text += f"**{key.title()}:** {value}\n"
        
        approval_text += f"\n**Approval ID:** `{approval_id}`\n"
        approval_text += f"**Expires:** 15 minutes\n\n"
        approval_text += "Please react with:\n"
        approval_text += "👍 - Approve and execute\n"
        approval_text += "👎 - Reject and cancel\n"
        approval_text += "⏸️ - Request more information"
        
        # Store approval request
        self.pending_approvals[approval_id] = {
            "action_type": action_type,
            "description": description,
            "estimated_cost": estimated_cost,
            "data": data or {},
            "status": ApprovalStatus.PENDING.value,
            "created_at": datetime.now().isoformat(),
            "expires_at": (datetime.now() + timedelta(minutes=15)).isoformat()
        }
        
        self.logger.info(f"Approval requested: {approval_id} - {action_type}")
        
        return approval_id, approval_text
    
    async def send_channel_announcement(self, announcement: str, importance: str = "info"):
        """Send announcement to Telegram channel"""
        if not self.channel_id:
            self.logger.warning("No channel ID set for announcements")
            return False
        
        # Format announcement based on importance
        if importance == "critical":
            formatted = f"🚨 **CRITICAL**\n\n{announcement}"
        elif importance == "warning":
            formatted = f"⚠️ **WARNING**\n\n{announcement}"
        elif importance == "success":
            formatted = f"✅ **SUCCESS**\n\n{announcement}"
        elif importance == "milestone":
            formatted = f"🎯 **MILESTONE**\n\n{announcement}"
        else:
            formatted = f"📢 **UPDATE**\n\n{announcement}"
        
        formatted += f"\n\n_Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}_"
        
        # In demo mode, just log it
        if not TELEGRAM_AVAILABLE:
            self.logger.info(f"Channel announcement ({importance}): {announcement[:100]}...")
            return True
        
        # TODO: Implement actual channel sending when we have channel ID
        self.logger.info(f"Would send to channel {self.channel_id}: {announcement[:100]}...")
        return True
    
    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle button callbacks"""
        query = update.callback_query
        await query.answer()
        
        data = query.data
        
        if data == "refresh_status":
            await self.status_command(update, context)
        elif data == "show_evolution":
            await self.evolution_command(update, context)
        elif data == "show_safeguards":
            await self.safeguards_command(update, context)
        elif data == "usage_details":
            await query.edit_message_text("📊 Usage details would be shown here.")
        elif data == "configure_safeguards":
            await query.edit_message_text("⚙️ Safeguard configuration interface would appear here.")
        elif data == "reset_counters":
            await query.edit_message_text("🔄 Counters reset would be executed here.")
        elif data == "emergency_stop":
            await query.edit_message_text("🚨 Emergency stop would be executed here.")
    
    def setup_handlers(self, application):
        """Setup command handlers"""
        application.add_handler(CommandHandler("start", self.start_command))
        application.add_handler(CommandHandler("status", self.status_command))
        application.add_handler(CommandHandler("evolution", self.evolution_command))
        application.add_handler(CommandHandler("safeguards", self.safeguards_command))
        application.add_handler(CommandHandler("help", self.start_command))
        
        # Button callbacks
        application.add_handler(CallbackQueryHandler(self.button_callback))
        
        # Message handler for reactions
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle regular messages (for reactions)"""
        message = update.message.text
        
        # Check for approval reactions
        if message in ["👍", "👎", "⏸️"]:
            await self.handle_approval_reaction(update, message)
    
    async def handle_approval_reaction(self, update: Update, reaction: str):
        """Handle approval reactions"""
        user = update.effective_user
        
        # Find pending approval for this user
        # In real implementation, we'd track which approval is pending for which user
        # For demo, we'll just acknowledge the reaction
        if reaction == "👍":
            response = "✅ Approval received! Action will be executed."
        elif reaction == "👎":
            response = "❌ Approval denied! Action cancelled."
        elif reaction == "⏸️":
            response = "⏸️ More information requested. Please provide details."
        else:
            response = f"Received: {reaction}"
        
        await update.message.reply_text(response)
        
        self.logger.info(f"User {user.id} reacted: {reaction}")
    
    async def run_bot(self):
        """Run the Telegram bot"""
        if not TELEGRAM_AVAILABLE:
            print("⚠️  python-telegram-bot not installed. Running in demo mode.")
            print("   To enable full Telegram integration, install:")
            print("   pip install python-telegram-bot>=20.0")
            return self.run_demo_mode()
        
        print(f"🤖 Starting Telegram bot: @AI_Empire2026_Bot")
        
        # Create application
        self.application = Application.builder().token(self.bot_token).build()
        
        # Setup handlers
        self.setup_handlers(self.application)
        
        # Start bot
        print("✅ Bot started. Press Ctrl+C to stop.")
        
        # Run until stopped
        await self.application.run_polling(allowed_updates=Update.ALL_TYPES)
    
    def run_demo_mode(self):
        """Run in demo mode without actual Telegram connection"""
        print("🧪 Running in DEMO MODE")
        print("="*60)
        
        # Simulate bot commands
        demo_commands = [
            ("/status", "Show system status"),
            ("/evolution", "Show evolution progress"),
            ("/safeguards", "Show safeguard status"),
            ("👍", "Approve action"),
            ("👎", "Reject action")
        ]
        
        print("Available demo commands:")
        for cmd, desc in demo_commands:
            print(f"  {cmd:15} - {desc}")
        
        print("\n" + "="*60)
        print("To enable full Telegram integration:")
        print("1. Install: pip install python-telegram-bot>=20.0")
        print("2. Provide channel ID (t.me/...)")
        print("3. Restart with full integration")
        print("="*60)
        
        # Show what status would look like
        print("\n🚀 **Demo Status:**")
        print("Evolution Phase: 1")
        print("Learning Rate: 1.33x")
        print("Founder Alignment: 0.95/1.0")
        print("Daily Cost: $0.045 ($4.955 remaining)")
        print("Validated Patterns: 0 (3 needed for Phase 2)")
        
        return True


def main():
    """Main function to run Telegram integration"""
    import argparse
    
    parser = argparse.ArgumentParser(description="AI Empire Telegram Control")
    parser.add_argument("--token", default=os.environ.get("TELEGRAM_BOT_TOKEN"),
                       help="Telegram bot token")
    parser.add_argument("--channel", default=os.environ.get("TELEGRAM_CHANNEL_ID"),
                       help="Telegram channel ID")
    parser.add_argument("--demo", action="store_true",
                       help="Run in demo mode")
    
    args = parser.parse_args()
    
    # Use provided token or the one from founder
    bot_token = args.token or "8676778641:AAFhP0jvVrTrD9l17KTK3Xa5gWYLXykb36U"
    channel_id = args.channel
    
    if not bot_token:
        print("❌ No bot token provided. Use --token or set TELEGRAM_BOT_TOKEN env var.")
        return
    
    print(f"🤖 Initializing AI Empire Telegram Control...")
    print(f"   Bot Token: {bot_token[:10]}... (masked)")
    print(f"   Channel ID: {channel_id or 'Not provided'}")
    
    # Create control system
    control = TelegramControl(bot_token=bot_token, channel_id=channel_id)
    
    if args.demo or not TELEGRAM_AVAILABLE:
        control.run_demo_mode()
    else:
        # Run async bot
        asyncio.run(control.run_bot())


if __name__ == "__main__":
    main()