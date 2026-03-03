"""
LangGraph Workflow for Text-to-SQL Agent System
Defines the state and workflow connecting all 5 agents.
"""
from typing import TypedDict, Optional, List, Dict, Any
from langgraph.graph import StateGraph, END
import os
from dotenv import load_dotenv

from agents import (
    create_guardrail_agent,
    create_schema_agent,
    create_sql_generator_agent,
    create_sql_executor_agent,
    create_analysis_agent
)

# Load environment variables
load_dotenv()


class GraphState(TypedDict):
    """State that flows through the graph."""
    user_query: str
    is_relevant: bool
    guardrail_response: str
    db_schema: str
    sql_query: str
    query_results: List[Dict[Any, Any]]
    row_count: int
    final_answer: str
    error: Optional[str]


def create_text_to_sql_graph(db_path: str = "server_data.db"):
    """Create and return the LangGraph workflow."""
    
    # Get API key
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("Please set GROQ_API_KEY in your .env file")
    
    # Initialize agents
    guardrail_agent = create_guardrail_agent(api_key)
    schema_agent = create_schema_agent(db_path)
    sql_generator_agent = create_sql_generator_agent(api_key)
    sql_executor_agent = create_sql_executor_agent(db_path)
    analysis_agent = create_analysis_agent(api_key)
    
    # Define node functions
    def guardrail_node(state: GraphState) -> GraphState:
        """Node 1: Check if query is relevant."""
        result = guardrail_agent(state["user_query"])
        return {
            **state,
            "is_relevant": result["is_relevant"],
            "guardrail_response": result["guardrail_response"]
        }
    
    def schema_node(state: GraphState) -> GraphState:
        """Node 2: Get database schema."""
        result = schema_agent()
        return {
            **state,
            "db_schema": result["schema"]
        }
    
    def sql_generator_node(state: GraphState) -> GraphState:
        """Node 3: Generate SQL query."""
        result = sql_generator_agent(state["user_query"], state["db_schema"])
        return {
            **state,
            "sql_query": result["sql_query"]
        }
    
    def sql_executor_node(state: GraphState) -> GraphState:
        """Node 4: Execute SQL query."""
        result = sql_executor_agent(state["sql_query"])
        if not result["success"]:
            return {
                **state,
                "query_results": [],
                "row_count": 0,
                "error": result["error"]
            }
        return {
            **state,
            "query_results": result["results"],
            "row_count": result["row_count"],
            "error": None
        }
    
    def analysis_node(state: GraphState) -> GraphState:
        """Node 5: Analyze results."""
        # Handle SQL execution errors
        if state.get("error"):
            return {
                **state,
                "final_answer": f"Sorry, there was an error executing the query: {state['error']}\n\nGenerated SQL: {state['sql_query']}"
            }
        
        result = analysis_agent(
            state["user_query"],
            state["sql_query"],
            state["query_results"],
            state["row_count"]
        )
        return {
            **state,
            "final_answer": result["analysis"]
        }
    
    def not_relevant_node(state: GraphState) -> GraphState:
        """Handle non-relevant queries."""
        return {
            **state,
            "final_answer": f"I'm sorry, but your question doesn't seem to be related to the server XML error database.\n\n{state['guardrail_response']}\n\nPlease ask a question about XML errors, processing stages, job IDs, or error statistics."
        }
    
    # Define routing function
    def route_after_guardrail(state: GraphState) -> str:
        """Route based on relevance check."""
        if state["is_relevant"]:
            return "get_schema"
        return "not_relevant"
    
    # Build the graph
    workflow = StateGraph(GraphState)
    
    # Add nodes
    workflow.add_node("check_relevance", guardrail_node)
    workflow.add_node("get_schema", schema_node)
    workflow.add_node("generate_sql", sql_generator_node)
    workflow.add_node("execute_sql", sql_executor_node)
    workflow.add_node("analyze_results", analysis_node)
    workflow.add_node("reject_query", not_relevant_node)
    
    # Add edges
    workflow.set_entry_point("check_relevance")
    workflow.add_conditional_edges(
        "check_relevance",
        route_after_guardrail,
        {
            "get_schema": "get_schema",
            "not_relevant": "reject_query"
        }
    )
    workflow.add_edge("get_schema", "generate_sql")
    workflow.add_edge("generate_sql", "execute_sql")
    workflow.add_edge("execute_sql", "analyze_results")
    workflow.add_edge("analyze_results", END)
    workflow.add_edge("reject_query", END)
    
    # Compile and return
    return workflow.compile()


def run_query(query: str, db_path: str = "server_data.db") -> dict:
    """Run a query through the text-to-SQL pipeline."""
    graph = create_text_to_sql_graph(db_path)
    
    initial_state: GraphState = {
        "user_query": query,
        "is_relevant": False,
        "guardrail_response": "",
        "db_schema": "",
        "sql_query": "",
        "query_results": [],
        "row_count": 0,
        "final_answer": "",
        "error": None
    }
    
    result = graph.invoke(initial_state)
    return result
