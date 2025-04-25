from typing import List, Dict
import chess
import chess.engine

STOCKFISH_PATH = "/opt/homebrew/bin/stockfish"

class Continuation(Dict):
    move: str
    score: int

class BestMove(Dict):
    move: str
    score: int
    continuations: List[Continuation]

def get_best_moves(fen: str, depth: int = 15, multipv: int = 3) -> List[BestMove]:
    results: List[BestMove] = []
    with chess.engine.SimpleEngine.popen_uci(STOCKFISH_PATH) as engine:
        board = chess.Board(fen)
        top_moves = engine.analyse(board, chess.engine.Limit(depth=depth), multipv=multipv)

        for info in top_moves:
            move = info["pv"][0]
            score = info["score"].pov(board.turn).score()
            move_san = board.san(move)

            new_board = board.copy()
            new_board.push(move)
            next_moves_info = engine.analyse(new_board, chess.engine.Limit(depth=depth), multipv=multipv)

            continuations = []
            continuations = [
                {"move": new_board.san(next_info["pv"][0]), "score": next_info["score"].pov(new_board.turn).score()}
                for next_info in next_moves_info
            ]

            results.append({"move": move_san, "score": score, "continuations": continuations})
    return results
