import logging

import zzlog

from . import TictactoePlayground

logger = logging.getLogger('reachy.tictactoe')


def run_game_loop(tictactoe_playground):
    # Wait for the board to be cleaned and ready to be played
    while True:
        board = tictactoe_playground.analyze_board()
        logger.info(
            'Waiting for board to be cleaned.',
            extra={
                'board': board,
            },
        )
        if tictactoe_playground.is_ready(board):
            break

        tictactoe_playground.run_random_idle_behavior()

    last_board = tictactoe_playground.reset()

    # Decide who goes first
    reachy_turn = tictactoe_playground.coin_flip()

    # Start game loop
    while True:
        board = tictactoe_playground.analyze_board()

        # We found an invalid board
        if board is None:
            continue

        # If we have detected some cheating or any issue
        # We reset the whole game
        if tictactoe_playground.cheating_detected(board, last_board):
            tictactoe_playground.shuffle_board()
            break

        # When it's human's turn to play
        # We wait for a change in board while running random idle behavior
        if not reachy_turn:
            if tictactoe_playground.has_human_played(board, last_board):
                reachy_turn = True
                logger.info('Next turn', extra={
                    'next_player': 'Reachy',
                })
            else:
                tictactoe_playground.run_random_idle_behavior()

        # When it's the robot's turn to play
        # We decide which action to take and plays it
        if (not tictactoe_playground.is_final(board)) and reachy_turn:
            action, _ = tictactoe_playground.choose_next_action(board)
            board = tictactoe_playground.play(action, board)

            last_board = board
            reachy_turn = False
            logger.info('Next turn', extra={
                'next_player': 'Human',
            })

        # If the game is over, determine who is the winner
        # and behave accordingly
        if tictactoe_playground.is_final(board):
            winner = tictactoe_playground.get_winner(board)

            if winner == 'robot':
                tictactoe_playground.run_celebration()
            elif winner == 'human':
                tictactoe_playground.run_defeat_behavior()
            else:
                tictactoe_playground.run_draw_behavior()

            return winner


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('--log-file')
    args = parser.parse_args()

    logger = zzlog.setup(
        logger_root='',
        filename=args.log_file,
    )

    logger.info(
        'Creating a Tic Tac Toe playground.'
    )

    with TictactoePlayground() as tictactoe_playground:
        tictactoe_playground.setup()

        game_played = 0

        while True:
            winner = run_game_loop(tictactoe_playground)
            game_played += 1
            logger.info(
                f'Game {game_played} ended - winner: {winner}',
                extra={
                    'winner': winner,
                }
            )

            if tictactoe_playground.need_cooldown():
                logger.warning('Reachy needs cooldown')
                tictactoe_playground.wait_for_cooldown()
                logger.info('Reachy cooldown finished')
