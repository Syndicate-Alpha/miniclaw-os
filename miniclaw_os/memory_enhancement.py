#!/usr/bin/env python3
"""
Memory System Enhancement - Solving "forgetful agents"
Structured knowledge graphs, automatic summarization, context-aware retrieval
"""

import sqlite3
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import re
from collections import defaultdict
import math


class EnhancedPersistenceService:
    """Enhanced persistence with knowledge graphs and summarization"""
    
    def __init__(self, db_path: str = "miniclaw_data.db"):
        self.db_path = db_path
        self.conn = None
        self.setup_enhanced_database()
        
    def setup_enhanced_database(self):
        """Initialize enhanced database schema"""
        self.conn = sqlite3.connect(self.db_path)
        cursor = self.conn.cursor()
        
        # Enhanced knowledge table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS knowledge_enhanced (
                id TEXT PRIMARY KEY,
                category TEXT,
                content TEXT,
                summary TEXT,
                key_points TEXT,
                importance_score REAL DEFAULT 0.5,
                metadata TEXT,
                created_at TIMESTAMP,
                updated_at TIMESTAMP,
                access_count INTEGER DEFAULT 0,
                last_accessed TIMESTAMP
            )
        ''')
        
        # Knowledge relationships (graph structure)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS knowledge_relationships (
                source_id TEXT,
                target_id TEXT,
                relationship_type TEXT,
                strength REAL DEFAULT 0.5,
                metadata TEXT,
                created_at TIMESTAMP,
                PRIMARY KEY (source_id, target_id, relationship_type),
                FOREIGN KEY (source_id) REFERENCES knowledge_enhanced(id),
                FOREIGN KEY (target_id) REFERENCES knowledge_enhanced(id)
            )
        ''')
        
        # Conversation context (for summarization)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS conversation_context (
                conversation_id TEXT PRIMARY KEY,
                user_id TEXT,
                messages TEXT,
                summary TEXT,
                key_decisions TEXT,
                preferences TEXT,
                start_time TIMESTAMP,
                end_time TIMESTAMP,
                turn_count INTEGER DEFAULT 0
            )
        ''')
        
        # Memory access patterns (for context-aware retrieval)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS memory_access_patterns (
                pattern_id TEXT PRIMARY KEY,
                query_template TEXT,
                retrieved_ids TEXT,
                success_score REAL DEFAULT 0.5,
                access_count INTEGER DEFAULT 0,
                last_accessed TIMESTAMP
            )
        ''')
        
        self.conn.commit()
        print(f"✅ Enhanced persistence service initialized: {self.db_path}")
    
    def save_enhanced_knowledge(self, category: str, content: str, 
                               context: Dict = None, importance_hint: float = 0.5) -> str:
        """Save knowledge with automatic summarization and relationship detection"""
        knowledge_id = f"kb_enh_{int(time.time())}_{hash(content) % 10000}"
        
        # Generate summary and key points
        summary, key_points = self.summarize_content(content, context)
        
        # Calculate importance score
        importance_score = self.calculate_importance(content, summary, importance_hint)
        
        # Detect relationships with existing knowledge
        relationships = self.detect_relationships(content, category)
        
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO knowledge_enhanced 
            (id, category, content, summary, key_points, importance_score, metadata, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            knowledge_id,
            category,
            content,
            summary,
            json.dumps(key_points),
            importance_score,
            json.dumps(context or {}),
            datetime.now().isoformat(),
            datetime.now().isoformat()
        ))
        
        # Save relationships
        for target_id, rel_type, strength in relationships:
            cursor.execute('''
                INSERT OR REPLACE INTO knowledge_relationships 
                (source_id, target_id, relationship_type, strength, created_at)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                knowledge_id,
                target_id,
                rel_type,
                strength,
                datetime.now().isoformat()
            ))
        
        self.conn.commit()
        
        print(f"🧠 Enhanced knowledge saved: {category} -> {knowledge_id}")
        print(f"   Summary: {summary[:100]}...")
        print(f"   Key points: {len(key_points)}")
        print(f"   Relationships: {len(relationships)}")
        
        return knowledge_id
    
    def summarize_content(self, content: str, context: Dict = None) -> Tuple[str, List[str]]:
        """Extract summary and key points from content"""
        # Simple extractive summarization (mock - real would use NLP)
        sentences = re.split(r'[.!?]+', content)
        sentences = [s.strip() for s in sentences if len(s.strip()) > 10]
        
        if not sentences:
            return content[:200] + "...", []
        
        # Simple importance scoring (mock)
        importance_scores = []
        for sentence in sentences:
            score = 0.1  # Base score
            
            # Heuristics for importance
            if len(sentence) > 50:
                score += 0.1
            if any(keyword in sentence.lower() for keyword in ['important', 'critical', 'key', 'must', 'should']):
                score += 0.2
            if '?' in sentence:
                score += 0.1  # Questions often important
            
            importance_scores.append(score)
        
        # Get top sentences for summary
        if len(sentences) <= 3:
            summary = ' '.join(sentences)
            key_points = sentences[:3]
        else:
            # Get top 3 sentences by importance
            top_indices = sorted(range(len(importance_scores)), 
                               key=lambda i: importance_scores[i], 
                               reverse=True)[:3]
            top_indices.sort()  # Maintain original order
            summary = ' '.join(sentences[i] for i in top_indices)
            key_points = [sentences[i] for i in top_indices]
        
        # Add context if provided
        if context:
            context_str = ' '.join(f"{k}: {v}" for k, v in context.items() if v)
            if context_str:
                summary = f"[Context: {context_str}] {summary}"
        
        return summary, key_points
    
    def calculate_importance(self, content: str, summary: str, hint: float = 0.5) -> float:
        """Calculate importance score for knowledge"""
        # Base score from hint
        score = hint
        
        # Adjust based on content characteristics
        content_length = len(content)
        summary_length = len(summary)
        
        # Longer content with concise summary = likely important
        if content_length > 100 and summary_length < content_length * 0.3:
            score += 0.2
        
        # Check for important indicators
        important_indicators = [
            'decision', 'agreement', 'preference', 'requirement',
            'always', 'never', 'must', 'should', 'critical'
        ]
        
        content_lower = content.lower()
        for indicator in important_indicators:
            if indicator in content_lower:
                score += 0.05
        
        # Cap score between 0.1 and 1.0
        return max(0.1, min(1.0, score))
    
    def detect_relationships(self, new_content: str, category: str) -> List[Tuple[str, str, float]]:
        """Detect relationships with existing knowledge"""
        relationships = []
        
        cursor = self.conn.cursor()
        
        # Get recent knowledge in same category
        cursor.execute('''
            SELECT id, content FROM knowledge_enhanced 
            WHERE category = ? 
            ORDER BY created_at DESC 
            LIMIT 20
        ''', (category,))
        
        for row in cursor.fetchall():
            target_id, target_content = row
            
            # Simple similarity detection (mock - real would use embeddings)
            similarity = self.calculate_similarity(new_content, target_content)
            
            if similarity > 0.3:  # Threshold for relationship
                rel_type = "related_to"
                if similarity > 0.7:
                    rel_type = "highly_related"
                elif similarity > 0.5:
                    rel_type = "moderately_related"
                
                relationships.append((target_id, rel_type, similarity))
        
        return relationships
    
    def calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate text similarity (mock implementation)"""
        # Simple word overlap
        words1 = set(re.findall(r'\w+', text1.lower()))
        words2 = set(re.findall(r'\w+', text2.lower()))
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union)
    
    def get_context_aware_knowledge(self, query: str, context: Dict = None, limit: int = 10) -> List[Dict]:
        """Retrieve knowledge with context awareness"""
        cursor = self.conn.cursor()
        
        # Base query
        base_query = '''
            SELECT id, category, content, summary, key_points, importance_score, 
                   metadata, created_at, access_count
            FROM knowledge_enhanced 
            WHERE 1=1
        '''
        
        params = []
        
        # Add category filter if in context
        if context and 'category' in context:
            base_query += ' AND category = ?'
            params.append(context['category'])
        
        # Add temporal filter if in context
        if context and 'timeframe' in context:
            if context['timeframe'] == 'recent':
                base_query += ' AND created_at > datetime("now", "-7 days")'
            elif context['timeframe'] == 'today':
                base_query += ' AND date(created_at) = date("now")'
        
        # Order by relevance (importance + recency + access pattern)
        base_query += '''
            ORDER BY 
                importance_score DESC,
                CASE WHEN date(created_at) = date("now") THEN 1 ELSE 0 END DESC,
                access_count DESC,
                created_at DESC
            LIMIT ?
        '''
        params.append(limit * 3)  # Get more, then filter
        
        cursor.execute(base_query, params)
        results = []
        
        for row in cursor.fetchall():
            knowledge_id, category, content, summary, key_points_json, \
            importance_score, metadata_json, created_at, access_count = row
            
            # Calculate query relevance
            relevance = self.calculate_relevance(query, content, summary, context)
            
            # Boost relevance for frequently accessed knowledge
            if access_count > 10:
                relevance *= 1.1
            
            results.append({
                "id": knowledge_id,
                "category": category,
                "content": content,
                "summary": summary,
                "key_points": json.loads(key_points_json) if key_points_json else [],
                "importance_score": importance_score,
                "metadata": json.loads(metadata_json) if metadata_json else {},
                "created_at": created_at,
                "relevance_score": relevance,
                "access_count": access_count
            })
        
        # Sort by relevance and take top results
        results.sort(key=lambda x: x["relevance_score"], reverse=True)
        
        # Update access counts
        for result in results[:limit]:
            cursor.execute('''
                UPDATE knowledge_enhanced 
                SET access_count = access_count + 1, last_accessed = ?
                WHERE id = ?
            ''', (datetime.now().isoformat(), result["id"]))
        
        self.conn.commit()
        
        return results[:limit]
    
    def calculate_relevance(self, query: str, content: str, summary: str, context: Dict = None) -> float:
        """Calculate relevance score for query"""
        # Base similarity with query
        query_similarity = self.calculate_similarity(query, content)
        query_summary_similarity = self.calculate_similarity(query, summary)
        
        # Weighted combination
        relevance = (query_similarity * 0.7) + (query_summary_similarity * 0.3)
        
        # Context boosting
        if context:
            # Boost if category matches
            if 'category' in context and context['category'] in content.lower():
                relevance *= 1.2
            
            # Boost for recent knowledge if context suggests recency matters
            if 'prefer_recent' in context and context['prefer_recent']:
                # This would use created_at from the result
                relevance *= 1.1
        
        return relevance
    
    def get_related_knowledge(self, knowledge_id: str, relationship_type: str = None, 
                             limit: int = 5) -> List[Dict]:
        """Get knowledge related to a specific piece"""
        cursor = self.conn.cursor()
        
        query = '''
            SELECT k.id, k.category, k.content, k.summary, k.importance_score,
                   r.relationship_type, r.strength
            FROM knowledge_enhanced k
            JOIN knowledge_relationships r ON k.id = r.target_id
            WHERE r.source_id = ?
        '''
        
        params = [knowledge_id]
        
        if relationship_type:
            query += ' AND r.relationship_type = ?'
            params.append(relationship_type)
        
        query += ' ORDER BY r.strength DESC LIMIT ?'
        params.append(limit)
        
        cursor.execute(query, params)
        
        results = []
        for row in cursor.fetchall():
            target_id, category, content, summary, importance_score, \
            rel_type, strength = row
            
            results.append({
                "id": target_id,
                "category": category,
                "content_preview": content[:200] + "..." if len(content) > 200 else content,
                "summary": summary,
                "importance_score": importance_score,
                "relationship_type": rel_type,
                "relationship_strength": strength
            })
        
        return results
    
    def save_conversation_context(self, conversation_id: str, user_id: str, 
                                 messages: List[Dict], summary: str = None,
                                 key_decisions: List[str] = None, preferences: Dict = None):
        """Save conversation context for future reference"""
        if not summary:
            # Generate summary from messages
            all_text = ' '.join([msg.get('text', '') for msg in messages])
            summary, _ = self.summarize_content(all_text)
        
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO conversation_context 
            (conversation_id, user_id, messages, summary, key_decisions, preferences, 
             start_time, end_time, turn_count)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            conversation_id,
            user_id,
            json.dumps(messages),
            summary,
            json.dumps(key_decisions or []),
            json.dumps(preferences or {}),
            datetime.now().isoformat(),
            datetime.now().isoformat(),
            len(messages)
        ))
        
        self.conn.commit()
        
        # Extract and save key knowledge from conversation
        for message in messages:
            if message.get('role') == 'user' and len(message.get('text', '')) > 20:
                self.save_enhanced_knowledge(
                    category="conversation",
                    content=message['text'],
                    context={
                        "conversation_id": conversation_id,
                        "user_id": user_id,
                        "message_index": messages.index(message)
                    },
                    importance_hint=0.3  # Conversation content is moderately important
                )
    
    def get_conversation_history(self, user_id: str, limit: int = 5) -> List[Dict]:
        """Get conversation history for a user"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT conversation_id, summary, key_decisions, preferences, 
                   start_time, end_time, turn_count
            FROM conversation_context
            WHERE user_id = ?
            ORDER BY end_time DESC
            LIMIT ?
        ''', (user_id, limit))
        
        results = []
        for row in cursor.fetchall():
            conv_id, summary, key_decisions_json, preferences_json, \
            start_time, end_time, turn_count = row
            
            results.append({
                "conversation_id": conv_id,
                "summary": summary,
                "key_decisions": json.loads(key_decisions_json) if key_decisions_json else [],
                "preferences": json.loads(preferences_json) if preferences_json else {},
                "start_time": start_time,
                "end_time": end_time,
                "turn_count": turn_count,
                "duration_minutes": self.calculate_duration(start_time, end_time)
            })
        
        return results
    
    def calculate_duration(self, start_time: str, end_time: str) -> float:
        """Calculate duration in minutes"""
        try:
            start = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
            end = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
            return (end - start).total_seconds() / 60
        except:
            return 0.0
    
    def prune_low_importance_knowledge(self, keep_count: int = 1000):
        """Prune low-importance knowledge to manage memory"""
        cursor = self.conn.cursor()
        
        # Count total entries
        cursor.execute("SELECT COUNT(*) FROM knowledge_enhanced")
        total = cursor.fetchone()[0]
        
        if total <= keep_count:
            print(f"🧹 No pruning needed: {total} <= {keep_count}")
            return 0
        
        # Delete low-importance entries, keeping relationships
        cursor.execute('''
            DELETE FROM knowledge_enhanced 
            WHERE id IN (
                SELECT id FROM knowledge_enhanced 
                ORDER BY importance_score ASC, access_count ASC, created_at ASC
                LIMIT ?
            )
        ''', (total - keep_count,))
        
        deleted = cursor.rowcount
        
        # Also clean up orphaned relationships
        cursor.execute('''
            DELETE FROM knowledge_relationships 
            WHERE source_id NOT IN (SELECT id FROM knowledge_enhanced)
               OR target_id NOT IN (SELECT id FROM knowledge_enhanced)
        ''')
        
        orphaned_rels = cursor.rowcount
        
        self.conn.commit()
        
        print(f"🧹 Pruned {deleted} low-importance knowledge entries")
        print(f"   Cleaned {orphaned_rels} orphaned relationships")
        
        return deleted
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """Get memory system statistics"""
        cursor = self.conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM knowledge_enhanced")
        knowledge_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM knowledge_relationships")
        relationship_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM conversation_context")
        conversation_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT AVG(importance_score) FROM knowledge_enhanced")
        avg_importance = cursor.fetchone()[0] or 0.0
        
        cursor.execute("SELECT SUM(access_count) FROM knowledge_enhanced")
        total_accesses = cursor.fetchone()[0] or 0
        
        # Calculate memory efficiency
        cursor.execute("SELECT content FROM knowledge_enhanced LIMIT 100")
        sample_content = [row[0] for row in cursor.fetchall()]
        avg_content_length = sum(len(c) for c in sample_content) / len(sample_content) if sample_content else 0
        
        return {
            "knowledge_entries": knowledge_count,
            "relationships": relationship_count,
            "conversations": conversation_count,
            "avg_importance": round(avg_importance, 3),
            "total_accesses": total_accesses,
            "avg_content_length": round(avg_content_length),
            "memory_efficiency": "🟢 Good" if avg_importance > 0.4 else "🟡 Moderate" if avg_importance > 0.2 else "🔴 Poor"
        }


