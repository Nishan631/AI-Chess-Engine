import pygame as p
import sys
import ChessEngine
from ai_engine import find_best_move

# ---------------------- GLOBAL SETTINGS ----------------------
WIDTH = HEIGHT = 512
DIMENSION = 8
SQ_SIZE = HEIGHT // DIMENSION
MAX_FPS = 15
IMAGES = {}

# ---------------------- LOAD PIECE IMAGES ----------------------
def load_images():
    pieces = ["wp", "wR", "wN", "wB", "wQ", "wK",
              "bp", "bR", "bN", "bB", "bQ", "bK"]
    for piece in pieces:
        filename = piece[0] + piece[1].upper()
        IMAGES[piece] = p.transform.scale(
            p.image.load(f"images/{filename}.png"), (SQ_SIZE, SQ_SIZE))

# ---------------------- DRAW FUNCTIONS ----------------------
def draw_board(screen):
    colors = [p.Color("white"), p.Color("gray")]
    for r in range(DIMENSION):
        for c in range(DIMENSION):
            p.draw.rect(screen, colors[(r + c) % 2],
                        p.Rect(c * SQ_SIZE, r * SQ_SIZE, SQ_SIZE, SQ_SIZE))

def draw_pieces(screen, board):
    for r in range(DIMENSION):
        for c in range(DIMENSION):
            piece = board[r][c]
            if piece != "--":
                screen.blit(IMAGES[piece],
                            p.Rect(c * SQ_SIZE, r * SQ_SIZE, SQ_SIZE, SQ_SIZE))

def show_game_over(screen, result):
    font = p.font.SysFont("Arial", 48)
    if result == "checkmate":
        winner = "Black" if gs.whiteToMove else "White"
        text = font.render(f"Checkmate! {winner} wins!", True, p.Color("red"))
    elif result == "stalemate":
        text = font.render("Stalemate!", True, p.Color("red"))
    screen.blit(text, (WIDTH // 2 - text.get_width() // 2,
                       HEIGHT // 2 - text.get_height() // 2))
    p.display.flip()
    p.time.wait(3000)

# ---------------------- FRONT-END MENU ----------------------
def draw_menu(screen):
    screen.fill(p.Color("black"))
    font_title = p.font.SysFont("Arial", 60, True)
    font_option = p.font.SysFont("Arial", 36)

    title_text = font_title.render("CHESS GAME", True, p.Color("white"))
    screen.blit(title_text,
                (WIDTH // 2 - title_text.get_width() // 2, 100))

    options = ["1. Player vs Player", "2. Player vs AI", "3. Quit"]
    y = 250
    for option in options:
        txt = font_option.render(option, True, p.Color("lightgray"))
        screen.blit(txt, (WIDTH // 2 - txt.get_width() // 2, y))
        y += 60

    p.display.flip()

# ---------------------- MAIN LOOP ----------------------
def main():
    global gs
    p.init()
    screen = p.display.set_mode((WIDTH, HEIGHT))
    p.display.set_caption("Chess Game")
    clock = p.time.Clock()
    load_images()

    # ------------------ MENU LOOP ------------------
    mode = None
    while mode not in ["1", "2", "3"]:
        draw_menu(screen)
        for e in p.event.get():
            if e.type == p.QUIT:
                p.quit()
                sys.exit()
            elif e.type == p.KEYDOWN:
                if e.key == p.K_1:
                    mode = "1"
                elif e.key == p.K_2:
                    mode = "2"
                elif e.key == p.K_3:
                    p.quit()
                    sys.exit()

    player_vs_ai = (mode == "2")

    # ------------------ GAME LOGIC ------------------
    gs = ChessEngine.GameState()
    selectedSq = ()
    playerClicks = []
    running = True

    while running:
        draw_board(screen)
        draw_pieces(screen, gs.board)

        # Check for checkmate/stalemate
        result = gs.checkmate_or_stalemate()
        if result:
            show_game_over(screen, result)
            running = False

        for e in p.event.get():
            if e.type == p.QUIT:
                running = False
                p.quit()
                sys.exit()

            elif e.type == p.MOUSEBUTTONDOWN and (not player_vs_ai or gs.whiteToMove):
                pos = p.mouse.get_pos()
                col = pos[0] // SQ_SIZE
                row = pos[1] // SQ_SIZE
                if selectedSq == (row, col):
                    selectedSq = ()
                    playerClicks = []
                else:
                    selectedSq = (row, col)
                    playerClicks.append(selectedSq)

                if len(playerClicks) == 2:
                    move = ChessEngine.Move(playerClicks[0], playerClicks[1], gs.board)
                    matched_move = None
                    for valid_move in gs.get_valid_moves():
                        if move == valid_move:
                            matched_move = valid_move
                            break
                    if matched_move is not None:
                        gs.make_move(matched_move)
                        selectedSq = ()
                        playerClicks = []
                    else:
                        playerClicks = [selectedSq]

            elif e.type == p.KEYDOWN:
                if e.key == p.K_z:  # Undo
                    gs.undo_move()
                elif e.key == p.K_y:  # Redo
                    gs.redo_move()

        # AI Move
        if player_vs_ai and not gs.whiteToMove:
            ai_move = find_best_move(gs, level="intermediate")
            if ai_move:
                gs.make_move(ai_move)

        clock.tick(MAX_FPS)
        p.display.flip()

if __name__ == "__main__":
    main()
