import pygame as p
import sys
import time
import os
import ChessEngine
from ai_engine import find_best_move
import chess_db as db
import random
import copy

WIDTH = 1200
HEIGHT = 800
BOARD_SIZE = 800
PANEL_WIDTH = WIDTH - BOARD_SIZE
DIMENSION = 8
SQ_SIZE = BOARD_SIZE // DIMENSION
MAX_FPS = 60
IMAGES = {}
SMALL_IMAGES = {}
CAPTURE_ICON_SIZE = 28

LIGHT_COLOR = p.Color(240, 217, 181)
DARK_COLOR = p.Color(181, 136, 99)
HIGHLIGHT_COLOR = p.Color(86, 167, 255)
LAST_MOVE_COLOR = p.Color(247, 246, 105)
LEGAL_MOVE_COLOR = p.Color(108, 197, 122)
CHECK_COLOR = p.Color(228, 94, 94)
BOARD_BORDER_COLOR = p.Color(72, 52, 31)

MENU_BG_TOP = (18, 31, 52)
MENU_BG_BOTTOM = (7, 13, 24)
PANEL_BG_TOP = (34, 43, 58)
PANEL_BG_BOTTOM = (17, 23, 33)
ANIMATION_SPEED = 8

flip_board = False

db.init_db()

def load_images():
    # Engine piece codes use lowercase pawns and uppercase for other piece letters.
    pieces = ["wp", "wR", "wN", "wB", "wQ", "wK",
              "bp", "bR", "bN", "bB", "bQ", "bK"]
    for piece in pieces:
        filename = piece[0] + piece[1].upper()
        image_path = os.path.join("images", f"{filename}.png")
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Missing image asset: {image_path}")
        IMAGES[piece] = p.transform.smoothscale(
            p.image.load(image_path).convert_alpha(), (SQ_SIZE, SQ_SIZE)
        )
        SMALL_IMAGES[piece] = p.transform.smoothscale(IMAGES[piece], (CAPTURE_ICON_SIZE, CAPTURE_ICON_SIZE))

def draw_vertical_gradient(screen, rect, top_color, bottom_color):
    if rect.height <= 0:
        return
    for i in range(rect.height):
        t = i / max(1, rect.height - 1)
        r = int(top_color[0] + (bottom_color[0] - top_color[0]) * t)
        g = int(top_color[1] + (bottom_color[1] - top_color[1]) * t)
        b = int(top_color[2] + (bottom_color[2] - top_color[2]) * t)
        p.draw.line(screen, (r, g, b), (rect.x, rect.y + i), (rect.x + rect.width, rect.y + i))