class MemoryLane:
    """Memory Lane feature - timeline of interactions and insights"""
    
    def __init__(self, persistence: EnhancedPersistenceService):
        self.persistence = persistence
    
    def generate_timeline(self, user_id: str, days_back: int = 30) -> List[Dict]:
        """Generate timeline of user interactions"""
        # Get conversations
        conversations = self.persistence.get_conversation_history(user_id, limit=50)
        
        # Get relevant knowledge
        relevant_knowledge = self.persistence.get_context_aware_knowledge(
            query=f"user {user_id} interactions",
            context={"category": "conversation", "prefer_recent": True},
            limit=20
        )
        
        timeline = []
        
        # Add conversations to timeline
        for conv in conversations:
            timeline.append({
                "type": "conversation",
                "id": conv["conversation_id"],
                "timestamp": conv["end_time"],
                "title": f"Conversation ({conv['turn_count']} turns)",
                "description": conv["summary"],
                "duration": conv["duration_minutes"],
                "key_decisions": conv["key_decisions"],
                "preferences": conv["preferences"]
            })
        
        # Add knowledge entries to timeline
        for knowledge in relevant_knowledge:
            if "conversation_id" in knowledge.get("metadata", {}):
                timeline.append({
                    "type": "knowledge",
                    "id": knowledge["id"],
                    "timestamp": knowledge["created_at"],
                    "title": f"Knowledge: {knowledge['category']}",
                    "description": knowledge["summary"],
                    "importance": knowledge["importance_score"],
                    "relevance": knowledge["relevance_score"]
                })
        
        # Sort by timestamp
        timeline.sort(key=lambda x: x["timestamp"], reverse=True)
        
        # Limit to requested timeframe
        cutoff_date = datetime.now() - timedelta(days=days_back)
        timeline = [item for item in timeline 
                   if datetime.fromisoformat(item["timestamp"].replace('Z', '+00:00')) > cutoff_date]
        
        return timeline
    
    def detect_patterns(self, user_id: str) -> Dict[str, Any]:
        """Detect patterns in user interactions"""
        timeline = self.generate_timeline(user_id, days_back=90)
        
        if not timeline:
            return {"patterns": [], "insights": []}
        
        # Simple pattern detection (mock - real would use ML)
        patterns = []
        insights = []
        
        # Count interaction types
        type_counts = defaultdict(int)
        for item in timeline:
            type_counts[item["type"]] += 1
        
        # Pattern: Frequent conversations
        if type_counts.get("conversation", 0) > 10:
            patterns.append({
                "type": "frequent_interaction",
                "description": f"User has {type_counts['conversation']} conversations in last 90 days",
                "confidence": min(0.9, type_counts["conversation"] / 20.0)
            })
        
        # Pattern: Knowledge accumulation
        if type_counts.get("knowledge", 0) > 5:
            patterns.append({
                "type": "knowledge_accumulation",
                "description": f"User has accumulated {type_counts['knowledge']} knowledge entries",
                "confidence": min(0.8, type_counts["knowledge"] / 10.0)
            })
        
        # Generate insights
        if patterns:
            insights.append("User is actively engaging with the system")
        
        if type_counts.get("conversation", 0) > 5:
            insights.append("Consider creating a personalized interaction pattern")
        
        return {
            "patterns": patterns,
            "insights": insights,
            "timeline_summary": {
                "total_interactions": len(timeline),
                "conversations": type_counts.get("conversation", 0),
                "knowledge_entries": type_counts.get("knowledge", 0),
                "timeframe_days": 90
            }
        }
    
    def get_user_profile(self, user_id: str) -> Dict[str, Any]:
        """Generate user profile from memory"""
        patterns = self.detect_patterns(user_id)
        timeline = self.generate_timeline(user_id, days_back=30)
        
        # Extract preferences from conversations
        preferences = defaultdict(set)
        for item in timeline:
            if item["type"] == "conversation" and item.get("preferences"):
                for key, value in item["preferences"].items():
                    if value:
                        preferences[key].add(str(value))
        
        # Simplify preferences
        simplified_prefs = {}
        for key, values in preferences.items():
            if len(values) == 1:
                simplified_prefs[key] = next(iter(values))
            elif len(values) > 1:
                # User has multiple preferences for this key
                simplified_prefs[key] = f"Varied: {', '.join(list(values)[:3])}"
        
        return {
            "user_id": user_id,
            "interaction_summary": patterns["timeline_summary"],
            "patterns": patterns["patterns"],
            "insights": patterns["insights"],
            "preferences": simplified_prefs,
            "recent_activity": {
                "last_interaction": timeline[0]["timestamp"] if timeline else None,
                "interaction_count_30d": len(timeline),
                "active_days": len(set(item["timestamp"][:10] for item in timeline))  # Date part only
            }
        }


