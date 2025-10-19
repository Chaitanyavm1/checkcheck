# Chess Learning Coach - Backend API with Stockfish Integration
# Requirements: pip install flask flask-cors python-chess psycopg2-binary

from flask import Flask, request, jsonify
from flask_cors import CORS
import chess
import chess.engine
import chess.pgn
from datetime import datetime
import psycopg2
from psycopg2.extras import RealDictCursor
import os
import json

app = Flask(__name__)
CORS(app)

# Database Configuration
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'database': os.getenv('DB_NAME', 'chess_coach'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', 'password')
}

# Stockfish Engine Path (adjust based on your system)
STOCKFISH_PATH = os.getenv('STOCKFISH_PATH', r'C:\Users\Chaitanya V M\Desktop\chesscoach\stockfish-windows-x86-64-avx2.exe')

# Initialize Stockfish engine
try:
    engine = chess.engine.SimpleEngine.popen_uci(STOCKFISH_PATH)
except:
    engine = None
    print("Warning: Stockfish engine not found. Analysis features will be limited.")

# Database Helper Functions
def get_db_connection():
    """Create database connection"""
    return psycopg2.connect(**DB_CONFIG, cursor_factory=RealDictCursor)

def init_database():
    """Initialize database tables"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Users table
    cur.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username VARCHAR(50) UNIQUE NOT NULL,
            email VARCHAR(100) UNIQUE NOT NULL,
            rating INTEGER DEFAULT 1200,
            games_played INTEGER DEFAULT 0,
            wins INTEGER DEFAULT 0,
            losses INTEGER DEFAULT 0,
            draws INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Games table
    cur.execute('''
        CREATE TABLE IF NOT EXISTS games (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id),
            opponent_type VARCHAR(20),
            result VARCHAR(20),
            pgn_notation TEXT,
            fen_final VARCHAR(100),
            moves_count INTEGER,
            game_duration INTEGER,
            accuracy_white FLOAT,
            accuracy_black FLOAT,
            brilliant_moves INTEGER DEFAULT 0,
            blunders INTEGER DEFAULT 0,
            mistakes INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Move Analysis table
    cur.execute('''
        CREATE TABLE IF NOT EXISTS move_analysis (
            id SERIAL PRIMARY KEY,
            game_id INTEGER REFERENCES games(id),
            move_number INTEGER,
            move_notation VARCHAR(10),
            player_color VARCHAR(5),
            fen_before VARCHAR(100),
            fen_after VARCHAR(100),
            evaluation_before FLOAT,
            evaluation_after FLOAT,
            best_move VARCHAR(10),
            classification VARCHAR(20),
            centipawn_loss INTEGER,
            tactical_theme VARCHAR(50),
            positional_theme VARCHAR(50)
        )
    ''')
    
    # User Statistics table
    cur.execute('''
        CREATE TABLE IF NOT EXISTS user_statistics (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id) UNIQUE,
            tactical_accuracy FLOAT DEFAULT 0,
            positional_awareness FLOAT DEFAULT 0,
            endgame_skill FLOAT DEFAULT 0,
            opening_knowledge FLOAT DEFAULT 0,
            time_management FLOAT DEFAULT 0,
            avg_centipawn_loss FLOAT DEFAULT 0,
            common_opening VARCHAR(100),
            weakest_phase VARCHAR(20),
            strongest_phase VARCHAR(20),
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Weakness Tracking table
    cur.execute('''
        CREATE TABLE IF NOT EXISTS weaknesses (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id),
            weakness_type VARCHAR(50),
            description TEXT,
            severity VARCHAR(20),
            occurrence_count INTEGER DEFAULT 1,
            last_occurred TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Training Recommendations table
    cur.execute('''
        CREATE TABLE IF NOT EXISTS recommendations (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id),
            recommendation_type VARCHAR(50),
            title VARCHAR(200),
            description TEXT,
            priority VARCHAR(20),
            completed BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    cur.close()
    conn.close()
    print("Database initialized successfully!")

# Chess Analysis Functions
def analyze_position(board, depth=15):
    """Analyze current position using Stockfish"""
    if not engine:
        return {
            'evaluation': 0,
            'best_move': None,
            'mate_in': None
        }
    
    try:
        info = engine.analyse(board, chess.engine.Limit(depth=depth))
        
        score = info['score'].relative
        evaluation = score.score(mate_score=10000) / 100.0 if score.score() else 0
        best_move = info.get('pv', [None])[0]
        mate_in = score.mate() if score.is_mate() else None
        
        return {
            'evaluation': evaluation,
            'best_move': best_move.uci() if best_move else None,
            'mate_in': mate_in
        }
    except Exception as e:
        print(f"Analysis error: {e}")
        return {'evaluation': 0, 'best_move': None, 'mate_in': None}

def classify_move(eval_before, eval_after, is_best_move, player_color):
    """Classify move quality based on evaluation change"""
    # Adjust perspective based on player color
    if player_color == 'black':
        eval_before = -eval_before
        eval_after = -eval_after
    
    centipawn_loss = (eval_before - eval_after) * 100
    
    classification = {
        'type': 'good',
        'symbol': '',
        'centipawn_loss': int(centipawn_loss)
    }
    
    if is_best_move:
        classification['type'] = 'best'
        classification['symbol'] = '!'
    elif centipawn_loss < -50:  # Significant improvement
        classification['type'] = 'brilliant'
        classification['symbol'] = '!!'
    elif centipawn_loss < 50:
        classification['type'] = 'good'
        classification['symbol'] = ''
    elif centipawn_loss < 100:
        classification['type'] = 'inaccuracy'
        classification['symbol'] = '?'
    elif centipawn_loss < 300:
        classification['type'] = 'mistake'
        classification['symbol'] = '??'
    else:
        classification['type'] = 'blunder'
        classification['symbol'] = '???'
    
    return classification

def detect_tactical_theme(board, move):
    """Detect tactical themes in a move"""
    themes = []
    
    # Check for captures
    if board.is_capture(move):
        themes.append('capture')
        
        # Check for exchange
        from_piece = board.piece_at(move.from_square)
        to_piece = board.piece_at(move.to_square)
        if to_piece:
            if from_piece.piece_type == to_piece.piece_type:
                themes.append('exchange')
    
    # Check for checks
    board.push(move)
    if board.is_check():
        themes.append('check')
        if board.is_checkmate():
            themes.append('checkmate')
    board.pop()
    
    # Check for pins, forks, skewers (simplified detection)
    if board.piece_at(move.from_square).piece_type == chess.KNIGHT:
        # Check if knight can attack multiple pieces
        board.push(move)
        attacks = list(board.attacks(move.to_square))
        valuable_attacks = [sq for sq in attacks if board.piece_at(sq) and 
                          board.piece_at(sq).piece_type in [chess.QUEEN, chess.ROOK]]
        if len(valuable_attacks) >= 2:
            themes.append('fork')
        board.pop()
    
    return themes

def analyze_game_complete(pgn_string):
    """Complete game analysis with Stockfish"""
    game = chess.pgn.read_game(chess.pgn.StringIO(pgn_string))
    if not game:
        return None
    
    board = game.board()
    analysis_results = []
    move_number = 1
    
    for move in game.mainline_moves():
        # Analyze position before move
        eval_before = analyze_position(board)
        
        # Get best move
        best_move = eval_before['best_move']
        is_best = (move.uci() == best_move) if best_move else False
        
        # Detect tactical themes
        themes = detect_tactical_theme(board, move)
        
        # Make move
        fen_before = board.fen()
        player_color = 'white' if board.turn else 'black'
        board.push(move)
        fen_after = board.fen()
        
        # Analyze position after move
        eval_after = analyze_position(board)
        
        # Classify move
        classification = classify_move(
            eval_before['evaluation'],
            eval_after['evaluation'],
            is_best,
            player_color
        )
        
        analysis_results.append({
            'move_number': move_number,
            'move': move.uci(),
            'san': board.san(move) if not board.is_game_over() else move.uci(),
            'player_color': player_color,
            'fen_before': fen_before,
            'fen_after': fen_after,
            'eval_before': eval_before['evaluation'],
            'eval_after': eval_after['evaluation'],
            'best_move': best_move,
            'classification': classification,
            'themes': themes,
            'mate_threat': eval_after['mate_in']
        })
        
        move_number += 1
    
    return analysis_results

def generate_weaknesses_report(user_id):
    """Generate personalized weakness report for user"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Get recent game analysis
    cur.execute('''
        SELECT ma.*, g.created_at 
        FROM move_analysis ma
        JOIN games g ON ma.game_id = g.id
        WHERE g.user_id = %s
        ORDER BY g.created_at DESC
        LIMIT 200
    ''', (user_id,))
    
    moves = cur.fetchall()
    
    weaknesses = []
    
    # Analyze blunder patterns
    blunders = [m for m in moves if m['classification'] == 'blunder']
    if len(blunders) > 5:
        weaknesses.append({
            'type': 'tactical_awareness',
            'severity': 'high',
            'description': f'{len(blunders)} blunders in recent games. Focus on calculating forcing moves.',
            'recommendation': 'Practice tactical puzzles daily (20-30 min)'
        })
    
    # Analyze opening phase
    opening_moves = [m for m in moves if m['move_number'] <= 10]
    opening_mistakes = [m for m in opening_moves if m['classification'] in ['mistake', 'blunder']]
    if len(opening_mistakes) / max(len(opening_moves), 1) > 0.3:
        weaknesses.append({
            'type': 'opening_knowledge',
            'severity': 'medium',
            'description': 'Frequent mistakes in opening phase',
            'recommendation': 'Study opening principles and 2-3 specific openings'
        })
    
    # Analyze endgame
    endgame_moves = [m for m in moves if m['move_number'] > 30]
    if endgame_moves:
        endgame_accuracy = 1 - (len([m for m in endgame_moves if m['classification'] in ['mistake', 'blunder']]) / len(endgame_moves))
        if endgame_accuracy < 0.7:
            weaknesses.append({
                'type': 'endgame_technique',
                'severity': 'medium',
                'description': 'Struggling to convert winning endgames',
                'recommendation': 'Practice basic endgames: King+Pawn, Rook endgames'
            })
    
    # Check for positional understanding
    avg_centipawn_loss = sum([abs(m.get('centipawn_loss', 0)) for m in moves]) / max(len(moves), 1)
    if avg_centipawn_loss > 100:
        weaknesses.append({
            'type': 'positional_play',
            'severity': 'medium',
            'description': 'High average centipawn loss indicates positional weaknesses',
            'recommendation': 'Study pawn structures and piece placement principles'
        })
    
    cur.close()
    conn.close()
    
    return weaknesses

