"""
Main Entry Point for Text-to-SQL Agent System
CLI interface for interacting with the agent pipeline.
"""
import os
import sys
from pathlib import Path

# Ensure we're in the correct directory
os.chdir(Path(__file__).parent)

from dotenv import load_dotenv
load_dotenv()

from db_setup import create_database, get_schema
from graph import run_query


def setup_database():
    """Ensure database is set up."""
    db_path = Path("server_data.db")
    if not db_path.exists():
        print("=" * 60)
        print("Setting up database...")
        print("=" * 60)
        create_database()
        print()


def print_banner():
    """Print welcome banner."""
    print()
    print("=" * 60)
    print("  TEXT-TO-SQL AGENT SYSTEM")
    print("  Powered by LangGraph + Groq (Llama 3)")
    print("Ask questions about the server XML error database in natural language.")
    print("Type 'quit' or 'exit' to stop.")
    print("Type 'schema' to see the database schema.")
    print()


def main():
    """Main entry point."""
    # Check API key
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        print("ERROR: Please set your GROQ_API_KEY in the .env file")
        print("Example: GROQ_API_KEY=gsk_...")
        sys.exit(1)
    
    # Setup database
    setup_database()
    
    # Print banner
    print_banner()
    
    # Interactive loop
    while True:
        try:
            query = input("You: ").strip()
            
            if not query:
                continue
            
            if query.lower() in ['quit', 'exit', 'q']:
                print("\nGoodbye!")
                break
            
            if query.lower() == 'schema':
                print("\n" + get_schema())
                continue
            
            print("\nProcessing...\n")
            
            # Run the query through the pipeline
            result = run_query(query)
            
            # Print results
            print("-" * 40)
            print("ANALYSIS:")
            print("-" * 40)
            print(result["final_answer"])
            print()
            
            if result.get("sql_query") and result.get("is_relevant"):
                print("-" * 40)
                print("SQL QUERY USED:")
                print("-" * 40)
                print(result["sql_query"])
                print(f"\n(Returned {result['row_count']} rows)")
                print()
                
                if result.get("query_results"):
                    print("-" * 40)
                    print(f"RESULTS (First {min(20, len(result['query_results']))} rows):")
                    print("-" * 40)
                    for i, row in enumerate(result['query_results'][:20]):
                        print(f"{i+1}. {row}")
                    
                    if len(result['query_results']) > 20:
                        print(f"... and {len(result['query_results']) - 20} more rows")
                    print()
            
        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break
        except Exception as e:
            print(f"\nError: {e}\n")


if __name__ == "__main__":
    main()
