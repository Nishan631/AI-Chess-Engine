from copy import deepcopy

class CastlingRights:
    def __init__(self, wks, wqs, bks, bqs):
        self.wks = wks
        self.wqs = wqs
        self.bks = bks
        self.bqs = bqs

    def copy(self):
        return CastlingRights(self.wks, self.wqs, self.bks, self.bqs)

class Move:
    ranksToRows = {"1": 7, "2": 6, "3": 5, "4": 4, "5": 3, "6": 2, "7": 1, "8": 0}
    rowsToRanks = {v: k for k, v in ranksToRows.items()}
    filesToCols = {"a": 0, "b": 1, "c": 2, "d": 3, "e": 4, "f": 5, "g": 6, "h": 7}
    colsToFiles = {v: k for k, v in filesToCols.items()}

    def __init__(self, startSq, endSq, board, isEnPassantMove=False, isCastleMove=False, promotionChoice=None):
        self.startRow, self.startCol = startSq
        self.endRow, self.endCol = endSq
        self.pieceMoved = board[self.startRow][self.startCol]
        self.pieceCaptured = board[self.endRow][self.endCol]
        self.isEnPassantMove = isEnPassantMove
        if self.isEnPassantMove:
            self.pieceCaptured = ('bp' if self.pieceMoved[0].lower() == 'w' else 'wp')
        self.isCastleMove = isCastleMove
        self.promotionChoice = promotionChoice
        self.castlingRightsBefore = None
        self.enPassantBefore = None
        self.halfmoveClockBefore = 0
        self.moveID = self.startRow * 1000 + self.startCol * 100 + self.endRow * 10 + self.endCol

    def __eq__(self, other):
        return isinstance(other, Move) and self.moveID == other.moveID

    def getRankFile(self, r, c):
        return self.colsToFiles[c] + self.rowsToRanks[r]

    def getChessNotation(self):
        if self.isCastleMove:
            return "O-O" if self.endCol == 6 else "O-O-O"
        return self.getRankFile(self.startRow, self.startCol) + self.getRankFile(self.endRow, self.endCol)

