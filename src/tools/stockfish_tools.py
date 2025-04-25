from typing import List
import chess
import chess.engine

from agents import function_tool
from src.models import Game
from src.config import STOCKFISH_PATH


from src.models import BestMove, Continuation

from typing import Optional


@function_tool
def get_best_moves(
    game: Game, depth: Optional[int] = None, multipv: Optional[int] = None
) -> List[BestMove]:
    results: List[BestMove] = []
    fen = game.fen

    # Domyślne wartości jeśli nie podano
    depth = depth or 15
    multipv = multipv or 3

    with chess.engine.SimpleEngine.popen_uci(STOCKFISH_PATH) as engine:
        board = chess.Board(fen)
        top_moves = engine.analyse(
            board, chess.engine.Limit(depth=depth), multipv=multipv
        )

        for info in top_moves:
            move = info["pv"][0]
            score = info["score"].pov(board.turn).score()
            move_san = board.san(move)

            new_board = board.copy()
            new_board.push(move)
            next_moves_info = engine.analyse(
                new_board, chess.engine.Limit(depth=depth), multipv=multipv
            )

            continuations = [
                Continuation(
                    move=new_board.san(next_info["pv"][0]),
                    score=next_info["score"].pov(new_board.turn).score(),
                )
                for next_info in next_moves_info
            ]

            results.append(
                BestMove(move=move_san, score=score, continuations=continuations)
            )
    return results
