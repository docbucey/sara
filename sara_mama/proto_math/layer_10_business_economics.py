"""
Layer X: Business & Economics Mathematics

This layer provides core quantitative tools used in business, finance, and economics.
It includes:

- percentage change and growth rate calculations
- simple interest and compound interest
- present value (PV) and future value (FV)
- net present value (NPV)
- internal rate of return (IRR) approximation
- break-even analysis
- elasticity calculations (price elasticity of demand)
- marginal cost, marginal revenue, marginal profit
- supply and demand equilibrium solvers

This layer should NOT include statistics, calculus, or linear algebra beyond what is needed
for basic economic formulas. Keep the functions simple and domain-specific.
"""

# -------------------------
# Business & Economics Math
# -------------------------

def percentage_change(old, new):
    """
    Compute the percentage change between an old value and a new value.
    Formula: ((new - old) / old) * 100
    """
    if old == 0:
        return None
    return ((new - old) / old) * 100

def simple_interest(principal, rate, time):
    """
    Compute the simple interest.
    Formula: I = P * r * t
    """
    return principal * rate * time

def compound_interest(principal, rate, time, n=1):
    """
    Compute the compound interest.
    Formula: A = P * (1 + r/n)^(n*t)
    """
    return principal * (1 + rate / n) ** (n * time)

def present_value(future_value, rate, time):
    """
    Compute the present value of a future amount.
    Formula: PV = FV / (1 + r)^t
    """
    return future_value / (1 + rate) ** time

def future_value(present_value, rate, time):
    """
    Compute the future value of a present amount.
    Formula: FV = PV * (1 + r)^t
    """
    return present_value * (1 + rate) ** time

def net_present_value(cash_flows, rate):
    """
    Compute the net present value of a series of cash flows.
    Formula: NPV = Σ(CF_t / (1 + r)^t)
    """
    return sum(cf / (1 + rate) ** t for t, cf in enumerate(cash_flows, start=1))

def internal_rate_of_return(cash_flows, iterations=100):
    """
    Approximate the internal rate of return (IRR) for a series of cash flows.
    Uses the Newton-Raphson method.
    """
    rate = 0.1  # Initial guess
    for _ in range(iterations):
        npv = sum(cf / (1 + rate) ** t for t, cf in enumerate(cash_flows, start=1))
        d_npv = sum(-t * cf / (1 + rate) ** (t + 1) for t, cf in enumerate(cash_flows, start=1))
        if d_npv == 0:
            break
        rate -= npv / d_npv
    return rate

def break_even_point(fixed_costs, price_per_unit, cost_per_unit):
    """
    Compute the break-even point in units.
    Formula: BEP = Fixed Costs / (Price per Unit - Cost per Unit)
    """
    margin = price_per_unit - cost_per_unit
    if margin == 0:
        return None
    return fixed_costs / margin

def price_elasticity_of_demand(q1, q2, p1, p2):
    """
    Compute the price elasticity of demand.
    Formula: E = (% change in quantity) / (% change in price)
    """
    if p1 == 0 or q1 == 0:
        return None
    percent_change_quantity = (q2 - q1) / q1
    percent_change_price = (p2 - p1) / p1
    if percent_change_price == 0:
        return None
    return percent_change_quantity / percent_change_price

def marginal_cost(cost_function, quantity, delta=1e-5):
    """
    Compute the marginal cost at a given quantity.
    Formula: MC = dC/dQ ≈ (C(Q + ΔQ) - C(Q)) / ΔQ
    """
    return (cost_function(quantity + delta) - cost_function(quantity)) / delta

def marginal_revenue(revenue_function, quantity, delta=1e-5):
    """
    Compute the marginal revenue at a given quantity.
    Formula: MR = dR/dQ ≈ (R(Q + ΔQ) - R(Q)) / ΔQ
    """
    return (revenue_function(quantity + delta) - revenue_function(quantity)) / delta

def supply_demand_equilibrium(supply_fn, demand_fn, guess=1.0, iterations=100):
    """
    Solve for the supply and demand equilibrium price.
    Uses the Newton-Raphson method.
    """
    price = guess
    for _ in range(iterations):
        excess_supply = supply_fn(price) - demand_fn(price)
        slope = (supply_fn(price + 1e-5) - demand_fn(price + 1e-5) - excess_supply) / 1e-5
        if slope == 0:
            break
        price -= excess_supply / slope
    return price
# -------------------------
# Expansion: ROI + Analysis
# -------------------------

def horizontal_analysis(values):
    """
    Perform horizontal analysis across a series of values (e.g., revenues over years).
    Returns percentage changes between consecutive periods.
    Example: [100, 120, 150] -> [20.0, 25.0]
    """
    if len(values) < 2:
        return None
    return [((values[i] - values[i-1]) / values[i-1]) * 100
            if values[i-1] != 0 else None
            for i in range(1, len(values))]

def vertical_analysis(line_items, base_item):
    """
    Perform vertical analysis by expressing each line item as a percentage of a base.
    Example: line_items=[50, 30, 20], base_item=100 -> [50.0, 30.0, 20.0]
    """
    if base_item == 0:
        return None
    return [(item / base_item) * 100 for item in line_items]

def roi(expected_return, actual_cost):
    """
    ROI Calculator (Business Math Layer):
    Formula: ROI = (Expected Return - Actual Cost) / Actual Cost
    Returns ROI value and interpretation.
    """
    try:
        roi_value = (expected_return - actual_cost) / actual_cost
    except ZeroDivisionError:
        roi_value = 0

    interpretation = "capital_gain" if roi_value >= 0 else "capital_loss"

    return {
        "roi_value": roi_value,
        "interpretation": interpretation,
        "expected_return": expected_return,
        "actual_cost": actual_cost,
    }