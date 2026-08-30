from dataclasses import dataclass
from typing import List, Tuple, Optional, Dict, Any


@dataclass
class OptimizationRequest:
    objective: str
    dimensions: int
    bounds: List[Tuple[float, float]]
    max_stages: int = 5
    patience: int = 3


@dataclass
class OptimizationResult:
    best_position: Optional[List[float]]
    best_score: float
    strategy_history: List[str]
    stage_history: List[Dict[str, Any]]
    convergence_history: List[Dict[str, Any]]