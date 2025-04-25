from agents import Agent
from src.agents.summary_agent import summary_agent
from src.tools.formatting_tools import evaluate_style

style_advisor_agent = Agent(
    name="StyleAdvisor",
    instructions=(
        "You analyze a player's moves and determine if their play style matches their declared style "
        "(aggressive, positional, tactical). Give friendly advice based on your evaluation."
    ),
    tools=[evaluate_style],
    handoffs=[summary_agent],
)
