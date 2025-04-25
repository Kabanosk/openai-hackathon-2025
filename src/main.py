# main.py

from src.agents.stockfish_agent import stockfish_analyzer
from src.models import User, Game
from agents import Runner


def main():
    # 1. Tworzymy użytkownika
    user = User(
        name="Janek",
        elo=1450,
        style="aggressive",
        openings=["Sicilian Defense", "King's Gambit"]
    )

    # 2. Tworzymy pozycję gry
    game = Game(
        fen="r1bqkbnr/pppp1ppp/2n5/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq - 2 3",
        user=user
    )

    # 3. Odpalamy TYLKO stockfish_analyzer - cała reszta idzie automatycznie dzięki handoffs!
    print("🚀 Uruchamiam pipeline analizy gry...")
    final_result = Runner.run_sync(stockfish_analyzer, f"Analyze and summarize this game: {game}")

    # 4. Wyświetlamy końcowy raport
    print("\n=== RAPORT Z GRY ===")
    print(final_result.final_output)


if __name__ == "__main__":
    main()
