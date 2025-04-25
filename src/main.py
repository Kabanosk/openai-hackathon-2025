from agents import Runner
from agents.game_state import Game, User
from agents.stockfish_agent import stockfish_analyzer


def main():
    # Symulujemy użytkownika
    user = User(
        name="Janek",
        elo=1450,
        style="aggressive",
        openings=["Sicilian Defense", "King's Gambit"],
    )

    # Symulujemy pozycję
    game_state = Game(
        fen="r1bqkbnr/pppp1ppp/2n5/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq - 2 3",
        user=user,
    )

    # Uruchamiamy analizę
    result = Runner.run_sync(stockfish_analyzer, f"Analyze this position: {game_state}")
    print(result.final_output)


if __name__ == "__main__":
    main()
