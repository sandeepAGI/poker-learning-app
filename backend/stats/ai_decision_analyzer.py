from typing import List, Dict, Any, Tuple, Optional
import copy
import sys
import os

# Add the parent directory to sys.path to allow imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai.ai_manager import AIDecisionMaker
from stats.statistics_manager import get_statistics_manager
from utils.logger import get_logger

# Import the analyzer modules
try:
    from stats.analyzer.feedback_generator import FeedbackGenerator
    from stats.analyzer.hand_analyzer import HandAnalyzer
    from stats.analyzer.pattern_analyzer import PatternAnalyzer
    from stats.analyzer.recommendation_engine import RecommendationEngine
    from stats.analyzer.trend_analyzer import TrendAnalyzer
except ImportError as e:
    #print, which module failed to import   
    failed_module = e.name
    print(f"Failed to import module: {failed_module}")
# Create a logger for the AI decision analyzer
logger = get_logger("ai.decision_analyzer")