class GameState:
    def __init__(self):
        self.board = [
            ["bR", "bN", "bB", "bQ", "bK", "bB", "bN", "bR"],
            ["bp", "bp", "bp", "bp", "bp", "bp", "bp", "bp"],
            ["--", "--", "--", "--", "--", "--", "--", "--"],
            ["--", "--", "--", "--", "--", "--", "--", "--"],
            ["--", "--", "--", "--", "--", "--", "--", "--"],
            ["--", "--", "--", "--", "--", "--", "--", "--"],
            ["wp", "wp", "wp", "wp", "wp", "wp", "wp", "wp"],
            ["wR", "wN", "wB", "wQ", "wK", "wB", "wN", "wR"]
        ]
        self.whiteToMove = True
        self.moveLog = []
        self.redoLog = []
        self.whiteKingLocation = (7, 4)
        self.blackKingLocation = (0, 4)
        self.enPassantPossible = ()
        self.currentCastlingRights = CastlingRights(True, True, True, True)
        self.castleRightsLog = [self.currentCastlingRights.copy()]
        self.checkmate = False
        self.stalemate = False
        self.drawReason = None
        self.halfmoveClock = 0
        self.positionCounts = {}
        self.positionHistory = []
        self._valid_moves_cache = None
        self._valid_moves_cache_key = (None, None)
        start_key = self._position_key()
        self.positionHistory.append(start_key)
        self.positionCounts[start_key] = 1

    def _castle_rights_key(self):
        return (
            self.currentCastlingRights.wks,
            self.currentCastlingRights.wqs,
            self.currentCastlingRights.bks,
            self.currentCastlingRights.bqs
        )

    def _position_key(self):
        board_key = tuple(tuple(row) for row in self.board)
        ep_key = self.enPassantPossible if self.enPassantPossible else None
        return (board_key, self.whiteToMove, self._castle_rights_key(), ep_key)

    def _track_position(self):
        key = self._position_key()
        self.positionHistory.append(key)
        self.positionCounts[key] = self.positionCounts.get(key, 0) + 1

    def _untrack_position(self):
        if not self.positionHistory:
            return
        key = self.positionHistory.pop()
        count = self.positionCounts.get(key, 0)
        if count <= 1:
            self.positionCounts.pop(key, None)
        else:
            self.positionCounts[key] = count - 1

    def makeMove(self, move):
        move.castlingRightsBefore = self.currentCastlingRights.copy()
        move.enPassantBefore = self.enPassantPossible
        move.halfmoveClockBefore = self.halfmoveClock
        is_pawn_move = len(move.pieceMoved) >= 2 and move.pieceMoved[1].lower() == 'p'
        is_capture_move = move.pieceCaptured != "--" or move.isEnPassantMove
        self.board[move.endRow][move.endCol] = move.pieceMoved
        self.board[move.startRow][move.startCol] = "--"
        if is_pawn_move:
            if move.endRow == 0 or move.endRow == 7:
                choice = (move.promotionChoice or 'Q').upper()
                self.board[move.endRow][move.endCol] = move.pieceMoved[0] + choice
        if move.isEnPassantMove:
            if move.pieceMoved[0].lower() == 'w':
                self.board[move.endRow + 1][move.endCol] = "--"
            else:
                self.board[move.endRow - 1][move.endCol] = "--"
        if len(move.pieceMoved) >= 2 and move.pieceMoved[1].upper() == 'K':
            if move.pieceMoved[0].lower() == 'w':
                self.whiteKingLocation = (move.endRow, move.endCol)
            else:
                self.blackKingLocation = (move.endRow, move.endCol)
        if move.isCastleMove:
            if move.endCol - move.startCol == 2:
                self.board[move.endRow][move.endCol - 1] = self.board[move.endRow][7]
                self.board[move.endRow][7] = "--"
            else:
                self.board[move.endRow][move.endCol + 1] = self.board[move.endRow][0]
                self.board[move.endRow][0] = "--"
        self.update_castle_rights(move)
        self.castleRightsLog.append(self.currentCastlingRights.copy())
        self.enPassantPossible = ()
        if is_pawn_move and abs(move.startRow - move.endRow) == 2:
            self.enPassantPossible = ((move.startRow + move.endRow) // 2, move.startCol)
        self.halfmoveClock = 0 if (is_pawn_move or is_capture_move) else (self.halfmoveClock + 1)
        self.moveLog.append(move)
        self.redoLog.clear()
        self.whiteToMove = not self.whiteToMove
        self._track_position()
        self.drawReason = None
        self._valid_moves_cache = None
        self._valid_moves_cache_key = (None, None)

    def make_move(self, move):
        return self.makeMove(move)

    def undoMove(self):
        if not self.moveLog:
            return
        self._untrack_position()
        move = self.moveLog.pop()
        self.board[move.startRow][move.startCol] = move.pieceMoved
        if move.isEnPassantMove:
            self.board[move.endRow][move.endCol] = "--"
            if move.pieceMoved[0].lower() == 'w':
                self.board[move.endRow + 1][move.endCol] = 'bp'
            else:
                self.board[move.endRow - 1][move.endCol] = 'wp'
        else:
            self.board[move.endRow][move.endCol] = move.pieceCaptured
        if move.isCastleMove:
            if move.endCol - move.startCol == 2:
                self.board[move.endRow][7] = self.board[move.endRow][move.endCol - 1]
                self.board[move.endRow][move.endCol - 1] = "--"
            else:
                self.board[move.endRow][0] = self.board[move.endRow][move.endCol + 1]
                self.board[move.endRow][move.endCol + 1] = "--"
        if len(move.pieceMoved) >= 2 and move.pieceMoved[1].upper() == 'K':
            if move.pieceMoved[0].lower() == 'w':
                self.whiteKingLocation = (move.startRow, move.startCol)
            else:
                self.blackKingLocation = (move.startRow, move.startCol)
        if move.castlingRightsBefore is not None:
            self.currentCastlingRights = move.castlingRightsBefore.copy()
        else:
            if self.castleRightsLog:
                self.castleRightsLog.pop()
                if self.castleRightsLog:
                    self.currentCastlingRights = self.castleRightsLog[-1].copy()
                else:
                    self.currentCastlingRights = CastlingRights(True, True, True, True)
        self.enPassantPossible = move.enPassantBefore if move.enPassantBefore is not None else ()
        self.halfmoveClock = move.halfmoveClockBefore
        self.whiteToMove = not self.whiteToMove
        self.redoLog.append(move)
        self.drawReason = None
        self._valid_moves_cache = None
        self._valid_moves_cache_key = (None, None)

    def undo_move(self):
        return self.undoMove()

    def redoMove(self):
        if self.redoLog:
            move = self.redoLog.pop()
            remaining_redo = list(self.redoLog)
            self.makeMove(move)
            self.redoLog = remaining_redo

    def redo_move(self):
        return self.redoMove()

    def update_castle_rights(self, move):
        if len(move.pieceMoved) >= 2 and move.pieceMoved[1].upper() == 'K':
            if move.pieceMoved[0].lower() == 'w':
                self.currentCastlingRights.wks = False
                self.currentCastlingRights.wqs = False
            else:
                self.currentCastlingRights.bks = False
                self.currentCastlingRights.bqs = False
        if len(move.pieceMoved) >= 2 and move.pieceMoved[1].upper() == 'R':
            if move.pieceMoved[0].lower() == 'w':
                if move.startRow == 7 and move.startCol == 0:
                    self.currentCastlingRights.wqs = False
                elif move.startRow == 7 and move.startCol == 7:
                    self.currentCastlingRights.wks = False
            else:
                if move.startRow == 0 and move.startCol == 0:
                    self.currentCastlingRights.bqs = False
                elif move.startRow == 0 and move.startCol == 7:
                    self.currentCastlingRights.bks = False
        if move.pieceCaptured != "--" and len(move.pieceCaptured) >= 2 and move.pieceCaptured[1].upper() == 'R':
            if move.endRow == 7 and move.endCol == 0:
                self.currentCastlingRights.wqs = False
            elif move.endRow == 7 and move.endCol == 7:
                self.currentCastlingRights.wks = False
            elif move.endRow == 0 and move.endCol == 0:
                self.currentCastlingRights.bqs = False
            elif move.endRow == 0 and move.endCol == 7:
                self.currentCastlingRights.bks = False

    def get_game_status(self):
        valid_moves = self.getValidMoves()
        in_check = self.in_check_for_current_player()
        self.drawReason = None
        if not valid_moves:
            if in_check:
                self.checkmate = True
                self.stalemate = False
                return "checkmate"
            else:
                self.checkmate = False
                self.stalemate = True
                self.drawReason = "stalemate"
                return "stalemate"
        if self.is_fifty_move_rule():
            self.checkmate = False
            self.stalemate = True
            self.drawReason = "fifty_move_rule"
            return "stalemate"
        if self.is_threefold_repetition():
            self.checkmate = False
            self.stalemate = True
            self.drawReason = "threefold_repetition"
            return "stalemate"
        if self.is_insufficient_material():
            self.checkmate = False
            self.stalemate = True
            self.drawReason = "insufficient_material"
            return "stalemate"
        elif in_check:
            self.checkmate = False
            self.stalemate = False
            return "check"
        else:
            self.checkmate = False
            self.stalemate = False
            return "ongoing"

    def checkmate_or_stalemate(self):
        status = self.get_game_status()
        return status if status in ["checkmate", "stalemate"] else None

    def is_game_over(self):
        return self.get_game_status() in ["checkmate", "stalemate"]

    def get_draw_reason(self):
        status = self.get_game_status()
        return self.drawReason if status == "stalemate" else None

    def is_threefold_repetition(self):
        current = self._position_key()
        return self.positionCounts.get(current, 0) >= 3

    def is_fifty_move_rule(self):
        return self.halfmoveClock >= 100

    def is_insufficient_material(self):
        non_king_minors = []
        for r in range(8):
            for c in range(8):
                piece = self.board[r][c]
                if piece == "--":
                    continue
                ptype = piece[1].upper()
                if ptype == 'K':
                    continue
                if ptype in ('P', 'R', 'Q'):
                    return False
                non_king_minors.append((piece[0].lower(), ptype, r, c))

        if not non_king_minors:
            return True
        if len(non_king_minors) == 1:
            return True

        # K + N + N vs K is an automatic draw by insufficient material.
        if len(non_king_minors) == 2:
            a, b = non_king_minors
            if a[1] == 'N' and b[1] == 'N' and a[0] == b[0]:
                return True

        # If all remaining pieces are bishops and they are all on the same color complex,
        # checkmate is impossible.
        if all(p[1] == 'B' for p in non_king_minors):
            bishop_square_colors = {(r + c) % 2 for _, _, r, c in non_king_minors}
            if len(bishop_square_colors) == 1:
                return True

        return False

    def getValidMoves(self):
        cache_key = (len(self.moveLog), self.whiteToMove)
        if self._valid_moves_cache is not None and self._valid_moves_cache_key == cache_key:
            return deepcopy(self._valid_moves_cache)
        moves = self.get_all_possible_moves()
        validMoves = []
        side_white = self.whiteToMove
        redo_backup = list(self.redoLog)
        for move in moves:
            self.makeMove(move)
            if side_white:
                in_check_after = self.square_under_attack(self.whiteKingLocation[0], self.whiteKingLocation[1], by_color='b')
            else:
                in_check_after = self.square_under_attack(self.blackKingLocation[0], self.blackKingLocation[1], by_color='w')
            if not in_check_after:
                validMoves.append(move)
            self.undoMove()
        self.redoLog = redo_backup
        if not validMoves:
            if self.in_check_for_current_player():
                self.checkmate = True
                self.stalemate = False
            else:
                self.stalemate = True
                self.checkmate = False
        else:
            self.checkmate = False
            self.stalemate = False
        self._valid_moves_cache = deepcopy(validMoves)
        self._valid_moves_cache_key = cache_key
        return deepcopy(validMoves)

    def get_valid_moves(self):
        return self.getValidMoves()

    def in_check_for_current_player(self):
        king = self.whiteKingLocation if self.whiteToMove else self.blackKingLocation
        return self.square_under_attack(king[0], king[1], by_color=('b' if self.whiteToMove else 'w'))

    def square_under_attack(self, r, c, by_color=None):
        attacker = by_color if by_color is not None else ('b' if self.whiteToMove else 'w')
        attacker = attacker.lower()
        if attacker == 'w':
            for dc in (-1, 1):
                rr = r + 1
                cc = c + dc
                if 0 <= rr <= 7 and 0 <= cc <= 7:
                    p = self.board[rr][cc]
                    if p != "--" and p[0].lower() == 'w' and p[1].lower() == 'p':
                        return True
        else:
            for dc in (-1, 1):
                rr = r - 1
                cc = c + dc
                if 0 <= rr <= 7 and 0 <= cc <= 7:
                    p = self.board[rr][cc]
                    if p != "--" and p[0].lower() == 'b' and p[1].lower() == 'p':
                        return True
        knight_offsets = [(-2,-1),(-2,1),(-1,-2),(-1,2),(1,-2),(1,2),(2,-1),(2,1)]
        for dr, dc in knight_offsets:
            rr = r + dr
            cc = c + dc
            if 0 <= rr <= 7 and 0 <= cc <= 7:
                p = self.board[rr][cc]
                if p != "--" and p[0].lower() == attacker and p[1].upper() == 'N':
                    return True
        orth_dirs = [(-1,0),(1,0),(0,-1),(0,1)]
        for dr, dc in orth_dirs:
            for i in range(1,8):
                rr = r + dr*i
                cc = c + dc*i
                if not (0 <= rr <= 7 and 0 <= cc <= 7):
                    break
                p = self.board[rr][cc]
                if p == "--":
                    continue
                if p[0].lower() == attacker:
                    if p[1].upper() in ('R','Q'):
                        return True
                    else:
                        break
                else:
                    break
        diag_dirs = [(-1,-1),(-1,1),(1,-1),(1,1)]
        for dr, dc in diag_dirs:
            for i in range(1,8):
                rr = r + dr*i
                cc = c + dc*i
                if not (0 <= rr <= 7 and 0 <= cc <= 7):
                    break
                p = self.board[rr][cc]
                if p == "--":
                    continue
                if p[0].lower() == attacker:
                    if p[1].upper() in ('B','Q'):
                        return True
                    else:
                        break
                else:
                    break
        for dr in (-1,0,1):
            for dc in (-1,0,1):
                if dr == 0 and dc == 0:
                    continue
                rr = r + dr
                cc = c + dc
                if 0 <= rr <= 7 and 0 <= cc <= 7:
                    p = self.board[rr][cc]
                    if p != "--" and p[0].lower() == attacker and p[1].upper() == 'K':
                        return True
        return False

    def get_all_possible_moves(self):
        moves = []
        for r in range(8):
            for c in range(8):
                piece = self.board[r][c]
                if piece == "--":
                    continue
                color = piece[0].lower()
                if (self.whiteToMove and color != 'w') or (not self.whiteToMove and color != 'b'):
                    continue
                ptype = piece[1].upper()
                if ptype == 'P':
                    self.get_pawn_moves(r, c, moves)
                elif ptype == 'R':
                    self._slide_moves(r, c, [(-1,0),(1,0),(0,-1),(0,1)], moves)
                elif ptype == 'B':
                    self._slide_moves(r, c, [(-1,-1),(-1,1),(1,-1),(1,1)], moves)
                elif ptype == 'Q':
                    self._slide_moves(r, c, [(-1,0),(1,0),(0,-1),(0,1),(-1,-1),(-1,1),(1,-1),(1,1)], moves)
                elif ptype == 'K':
                    self.get_king_moves(r, c, moves)
                elif ptype == 'N':
                    self.get_knight_moves(r, c, moves)
        return moves

    def get_pawn_moves(self, r, c, moves):
        piece = self.board[r][c]
        color = piece[0].lower()
        direction = -1 if color == 'w' else 1
        startRow = 6 if color == 'w' else 1
        if 0 <= r + direction <= 7 and self.board[r + direction][c] == "--":
            moves.append(Move((r, c), (r + direction, c), self.board))
            if r == startRow and self.board[r + 2*direction][c] == "--":
                moves.append(Move((r, c), (r + 2*direction, c), self.board))
        for dc in (-1, 1):
            nc = c + dc
            nr = r + direction
            if 0 <= nc <= 7 and 0 <= nr <= 7:
                target = self.board[nr][nc]
                if target != "--" and target[0].lower() != color:
                    moves.append(Move((r, c), (nr, nc), self.board))
                elif (nr, nc) == self.enPassantPossible:
                    moves.append(Move((r, c), (nr, nc), self.board, isEnPassantMove=True))

    def _slide_moves(self, r, c, directions, moves):
        color = self.board[r][c][0].lower()
        for dr, dc in directions:
            for i in range(1,8):
                nr = r + dr*i
                nc = c + dc*i
                if not (0 <= nr <= 7 and 0 <= nc <= 7):
                    break
                target = self.board[nr][nc]
                if target == "--":
                    moves.append(Move((r,c),(nr,nc),self.board))
                else:
                    if target[0].lower() != color:
                        moves.append(Move((r,c),(nr,nc),self.board))
                    break

    def get_king_moves(self, r, c, moves):
        color = self.board[r][c][0].lower()
        for dr in (-1,0,1):
            for dc in (-1,0,1):
                if dr == 0 and dc == 0:
                    continue
                nr = r + dr
                nc = c + dc
                if 0 <= nr <= 7 and 0 <= nc <= 7:
                    target = self.board[nr][nc]
                    if target == "--" or target[0].lower() != color:
                        moves.append(Move((r,c),(nr,nc),self.board))
        if color == 'w' and self.whiteToMove:
            if self.currentCastlingRights.wks:
                if self.board[7][5] == "--" and self.board[7][6] == "--":
                    if (not self.square_under_attack(7,4,'b') and
                        not self.square_under_attack(7,5,'b') and
                        not self.square_under_attack(7,6,'b')):
                        moves.append(Move((7,4),(7,6),self.board,isCastleMove=True))
            if self.currentCastlingRights.wqs:
                if self.board[7][1] == "--" and self.board[7][2] == "--" and self.board[7][3] == "--":
                    if (not self.square_under_attack(7,4,'b') and
                        not self.square_under_attack(7,3,'b') and
                        not self.square_under_attack(7,2,'b')):
                        moves.append(Move((7,4),(7,2),self.board,isCastleMove=True))
        elif color == 'b' and not self.whiteToMove:
            if self.currentCastlingRights.bks:
                if self.board[0][5] == "--" and self.board[0][6] == "--":
                    if (not self.square_under_attack(0,4,'w') and
                        not self.square_under_attack(0,5,'w') and
                        not self.square_under_attack(0,6,'w')):
                        moves.append(Move((0,4),(0,6),self.board,isCastleMove=True))
            if self.currentCastlingRights.bqs:
                if self.board[0][1] == "--" and self.board[0][2] == "--" and self.board[0][3] == "--":
                    if (not self.square_under_attack(0,4,'w') and
                        not self.square_under_attack(0,3,'w') and
                        not self.square_under_attack(0,2,'w')):
                        moves.append(Move((0,4),(0,2),self.board,isCastleMove=True))

    def get_knight_moves(self, r, c, moves):
        knight_moves = [(-2,-1),(-2,1),(-1,-2),(-1,2),(1,-2),(1,2),(2,-1),(2,1)]
        color = self.board[r][c][0].lower()
        for dr, dc in knight_moves:
            nr = r + dr
            nc = c + dc
            if 0 <= nr <= 7 and 0 <= nc <= 7:
                target = self.board[nr][nc]
                if target == "--" or target[0].lower() != color:
                    moves.append(Move((r,c),(nr,nc),self.board))
