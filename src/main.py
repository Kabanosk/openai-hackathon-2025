from stockfish import get_best_moves

def main() -> None:
    fen = "r1bqkbnr/pppppppp/n7/8/8/5N2/PPPPPPPP/RNBQKB1R w KQkq - 2 2"
    # Call the get_best_moves function to analyze the position
    best_moves = get_best_moves(fen, depth=15, multipv=3)

    # Print the analysis results
    for idx, move_info in enumerate(best_moves, start=1):
        print(f"Top move {idx}: {move_info['move']} (Score: {move_info['score']})")
        for jdx, continuation in enumerate(move_info['continuations'], start=1):
            print(f"  Continuation {jdx}: {continuation['move']} (Score: {continuation['score']})")

if __name__ == "__main__":
    main()
