from agents import Agent
from src.tools.formatting_tools import generate_summary

summary_agent = Agent(
    name="SummaryAgent",
    instructions=(
        "You are a chess coach creating a final game summary.\n"
        "Use the list of best moves and style advice to generate a clear, encouraging, and educational report.\n"
        "Highlight performance, mistakes, style match, and improvements."
    ),
    tools=[generate_summary],
)