def draw_scene_background(screen):
    draw_vertical_gradient(screen, p.Rect(0, 0, WIDTH, HEIGHT), MENU_BG_TOP, MENU_BG_BOTTOM)
    glow = p.Surface((WIDTH, HEIGHT), p.SRCALPHA)
    p.draw.circle(glow, (35, 120, 220, 35), (WIDTH // 2, 120), 260)
    p.draw.circle(glow, (220, 180, 70, 18), (WIDTH // 2, HEIGHT - 80), 320)
    screen.blit(glow, (0, 0))

def display_coords_from_board(r, c):
    if not flip_board:
        return r, c
    return 7 - r, 7 - c

def board_coords_from_mouse(x, y):
    col = x // SQ_SIZE
    row = y // SQ_SIZE
    if col < 0: col = 0
    if col > 7: col = 7
    if row < 0: row = 0
    if row > 7: row = 7
    if not flip_board:
        return row, col
    return 7 - row, 7 - col

def display_rect_for_square(r, c):
    dr, dc = display_coords_from_board(r, c)
    return p.Rect(dc * SQ_SIZE, dr * SQ_SIZE, SQ_SIZE, SQ_SIZE)

def pixel_center_of_square(r, c):
    dr, dc = display_coords_from_board(r, c)
    return (dc * SQ_SIZE + SQ_SIZE//2, dr * SQ_SIZE + SQ_SIZE//2)

def draw_menu(screen, hover_idx=-1):
    draw_scene_background(screen)
    title_font = p.font.SysFont("Arial", 56, True)
    opt_font = p.font.SysFont("Arial", 28, True)
    small = p.font.SysFont("Arial", 16)

    title = title_font.render("AI CHESS ENGINE", True, p.Color("white"))
    screen.blit(title, (WIDTH//2 - title.get_width()//2, 48))

    options = ["Player vs Player", "Player vs AI", "Scorecard / Leaderboard", "Quit"]
    card_w, card_h = 420, 64
    start_y = 160
    gap = 22

    buttons = []
    for i, txt in enumerate(options):
        x = WIDTH//2 - card_w//2
        y = start_y + i*(card_h + gap)
        hovered = (i == hover_idx)
        bg_col = (26,28,36) if not hovered else (0,140,200)
        p.draw.rect(screen, (0, 0, 0, 80), (x + 2, y + 4, card_w, card_h), border_radius=12)
        p.draw.rect(screen, bg_col, (x, y, card_w, card_h), border_radius=12)
        p.draw.rect(screen, (60,60,70), (x, y, card_w, card_h), 2, border_radius=12)
        lbl = opt_font.render(txt, True, p.Color("white"))
        screen.blit(lbl, (x + 22, y + card_h//2 - lbl.get_height()//2))
        buttons.append((x, y, card_w, card_h))
    hint = small.render("Click a card to choose - Mouse & Keyboard supported (Esc to quit)", True, (180,180,185))
    screen.blit(hint, (WIDTH//2 - hint.get_width()//2, HEIGHT - 40))
    return buttons

def menu_loop(screen):
    clock = p.time.Clock()
    while True:
        mx, my = p.mouse.get_pos()
        clicked = False
        for e in p.event.get():
            if e.type == p.QUIT:
                p.quit(); sys.exit()
            if e.type == p.KEYDOWN:
                if e.key == p.K_ESCAPE:
                    p.quit(); sys.exit()
                if e.key == p.K_1:
                    return "1"
                if e.key == p.K_2:
                    return "2"
                if e.key == p.K_3:
                    return "3"
                if e.key == p.K_4:
                    return "4"
            if e.type == p.MOUSEBUTTONDOWN:
                clicked = True

        buttons = draw_menu(screen)
        hover = -1
        for i, (x, y, w, h) in enumerate(buttons):
            if x <= mx <= x+w and y <= my <= y+h:
                hover = i
                glow = p.Surface((w, h), p.SRCALPHA)
                glow.fill((0,170,255,30))
                screen.blit(glow, (x, y))
                if clicked:
                    return str(i+1)
        if hover != -1:
            draw_menu(screen, hover)
        p.display.flip()
        clock.tick(60)

def choose_color_ui(screen):
    clock = p.time.Clock()
    font = p.font.SysFont("Arial", 36, True)
    small = p.font.SysFont("Arial", 18)
    options = ["Play as White ", "Play as Black"]
    btn_w, btn_h = 520, 68
    while True:
        mx, my = p.mouse.get_pos(); clicked=False
        for e in p.event.get():
            if e.type == p.QUIT:
                p.quit(); sys.exit()
            if e.type == p.KEYDOWN and e.key == p.K_ESCAPE:
                p.quit(); sys.exit()
            if e.type == p.MOUSEBUTTONDOWN:
                clicked = True

        draw_scene_background(screen)
        title = font.render("Choose Your Color", True, p.Color("white"))
        screen.blit(title, (WIDTH//2 - title.get_width()//2, 48))
        start_y = 160; gap=28
        hover = -1
        for i, txt in enumerate(options):
            x = WIDTH//2 - btn_w//2
            y = start_y + i*(btn_h+gap)
            rect = p.Rect(x,y,btn_w,btn_h)
            if rect.collidepoint(mx,my):
                p.draw.rect(screen, (0, 0, 0, 80), (x + 2, y + 4, btn_w, btn_h), border_radius=12)
                p.draw.rect(screen, (0,140,200), rect, border_radius=12)
                hover = i
                if clicked:
                    return "2" if i==1 else "1"
            else:
                p.draw.rect(screen, (0, 0, 0, 80), (x + 2, y + 4, btn_w, btn_h), border_radius=12)
                p.draw.rect(screen, (30,34,42), rect, border_radius=12)
            txt_s = p.font.SysFont("Arial", 22).render(txt, True, p.Color("white"))
            screen.blit(txt_s, (x+22, y + btn_h//2 - txt_s.get_height()//2))
        hint = small.render("Click a card to select. (Esc to quit)", True, (170,170,170))
        screen.blit(hint, (WIDTH//2 - hint.get_width()//2, HEIGHT-40))
        p.display.flip(); clock.tick(60)

def choose_difficulty_ui(screen):
    clock = p.time.Clock()
    title_font = p.font.SysFont("Arial", 36, True)
    opt_font = p.font.SysFont("Arial", 20)
    opts = [("Beginner", "Easy "), ("Intermediate", "Balanced"), ("Advanced", "Stronger, deeper")]
    btn_w, btn_h = 480, 60
    while True:
        mx, my = p.mouse.get_pos(); clicked=False
        for e in p.event.get():
            if e.type == p.QUIT:
                p.quit(); sys.exit()
            if e.type == p.MOUSEBUTTONDOWN:
                clicked = True
            if e.type == p.KEYDOWN and e.key == p.K_ESCAPE:
                p.quit(); sys.exit()

        draw_scene_background(screen)
        title = title_font.render("Choose Difficulty", True, p.Color("white"))
        screen.blit(title, (WIDTH//2 - title.get_width()//2, 40))
        start_y = 140; gap = 20
        for i, (t,s) in enumerate(opts):
            x = WIDTH//2 - btn_w//2
            y = start_y + i*(btn_h+gap)
            rect = p.Rect(x,y,btn_w,btn_h)
            if rect.collidepoint(mx,my):
                p.draw.rect(screen, (0, 0, 0, 80), (x + 2, y + 4, btn_w, btn_h), border_radius=10)
                p.draw.rect(screen, (0,130,200), rect, border_radius=10)
                if clicked:
                    return ["beginner","intermediate","advanced"][i]
            else:
                p.draw.rect(screen, (0, 0, 0, 80), (x + 2, y + 4, btn_w, btn_h), border_radius=10)
                p.draw.rect(screen, (28,30,36), rect, border_radius=10)
            lbl = opt_font.render(f"{t} - {s}", True, p.Color("white"))
            screen.blit(lbl, (x+18, y + btn_h//2 - lbl.get_height()//2))
        p.display.flip(); clock.tick(60)

def show_scoreboard(screen):
    font = p.font.SysFont("Arial", 26, True)
    small = p.font.SysFont("Arial", 18)
    clock = p.time.Clock()
    players = db.list_players(limit=50)
    while True:
        for e in p.event.get():
            if e.type == p.QUIT:
                p.quit(); sys.exit()
            if e.type == p.KEYDOWN or e.type == p.MOUSEBUTTONDOWN:
                return
        draw_scene_background(screen)
        title = font.render("Scorecard - Leaderboard (Top by wins)", True, p.Color("white"))
        screen.blit(title, (WIDTH//2 - title.get_width()//2, 18))
        y = 70
        header = small.render(f"{ 'Rank':<6}{'Name':<22}{'W':>4}{'L':>5}{'D':>5}{'Total':>7}{'Win%':>8}", True, p.Color("lightgray"))
        screen.blit(header, (48, y)); y += 28
        rank = 1
        for row in players:
            total = row["wins"] + row["losses"] + row["draws"]
            win_pct = (row["wins"]/total*100.0) if total>0 else 0.0
            line = small.render(f"{rank:<6}{row['name']:<22}{row['wins']:>4}{row['losses']:>5}{row['draws']:>5}{total:>7}{win_pct:>7.1f}%", True, p.Color("lightgray"))
            screen.blit(line, (48,y)); y += 22; rank += 1
            if y > HEIGHT - 40:
                break
        foot = small.render("Press any key or click to return", True, p.Color("gray"))
        screen.blit(foot, (WIDTH//2 - foot.get_width()//2, HEIGHT - 36))
        p.display.flip(); clock.tick(60)

def square_name(r, c):
    return ChessEngine.Move.colsToFiles[c] + ChessEngine.Move.rowsToRanks[r]

def is_capture(move):
    return (move.pieceCaptured != "--") or move.isEnPassantMove

def is_pawn_promotion_move(move):
    return move.pieceMoved[1].lower() == 'p' and move.endRow in (0, 7)

def choose_promotion_ui(screen, color):
    clock = p.time.Clock()
    title_font = p.font.SysFont("Arial", 28, True)
    opt_font = p.font.SysFont("Arial", 22)
    options = [("Q", "Queen"), ("R", "Rook"), ("B", "Bishop"), ("N", "Knight")]
    btn_w, btn_h = 300, 52
    while True:
        mx, my = p.mouse.get_pos()
        clicked = False
        for e in p.event.get():
            if e.type == p.QUIT:
                p.quit(); sys.exit()
            if e.type == p.KEYDOWN:
                if e.key == p.K_ESCAPE:
                    return "Q"
                if e.unicode:
                    c = e.unicode.upper()
                    if c in ("Q", "R", "B", "N"):
                        return c
            if e.type == p.MOUSEBUTTONDOWN:
                clicked = True

        overlay = p.Surface((WIDTH, HEIGHT), p.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (0, 0))

        panel_h = 340
        panel = p.Rect(WIDTH // 2 - 220, HEIGHT // 2 - panel_h // 2, 440, panel_h)
        p.draw.rect(screen, (28, 30, 36), panel, border_radius=12)
        p.draw.rect(screen, (90, 90, 100), panel, 2, border_radius=12)

        title = title_font.render(f"Promote {color} pawn", True, p.Color("white"))
        screen.blit(title, (panel.centerx - title.get_width() // 2, panel.y + 18))

        start_y = panel.y + 72
        gap = 12
        for i, (code, name) in enumerate(options):
            rect = p.Rect(panel.x + 70, start_y + i * (btn_h + gap), btn_w, btn_h)
            hovered = rect.collidepoint(mx, my)
            p.draw.rect(screen, (0, 140, 200) if hovered else (52, 56, 66), rect, border_radius=10)
            txt = opt_font.render(f"{code} - {name}", True, p.Color("white"))
            screen.blit(txt, (rect.x + 16, rect.y + (btn_h - txt.get_height()) // 2))
            if hovered and clicked:
                return code

        hint = p.font.SysFont("Arial", 16).render("Keyboard: Q / R / B / N (Esc = Queen)", True, (180, 180, 180))
        screen.blit(hint, (panel.centerx - hint.get_width() // 2, panel.bottom - 28))
        p.display.flip()
        clock.tick(60)

def find_other_movers(gs, move):
    others = []
    typ = move.pieceMoved[1].upper()
    color = move.pieceMoved[0]
    for r in range(8):
        for c in range(8):
            if (r, c) == (move.startRow, move.startCol):
                continue
            pce = gs.board[r][c]
            if pce != "--" and pce[0] == color and pce[1].upper() == typ:
                pmoves = []
                pieceType = pce[1].upper()
                if pieceType == 'P':
                    gs.get_pawn_moves(r, c, pmoves)
                elif pieceType == 'R':
                    gs._slide_moves(r, c, [(-1,0),(1,0),(0,-1),(0,1)], pmoves)
                elif pieceType == 'B':
                    gs._slide_moves(r, c, [(-1,-1),(-1,1),(1,-1),(1,1)], pmoves)
                elif pieceType == 'Q':
                    gs._slide_moves(r, c, [(-1,0),(1,0),(0,-1),(0,1),(-1,-1),(-1,1),(1,-1),(1,1)], pmoves)
                elif pieceType == 'N':
                    gs.get_knight_moves(r, c, pmoves)
                elif pieceType == 'K':
                    gs.get_king_moves(r, c, pmoves)
                for m in pmoves:
                    if m.endRow == move.endRow and m.endCol == move.endCol:
                        others.append((r,c))
                        break
    return others

def move_to_san(move, gs_before):
    if move.isCastleMove:
        san = "O-O" if move.endCol == 6 else "O-O-O"
    else:
        piece = move.pieceMoved
        piece_letter = '' if piece[1].lower() == 'p' else piece[1].upper()
        capture = is_capture(move)
        dest = square_name(move.endRow, move.endCol)
        promotion = ''
        if move.promotionChoice:
            promotion = '=' + move.promotionChoice.upper()
        else:
            if piece[1].lower() == 'p' and (move.endRow == 0 or move.endRow == 7):
                promotion = '=Q'

        if piece_letter == '':
            if capture:
                san = ChessEngine.Move.colsToFiles[move.startCol] + 'x' + dest
            else:
                san = dest
            san += promotion
        else:
            others = find_other_movers(gs_before, move)
            disamb = ''
            if others:
                file_conflict = any(o[1] != move.startCol for o in others)
                rank_conflict = any(o[0] != move.startRow for o in others)
                if file_conflict and not rank_conflict:
                    disamb = ChessEngine.Move.colsToFiles[move.startCol]
                elif rank_conflict and not file_conflict:
                    disamb = ChessEngine.Move.rowsToRanks[move.startRow]
                else:
                    disamb = ChessEngine.Move.colsToFiles[move.startCol] + ChessEngine.Move.rowsToRanks[move.startRow]
            san = piece_letter + disamb + ('x' if capture else '') + dest + promotion

    gs_copy = copy.deepcopy(gs_before)
    gs_copy.makeMove(move)
    status = gs_copy.get_game_status()
    if status == "checkmate":
        san += '#'
    elif status == "check":
        san += '+'
    return san

def draw_board_frame(screen):
    p.draw.rect(screen, BOARD_BORDER_COLOR, p.Rect(0, 0, BOARD_SIZE, BOARD_SIZE), 4, border_radius=6)

def draw_board(screen):
    for r in range(DIMENSION):
        for c in range(DIMENSION):
            dr, dc = display_coords_from_board(r, c)
            color = LIGHT_COLOR if (r + c) % 2 == 0 else DARK_COLOR
            p.draw.rect(screen, color, p.Rect(dc * SQ_SIZE, dr * SQ_SIZE, SQ_SIZE, SQ_SIZE))

def draw_board_coordinates(screen):
    coord_font = p.font.SysFont("Arial", 13, True)

    # Rank labels on the left side.
    for board_r in range(8):
        disp_r, _ = display_coords_from_board(board_r, 0)
        rank = ChessEngine.Move.rowsToRanks[board_r]
        txt_color = DARK_COLOR if board_r % 2 == 0 else LIGHT_COLOR
        label = coord_font.render(rank, True, txt_color)
        screen.blit(label, (4, disp_r * SQ_SIZE + 4))

    # File labels along the bottom.
    edge_row = 7 if not flip_board else 0
    for board_c in range(8):
        _, disp_c = display_coords_from_board(edge_row, board_c)
        file_ch = ChessEngine.Move.colsToFiles[board_c]
        base_square_is_light = (edge_row + board_c) % 2 == 0
        txt_color = DARK_COLOR if base_square_is_light else LIGHT_COLOR
        label = coord_font.render(file_ch, True, txt_color)
        screen.blit(label, (disp_c * SQ_SIZE + SQ_SIZE - label.get_width() - 4, BOARD_SIZE - label.get_height() - 4))

def draw_last_move(screen, move):
    if not move:
        return
    s = p.Surface((SQ_SIZE, SQ_SIZE))
    s.set_alpha(120)
    s.fill(LAST_MOVE_COLOR)
    sr, sc = display_coords_from_board(move.startRow, move.startCol)
    er, ec = display_coords_from_board(move.endRow, move.endCol)
    screen.blit(s, (sc * SQ_SIZE, sr * SQ_SIZE))
    screen.blit(s, (ec * SQ_SIZE, er * SQ_SIZE))

def highlight_square(screen, sq):
    if not sq:
        return
    r, c = sq
    dr, dc = display_coords_from_board(r, c)
    s = p.Surface((SQ_SIZE, SQ_SIZE))
    s.set_alpha(120)
    s.fill(HIGHLIGHT_COLOR)
    screen.blit(s, (dc * SQ_SIZE, dr * SQ_SIZE))

def draw_check_square(screen, gs, status):
    if status != "check":
        return
    king_r, king_c = gs.whiteKingLocation if gs.whiteToMove else gs.blackKingLocation
    dr, dc = display_coords_from_board(king_r, king_c)
    s = p.Surface((SQ_SIZE, SQ_SIZE))
    s.set_alpha(115)
    s.fill(CHECK_COLOR)
    screen.blit(s, (dc * SQ_SIZE, dr * SQ_SIZE))

def draw_legal_moves(screen, moves):
    dot_radius = max(6, SQ_SIZE // 8)
    for r, c in moves:
        cx, cy = pixel_center_of_square(r, c)
        p.draw.circle(screen, LEGAL_MOVE_COLOR, (cx, cy), dot_radius)

def get_captured_pieces(board):
    target_counts = {"P": 8, "R": 2, "N": 2, "B": 2, "Q": 1}
    present = {
        "w": {"P": 0, "R": 0, "N": 0, "B": 0, "Q": 0},
        "b": {"P": 0, "R": 0, "N": 0, "B": 0, "Q": 0}
    }
    for r in range(8):
        for c in range(8):
            piece = board[r][c]
            if piece == "--":
                continue
            color = piece[0].lower()
            ptype = piece[1].upper()
            if ptype in present[color]:
                present[color][ptype] += 1

    order = ["Q", "R", "B", "N", "P"]
    captured_by_white = []
    captured_by_black = []
    for ptype in order:
        missing_black = max(0, target_counts[ptype] - present["b"][ptype])
        missing_white = max(0, target_counts[ptype] - present["w"][ptype])
        piece_code_black = "b" + ("p" if ptype == "P" else ptype)
        piece_code_white = "w" + ("p" if ptype == "P" else ptype)
        captured_by_white.extend([piece_code_black] * missing_black)
        captured_by_black.extend([piece_code_white] * missing_white)
    return captured_by_white, captured_by_black

def draw_pieces(screen, board, animate_move=None):
    if animate_move:
        move, progress = animate_move
    else:
        move = None
    for r in range(DIMENSION):
        for c in range(DIMENSION):
            piece = board[r][c]
            if piece != "--":
                if move and (r, c) == (move.startRow, move.startCol):
                    continue
                key = piece
                if key in IMAGES:
                    dr, dc = display_coords_from_board(r, c)
                    screen.blit(IMAGES[key], p.Rect(dc * SQ_SIZE, dr * SQ_SIZE, SQ_SIZE, SQ_SIZE))
    if move:
        sr, sc = move.startRow, move.startCol
        er, ec = move.endRow, move.endCol
        start_disp_r, start_disp_c = display_coords_from_board(sr, sc)
        end_disp_r, end_disp_c = display_coords_from_board(er, ec)
        start_pix = (start_disp_c * SQ_SIZE, start_disp_r * SQ_SIZE)
        end_pix = (end_disp_c * SQ_SIZE, end_disp_r * SQ_SIZE)
        cur_x = start_pix[0] + (end_pix[0] - start_pix[0]) * progress
        cur_y = start_pix[1] + (end_pix[1] - start_pix[1]) * progress
        key = move.pieceMoved
        if key in IMAGES:
            screen.blit(IMAGES[key], p.Rect(int(cur_x), int(cur_y), SQ_SIZE, SQ_SIZE))

def get_panel_layout():
    panel_rect = p.Rect(BOARD_SIZE, 0, PANEL_WIDTH, HEIGHT)
    header_rect = p.Rect(BOARD_SIZE + 14, 14, PANEL_WIDTH - 28, 34)
    status_rect = p.Rect(BOARD_SIZE + 16, 56, PANEL_WIDTH - 32, 32)
    info_rect = p.Rect(BOARD_SIZE + 16, 92, PANEL_WIDTH - 32, 26)
    captured_white_rect = p.Rect(BOARD_SIZE + 16, 126, PANEL_WIDTH - 32, 40)
    captured_black_rect = p.Rect(BOARD_SIZE + 16, 172, PANEL_WIDTH - 32, 40)
    cx = BOARD_SIZE + PANEL_WIDTH // 2
    cy = 232
    flip_radius = 20
    log_rect = p.Rect(BOARD_SIZE + 16, 272, PANEL_WIDTH - 32, 330)
    btn_w = PANEL_WIDTH - 40
    btn_h = 34
    btn_x = BOARD_SIZE + 20
    btn_y = HEIGHT - 150
    undo_rect = p.Rect(btn_x, btn_y, btn_w, btn_h)
    restart_rect = p.Rect(btn_x, btn_y + 44, btn_w, btn_h)
    toggle_rect = p.Rect(btn_x, btn_y + 88, btn_w, btn_h)
    return {
        'panel': panel_rect,
        'header': header_rect,
        'status': status_rect,
        'info': info_rect,
        'captured_white': captured_white_rect,
        'captured_black': captured_black_rect,
        'flip_center': (cx, cy),
        'flip_radius': flip_radius,
        'log': log_rect,
        'undo': undo_rect,
        'restart': restart_rect,
        'toggle': toggle_rect
    }

def status_label(gs, status):
    if status == "check":
        side = "White" if gs.whiteToMove else "Black"
        return f"{side} in check"
    if status == "checkmate":
        winner = "Black" if gs.whiteToMove else "White"
        return f"Checkmate: {winner} wins"
    if status == "stalemate":
        reason = gs.get_draw_reason() if hasattr(gs, "get_draw_reason") else None
        return {
            "stalemate": "Draw: stalemate",
            "threefold_repetition": "Draw: threefold repetition",
            "fifty_move_rule": "Draw: 50-move rule",
            "insufficient_material": "Draw: insufficient material",
        }.get(reason, "Draw")
    return "Game in progress"

def draw_captured_row(screen, rect, label, pieces):
    p.draw.rect(screen, (21, 24, 30), rect, border_radius=8)
    p.draw.rect(screen, (62, 68, 79), rect, 1, border_radius=8)
    label_font = p.font.SysFont("Arial", 14, True)
    label_s = label_font.render(label, True, (190, 200, 214))
    screen.blit(label_s, (rect.x + 8, rect.y + 4))
    x = rect.x + 8
    y = rect.y + 18
    for code in pieces:
        icon = SMALL_IMAGES.get(code)
        if icon:
            screen.blit(icon, (x, y))
            x += CAPTURE_ICON_SIZE - 2
            if x + CAPTURE_ICON_SIZE > rect.right - 6:
                break
    if not pieces:
        empty_s = p.font.SysFont("Arial", 14).render("-", True, (124, 132, 145))
        screen.blit(empty_s, (rect.x + 10, y + 3))

def draw_panel(screen, gs, san_moves, move_log_shown, font, player_vs_ai=False, ai_level="intermediate", human_turn=True, status="ongoing", matchup_text="", flip_btn_hover=False):
    L = get_panel_layout()
    draw_vertical_gradient(screen, L['panel'], PANEL_BG_TOP, PANEL_BG_BOTTOM)

    title = p.font.SysFont("Arial", 22, True).render("AI Chess Console", True, p.Color("white"))
    screen.blit(title, (L['header'].x, L['header'].y))

    badge_color = {
        "ongoing": (33, 111, 66),
        "check": (158, 89, 20),
        "checkmate": (165, 50, 52),
        "stalemate": (83, 88, 98),
    }.get(status, (83, 88, 98))
    p.draw.rect(screen, badge_color, L['status'], border_radius=8)
    st = p.font.SysFont("Arial", 15, True).render(status_label(gs, status), True, p.Color("white"))
    screen.blit(st, (L['status'].x + 10, L['status'].y + (L['status'].h - st.get_height()) // 2))

    turn_text = f"Turn: {'White' if gs.whiteToMove else 'Black'}"
    turn_text += f" | Move {len(san_moves) // 2 + 1}"
    if player_vs_ai:
        turn_text += f" | AI: {ai_level.title()}"
        if not human_turn and status in ("ongoing", "check"):
            turn_text += " | AI thinking"
    info_s = p.font.SysFont("Arial", 14).render(turn_text, True, (196, 206, 220))
    screen.blit(info_s, (L['info'].x, L['info'].y))
    if matchup_text:
        match_s = p.font.SysFont("Arial", 13).render(matchup_text, True, (157, 168, 186))
        screen.blit(match_s, (L['info'].x, L['info'].y + 15))

    captured_by_white, captured_by_black = get_captured_pieces(gs.board)
    draw_captured_row(screen, L['captured_white'], "Captured by White", captured_by_white)
    draw_captured_row(screen, L['captured_black'], "Captured by Black", captured_by_black)

    subtitle = font.render("Move Log (SAN)", True, p.Color("white"))
    screen.blit(subtitle, (L['log'].x, L['log'].y - 24))

    circle_color = (50, 50, 60) if not flip_btn_hover else (0, 140, 200)
    p.draw.circle(screen, circle_color, L['flip_center'], L['flip_radius'])
    p.draw.circle(screen, (100,100,110), L['flip_center'], L['flip_radius'], 2)
    icon_font = p.font.SysFont("Arial", 20, True)
    icon_s = icon_font.render("F", True, p.Color("white"))
    screen.blit(icon_s, (L['flip_center'][0] - icon_s.get_width()//2, L['flip_center'][1] - icon_s.get_height()//2))
    lbl = font.render("Flip (F)", True, p.Color("lightgray"))
    screen.blit(lbl, (L['flip_center'][0] - lbl.get_width()//2, L['flip_center'][1] + L['flip_radius'] + 6))
    p.draw.rect(screen, (22,24,28), L['log'], border_radius=8)
    p.draw.rect(screen, (60,60,70), L['log'], 2, border_radius=8)
    pad_x = 8
    pad_y = 8
    line_h = 20
    sx = L['log'].x + pad_x
    sy = L['log'].y + pad_y
    max_lines = (L['log'].h - pad_y*2)//line_h
    pairs = []
    for i in range(0, len(san_moves), 2):
        move_no = i//2 + 1
        w = san_moves[i] if i < len(san_moves) else ""
        b = san_moves[i+1] if (i+1) < len(san_moves) else ""
        pairs.append(f"{move_no}. {w}  {b}")
    if not move_log_shown:
        pairs = pairs[-(max_lines):]
    small = p.font.SysFont("Arial", 16)
    y = sy
    for line in pairs:
        txt = small.render(line, True, p.Color("lightgray"))
        screen.blit(txt, (sx, y)); y += line_h
        if y > L['log'].y + L['log'].h - pad_y:
            break
    for text, rect in [("Undo (Z)", L['undo']), ("Restart (R)", L['restart']), ("Toggle Log (M)", L['toggle'])]:
        p.draw.rect(screen, p.Color(60, 60, 60), rect, border_radius=8)
        p.draw.rect(screen, p.Color(90, 90, 100), rect, 2, border_radius=8)
        btn_font = p.font.SysFont("Arial", 16)
        txt = btn_font.render(text, True, p.Color("white"))
        screen.blit(txt, (rect.x + 12, rect.y + (rect.h - txt.get_height())//2))

def draw_debug_strip(screen, clock, gs, status, player_vs_ai, ai_level, human_turn, ai_pending, ai_last_think_seconds, enabled):
    if not enabled:
        return
    strip_h = 24
    y = HEIGHT - strip_h
    strip = p.Surface((WIDTH, strip_h), p.SRCALPHA)
    strip.fill((0, 0, 0, 160))
    screen.blit(strip, (0, y))

    fps = clock.get_fps()
    draw_reason = gs.get_draw_reason() if hasattr(gs, "get_draw_reason") else None
    ai_think_text = "n/a" if ai_last_think_seconds is None else f"{ai_last_think_seconds:.2f}s"
    ai_state = "thinking" if (player_vs_ai and not human_turn and ai_pending) else "idle"
    parts = [
        f"FPS {fps:5.1f}",
        f"status={status}",
        f"turn={'W' if gs.whiteToMove else 'B'}",
        f"plies={len(gs.moveLog)}",
        f"halfmove={getattr(gs, 'halfmoveClock', 0)}",
        f"draw={draw_reason or '-'}",
    ]
    if player_vs_ai:
        parts.extend([
            f"ai_level={ai_level}",
            f"ai_state={ai_state}",
            f"ai_last={ai_think_text}",
        ])
    parts.append("toggle=D")
    text = " | ".join(parts)
    font = p.font.SysFont("Consolas", 14)
    label = font.render(text, True, (220, 235, 240))
    screen.blit(label, (8, y + 4))

def show_game_over(screen, result, gs, draw_reason=None):
    font = p.font.SysFont("Arial", 36, True)
    if result == "checkmate":
        winner = "Black" if gs.whiteToMove else "White"
        text = font.render(f"Checkmate! {winner} wins!", True, p.Color("red"))
    elif result == "stalemate":
        reason = draw_reason
        if reason is None and hasattr(gs, "get_draw_reason"):
            reason = gs.get_draw_reason()
        draw_text = {
            "stalemate": "Draw by stalemate",
            "threefold_repetition": "Draw by threefold repetition",
            "fifty_move_rule": "Draw by 50-move rule",
            "insufficient_material": "Draw by insufficient material",
        }.get(reason, "Draw")
        text = font.render(draw_text, True, p.Color("red"))
    else:
        return
    s = p.Surface((BOARD_SIZE, BOARD_SIZE))
    s.set_alpha(220)
    s.fill(p.Color(0, 0, 0))
    screen.blit(s, (0, 0))
    screen.blit(text, (BOARD_SIZE//2 - text.get_width()//2, BOARD_SIZE//2 - text.get_height()//2))
    p.display.flip()
    p.time.wait(2000)

def get_text_input(screen, prompt="Enter name:", font=None, max_len=20):
    if font is None:
        font = p.font.SysFont("Arial", 24)
    clock = p.time.Clock()
    text = ""
    while True:
        for e in p.event.get():
            if e.type == p.QUIT:
                p.quit(); sys.exit()
            elif e.type == p.KEYDOWN:
                if e.key == p.K_RETURN:
                    if text.strip():
                        return text.strip()
                elif e.key == p.K_BACKSPACE:
                    text = text[:-1]
                else:
                    if len(text) < max_len and e.unicode.isprintable():
                        text += e.unicode
        s = p.Surface((WIDTH, HEIGHT))
        s.set_alpha(200)
        s.fill(p.Color(0,0,0))
        screen.blit(s, (0,0))
        prompt_s = font.render(prompt, True, p.Color("white"))
        screen.blit(prompt_s, (WIDTH//2 - prompt_s.get_width()//2, HEIGHT//2 - 60))
        input_box = p.Rect(WIDTH//2 - 200, HEIGHT//2 - 20, 400, 40)
        p.draw.rect(screen, p.Color(255,255,255), input_box, 2)
        txt_s = font.render(text, True, p.Color("white"))
        screen.blit(txt_s, (input_box.x + 10, input_box.y + 6))
        hint = font.render("Press Enter to confirm", True, p.Color("gray"))
        screen.blit(hint, (WIDTH//2 - hint.get_width()//2, HEIGHT//2 + 30))
        p.display.flip()
        clock.tick(30)

def show_stats_screen(screen, player_name, font):
    stats = db.get_player_stats(player_name)
    recent = db.get_recent_games_for_player(player_name, limit=10)
    running = True
    clock = p.time.Clock()
    while running:
        for e in p.event.get():
            if e.type == p.QUIT:
                p.quit(); sys.exit()
            elif e.type == p.KEYDOWN or e.type == p.MOUSEBUTTONDOWN:
                running = False
        s = p.Surface((WIDTH, HEIGHT))
        s.set_alpha(220)
        s.fill((10, 10, 10))
        screen.blit(s, (0, 0))
        title_font = p.font.SysFont("Arial", 30, True)
        title = title_font.render("Player Stats", True, p.Color("white"))
        screen.blit(title, (WIDTH//2 - title.get_width()//2, 20))
        small = p.font.SysFont("Arial", 20)
        y = 80
        lines = [
            f"Name: {stats['name']}",
            f"Wins: {stats['wins']}",
            f"Losses: {stats['losses']}",
            f"Draws: {stats['draws']}",
            f"Total games: {stats['total']}",
            f"Win rate: {stats['win_rate']:.1f} %"
        ]
        for line in lines:
            tx = small.render(line, True, p.Color("lightgray"))
            screen.blit(tx, (WIDTH//2 - 150, y)); y += 28
        sub = p.font.SysFont("Arial", 22, True)
        sub_t = sub.render("Recent games:", True, p.Color("white"))
        screen.blit(sub_t, (WIDTH//2 - 150, y + 10)); y += 40
        for g in recent:
            created = g["created_at"][:19].replace("T", " ")
            detail = g["draw_reason"] if g["result"] == "draw" and g["draw_reason"] else (g["game_status"] or g["result"])
            ai_meta = f"lvl={g['ai_level'] or '-'} d={g['ai_depth']}"
            text = f"{created} | {g['opponent_type']} | {detail} | {ai_meta} | {g['moves'][:45]}"
            tx = small.render(text, True, p.Color("lightgray"))
            screen.blit(tx, (WIDTH//2 - 350, y)); y += 20
            if y > HEIGHT - 40:
                break
        hint = small.render("Press any key or click to return", True, p.Color("gray"))
        screen.blit(hint, (WIDTH//2 - hint.get_width()//2, HEIGHT - 40))
        p.display.flip()
        clock.tick(30)

def main():
    global flip_board
    p.init()
    screen = p.display.set_mode((WIDTH, HEIGHT))
    p.display.set_caption("Chess (levels + SAN + DB) - Clean UI")
    clock = p.time.Clock()
    load_images()

    font = p.font.SysFont("Arial", 18)
    big_font = p.font.SysFont("Arial", 48, True)

    mode = menu_loop(screen)
    ai_depth_map = {"beginner": 2, "intermediate": 3, "advanced": 4}

    if mode == "1":
        player_vs_ai = False
        ai_plays_white = False
        player_name = None
        opponent_name = None
        ai_level = "intermediate"
        p1 = get_text_input(screen, prompt="Player 1 name (White):", font=font)
        db.get_or_create_player(p1)
        p2 = get_text_input(screen, prompt="Player 2 name (Black):", font=font)
        db.get_or_create_player(p2)
        player_name = p1; opponent_name = p2

    elif mode == "2":
        player_vs_ai = True
        ai_plays_white = False
        player_name = None
        opponent_name = None
        color_choice = choose_color_ui(screen)
        ai_plays_white = True if color_choice == "2" else False
        flip_board = True if ai_plays_white else False
        ai_level = choose_difficulty_ui(screen)
        player_name = get_text_input(screen, prompt="Enter your name:", font=font)
        db.get_or_create_player(player_name)
        db.set_setting("ai_level", ai_level)

    elif mode == "3":
        show_scoreboard(screen)
        mode = menu_loop(screen)
        if mode == "1":
            player_vs_ai = False
            ai_plays_white = False
            player_name = None
            opponent_name = None
            ai_level = "intermediate"
            p1 = get_text_input(screen, prompt="Player 1 name (White):", font=font)
            db.get_or_create_player(p1)
            p2 = get_text_input(screen, prompt="Player 2 name (Black):", font=font)
            db.get_or_create_player(p2)
            player_name = p1; opponent_name = p2
        elif mode == "2":
            player_vs_ai = True
            ai_plays_white = False
            player_name = None
            opponent_name = None
            color_choice = choose_color_ui(screen)
            ai_plays_white = True if color_choice == "2" else False
            flip_board = True if ai_plays_white else False
            ai_level = choose_difficulty_ui(screen)
            player_name = get_text_input(screen, prompt="Enter your name:", font=font)
            db.get_or_create_player(player_name)
            db.set_setting("ai_level", ai_level)
        else:
            p.quit(); sys.exit()

    else:
        p.quit(); sys.exit()

    gs = ChessEngine.GameState()
    valid_moves = gs.getValidMoves()
    move_made = False
    selected_sq = ()
    player_clicks = []
    running = True
    move_log_shown = True
    last_move = None
    animate = None
    san_moves = []
    ai_pending = False
    ai_last_think_seconds = None
    debug_strip_enabled = True
    game_start_ts = time.time()

    def build_record_kwargs(status, winner_color="", draw_reason="", perspective="", player_color="", opponent_label=""):
        elapsed = round(time.time() - game_start_ts, 2)
        metadata = {
            "perspective": perspective or "",
            "player_color": player_color or "",
            "opponent": opponent_label or "",
            "san_move_count": len(san_moves),
        }
        if player_vs_ai:
            metadata["ai_plays_white"] = ai_plays_white
        return {
            "game_mode": "pvai" if player_vs_ai else "pvp",
            "game_status": status,
            "draw_reason": draw_reason or "",
            "winner_color": winner_color.lower() if winner_color else "",
            "ai_level": ai_level if player_vs_ai else "",
            "move_count": len(san_moves),
            "duration_seconds": elapsed,
            "metadata": metadata,
        }

    while running:
        human_turn = (not player_vs_ai) or (gs.whiteToMove != ai_plays_white)

        for e in p.event.get():
            if e.type == p.QUIT:
                running = False; p.quit(); sys.exit()

            elif e.type == p.KEYDOWN:
                if e.key == p.K_f:
                    flip_board = not flip_board
                elif e.key == p.K_z:
                    gs.undoMove()
                    if san_moves:
                        san_moves.pop()
                    last_move = gs.moveLog[-1] if gs.moveLog else None
                    move_made = True
                    ai_pending = False
                elif e.key == p.K_r:
                    gs = ChessEngine.GameState()
                    valid_moves = gs.getValidMoves(); selected_sq = (); player_clicks = []
                    move_made = False; last_move = None; san_moves = []
                    ai_pending = False
                    ai_last_think_seconds = None
                elif e.key == p.K_m:
                    move_log_shown = not move_log_shown
                elif e.key == p.K_d:
                    debug_strip_enabled = not debug_strip_enabled

            elif e.type == p.MOUSEBUTTONDOWN and human_turn and animate is None:
                x, y = p.mouse.get_pos()
                layout = get_panel_layout()
                if x >= BOARD_SIZE:
                    if layout['undo'].collidepoint(x, y):
                        gs.undoMove()
                        if san_moves:
                            san_moves.pop()
                        last_move = gs.moveLog[-1] if gs.moveLog else None
                        move_made = True
                        ai_pending = False
                    elif layout['restart'].collidepoint(x, y):
                        gs = ChessEngine.GameState()
                        valid_moves = gs.getValidMoves()
                        selected_sq = (); player_clicks = []
                        move_made = False; last_move = None; san_moves = []
                        ai_pending = False
                        ai_last_think_seconds = None
                    elif layout['toggle'].collidepoint(x, y):
                        move_log_shown = not move_log_shown
                    elif (x - layout['flip_center'][0]) ** 2 + (y - layout['flip_center'][1]) ** 2 <= layout['flip_radius'] ** 2:
                        flip_board = not flip_board
                    elif layout['header'].collidepoint(x, y):
                        if player_name:
                            show_stats_screen(screen, player_name, font)
                else:
                    row, col = board_coords_from_mouse(x, y)
                    if selected_sq == (row, col):
                        selected_sq = (); player_clicks = []
                    else:
                        selected_sq = (row, col); player_clicks.append(selected_sq)
                    if len(player_clicks) == 2:
                        move = ChessEngine.Move(player_clicks[0], player_clicks[1], gs.board)
                        for valid in valid_moves:
                            if move == valid:
                                if is_pawn_promotion_move(valid):
                                    color = "white" if valid.pieceMoved[0].lower() == "w" else "black"
                                    valid.promotionChoice = choose_promotion_ui(screen, color)
                                san = move_to_san(valid, gs)
                                san_moves.append(san)
                                animate = (valid, 0.0)
                                gs.makeMove(valid)
                                last_move = valid
                                move_made = True
                                ai_pending = False
                                selected_sq = (); player_clicks = []
                                break
                        if not move_made:
                            player_clicks = [selected_sq]

        status = gs.get_game_status()
        if human_turn:
            ai_pending = False
        if player_vs_ai and not human_turn and status not in ("checkmate", "stalemate") and animate is None:
            if not ai_pending:
                ai_pending = True
            else:
                ai_pending = False
                ai_start = time.perf_counter()
                ai_move = find_best_move(gs, level=ai_level)
                ai_last_think_seconds = time.perf_counter() - ai_start
                if ai_move is None:
                    valid_moves = gs.getValidMoves()
                    if valid_moves:
                        ai_move = random.choice(valid_moves)
                if ai_move:
                    if is_pawn_promotion_move(ai_move) and not ai_move.promotionChoice:
                        ai_move.promotionChoice = "Q"
                    san = move_to_san(ai_move, gs)
                    san_moves.append(san)
                    animate = (ai_move, 0.0)
                    gs.makeMove(ai_move)
                    last_move = ai_move
                    move_made = True

        if animate:
            move_obj, progress = animate
            progress += ANIMATION_SPEED * clock.get_time() / 1000.0
            if progress >= 1.0:
                animate = None; progress = 1.0
            else:
                animate = (move_obj, progress)

        if move_made:
            valid_moves = gs.getValidMoves()
            move_made = False

        status = gs.get_game_status()
        human_turn = (not player_vs_ai) or (gs.whiteToMove != ai_plays_white)

        draw_scene_background(screen)
        draw_board_frame(screen)
        draw_board(screen)
        draw_last_move(screen, last_move)
        draw_check_square(screen, gs, status)
        highlight_square(screen, selected_sq)
        if selected_sq:
            legal = [(m.endRow, m.endCol) for m in valid_moves if m.startRow == selected_sq[0] and m.startCol == selected_sq[1]]
            draw_legal_moves(screen, legal)
        draw_pieces(screen, gs.board, animate_move=animate)
        draw_board_coordinates(screen)

        mx, my = p.mouse.get_pos()
        layout = get_panel_layout()
        flip_hover = ((mx - layout['flip_center'][0]) ** 2 + (my - layout['flip_center'][1]) ** 2 <= layout['flip_radius'] ** 2) and (BOARD_SIZE <= mx <= WIDTH)
        draw_panel(
            screen,
            gs,
            san_moves,
            move_log_shown,
            font,
            player_vs_ai=player_vs_ai,
            ai_level=ai_level,
            human_turn=human_turn and not ai_pending,
            status=status,
            matchup_text=(f"{player_name or 'Player'} vs AI" if player_vs_ai else f"{player_name or 'White'} vs {opponent_name or 'Black'}"),
            flip_btn_hover=flip_hover
        )
        draw_debug_strip(
            screen,
            clock,
            gs,
            status,
            player_vs_ai,
            ai_level,
            human_turn,
            ai_pending,
            ai_last_think_seconds,
            debug_strip_enabled
        )

        if status == "checkmate":
            show_game_over(screen, "checkmate", gs)
            winner_color = "White" if not gs.whiteToMove else "Black"

            if player_vs_ai:
                human_is_white = not ai_plays_white
                human_won = (winner_color == "White" and human_is_white) or (winner_color == "Black" and not human_is_white)
                human_color = "white" if human_is_white else "black"
                ai_color = "black" if human_is_white else "white"

                db.get_or_create_player("AI")
                if human_won:
                    db.record_game(
                        player_name, "AI", "AI", "win", ' '.join(san_moves), ai_depth=ai_depth_map.get(ai_level, 3),
                        **build_record_kwargs("checkmate", winner_color=winner_color, perspective="human", player_color=human_color, opponent_label="AI")
                    )
                    db.record_game(
                        "AI", "Human", player_name, "loss", ' '.join(san_moves), ai_depth=ai_depth_map.get(ai_level, 3),
                        **build_record_kwargs("checkmate", winner_color=winner_color, perspective="ai", player_color=ai_color, opponent_label=player_name)
                    )
                else:
                    db.record_game(
                        player_name, "AI", "AI", "loss", ' '.join(san_moves), ai_depth=ai_depth_map.get(ai_level, 3),
                        **build_record_kwargs("checkmate", winner_color=winner_color, perspective="human", player_color=human_color, opponent_label="AI")
                    )
                    db.record_game(
                        "AI", "Human", player_name, "win", ' '.join(san_moves), ai_depth=ai_depth_map.get(ai_level, 3),
                        **build_record_kwargs("checkmate", winner_color=winner_color, perspective="ai", player_color=ai_color, opponent_label=player_name)
                    )

            else:
                white_player = player_name
                black_player = opponent_name

                if winner_color == "White":
                    db.record_game(
                        white_player, "Human", black_player, "win", ' '.join(san_moves),
                        **build_record_kwargs("checkmate", winner_color=winner_color, perspective="human", player_color="white", opponent_label=black_player)
                    )
                    db.record_game(
                        black_player, "Human", white_player, "loss", ' '.join(san_moves),
                        **build_record_kwargs("checkmate", winner_color=winner_color, perspective="human", player_color="black", opponent_label=white_player)
                    )
                else:
                    db.record_game(
                        white_player, "Human", black_player, "loss", ' '.join(san_moves),
                        **build_record_kwargs("checkmate", winner_color=winner_color, perspective="human", player_color="white", opponent_label=black_player)
                    )
                    db.record_game(
                        black_player, "Human", white_player, "win", ' '.join(san_moves),
                        **build_record_kwargs("checkmate", winner_color=winner_color, perspective="human", player_color="black", opponent_label=white_player)
                    )

            running = False

        elif status == "stalemate":
            draw_reason = gs.get_draw_reason() or "stalemate"
            show_game_over(screen, "stalemate", gs, draw_reason=draw_reason)

            if player_vs_ai:
                human_color = "black" if ai_plays_white else "white"
                ai_color = "white" if ai_plays_white else "black"
                db.get_or_create_player("AI")
                db.record_game(
                    player_name, "AI", "AI", "draw", ' '.join(san_moves), ai_depth=ai_depth_map.get(ai_level, 3),
                    **build_record_kwargs("stalemate", draw_reason=draw_reason, perspective="human", player_color=human_color, opponent_label="AI")
                )
                db.record_game(
                    "AI", "Human", player_name, "draw", ' '.join(san_moves), ai_depth=ai_depth_map.get(ai_level, 3),
                    **build_record_kwargs("stalemate", draw_reason=draw_reason, perspective="ai", player_color=ai_color, opponent_label=player_name)
                )
            else:
                white_player = player_name
                black_player = opponent_name
                db.record_game(
                    white_player, "Human", black_player, "draw", ' '.join(san_moves),
                    **build_record_kwargs("stalemate", draw_reason=draw_reason, perspective="human", player_color="white", opponent_label=black_player)
                )
                db.record_game(
                    black_player, "Human", white_player, "draw", ' '.join(san_moves),
                    **build_record_kwargs("stalemate", draw_reason=draw_reason, perspective="human", player_color="black", opponent_label=white_player)
                )

            running = False

        p.display.flip()
        clock.tick(MAX_FPS)

    p.quit()

if __name__ == "__main__":
    main()
