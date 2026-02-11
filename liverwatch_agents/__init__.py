"""
LiverWatch Google ADK Agents
============================

AI-powered agents for liver health assistance using Google Agent Development Kit.

This package provides:
- Root orchestrator agent that routes to specialized sub-agents
- Symptom assessment agent for health triage
- Diet and nutrition advisor agent
- Lab results interpreter agent  
- General health Q&A agent

Usage:
    from liverwatch_agents import root_agent
    
    # The root agent handles all interactions and routes to appropriate sub-agents
"""

from .agent import root_agent

__all__ = ['root_agent']
__version__ = '1.0.0'
