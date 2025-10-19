# services/chess_engine.py
# Advanced Chess Engine Service with Stockfish Integration

import chess
import chess.engine
import chess.pgn
from typing import Dict, List, Optional, Tuple
import logging
from datetime import datetime
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ChessEngineService:
    """Service for chess position analysis using Stockfish"""
    
    def __init__(self, stockfish_path: str, threads: int = 4, hash_size: int = 128):
        """
        Initialize chess engine service
        
        Args:
            stockfish_path: Path to Stockfish executable
            threads: Number of CPU threads to use
            hash_size: Hash table size in MB
        """
        self.stockfish_path = stockfish_path
        self.engine = None
        self.threads = threads
        self.hash_size = hash_size
        self._initialize_engine()
    
    def _initialize_engine(self):
        """Initialize Stockfish engine with configuration"""
        try:
            self.engine = chess.engine.SimpleEngine.popen_uci(self.stockfish_path)
            self.engine.configure({
                "Threads": self.threads,
                "Hash": self.hash_size
            })
            logger.info(f"Stockfish engine initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Stockfish: {e}")
            self.engine = None
    
    def analyze_position(
        self, 
        board: chess.Board, 
        depth: int = 20,
        time_limit: float = 2.0,
        multi_pv: int = 1
    ) -> Dict:
        """
        Analyze a chess position
        
        Args:
            board: Chess board position
            depth: Search depth (moves ahead)
            time_limit: Maximum analysis time in seconds
            multi_pv: Number of best lines to return
            
        Returns:
            Dictionary with analysis results
        """
        if not self.engine:
            return self._fallback_analysis(board)
        
        try:
            # Analyze position
            info = self.engine.analyse(
                board,
                chess.engine.Limit(depth=depth, time=time_limit),
                multipv=multi_pv
            )
            
            # Extract evaluation
            score = info[0]['score'].relative
            evaluation = self._score_to_pawns(score)
            
            # Get best moves
            best_moves = []
            for i in range(min(multi_pv, len(info))):
                pv = info[i].get('pv', [])
                if pv:
                    best_moves.append({
                        'move': pv[0].uci(),
                        'san': board.san(pv[0]),
                        'evaluation': self._score_to_pawns(info[i]['score'].relative),
                        'depth': info[i].get('depth', depth),
                        'pv': [m.uci() for m in pv[:5]]  # First 5 moves of principal variation
                    })
            
            # Detect threats and tactics
            threats = self._detect_threats(board)
            tactical_motifs = self._detect_tactical_motifs(board, best_moves[0] if best_moves else None)
            
            return {
                'evaluation': evaluation,
                'mate_in': score.mate() if score.is_mate() else None,
                'best_moves': best_moves,
                'threats': threats,
                'tactical_motifs': tactical_motifs,
                'position_type': self._classify_position(board, evaluation)
            }
            
        except Exception as e:
            logger.error(f"Analysis error: {e}")
            return self._fallback_analysis(board)
    
    def analyze_move(
        self, 
        board: chess.Board, 
        move: chess.Move,
        depth: int = 18
    ) -> Dict:
        """
        Analyze a specific move
        
        Args:
            board: Board position before the move
            move: The move to analyze
            depth: Analysis depth
            
        Returns:
            Dictionary with move analysis
        """
        # Get evaluation before move
        eval_before_analysis = self.analyze_position(board, depth=depth)
        eval_before = eval_before_analysis['evaluation']
        best_move_before = eval_before_analysis['best_moves'][0] if eval_before_analysis['best_moves'] else None
        
        # Make the move
        board_copy = board.copy()
        board_copy.push(move)
        
        # Get evaluation after move
        eval_after_analysis = self.analyze_position(board_copy, depth=depth)
        eval_after = -eval_after_analysis['evaluation']  # Flip perspective
        
        # Calculate centipawn loss
        centipawn_loss = int((eval_before - eval_after) * 100)
        
        # Classify move quality
        classification = self._classify_move_quality(
            centipawn_loss,
            move.uci() == (best_move_before['move'] if best_move_before else None)
        )
        
        # Detect move themes
        themes = self._detect_move_themes(board, move)
        
        return {
            'move': move.uci(),
            'san': board.san(move),
            'eval_before': eval_before,
            'eval_after': eval_after,
            'centipawn_loss': centipawn_loss,
            'classification': classification,
            'best_move': best_move_before['move'] if best_move_before else None,
            'themes': themes,
            'is_forcing': self._is_forcing_move(board, move),
            'positional_impact': self._evaluate_positional_impact(board, move)
        }
    
    def analyze_complete_game(
        self, 
        pgn_string: str,
        user_color: str = 'white',
        depth: int = 18
    ) -> Dict:
        """
        Analyze a complete game with detailed move-by-move breakdown
        
        Args:
            pgn_string: PGN notation of the game
            user_color: Color played by user ('white' or 'black')
            depth: Analysis depth per position
            
        Returns:
            Complete game analysis with statistics
        """
        try:
            game = chess.pgn.read_game(chess.pgn.StringIO(pgn_string))
            if not game:
                return {'error': 'Invalid PGN'}
            
            board = game.board()
            move_analysis = []
            move_number = 1
            
            # Statistics tracking
            stats = {
                'brilliant': 0,
                'best': 0,
                'good': 0,
                'inaccuracy': 0,
                'mistake': 0,
                'blunder': 0,
                'avg_centipawn_loss': 0,
                'accuracy': 0,
                'opening_accuracy': 0,
                'middlegame_accuracy': 0,
                'endgame_accuracy': 0
            }
            
            opening_moves = []
            middlegame_moves = []
            endgame_moves = []
            
            for move in game.mainline_moves():
                # Analyze this move
                analysis = self.analyze_move(board, move, depth=depth)
                
                # Track player moves only
                current_color = 'white' if board.turn == chess.WHITE else 'black'
                
                analysis['move_number'] = move_number
                analysis['player'] = current_color
                move_analysis.append(analysis)
                
                # Update statistics for user's moves
                if current_color == user_color:
                    classification = analysis['classification']['type']
                    stats[classification] = stats.get(classification, 0) + 1
                    
                    # Categorize by game phase
                    if move_number <= 15:
                        opening_moves.append(analysis)
                    elif move_number <= 40:
                        middlegame_moves.append(analysis)
                    else:
                        endgame_moves.append(analysis)
                
                board.push(move)
                if board.turn == chess.WHITE:
                    move_number += 1
            
            # Calculate accuracy metrics
            total_user_moves = len([m for m in move_analysis if m['player'] == user_color])
            if total_user_moves > 0:
                good_moves = stats['brilliant'] + stats['best'] + stats['good']
                stats['accuracy'] = round((good_moves / total_user_moves) * 100, 1)
                
                # Phase-specific accuracy
                stats['opening_accuracy'] = self._calculate_phase_accuracy(opening_moves)
                stats['middlegame_accuracy'] = self._calculate_phase_accuracy(middlegame_moves)
                stats['endgame_accuracy'] = self._calculate_phase_accuracy(endgame_moves)
                
                # Average centipawn loss
                user_moves = [m for m in move_analysis if m['player'] == user_color]
                if user_moves:
                    stats['avg_centipawn_loss'] = round(
                        sum(abs(m['centipawn_loss']) for m in user_moves) / len(user_moves), 1
                    )
            
            # Identify critical moments
            critical_moments = self._identify_critical_moments(move_analysis, user_color)
            
            # Generate insights
            insights = self._generate_game_insights(
                move_analysis, 
                stats, 
                user_color,
                opening_moves,
                middlegame_moves,
                endgame_moves
            )
            
            return {
                'success': True,
                'move_analysis': move_analysis,
                'statistics': stats,
                'critical_moments': critical_moments,
                'insights': insights,
                'opening_name': game.headers.get('Opening', 'Unknown'),
                'result': game.headers.get('Result', '*')
            }
            
        except Exception as e:
            logger.error(f"Game analysis error: {e}")
            return {'error': str(e)}
    
    def _score_to_pawns(self, score: chess.engine.Score) -> float:
        """Convert engine score to pawn units"""
        if score.is_mate():
            mate_in = score.mate()
            return 100.0 if mate_in > 0 else -100.0
        else:
            return round(score.score() / 100.0, 2)
    
    def _classify_move_quality(self, centipawn_loss: int, is_best_move: bool) -> Dict:
        """Classify move quality based on centipawn loss"""
        if is_best_move or centipawn_loss <= 10:
            return {
                'type': 'best',
                'symbol': '!',
                'description': 'Best move or near-perfect',
                'color': 'green'
            }
        elif centipawn_loss < -50:
            return {
                'type': 'brilliant',
                'symbol': '!!',
                'description': 'Brilliant move!',
                'color': 'purple'
            }
        elif centipawn_loss <= 50:
            return {
                'type': 'good',
                'symbol': '',
                'description': 'Good move',
                'color': 'blue'
            }
        elif centipawn_loss <= 100:
            return {
                'type': 'inaccuracy',
                'symbol': '?',
                'description': 'Inaccuracy',
                'color': 'yellow'
            }
        elif centipawn_loss <= 300:
            return {
                'type': 'mistake',
                'symbol': '??',
                'description': 'Mistake',
                'color': 'orange'
            }
        else:
            return {
                'type': 'blunder',
                'symbol': '???',
                'description': 'Blunder!',
                'color': 'red'
            }
    
    def _detect_threats(self, board: chess.Board) -> List[Dict]:
        """Detect immediate threats in position"""
        threats = []
        
        # Check for checks
        if board.is_check():
            threats.append({
                'type': 'check',
                'severity': 'high',
                'description': 'King is in check'
            })
        
        # Check for hanging pieces
        for square in chess.SQUARES:
            piece = board.piece_at(square)
            if piece and piece.color == board.turn:
                # Check if piece is attacked and not defended
                attackers = board.attackers(not board.turn, square)
                defenders = board.attackers(board.turn, square)
                
                if len(attackers) > len(defenders):
                    threats.append({
                        'type': 'hanging_piece',
                        'severity': 'high',
                        'piece': piece.symbol(),
                        'square': chess.square_name(square),
                        'description': f'{piece.symbol()} on {chess.square_name(square)} is hanging'
                    })
        
        return threats
    
    def _detect_tactical_motifs(self, board: chess.Board, best_move: Optional[Dict]) -> List[str]:
        """Detect tactical patterns in position"""
        motifs = []
        
        if not best_move:
            return motifs
        
        try:
            move = chess.Move.from_uci(best_move['move'])
            
            # Check for forks
            board_copy = board.copy()
            board_copy.push(move)
            piece = board_copy.piece_at(move.to_square)
            
            if piece:
                attacks = list(board_copy.attacks(move.to_square))
                valuable_attacks = [
                    sq for sq in attacks 
                    if board_copy.piece_at(sq) and 
                    board_copy.piece_at(sq).piece_type in [chess.QUEEN, chess.ROOK, chess.BISHOP, chess.KNIGHT]
                ]
                
                if len(valuable_attacks) >= 2:
                    motifs.append('fork')
                
                # Check for discovered attacks
                if piece.piece_type in [chess.BISHOP, chess.ROOK, chess.QUEEN]:
                    motifs.append('potential_discovery')
            
            # Check for pins
            if board.is_pinned(board.turn, move.from_square):
                motifs.append('pin_break')
            
            # Check for skewers
            if piece and piece.piece_type in [chess.BISHOP, chess.ROOK, chess.QUEEN]:
                motifs.append('potential_skewer')
            
        except:
            pass
        
        return motifs
    
    def _detect_move_themes(self, board: chess.Board, move: chess.Move) -> List[str]:
        """Detect themes in a specific move"""
        themes = []
        
        # Capture
        if board.is_capture(move):
            themes.append('capture')
            
            # En passant
            if board.is_en_passant(move):
                themes.append('en_passant')
        
        # Castling
        if board.is_castling(move):
            themes.append('castling')
            if move.to_square > move.from_square:
                themes.append('kingside_castle')
            else:
                themes.append('queenside_castle')
        
        # Check/Checkmate
        board_copy = board.copy()
        board_copy.push(move)
        
        if board_copy.is_checkmate():
            themes.append('checkmate')
        elif board_copy.is_check():
            themes.append('check')
        
        # Pawn promotion
        piece = board.piece_at(move.from_square)
        if piece and piece.piece_type == chess.PAWN:
            if move.promotion:
                themes.append('promotion')
            
            # Pawn structure changes
            if abs(chess.square_file(move.to_square) - chess.square_file(move.from_square)) > 0:
                themes.append('pawn_break')
        
        # Development
        if piece and piece.piece_type in [chess.KNIGHT, chess.BISHOP]:
            from_rank = chess.square_rank(move.from_square)
            back_rank = 0 if piece.color == chess.BLACK else 7
            if from_rank == back_rank:
                themes.append('development')
        
        # Center control
        center_squares = [chess.E4, chess.D4, chess.E5, chess.D5]
        if move.to_square in center_squares:
            themes.append('center_control')
        
        return themes
    
    def _is_forcing_move(self, board: chess.Board, move: chess.Move) -> bool:
        """Check if move is forcing (check, capture, or threat)"""
        board_copy = board.copy()
        board_copy.push(move)
        
        return (
            board_copy.is_check() or
            board.is_capture(move) or
            len(self._detect_threats(board_copy)) > 0
        )
    
    def _evaluate_positional_impact(self, board: chess.Board, move: chess.Move) -> Dict:
        """Evaluate positional aspects of a move"""
        impact = {
            'center_control': 0,
            'king_safety': 0,
            'piece_activity': 0,
            'pawn_structure': 0
        }
        
        # Center control
        center_squares = [chess.E4, chess.D4, chess.E5, chess.D5]
        if move.to_square in center_squares:
            impact['center_control'] = 1
        
        # King safety
        piece = board.piece_at(move.from_square)
        if piece:
            if piece.piece_type == chess.KING:
                # Moving king can affect safety
                impact['king_safety'] = -0.5 if not board.is_castling(move) else 1.0
            elif board.is_castling(move):
                impact['king_safety'] = 1.0
        
        # Piece activity (simplified)
        board_copy = board.copy()
        board_copy.push(move)
        mobility_after = len(list(board_copy.legal_moves))
        impact['piece_activity'] = min(1.0, mobility_after / 30.0)
        
        return impact
    
    def _classify_position(self, board: chess.Board, evaluation: float) -> str:
        """Classify position type"""
        piece_count = len(board.piece_map())
        
        if piece_count <= 10:
            return 'endgame'
        elif piece_count <= 20:
            return 'middlegame'
        else:
            return 'opening'
    
    def _calculate_phase_accuracy(self, moves: List[Dict]) -> float:
        """Calculate accuracy for a specific game phase"""
        if not moves:
            return 0.0
        
        good_moves = len([
            m for m in moves 
            if m['classification']['type'] in ['brilliant', 'best', 'good']
        ])
        
        return round((good_moves / len(moves)) * 100, 1)
    
    def _identify_critical_moments(self, moves: List[Dict], user_color: str) -> List[Dict]:
        """Identify critical moments in the game"""
        critical = []
        
        for i, move in enumerate(moves):
            if move['player'] != user_color:
                continue
            
            # Large evaluation swings
            if abs(move['centipawn_loss']) > 200:
                critical.append({
                    'move_number': move['move_number'],
                    'move': move['san'],
                    'type': 'blunder' if move['centipawn_loss'] > 0 else 'brilliant',
                    'eval_change': move['centipawn_loss'],
                    'description': f"Critical {'blunder' if move['centipawn_loss'] > 0 else 'tactical blow'}",
                    'best_move': move['best_move']
                })
            
            # Missed wins
            if i > 0 and move['eval_before'] > 300 and move['centipawn_loss'] > 100:
                critical.append({
                    'move_number': move['move_number'],
                    'move': move['san'],
                    'type': 'missed_win',
                    'description': 'Missed winning continuation',
                    'best_move': move['best_move']
                })
        
        return critical[:5]  # Return top 5 most critical moments
    
    def _generate_game_insights(
        self, 
        moves: List[Dict], 
        stats: Dict,
        user_color: str,
        opening_moves: List[Dict],
        middlegame_moves: List[Dict],
        endgame_moves: List[Dict]
    ) -> Dict:
        """Generate personalized insights from game analysis"""
        insights = {
            'strengths': [],
            'weaknesses': [],
            'recommendations': []
        }
        
        # Analyze opening phase
        if opening_moves:
            opening_blunders = len([m for m in opening_moves if m['classification']['type'] == 'blunder'])
            if opening_blunders > 1:
                insights['weaknesses'].append({
                    'area': 'Opening Preparation',
                    'severity': 'high',
                    'description': f'{opening_blunders} significant errors in opening phase'
                })
                insights['recommendations'].append({
                    'title': 'Study Opening Principles',
                    'priority': 'high',
                    'description': 'Focus on the first 10-15 moves. Learn key opening ideas for your repertoire.'
                })
            elif stats['opening_accuracy'] > 85:
                insights['strengths'].append({
                    'area': 'Opening Knowledge',
                    'description': 'Strong opening preparation and understanding'
                })
        
        # Analyze tactical play
        if stats['blunder'] > 2:
            insights['weaknesses'].append({
                'area': 'Tactical Awareness',
                'severity': 'high',
                'description': f'{stats["blunder"]} tactical oversights'
            })
            insights['recommendations'].append({
                'title': 'Daily Tactical Training',
                'priority': 'urgent',
                'description': 'Solve 15-20 tactical puzzles daily focusing on basic patterns'
            })
        
        # Analyze endgame
        if endgame_moves and stats['endgame_accuracy'] < 70:
            insights['weaknesses'].append({
                'area': 'Endgame Technique',
                'severity': 'medium',
                'description': 'Difficulty in endgame positions'
            })
            insights['recommendations'].append({
                'title': 'Endgame Fundamentals',
                'priority': 'medium',
                'description': 'Practice basic endgames: K+P vs K, Rook endgames, Opposition'
            })
        
        # Overall accuracy assessment
        if stats['accuracy'] > 90:
            insights['strengths'].append({
                'area': 'Overall Accuracy',
                'description': 'Excellent move accuracy throughout the game'
            })
        
        # Time management (if available)
        forcing_moves = [m for m in moves if m.get('is_forcing')]
        if len(forcing_moves) > len(moves) * 0.3:
            insights['strengths'].append({
                'area': 'Aggressive Play',
                'description': 'Good at creating threats and forcing opponent responses'
            })
        
        return insights
    
    def _fallback_analysis(self, board: chess.Board) -> Dict:
        """Fallback analysis when engine is unavailable"""
        return {
            'evaluation': 0.0,
            'mate_in': None,
            'best_moves': [],
            'threats': [],
            'tactical_motifs': [],
            'position_type': self._classify_position(board, 0.0),
            'note': 'Limited analysis - Stockfish engine unavailable'
        }
    
    def close(self):
        """Close the engine"""
        if self.engine:
            self.engine.quit()
            logger.info("Stockfish engine closed")


# Example usage and testing
if __name__ == "__main__":
    # Initialize service
    service = ChessEngineService("/usr/games/stockfish")
    
    # Test position analysis
    board = chess.Board()
    board.push_san("e4")
    board.push_san("e5")
    
    result = service.analyze_position(board, depth=15)
    print("Position Analysis:")
    print(json.dumps(result, indent=2))
    
    # Test game analysis
    sample_pgn = """
    [Event "Test Game"]
    [White "Player"]
    [Black "Opponent"]
    
    1. e4 e5 2. Nf3 Nc6 3. Bb5 a6 4. Ba4 Nf6 5. O-O Be7
    """
    
    game_result = service.analyze_complete_game(sample_pgn, user_color='white', depth=15)
    print("\nGame Analysis:")
    print(json.dumps(game_result, indent=2))
    
    # Close engine
    service.close()