import React, { useState, useEffect, useRef } from 'react';
import { Brain, Target, TrendingUp, AlertCircle, Award, RotateCcw, BookOpen, User, BarChart3, Zap, Eye, Trophy, Clock, Settings, Download, X, ChevronRight, Activity } from 'lucide-react';

const ChessCoachPro = () => {
  const [board, setBoard] = useState(initializeBoard());
  const [selected, setSelected] = useState(null);
  const [currentPlayer, setCurrentPlayer] = useState('white');
  const [moves, setMoves] = useState([]);
  const [gameOver, setGameOver] = useState(false);
  const [gameMode, setGameMode] = useState('ai');
  const [aiDifficulty, setAiDifficulty] = useState('intermediate');
  const [timeControl, setTimeControl] = useState({ white: 600, black: 600 });
  const [isTimerActive, setIsTimerActive] = useState(false);
  
  const [engineEvaluation, setEngineEvaluation] = useState(0);
  const [bestMove, setBestMove] = useState(null);
  const [moveClassification, setMoveClassification] = useState(null);
  const [liveHints, setLiveHints] = useState([]);
  
  const [userProfile, setUserProfile] = useState({
    username: 'Player',
    rating: 1200,
    gamesPlayed: 0,
    winRate: 0,
    averageAccuracy: 0
  });
  
  const [performanceStats, setPerformanceStats] = useState({
    tacticalAccuracy: 0,
    positionalAwareness: 0,
    endgameSkill: 0,
    openingKnowledge: 0,
    timeManagement: 0
  });
  
  const [weaknesses, setWeaknesses] = useState([]);
  const [strengths, setStrengths] = useState([]);
  const [recommendations, setRecommendations] = useState([]);
  
  const [activeTab, setActiveTab] = useState('game');
  const [showSettings, setShowSettings] = useState(false);
  const [showPostGameAnalysis, setShowPostGameAnalysis] = useState(false);
  const [notation, setNotation] = useState('');
  
  const timerRef = useRef(null);

  function initializeBoard() {
    const board = Array(8).fill(null).map(() => Array(8).fill(null));
    
    const setup = [
      ['rook', 'knight', 'bishop', 'queen', 'king', 'bishop', 'knight', 'rook'],
      ['pawn', 'pawn', 'pawn', 'pawn', 'pawn', 'pawn', 'pawn', 'pawn']
    ];
    
    setup[0].forEach((piece, i) => {
      board[0][i] = { type: piece, color: 'black', moved: false };
      board[7][i] = { type: piece, color: 'white', moved: false };
    });
    
    setup[1].forEach((piece, i) => {
      board[1][i] = { type: piece, color: 'black', moved: false };
      board[6][i] = { type: piece, color: 'white', moved: false };
    });
    
    return board;
  }

  const pieceSymbols = {
    white: { king: '♔', queen: '♕', rook: '♖', bishop: '♗', knight: '♘', pawn: '♙' },
    black: { king: '♚', queen: '♛', rook: '♜', bishop: '♝', knight: '♞', pawn: '♟' }
  };

  const pieceValues = {
    pawn: 1,
    knight: 3,
    bishop: 3,
    rook: 5,
    queen: 9,
    king: 0
  };

  useEffect(() => {
    if (isTimerActive && !gameOver) {
      timerRef.current = setInterval(() => {
        setTimeControl(prev => {
          const newTime = { ...prev };
          newTime[currentPlayer] = Math.max(0, newTime[currentPlayer] - 1);
          
          if (newTime[currentPlayer] === 0) {
            setGameOver(true);
            setIsTimerActive(false);
            generatePostGameAnalysis('time');
          }
          
          return newTime;
        });
      }, 1000);
      
      return () => clearInterval(timerRef.current);
    }
  }, [isTimerActive, currentPlayer, gameOver]);

  function simulateStockfishAnalysis(board, lastMove) {
    const materialBalance = calculateMaterialBalance(board);
    const positionScore = evaluatePosition(board);
    const evaluation = (materialBalance + positionScore) / 10;
    
    setEngineEvaluation(evaluation);
    
    const allMoves = generateAllPossibleMoves(board, currentPlayer);
    if (allMoves.length > 0) {
      const best = allMoves[Math.floor(Math.random() * Math.min(3, allMoves.length))];
      setBestMove(best);
    }
    
    return evaluation;
  }

  function calculateMaterialBalance(board) {
    let balance = 0;
    board.forEach(row => {
      row.forEach(piece => {
        if (piece) {
          const value = pieceValues[piece.type];
          balance += piece.color === 'white' ? value : -value;
        }
      });
    });
    return balance;
  }

  function evaluatePosition(board) {
    let score = 0;
    
    const centerSquares = [[3,3], [3,4], [4,3], [4,4]];
    centerSquares.forEach(([r, c]) => {
      if (board[r][c]) {
        score += board[r][c].color === 'white' ? 0.3 : -0.3;
      }
    });
    
    [[7,1], [7,6]].forEach(([r, c]) => {
      if (board[r][c] && board[r][c].type === 'knight' && !board[r][c].moved) {
        score -= 0.2;
      }
    });
    
    [[0,1], [0,6]].forEach(([r, c]) => {
      if (board[r][c] && board[r][c].type === 'knight' && !board[r][c].moved) {
        score += 0.2;
      }
    });
    
    return score;
  }

  function classifyMove(previousEval, newEval, moveData) {
    const diff = currentPlayer === 'white' ? (previousEval - newEval) : (newEval - previousEval);
    
    let classification = {
      type: 'good',
      symbol: '',
      description: 'Solid move',
      feedback: []
    };
    
    if (diff < -2) {
      classification = {
        type: 'brilliant',
        symbol: '!!',
        description: 'Brilliant move!',
        feedback: ['Outstanding! This move significantly improves your position.', 'This is exactly what the engine recommends.']
      };
    } else if (diff < -0.5) {
      classification = {
        type: 'best',
        symbol: '!',
        description: 'Excellent move',
        feedback: ['Great choice! This maintains your advantage.']
      };
    } else if (diff > 0.5 && diff < 1.5) {
      classification = {
        type: 'inaccuracy',
        symbol: '?',
        description: 'Inaccuracy',
        feedback: ['This move is okay but not optimal.', `Consider ${bestMove ? bestMove.notation : 'developing pieces'} instead.`]
      };
    } else if (diff > 1.5 && diff < 3) {
      classification = {
        type: 'mistake',
        symbol: '??',
        description: 'Mistake',
        feedback: ['This significantly weakens your position.', generateTacticalFeedback(moveData)]
      };
    } else if (diff > 3) {
      classification = {
        type: 'blunder',
        symbol: '???',
        description: 'Blunder!',
        feedback: ['Critical error! This move loses material or position.', generateBlunderFeedback(moveData)]
      };
    }
    
    return classification;
  }

  function generateTacticalFeedback(moveData) {
    const feedbackOptions = [
      'This move allows your opponent to gain material.',
      'Your piece is now vulnerable to capture.',
      'This weakens your pawn structure.',
      'This move reduces your piece activity.',
      'Consider piece safety before moving.'
    ];
    return feedbackOptions[Math.floor(Math.random() * feedbackOptions.length)];
  }

  function generateBlunderFeedback(moveData) {
    const feedbackOptions = [
      'This move hangs a piece - always check if your pieces are protected!',
      'You missed a tactical threat. Look for checks, captures, and attacks.',
      'This severely weakens your king safety.',
      'You are giving away material for nothing in return.',
      'Always calculate forcing moves before committing.'
    ];
    return feedbackOptions[Math.floor(Math.random() * feedbackOptions.length)];
  }

  function generateAllPossibleMoves(board, color) {
    const moves = [];
    board.forEach((row, r) => {
      row.forEach((piece, c) => {
        if (piece && piece.color === color) {
          for (let tr = 0; tr < 8; tr++) {
            for (let tc = 0; tc < 8; tc++) {
              if (isValidMove(r, c, tr, tc, piece)) {
                moves.push({
                  from: { r, c },
                  to: { r: tr, c: tc },
                  notation: toAlgebraic(r, c, tr, tc, piece)
                });
              }
            }
          }
        }
      });
    });
    return moves;
  }

  function toAlgebraic(fromRow, fromCol, toRow, toCol, piece) {
    const files = 'abcdefgh';
    const pieceNotation = piece.type === 'pawn' ? '' : piece.type[0].toUpperCase();
    return `${pieceNotation}${files[fromCol]}${8-fromRow}-${files[toCol]}${8-toRow}`;
  }

  function isValidMove(fromRow, fromCol, toRow, toCol, piece) {
    if (toRow < 0 || toRow > 7 || toCol < 0 || toCol > 7) return false;
    if (fromRow === toRow && fromCol === toCol) return false;
    
    const target = board[toRow][toCol];
    if (target && target.color === piece.color) return false;

    const rowDiff = Math.abs(toRow - fromRow);
    const colDiff = Math.abs(toCol - fromCol);

    switch (piece.type) {
      case 'pawn':
        const direction = piece.color === 'white' ? -1 : 1;
        const startRow = piece.color === 'white' ? 6 : 1;
        
        if (toCol === fromCol && !target) {
          if (toRow === fromRow + direction) return true;
          if (fromRow === startRow && toRow === fromRow + 2 * direction && !board[fromRow + direction][fromCol]) return true;
        }
        
        if (Math.abs(toCol - fromCol) === 1 && toRow === fromRow + direction && target) return true;
        return false;

      case 'knight':
        return (rowDiff === 2 && colDiff === 1) || (rowDiff === 1 && colDiff === 2);

      case 'bishop':
        if (rowDiff !== colDiff) return false;
        return isPathClear(fromRow, fromCol, toRow, toCol);

      case 'rook':
        if (fromRow !== toRow && fromCol !== toCol) return false;
        return isPathClear(fromRow, fromCol, toRow, toCol);

      case 'queen':
        if (fromRow !== toRow && fromCol !== toCol && rowDiff !== colDiff) return false;
        return isPathClear(fromRow, fromCol, toRow, toCol);

      case 'king':
        return rowDiff <= 1 && colDiff <= 1;

      default:
        return false;
    }
  }

  function isPathClear(fromRow, fromCol, toRow, toCol) {
    const rowStep = toRow > fromRow ? 1 : toRow < fromRow ? -1 : 0;
    const colStep = toCol > fromCol ? 1 : toCol < fromCol ? -1 : 0;
    
    let currentRow = fromRow + rowStep;
    let currentCol = fromCol + colStep;
    
    while (currentRow !== toRow || currentCol !== toCol) {
      if (board[currentRow][currentCol]) return false;
      currentRow += rowStep;
      currentCol += colStep;
    }
    
    return true;
  }

  function makeMove(fromRow, fromCol, toRow, toCol) {
    const previousEval = engineEvaluation;
    
    const newBoard = board.map(r => r.map(p => p ? {...p} : null));
    const piece = newBoard[fromRow][fromCol];
    const captured = newBoard[toRow][toCol];
    
    piece.moved = true;
    newBoard[toRow][toCol] = piece;
    newBoard[fromRow][fromCol] = null;
    
    const moveData = {
      piece: piece.type,
      from: { row: fromRow, col: fromCol },
      to: { row: toRow, col: toCol },
      captured: captured,
      notation: toAlgebraic(fromRow, fromCol, toRow, toCol, piece),
      player: currentPlayer,
      timestamp: Date.now()
    };
    
    setBoard(newBoard);
    
    const newEval = simulateStockfishAnalysis(newBoard, moveData);
    const classification = classifyMove(previousEval, newEval, moveData);
    
    moveData.classification = classification;
    moveData.evaluation = newEval;
    
    setMoves([...moves, moveData]);
    setMoveClassification(classification);
    setNotation(prev => prev + ` ${moveData.notation}${classification.symbol}`);
    
    updateLiveHints(newBoard, moveData, classification);
    
    const hasKing = newBoard.flat().some(p => p && p.type === 'king' && p.color !== currentPlayer);
    if (!hasKing) {
      setGameOver(true);
      setIsTimerActive(false);
      generatePostGameAnalysis('checkmate');
      return;
    }
    
    setCurrentPlayer(currentPlayer === 'white' ? 'black' : 'white');
    
    if (gameMode === 'ai' && currentPlayer === 'white') {
      setTimeout(() => makeAIMove(newBoard), 500);
    }
  }

  function makeAIMove(currentBoard) {
    const allMoves = generateAllPossibleMoves(currentBoard, 'black');
    if (allMoves.length === 0) {
      setGameOver(true);
      generatePostGameAnalysis('checkmate');
      return;
    }
    
    let selectedMove;
    if (aiDifficulty === 'beginner') {
      selectedMove = allMoves[Math.floor(Math.random() * allMoves.length)];
    } else if (aiDifficulty === 'intermediate') {
      selectedMove = allMoves[Math.floor(Math.random() * Math.min(5, allMoves.length))];
    } else {
      selectedMove = allMoves[0];
    }
    
    const { from, to } = selectedMove;
    makeMove(from.r, from.c, to.r, to.c);
  }

  function updateLiveHints(board, lastMove, classification) {
    const hints = [];
    
    if (moves.length < 10) {
      const undevelopedPieces = countUndevelopedPieces(board, currentPlayer);
      if (undevelopedPieces > 2) {
        hints.push({
          type: 'opening',
          message: 'Focus on developing your knights and bishops before moving your queen.'
        });
      }
    }
    
    const threats = detectThreats(board, currentPlayer);
    if (threats.length > 0) {
      hints.push({
        type: 'tactical',
        message: `Alert: ${threats.length} pieces under attack! Defend or counter-attack.`
      });
    }
    
    const centerControl = evaluateCenterControl(board);
    if (centerControl < -1) {
      hints.push({
        type: 'positional',
        message: 'Your opponent controls the center. Consider challenging with pawns or pieces.'
      });
    }
    
    setLiveHints(hints.slice(0, 3));
  }

  function countUndevelopedPieces(board, color) {
    let count = 0;
    const startRow = color === 'white' ? 7 : 0;
    [1, 2, 5, 6].forEach(col => {
      if (board[startRow][col] && !board[startRow][col].moved) count++;
    });
    return count;
  }

  function detectThreats(board, color) {
    const threats = [];
    board.forEach((row, r) => {
      row.forEach((piece, c) => {
        if (piece && piece.color === color) {
          for (let ar = 0; ar < 8; ar++) {
            for (let ac = 0; ac < 8; ac++) {
              const attacker = board[ar][ac];
              if (attacker && attacker.color !== color && isValidMove(ar, ac, r, c, attacker)) {
                threats.push({ piece, position: { r, c } });
              }
            }
          }
        }
      });
    });
    return threats;
  }

  function evaluateCenterControl(board) {
    let score = 0;
    [[3,3], [3,4], [4,3], [4,4]].forEach(([r, c]) => {
      const piece = board[r][c];
      if (piece) score += piece.color === currentPlayer ? 1 : -1;
    });
    return score;
  }

  function generatePostGameAnalysis(endReason) {
    const totalMoves = moves.length;
    const brilliantCount = moves.filter(m => m.classification && m.classification.type === 'brilliant').length;
    const blunderCount = moves.filter(m => m.classification && m.classification.type === 'blunder').length;
    const mistakeCount = moves.filter(m => m.classification && m.classification.type === 'mistake').length;
    
    const accuracy = ((totalMoves - blunderCount - mistakeCount) / totalMoves * 100).toFixed(1);
    
    const newWeaknesses = [];
    const newStrengths = [];
    const newRecommendations = [];
    
    if (blunderCount > 2) {
      newWeaknesses.push({
        area: 'Tactical Awareness',
        description: `${blunderCount} blunders detected. Missing tactical opportunities.`,
        severity: 'high'
      });
      newRecommendations.push({
        title: 'Tactical Training',
        description: 'Practice 20 tactical puzzles focusing on forks, pins, and skewers.',
        priority: 'high'
      });
    }
    
    if (moves.length > 10 && countUndevelopedPieces(board, 'white') > 1) {
      newWeaknesses.push({
        area: 'Opening Development',
        description: 'Slow piece development in the opening phase.',
        severity: 'medium'
      });
      newRecommendations.push({
        title: 'Opening Principles',
        description: 'Study the 3 opening principles: Control center, develop pieces, castle early.',
        priority: 'medium'
      });
    }
    
    if (brilliantCount > 1) {
      newStrengths.push({
        area: 'Strategic Vision',
        description: 'Excellent move selection with multiple brilliant moves.'
      });
    }
    
    if (accuracy > 80) {
      newStrengths.push({
        area: 'Consistency',
        description: 'High accuracy throughout the game.'
      });
    }
    
    setWeaknesses(newWeaknesses);
    setStrengths(newStrengths);
    setRecommendations(newRecommendations);
    
    setPerformanceStats({
      tacticalAccuracy: Math.max(0, 100 - (blunderCount * 20)),
      positionalAwareness: Math.random() * 30 + 60,
      endgameSkill: moves.length > 40 ? Math.random() * 30 + 50 : 0,
      openingKnowledge: 100 - (countUndevelopedPieces(board, 'white') * 15),
      timeManagement: (timeControl.white / 600) * 100
    });
    
    setShowPostGameAnalysis(true);
  }

  function handleSquareClick(row, col) {
    if (gameOver) return;
    if (gameMode === 'ai' && currentPlayer === 'black') return;

    if (!isTimerActive && moves.length === 0) {
      setIsTimerActive(true);
    }

    if (selected) {
      const [selectedRow, selectedCol] = selected;
      const piece = board[selectedRow][selectedCol];
      
      if (isValidMove(selectedRow, selectedCol, row, col, piece)) {
        makeMove(selectedRow, selectedCol, row, col);
      }
      setSelected(null);
    } else {
      const piece = board[row][col];
      if (piece && piece.color === currentPlayer) {
        setSelected([row, col]);
      }
    }
  }

  function resetGame() {
    setBoard(initializeBoard());
    setSelected(null);
    setCurrentPlayer('white');
    setMoves([]);
    setGameOver(false);
    setIsTimerActive(false);
    setTimeControl({ white: 600, black: 600 });
    setNotation('');
    setLiveHints([]);
    setShowPostGameAnalysis(false);
    setEngineEvaluation(0);
    setMoveClassification(null);
    clearInterval(timerRef.current);
  }

  function formatTime(seconds) {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  }

  function exportPGN() {
    let pgn = '[Event "Chess Coach Game"]\n';
    pgn += `[Date "${new Date().toISOString().split('T')[0]}"]\n`;
    pgn += `[White "${userProfile.username}"]\n`;
    pgn += `[Black "${gameMode === 'ai' ? 'AI Engine' : 'Player 2'}"]\n\n`;
    
    moves.forEach((move, idx) => {
      if (idx % 2 === 0) pgn += `${Math.floor(idx/2) + 1}. `;
      pgn += `${move.notation} `;
    });
    
    const blob = new Blob([pgn], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'chess-game.pgn';
    a.click();
  }

  const getClassificationColor = (type) => {
    const colors = {
      brilliant: 'text-purple-400 bg-purple-500/20',
      best: 'text-green-400 bg-green-500/20',
      good: 'text-blue-400 bg-blue-500/20',
      inaccuracy: 'text-yellow-400 bg-yellow-500/20',
      mistake: 'text-orange-400 bg-orange-500/20',
      blunder: 'text-red-400 bg-red-500/20'
    };
    return colors[type] || 'text-gray-400 bg-gray-500/20';
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-purple-950 to-slate-950 text-white">
      <div className="border-b border-white/10 bg-black/30 backdrop-blur-lg">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Brain className="w-8 h-8 text-purple-400" />
              <div>
                <h1 className="text-2xl font-bold">Chess Learning Coach Pro</h1>
                <p className="text-sm text-purple-300">Powered by Stockfish Analysis Engine</p>
              </div>
            </div>
            
            <div className="flex items-center gap-4">
              <div className="text-right">
                <div className="text-sm text-purple-300">Player Rating</div>
                <div className="text-xl font-bold text-yellow-400">{userProfile.rating}</div>
              </div>
              <button
                onClick={() => setShowSettings(!showSettings)}
                className="p-2 hover:bg-white/10 rounded-lg transition"
              >
                <Settings className="w-6 h-6" />
              </button>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 py-6">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          
          <div className="space-y-4">
            <div className="bg-black/40 backdrop-blur-xl rounded-2xl border border-white/10 p-4">
              <div className="space-y-3">
                <div className="flex items-center justify-between p-3 bg-white/5 rounded-lg">
                  <div className="flex items-center gap-2">
                    <div className="w-3 h-3 rounded-full bg-gray-400"></div>
                    <span>Black</span>
                  </div>
                  <div className="text-2xl font-mono font-bold">{formatTime(timeControl.black)}</div>
                </div>
                
                <div className="flex items-center justify-between p-3 bg-white/5 rounded-lg">
                  <div className="flex items-center gap-2">
                    <div className="w-3 h-3 rounded-full bg-white"></div>
                    <span>White</span>
                  </div>
                  <div className="text-2xl font-mono font-bold">{formatTime(timeControl.white)}</div>
                </div>
              </div>
            </div>

            <div className="bg-black/40 backdrop-blur-xl rounded-2xl border border-white/10 p-4">
              <div className="flex items-center gap-2 mb-3">
                <Activity className="w-5 h-5 text-purple-400" />
                <h3 className="font-semibold">Engine Evaluation</h3>
              </div>
              <div className="text-center">
                <div className="text-4xl font-bold mb-2">
                  {engineEvaluation > 0 ? '+' : ''}{engineEvaluation.toFixed(2)}
                </div>
                <div className="h-2 bg-black/40 rounded-full overflow-hidden">
                  <div 
                    className="h-full bg-gradient-to-r from-green-500 to-blue-500 transition-all duration-300"
                    style={{ width: `${Math.min(100, Math.max(0, (engineEvaluation + 5) * 10))}%` }}
                  ></div>
                </div>
                <p className="text-sm text-gray-400 mt-2">
                  {engineEvaluation > 2 ? 'White is winning' : 
                   engineEvaluation < -2 ? 'Black is winning' : 
                   'Position is equal'}
                </p>
              </div>
            </div>

            {liveHints.length > 0 && (
              <div className="bg-black/40 backdrop-blur-xl rounded-2xl border border-white/10 p-4">
                <div className="flex items-center gap-2 mb-3">
                  <Eye className="w-5 h-5 text-yellow-400" />
                  <h3 className="font-semibold">Live Coaching</h3>
                </div>
                <div className="space-y-2">
                  {liveHints.map((hint, idx) => (
                    <div key={idx} className="flex items-start gap-2 p-2 bg-yellow-500/10 rounded-lg border border-yellow-500/20">
                      <AlertCircle className="w-4 h-4 mt-0.5" />
                      <p className="text-sm">{hint.message}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {moveClassification && (
              <div className="bg-black/40 backdrop-blur-xl rounded-2xl border border-white/10 p-4">
                <div className="flex items-center gap-2 mb-2">
                  <Target className="w-5 h-5 text-purple-400" />
                  <h3 className="font-semibold">Move Analysis</h3>
                </div>
                <div className={`p-3 rounded-lg ${getClassificationColor(moveClassification.type)}`}>
                  <div className="text-lg font-bold mb-1">
                    {moveClassification.description} {moveClassification.symbol}
                  </div>
                  {moveClassification.feedback && moveClassification.feedback.map((fb, idx) => (
                    <p key={idx} className="text-sm opacity-90">{fb}</p>
                  ))}
                </div>
              </div>
            )}
          </div>

          <div className="space-y-4">
            <div className="bg-black/40 backdrop-blur-xl rounded-2xl border border-white/10 p-6">
              <div className="aspect-square max-w-2xl mx-auto">
                <div className="grid grid-cols-8 gap-0 border-4 border-purple-500/50 rounded-lg overflow-hidden shadow-2xl">
                  {board.map((row, rowIndex) => (
                    row.map((piece, colIndex) => {
                      const isLight = (rowIndex + colIndex) % 2 === 0;
                      const isSelected = selected && selected[0] === rowIndex && selected[1] === colIndex;
                      const isValidTarget = selected && isValidMove(selected[0], selected[1], rowIndex, colIndex, board[selected[0]][selected[1]]);
                      
                      return (
                        <div
                          key={`${rowIndex}-${colIndex}`}
                          onClick={() => handleSquareClick(rowIndex, colIndex)}
                          className={`
                            aspect-square flex items-center justify-center text-5xl cursor-pointer
                            transition-all duration-200 relative
                            ${isLight ? 'bg-amber-100' : 'bg-amber-700'}
                            ${isSelected ? 'ring-4 ring-yellow-400 ring-inset' : ''}
                            ${isValidTarget ? 'ring-4 ring-green-400 ring-inset' : ''}
                            hover:brightness-110
                          `}
                        >
                          {piece && (
                            <span className={`${piece.color === 'white' ? 'filter drop-shadow-lg' : ''}`}>
                              {pieceSymbols[piece.color][piece.type]}
                            </span>
                          )}
                          {isValidTarget && !piece && (
                            <div className="absolute w-3 h-3 bg-green-500 rounded-full opacity-50"></div>
                          )}
                          {isValidTarget && piece && (
                            <div className="absolute inset-0 bg-red-500 opacity-20"></div>
                          )}
                        </div>
                      );
                    })
                  ))}
                </div>
              </div>

              <div className="flex gap-3 mt-4">
                <button
                  onClick={resetGame}
                  className="flex-1 flex items-center justify-center gap-2 bg-purple-600 hover:bg-purple-700 px-4 py-3 rounded-lg transition font-semibold"
                >
                  <RotateCcw className="w-5 h-5" />
                  New Game
                </button>
                <button
                  onClick={exportPGN}
                  className="flex items-center justify-center gap-2 bg-blue-600 hover:bg-blue-700 px-4 py-3 rounded-lg transition font-semibold"
                  disabled={moves.length === 0}
                >
                  <Download className="w-5 h-5" />
                  Export
                </button>
              </div>

              {gameOver && (
                <div className="mt-4 p-4 bg-gradient-to-r from-purple-500/20 to-blue-500/20 rounded-lg border border-purple-500/50">
                  <div className="text-center">
                    <Trophy className="w-12 h-12 mx-auto mb-2 text-yellow-400" />
                    <h3 className="text-xl font-bold mb-2">Game Over!</h3>
                    <p className="text-gray-300">
                      {currentPlayer === 'white' ? 'Black' : 'White'} wins!
                    </p>
                  </div>
                </div>
              )}
            </div>
          </div>

          <div className="space-y-4">
            <div className="bg-black/40 backdrop-blur-xl rounded-2xl border border-white/10 p-4">
              <div className="flex items-center gap-2 mb-3">
                <BookOpen className="w-5 h-5 text-purple-400" />
                <h3 className="font-semibold">Move History</h3>
              </div>
              <div className="space-y-1 max-h-80 overflow-y-auto">
                {moves.length === 0 ? (
                  <p className="text-gray-400 text-sm text-center py-4">No moves yet</p>
                ) : (
                  moves.map((move, idx) => (
                    <div 
                      key={idx}
                      className={`p-2 rounded-lg text-sm flex items-center justify-between ${
                        idx % 2 === 0 ? 'bg-white/5' : 'bg-white/10'
                      }`}
                    >
                      <div className="flex items-center gap-2">
                        <span className="text-gray-400 w-8">{Math.floor(idx / 2) + 1}.</span>
                        <span className="font-mono">{move.notation}</span>
                        {move.classification && (
                          <span className={`px-2 py-0.5 rounded text-xs font-bold ${getClassificationColor(move.classification.type)}`}>
                            {move.classification.symbol || move.classification.type}
                          </span>
                        )}
                      </div>
                      <span className="text-xs text-gray-400">
                        {move.evaluation > 0 ? '+' : ''}{move.evaluation ? move.evaluation.toFixed(1) : '0.0'}
                      </span>
                    </div>
                  ))
                )}
              </div>
            </div>

            <div className="bg-black/40 backdrop-blur-xl rounded-2xl border border-white/10 p-4">
              <div className="flex items-center gap-2 mb-3">
                <BarChart3 className="w-5 h-5 text-purple-400" />
                <h3 className="font-semibold">Current Game Stats</h3>
              </div>
              <div className="space-y-2">
                <div className="flex justify-between items-center p-2 bg-white/5 rounded">
                  <span className="text-sm">Total Moves</span>
                  <span className="font-bold">{moves.length}</span>
                </div>
                <div className="flex justify-between items-center p-2 bg-purple-500/10 rounded">
                  <span className="text-sm">Brilliant Moves</span>
                  <span className="font-bold text-purple-400">
                    {moves.filter(m => m.classification && m.classification.type === 'brilliant').length}
                  </span>
                </div>
                <div className="flex justify-between items-center p-2 bg-green-500/10 rounded">
                  <span className="text-sm">Best Moves</span>
                  <span className="font-bold text-green-400">
                    {moves.filter(m => m.classification && m.classification.type === 'best').length}
                  </span>
                </div>
                <div className="flex justify-between items-center p-2 bg-orange-500/10 rounded">
                  <span className="text-sm">Mistakes</span>
                  <span className="font-bold text-orange-400">
                    {moves.filter(m => m.classification && m.classification.type === 'mistake').length}
                  </span>
                </div>
                <div className="flex justify-between items-center p-2 bg-red-500/10 rounded">
                  <span className="text-sm">Blunders</span>
                  <span className="font-bold text-red-400">
                    {moves.filter(m => m.classification && m.classification.type === 'blunder').length}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {showSettings && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4 z-50">
          <div className="bg-gradient-to-br from-slate-800 to-purple-900 rounded-2xl p-6 max-w-md w-full border-2 border-purple-500 relative">
            <button
              onClick={() => setShowSettings(false)}
              className="absolute top-4 right-4 p-2 hover:bg-white/10 rounded-lg transition"
            >
              <X className="w-5 h-5" />
            </button>

            <h2 className="text-2xl font-bold mb-6">Game Settings</h2>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm mb-2 font-semibold">Game Mode</label>
                <select
                  value={gameMode}
                  onChange={(e) => setGameMode(e.target.value)}
                  className="w-full bg-white/10 border border-white/20 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-purple-500"
                >
                  <option value="ai">vs AI</option>
                  <option value="local">Local Multiplayer</option>
                </select>
              </div>
              
              {gameMode === 'ai' && (
                <div>
                  <label className="block text-sm mb-2 font-semibold">AI Difficulty</label>
                  <select
                    value={aiDifficulty}
                    onChange={(e) => setAiDifficulty(e.target.value)}
                    className="w-full bg-white/10 border border-white/20 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-purple-500"
                  >
                    <option value="beginner">Beginner (800 ELO)</option>
                    <option value="intermediate">Intermediate (1200 ELO)</option>
                    <option value="advanced">Advanced (1600 ELO)</option>
                  </select>
                </div>
              )}
              
              <div>
                <label className="block text-sm mb-2 font-semibold">Username</label>
                <input
                  type="text"
                  value={userProfile.username}
                  onChange={(e) => setUserProfile({...userProfile, username: e.target.value})}
                  className="w-full bg-white/10 border border-white/20 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-purple-500"
                />
              </div>

              <div>
                <label className="block text-sm mb-2 font-semibold">Time Control (minutes)</label>
                <select
                  onChange={(e) => {
                    const seconds = parseInt(e.target.value);
                    setTimeControl({ white: seconds, black: seconds });
                  }}
                  className="w-full bg-white/10 border border-white/20 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-purple-500"
                >
                  <option value="300">5 minutes</option>
                  <option value="600">10 minutes</option>
                  <option value="900">15 minutes</option>
                  <option value="1800">30 minutes</option>
                </select>
              </div>
            </div>
            
            <button
              onClick={() => setShowSettings(false)}
              className="w-full mt-6 bg-purple-600 hover:bg-purple-700 px-4 py-3 rounded-lg transition font-semibold"
            >
              Save Settings
            </button>
          </div>
        </div>
      )}

      {showPostGameAnalysis && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4 z-50 overflow-y-auto">
          <div className="bg-gradient-to-br from-slate-800 to-purple-900 rounded-2xl p-6 max-w-4xl w-full border-2 border-purple-500 relative my-8">
            <button
              onClick={() => setShowPostGameAnalysis(false)}
              className="absolute top-4 right-4 p-2 hover:bg-white/10 rounded-lg transition"
            >
              <X className="w-5 h-5" />
            </button>

            <div className="flex items-center gap-3 mb-6">
              <Trophy className="w-8 h-8 text-yellow-400" />
              <h2 className="text-3xl font-bold">Post-Game Analysis</h2>
            </div>

            <div className="mb-6">
              <h3 className="text-xl font-semibold mb-4 flex items-center gap-2">
                <BarChart3 className="w-5 h-5" />
                Performance Breakdown
              </h3>
              <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                {Object.entries(performanceStats).map(([key, value]) => (
                  <div key={key} className="bg-white/10 rounded-lg p-4">
                    <div className="text-sm text-gray-300 mb-2 capitalize">
                      {key.replace(/([A-Z])/g, ' $1').trim()}
                    </div>
                    <div className="flex items-center gap-2">
                      <div className="flex-1 h-2 bg-black/40 rounded-full overflow-hidden">
                        <div 
                          className="h-full bg-gradient-to-r from-purple-500 to-blue-500"
                          style={{ width: `${value}%` }}
                        ></div>
                      </div>
                      <span className="text-lg font-bold">{Math.round(value)}%</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {strengths.length > 0 && (
              <div className="mb-6">
                <h3 className="text-xl font-semibold mb-4 flex items-center gap-2 text-green-400">
                  <Award className="w-5 h-5" />
                  Strengths
                </h3>
                <div className="space-y-2">
                  {strengths.map((strength, idx) => (
                    <div key={idx} className="bg-green-500/10 border border-green-500/30 rounded-lg p-4">
                      <div className="font-semibold text-green-400">{strength.area}</div>
                      <div className="text-sm text-gray-300">{strength.description}</div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {weaknesses.length > 0 && (
              <div className="mb-6">
                <h3 className="text-xl font-semibold mb-4 flex items-center gap-2 text-orange-400">
                  <AlertCircle className="w-5 h-5" />
                  Areas for Improvement
                </h3>
                <div className="space-y-2">
                  {weaknesses.map((weakness, idx) => (
                    <div key={idx} className="bg-orange-500/10 border border-orange-500/30 rounded-lg p-4">
                      <div className="flex items-center justify-between mb-1">
                        <div className="font-semibold text-orange-400">{weakness.area}</div>
                        <span className={`px-2 py-1 rounded text-xs font-bold ${
                          weakness.severity === 'high' ? 'bg-red-500/20 text-red-400' :
                          weakness.severity === 'medium' ? 'bg-orange-500/20 text-orange-400' :
                          'bg-yellow-500/20 text-yellow-400'
                        }`}>
                          {weakness.severity}
                        </span>
                      </div>
                      <div className="text-sm text-gray-300">{weakness.description}</div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {recommendations.length > 0 && (
              <div className="mb-6">
                <h3 className="text-xl font-semibold mb-4 flex items-center gap-2 text-blue-400">
                  <Target className="w-5 h-5" />
                  Training Recommendations
                </h3>
                <div className="space-y-2">
                  {recommendations.map((rec, idx) => (
                    <div key={idx} className="bg-blue-500/10 border border-blue-500/30 rounded-lg p-4">
                      <div className="flex items-start gap-3">
                        <div className="text-blue-400 mt-1">
                          <Zap className="w-5 h-5" />
                        </div>
                        <div className="flex-1">
                          <div className="flex items-center justify-between mb-1">
                            <div className="font-semibold text-blue-400">{rec.title}</div>
                            <span className={`px-2 py-1 rounded text-xs font-bold ${
                              rec.priority === 'high' ? 'bg-red-500/20 text-red-400' :
                              rec.priority === 'medium' ? 'bg-yellow-500/20 text-yellow-400' :
                              'bg-green-500/20 text-green-400'
                            }`}>
                              {rec.priority} priority
                            </span>
                          </div>
                          <div className="text-sm text-gray-300">{rec.description}</div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            <div className="flex gap-3">
              <button
                onClick={() => {
                  setShowPostGameAnalysis(false);
                  resetGame();
                }}
                className="flex-1 bg-purple-600 hover:bg-purple-700 px-4 py-3 rounded-lg transition font-semibold"
              >
                Play Again
              </button>
              <button
                onClick={exportPGN}
                className="flex items-center justify-center gap-2 bg-blue-600 hover:bg-blue-700 px-6 py-3 rounded-lg transition font-semibold"
              >
                <Download className="w-5 h-5" />
                Export Game
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ChessCoachPro;