# Demo function
def demo_enhanced_memory():
    """Demonstrate enhanced memory system"""
    print("🧠 DEMONSTRATING ENHANCED MEMORY SYSTEM")
    print("="*60)
    
    # Initialize enhanced persistence
    persistence = EnhancedPersistenceService(":memory:")  # In-memory database for demo
    
    print("\n1. 📝 Saving enhanced knowledge...")
    
    # Save some knowledge with automatic summarization
    kb1 = persistence.save_enhanced_knowledge(
        category="user_preference",
        content="The user prefers dark mode interface and wants notifications only for important updates. They mentioned this three times in different conversations.",
        context={"user_id": "user_123", "source": "conversation_analysis"},
        importance_hint=0.8
    )
    
    kb2 = persistence.save_enhanced_knowledge(
        category="technical_issue",
        content="User reported a bug where the dashboard doesn't update in real-time. The issue occurs when multiple tabs are open. Workaround: refresh the page.",
        context={"user_id": "user_123", "issue_severity": "medium"},
        importance_hint=0.7
    )
    
    print("\n2. 🔍 Context-aware retrieval...")
    
    # Retrieve knowledge with context
    results = persistence.get_context_aware_knowledge(
        query="user preferences",
        context={"category": "user_preference", "prefer_recent": True},
        limit=3
    )
    
    print(f"   Found {len(results)} relevant results:")
    for i, result in enumerate(results, 1):
        print(f"   {i}. {result['summary'][:100]}... (relevance: {result['relevance_score']:.2f})")
    
    print("\n3. 🔗 Relationship detection...")
    
    # Get related knowledge
    related = persistence.get_related_knowledge(kb1, limit=3)
    print(f"   Knowledge {kb1} has {len(related)} relationships:")
    for rel in related:
        print(f"   - {rel['relationship_type']} ({rel['relationship_strength']:.2f}): {rel['content_preview'][:80]}...")
    
    print("\n4. 💬 Conversation context...")
    
    # Save a conversation
    conversation_messages = [
        {"role": "user", "text": "I'm having trouble with the dashboard update."},
        {"role": "assistant", "text": "What seems to be the issue?"},
        {"role": "user", "text": "It doesn't show real-time data when I have multiple tabs open."},
        {"role": "assistant", "text": "That's a known issue. Try refreshing the page as a workaround."},
        {"role": "user", "text": "Thanks, that worked. Also, I prefer dark mode if possible."}
    ]
    
    persistence.save_conversation_context(
        conversation_id="conv_001",
        user_id="user_123",
        messages=conversation_messages,
        key_decisions=["Use refresh workaround", "Enable dark mode preference"],
        preferences={"interface_mode": "dark", "notifications": "important_only"}
    )
    
    print("   Conversation saved with context extraction")
    
    print("\n5. 🛣️ Memory Lane...")
    
    memory_lane = MemoryLane(persistence)
    timeline = memory_lane.generate_timeline("user_123", days_back=7)
    
    print(f"   Timeline for user_123 (last 7 days): {len(timeline)} events")
    for event in timeline[:3]:  # Show first 3
        print(f"   - {event['timestamp'][:10]}: {event['title']}")
    
    print("\n6. 🎯 User profile...")
    
    profile = memory_lane.get_user_profile("user_123")
    print(f"   User profile generated:")
    print(f"   - Interactions: {profile['interaction_summary']['total_interactions']}")
    print(f"   - Preferences: {len(profile['preferences'])} identified")
    print(f"   - Patterns: {len(profile['patterns'])} detected")
    
    print("\n7. 📊 Memory statistics...")
    
    stats = persistence.get_memory_stats()
    print(f"   Knowledge entries: {stats['knowledge_entries']}")
    print(f"   Relationships: {stats['relationships']}")
    print(f"   Average importance: {stats['avg_importance']:.2f}")
    print(f"   Memory efficiency: {stats['memory_efficiency']}")
    
    print("\n" + "="*60)
    print("✅ ENHANCED MEMORY SYSTEM DEMO COMPLETE")
    print("="*60)
    print("\nKey capabilities demonstrated:")
    print("1. 📝 Automatic summarization & key point extraction")
    print("2. 🔗 Relationship detection & knowledge graphs")
    print("3. 🔍 Context-aware retrieval with relevance scoring")
    print("4. 💬 Conversation context preservation")
    print("5. 🛣️ Memory Lane timeline & pattern detection")
    print("6. 🎯 User profile generation from memory")
    print("7. 📊 Memory efficiency monitoring")
    
    return {
        "knowledge_saved": 2,
        "relationships_detected": len(related),
        "context_retrieved": len(results),
        "conversation_context": True,
        "memory_efficiency": stats["memory_efficiency"]
    }


if __name__ == "__main__":
    demo_enhanced_memory()