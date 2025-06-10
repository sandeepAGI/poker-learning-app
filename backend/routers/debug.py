# backend/routers/debug.py
from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import PlainTextResponse, JSONResponse
from typing import List, Optional, Dict, Any
import os
import json
from datetime import datetime, timedelta
import glob

from utils.logger import get_logger, LOGS_DIR, get_correlation_id
from utils.auth import get_current_player
from utils.performance import performance_manager

router = APIRouter(prefix="/api/v1/debug", tags=["debug"])
logger = get_logger("debug")

@router.get("/logs", response_class=PlainTextResponse)
async def get_logs(
    log_type: str = Query("main", description="Log type: main, error, ai_decisions"),
    lines: int = Query(100, description="Number of lines to return"),
    player_id: str = Depends(get_current_player)
):
    """Get recent log entries"""
    
    # Map log types to files
    log_files = {
        "main": "poker_app.log",
        "error": "errors.log", 
        "ai_decisions": "ai_decisions.log"
    }
    
    if log_type not in log_files:
        raise HTTPException(status_code=400, detail=f"Invalid log type. Must be one of: {list(log_files.keys())}")
    
    log_file = os.path.join(LOGS_DIR, log_files[log_type])
    
    if not os.path.exists(log_file):
        raise HTTPException(status_code=404, detail=f"Log file {log_type} not found")
    
    try:
        # Read last N lines from log file
        with open(log_file, 'r') as f:
            all_lines = f.readlines()
            recent_lines = all_lines[-lines:] if len(all_lines) > lines else all_lines
            
        logger.info(f"Retrieved {len(recent_lines)} lines from {log_type} log")
        return ''.join(recent_lines)
        
    except Exception as e:
        logger.error(f"Error reading log file {log_type}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error reading log file: {str(e)}")

@router.get("/logs/search")
async def search_logs(
    query: str = Query(..., description="Search query"),
    log_type: str = Query("main", description="Log type to search"),
    hours: int = Query(24, description="Hours to search back"),
    player_id: str = Depends(get_current_player)
):
    """Search logs for specific patterns"""
    
    log_files = {
        "main": "poker_app.log",
        "error": "errors.log",
        "ai_decisions": "ai_decisions.log"
    }
    
    if log_type not in log_files:
        raise HTTPException(status_code=400, detail=f"Invalid log type. Must be one of: {list(log_files.keys())}")
    
    log_file = os.path.join(LOGS_DIR, log_files[log_type])
    
    if not os.path.exists(log_file):
        raise HTTPException(status_code=404, detail=f"Log file {log_type} not found")
    
    try:
        matches = []
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        with open(log_file, 'r') as f:
            for line_num, line in enumerate(f, 1):
                if query.lower() in line.lower():
                    # Try to parse as JSON for structured logs
                    try:
                        log_entry = json.loads(line.strip())
                        # Parse timestamp and check if within time range
                        log_time = datetime.fromisoformat(log_entry.get('timestamp', ''))
                        if log_time >= cutoff_time:
                            matches.append({
                                'line_number': line_num,
                                'entry': log_entry
                            })
                    except (json.JSONDecodeError, ValueError):
                        # Fallback for non-JSON logs
                        matches.append({
                            'line_number': line_num,
                            'entry': line.strip()
                        })
        
        logger.info(f"Found {len(matches)} matches for query '{query}' in {log_type} log")
        return {"matches": matches, "total_count": len(matches)}
        
    except Exception as e:
        logger.error(f"Error searching log file {log_type}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error searching log file: {str(e)}")

@router.get("/logs/correlation/{correlation_id}")
async def get_logs_by_correlation_id(
    correlation_id: str,
    player_id: str = Depends(get_current_player)
):
    """Get all log entries for a specific correlation ID"""
    
    try:
        matches = []
        log_files = ["poker_app.log", "errors.log", "ai_decisions.log"]
        
        for log_file in log_files:
            log_path = os.path.join(LOGS_DIR, log_file)
            if not os.path.exists(log_path):
                continue
                
            with open(log_path, 'r') as f:
                for line_num, line in enumerate(f, 1):
                    try:
                        log_entry = json.loads(line.strip())
                        if log_entry.get('correlation_id') == correlation_id:
                            matches.append({
                                'file': log_file,
                                'line_number': line_num,
                                'entry': log_entry
                            })
                    except json.JSONDecodeError:
                        # Skip non-JSON lines
                        continue
        
        # Sort by timestamp
        matches.sort(key=lambda x: x['entry'].get('timestamp', ''))
        
        logger.info(f"Found {len(matches)} log entries for correlation ID {correlation_id}")
        return {"correlation_id": correlation_id, "entries": matches, "total_count": len(matches)}
        
    except Exception as e:
        logger.error(f"Error retrieving logs for correlation ID {correlation_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error retrieving logs: {str(e)}")

@router.get("/system/info")
async def get_system_info(player_id: str = Depends(get_current_player)):
    """Get system debugging information"""
    
    try:
        # Get log file sizes and info
        log_info = {}
        for log_file in ["poker_app.log", "errors.log", "ai_decisions.log"]:
            log_path = os.path.join(LOGS_DIR, log_file)
            if os.path.exists(log_path):
                stat = os.stat(log_path)
                log_info[log_file] = {
                    "size_bytes": stat.st_size,
                    "size_mb": round(stat.st_size / (1024 * 1024), 2),
                    "modified": datetime.fromtimestamp(stat.st_mtime).isoformat()
                }
        
        # Get current correlation ID
        current_corr_id = get_correlation_id()
        
        info = {
            "current_correlation_id": current_corr_id,
            "logs_directory": LOGS_DIR,
            "log_files": log_info,
            "server_time": datetime.now().isoformat()
        }
        
        logger.info("System info requested")
        return info
        
    except Exception as e:
        logger.error(f"Error getting system info: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting system info: {str(e)}")

@router.post("/logs/test")
async def test_logging(
    message: str = Query("Test log message"),
    level: str = Query("info", description="Log level: debug, info, warning, error"),
    player_id: str = Depends(get_current_player)
):
    """Test logging functionality"""
    
    valid_levels = {"debug": logger.debug, "info": logger.info, "warning": logger.warning, "error": logger.error}
    
    if level not in valid_levels:
        raise HTTPException(status_code=400, detail=f"Invalid log level. Must be one of: {list(valid_levels.keys())}")
    
    try:
        # Log the test message
        log_func = valid_levels[level]
        log_func(f"Test message: {message}", extra={"test": True, "player_id": player_id})
        
        return {
            "message": f"Test log message sent at {level} level",
            "correlation_id": get_correlation_id(),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error testing logging: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error testing logging: {str(e)}")

@router.get("/performance/stats")
async def get_performance_stats(player_id: str = Depends(get_current_player)):
    """Get performance statistics including cache stats"""
    
    try:
        cache_stats = performance_manager.get_cache_stats()
        
        performance_stats = {
            "caching": cache_stats,
            "timestamp": datetime.now().isoformat(),
            "thread_pool": {
                "max_workers": 4,
                "active": True
            }
        }
        
        logger.info("Performance stats requested")
        return performance_stats
        
    except Exception as e:
        logger.error(f"Error getting performance stats: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting performance stats: {str(e)}")

@router.post("/performance/clear-cache")
async def clear_performance_cache(player_id: str = Depends(get_current_player)):
    """Clear all performance caches"""
    
    try:
        performance_manager.clear_caches()
        
        logger.info("Performance caches cleared")
        return {
            "message": "All performance caches cleared successfully",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error clearing performance cache: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error clearing performance cache: {str(e)}")