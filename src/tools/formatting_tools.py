from agents import function_tool

from src.models import Game
from src.models import GameSummary, StyleAdvice, BestMove


@function_tool
def generate_summary(
    best_moves: list[BestMove], style_advice: StyleAdvice
) -> GameSummary:
    """Generates a full summary of the game based on moves and style evaluation."""

    mistakes = [bm.move for bm in best_moves if bm.score < -100]
    suggestions = [
        f"Consider alternatives to {bm.move}" for bm in best_moves if bm.score < -100
    ]

    avg_score = (
        sum(bm.score for bm in best_moves) / len(best_moves) if best_moves else 0
    )

    if avg_score > 50:
        performance = "Excellent"
    elif avg_score > 0:
        performance = "Good"
    else:
        performance = "Needs improvement"

    return GameSummary(
        overall_performance=performance,
        main_mistakes=mistakes,
        style_feedback=style_advice.advice,
        suggestions=suggestions,
    )

@function_tool
def evaluate_style(game: Game, moves: list[BestMove]) -> StyleAdvice:
    """Evaluates if the player's moves match their declared style."""

    user_style = game.user.style or "positional"  # domyślnie positional
    total_moves = len(moves)

    # Policzymy ile ruchów było bardzo ofensywnych (duży wzrost eval)
    aggressive_moves = sum(1 for move in moves if move.score > 50)

    ratio_aggressive = aggressive_moves / total_moves if total_moves else 0

    if user_style == "aggressive":
        matched = ratio_aggressive >= 0.4  # min 40% ruchów agresywnych
        advice = (
            "Good job staying aggressive!"
            if matched
            else "Try playing more actively and putting pressure on the opponent."
        )
    elif user_style == "positional":
        matched = all(abs(move.score) < 150 for move in moves)  # unika błędów
        advice = (
            "You played solid positional chess."
            if matched
            else "Be more careful, avoid unnecessary complications."
        )
    elif user_style == "tactical":
        matched = any(
            abs(c.score) > 100 for move in moves for c in move.continuations
        )  # ostre kontynuacje
        advice = (
            "Nice tactical awareness!"
            if matched
            else "Look for sharper continuations and tactics."
        )
    else:
        matched = True
        advice = "Style not recognized, but you played fine."

    return StyleAdvice(matched=matched, advice=advice)
