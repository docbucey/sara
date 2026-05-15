# Game-Theoretic Science - Expanded
# Pure ASCII. No imports.

_INTERNAL = {
    "players": ["Player A", "Player B"],
    "strategies": ["cooperate", "defect"],
    "payoffs": {
        ("cooperate", "cooperate"): (3, 3),
        ("cooperate", "defect"): (0, 5),
        ("defect", "cooperate"): (5, 0),
        ("defect", "defect"): (1, 1)
    }
}

def _helper(text):
    return text.lower()

def _interpret_game(text):
    return {
        "players": _INTERNAL["players"],
        "strategies": _INTERNAL["strategies"],
        "payoffs": _INTERNAL["payoffs"]
    }

def _evaluate_strategies(game):
    equilibria = []
    for strategy_a in game["strategies"]:
        for strategy_b in game["strategies"]:
            payoff = game["payoffs"].get((strategy_a, strategy_b), (0, 0))
            equilibria.append({
                "strategies": (strategy_a, strategy_b),
                "payoff": payoff
            })
    return equilibria

def _select_equilibrium(equilibria):
    best = None
    best_sum = None
    for equilibrium in equilibria:
        total_payoff = sum(equilibrium["payoff"])
        if best is None or total_payoff > best_sum:
            best = equilibrium
            best_sum = total_payoff
    return best

def run_approach(input_data):
    text = _helper(str(input_data))
    game = _interpret_game(text)
    equilibria = _evaluate_strategies(game)
    best_equilibrium = _select_equilibrium(equilibria)
    
    return {
        "approach": "game_science",
        "input": text,
        "game": game,
        "equilibria": equilibria,
        "best_equilibrium": best_equilibrium,
        "status": "complete"
    }