# API Endpoints

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'engine_available': engine is not None
    })

@app.route('/api/users/register', methods=['POST'])
def register_user():
    """Register new user"""
    data = request.json
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        cur.execute('''
            INSERT INTO users (username, email)
            VALUES (%s, %s)
            RETURNING id, username, rating
        ''', (data['username'], data['email']))
        
        user = cur.fetchone()
        
        # Initialize user statistics
        cur.execute('''
            INSERT INTO user_statistics (user_id)
            VALUES (%s)
        ''', (user['id'],))
        
        conn.commit()
        
        return jsonify({
            'success': True,
            'user': dict(user)
        })
    except psycopg2.IntegrityError:
        conn.rollback()
        return jsonify({
            'success': False,
            'error': 'Username or email already exists'
        }), 400
    finally:
        cur.close()
        conn.close()

@app.route('/api/users/<int:user_id>', methods=['GET'])
def get_user_profile(user_id):
    """Get user profile and statistics"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute('SELECT * FROM users WHERE id = %s', (user_id,))
    user = cur.fetchone()
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    cur.execute('SELECT * FROM user_statistics WHERE user_id = %s', (user_id,))
    stats = cur.fetchone()
    
    cur.close()
    conn.close()
    
    return jsonify({
        'user': dict(user),
        'statistics': dict(stats) if stats else None
    })

@app.route('/api/analyze/position', methods=['POST'])
def analyze_position_endpoint():
    """Analyze a single position"""
    data = request.json
    fen = data.get('fen')
    depth = data.get('depth', 15)
    
    if not fen:
        return jsonify({'error': 'FEN required'}), 400
    
    try:
        board = chess.Board(fen)
        analysis = analyze_position(board, depth)
        
        return jsonify({
            'success': True,
            'analysis': analysis,
            'legal_moves': [move.uci() for move in board.legal_moves]
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/analyze/game', methods=['POST'])
def analyze_game_endpoint():
    """Analyze complete game"""
    data = request.json
    pgn = data.get('pgn')
    user_id = data.get('user_id')
    
    if not pgn:
        return jsonify({'error': 'PGN required'}), 400
    
    try:
        # Analyze game
        analysis = analyze_game_complete(pgn)
        
        if not analysis:
            return jsonify({'error': 'Invalid PGN'}), 400
        
        # Calculate statistics
        total_moves = len(analysis)
        brilliant_moves = len([m for m in analysis if m['classification']['type'] == 'brilliant'])
        blunders = len([m for m in analysis if m['classification']['type'] == 'blunder'])
        mistakes = len([m for m in analysis if m['classification']['type'] == 'mistake'])
        
        accuracy = ((total_moves - blunders - mistakes) / total_moves * 100) if total_moves > 0 else 0
        
        # Save to database if user_id provided
        if user_id:
            conn = get_db_connection()
            cur = conn.cursor()
            
            cur.execute('''
                INSERT INTO games (user_id, pgn_notation, moves_count, 
                                 brilliant_moves, blunders, mistakes, accuracy_white)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            ''', (user_id, pgn, total_moves, brilliant_moves, blunders, mistakes, accuracy))
            
            game_id = cur.fetchone()['id']
            
            # Save move analysis
            for move_data in analysis:
                cur.execute('''
                    INSERT INTO move_analysis (game_id, move_number, move_notation, 
                                             player_color, fen_before, fen_after,
                                             evaluation_before, evaluation_after, 
                                             best_move, classification, centipawn_loss)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ''', (game_id, move_data['move_number'], move_data['move'],
                     move_data['player_color'], move_data['fen_before'], 
                     move_data['fen_after'], move_data['eval_before'],
                     move_data['eval_after'], move_data['best_move'],
                     move_data['classification']['type'],
                     move_data['classification']['centipawn_loss']))
            
            conn.commit()
            cur.close()
            conn.close()
        
        return jsonify({
            'success': True,
            'analysis': analysis,
            'summary': {
                'total_moves': total_moves,
                'brilliant_moves': brilliant_moves,
                'blunders': blunders,
                'mistakes': mistakes,
                'accuracy': round(accuracy, 1)
            }
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/users/<int:user_id>/weaknesses', methods=['GET'])
def get_user_weaknesses(user_id):
    """Get personalized weakness analysis"""
    weaknesses = generate_weaknesses_report(user_id)
    
    return jsonify({
        'success': True,
        'weaknesses': weaknesses
    })

@app.route('/api/users/<int:user_id>/recommendations', methods=['GET'])
def get_recommendations(user_id):
    """Get personalized training recommendations"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute('''
        SELECT * FROM recommendations
        WHERE user_id = %s AND completed = FALSE
        ORDER BY priority DESC, created_at DESC
    ''', (user_id,))
    
    recommendations = cur.fetchall()
    
    cur.close()
    conn.close()
    
    return jsonify({
        'success': True,
        'recommendations': [dict(r) for r in recommendations]
    })

@app.route('/api/games/<int:game_id>', methods=['GET'])
def get_game_details(game_id):
    """Get detailed game analysis"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute('SELECT * FROM games WHERE id = %s', (game_id,))
    game = cur.fetchone()
    
    if not game:
        return jsonify({'error': 'Game not found'}), 404
    
    cur.execute('''
        SELECT * FROM move_analysis
        WHERE game_id = %s
        ORDER BY move_number
    ''', (game_id,))
    
    moves = cur.fetchall()
    
    cur.close()
    conn.close()
    
    return jsonify({
        'success': True,
        'game': dict(game),
        'moves': [dict(m) for m in moves]
    })

@app.route('/api/users/<int:user_id>/games', methods=['GET'])
def get_user_games(user_id):
    """Get user's game history"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute('''
        SELECT * FROM games
        WHERE user_id = %s
        ORDER BY created_at DESC
        LIMIT 50
    ''', (user_id,))
    
    games = cur.fetchall()
    
    cur.close()
    conn.close()
    
    return jsonify({
        'success': True,
        'games': [dict(g) for g in games]
    })

if __name__ == '__main__':
    # Initialize database on startup
    try:
        init_database()
    except Exception as e:
        print(f"Database initialization error: {e}")
    
    # Run Flask app
    app.run(debug=True, host='0.0.0.0', port=5000)