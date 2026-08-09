import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="StrideFi Protocol Scenario Simulator",
    page_icon="🏃",
    layout="wide"
)

st.title("🏃 StrideFi Protocol Scenario & Economic Simulator")
st.markdown("Proof-of-Physical-Work (PoPW) Tokenomics & Inclusive Game Economy Model")

# --- CONSTANTS & MAPPINGS ---
SOL_SPOT_DEFAULT = 72.50

FUEL_DATA = {
    "Standard": {"cost": 0.50, "mult": 1.0},
    "High-Octane": {"cost": 1.50, "mult": 3.0},
    "Nitro": {"cost": 4.50, "mult": 9.5}
}

PRESTIGE_TIERS = ["Plain", "Gold", "Platinum", "Ruby", "Diamond"]
PRESTIGE_MELTS = np.array([1.0, 1.25, 2.50, 6.00, 11.00])
DEFAULT_TIER_WEIGHTS = np.array([0.50, 0.25, 0.15, 0.08, 0.02])

# --- HELPER FUNCTIONS ---
def calculate_revenue_split(sol_amount):
    """
    60% AMM Liquidity Buyback & Burn
    20% Permanent JitoSOL Reserve Pool
    10% Daily Epoch Reward Pool
    10% Net Operator Profit
    """
    return {
        "amm_buyback": sol_amount * 0.60,
        "jito_reserve": sol_amount * 0.20,
        "epoch_pool": sol_amount * 0.10,
        "operator_profit": sol_amount * 0.10
    }

def simulate_prestige_progression(fuel_grade="Standard", sessions_per_day=1.0, voice_stations=0, **kwargs):
    fuel_mult = FUEL_DATA.get(fuel_grade, {"mult": 1.0})["mult"]
    station_bonus = 1.0 + (voice_stations * 0.05)
    weighted_multiplier = float(np.dot(DEFAULT_TIER_WEIGHTS, PRESTIGE_MELTS)) * fuel_mult * station_bonus
    return weighted_multiplier

# --- SIDEBAR CONTROLS ---
st.sidebar.header("⚙️ Global Parameters")
sol_price = st.sidebar.number_input("SOL Spot Price ($)", value=SOL_SPOT_DEFAULT, step=1.0)

# --- TAB SETUP ---
tab1, tab2, tab3 = st.tabs([
    "📊 Tab 1: Single Session Calculator",
    "📈 Tab 2: Macro Growth, Bonding Curve & Burn Sinks",
    "🏃 Tab 3: Minnow vs. Whale Progression"
])

# ==========================================
# TAB 1: SINGLE SESSION CALCULATOR
# ==========================================
with tab1:
    st.subheader("1. Single Workout Session & Revenue Split")
    
    col_input1, col_input2, col_input3, col_input4 = st.columns(4)
    
    with col_input1:
        fuel_choice = st.selectbox("Fuel Grade", list(FUEL_DATA.keys()), index=0)
    with col_input2:
        session_mins = st.slider("Session Duration (Mins)", 20, 90, 30, help="20 to 90 min preferred duration. Epoch shares remain identical.")
    with col_input3:
        prestige_choice = st.selectbox("Shoe Prestige Tier", PRESTIGE_TIERS, index=0)
    with col_input4:
        voice_stations_done = st.slider("Voice Stations Completed", 0, 5, 3)

    # Calculation logic
    sol_spent = FUEL_DATA[fuel_choice]["cost"]
    fuel_multiplier = FUEL_DATA[fuel_choice]["mult"]
    tier_idx = PRESTIGE_TIERS.index(prestige_choice)
    tier_multiplier = PRESTIGE_MELTS[tier_idx]
    
    # Revenue split
    split = calculate_revenue_split(sol_spent)
    
    # Calculate user weighted shares
    user_shares = fuel_multiplier * tier_multiplier * (1.0 + (voice_stations_done * 0.05))

    st.markdown("---")
    st.markdown("### On-Chain Revenue Allocation (60 / 20 / 10 / 10 Split)")
    
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("60% AMM Buyback & Burn", f"{split['amm_buyback']:.3f} SOL", f"${split['amm_buyback'] * sol_price:.2f}")
    m2.metric("20% JitoSOL Reserve", f"{split['jito_reserve']:.3f} SOL", f"${split['jito_reserve'] * sol_price:.2f}")
    m3.metric("10% Daily Epoch Pool", f"{split['epoch_pool']:.3f} SOL", f"${split['epoch_pool'] * sol_price:.2f}")
    m4.metric("10% Operator Profit", f"{split['operator_profit']:.3f} SOL", f"${split['operator_profit'] * sol_price:.2f}")

    st.info(f"💡 **User Session Output:** Total Weighted Epoch Shares Generated: **{user_shares:.2f}x** (Fuel: {fuel_multiplier}x | Tier: {tier_multiplier}x | Station Bonus: {1.0 + (voice_stations_done * 0.05):.2f}x)")

# ==========================================
# TAB 2: MACRO GROWTH, BONDING CURVE & BURN SINKS
# ==========================================
with tab2:
    st.subheader("2. 30-Day Macro Protocol Projection")
    
    col_mac1, col_mac2 = st.columns(2)
    with col_mac1:
        active_users = st.slider("Active Daily Users", 100, 10000, 1500, step=100)
    with col_mac2:
        pct_standard = st.slider("% Standard Fuel Users (0.50 SOL)", 0, 100, 80)
        pct_high_octane = st.slider("% High-Octane Fuel Users (1.50 SOL)", 0, 100 - pct_standard, 15)
        pct_nitro = 100 - pct_standard - pct_high_octane
        st.caption(f"Calculated Nitro Users (4.50 SOL): **{pct_nitro}%**")

    # Calculate daily SOL intake
    daily_std_count = active_users * (pct_standard / 100.0)
    daily_oct_count = active_users * (pct_high_octane / 100.0)
    daily_nit_count = active_users * (pct_nitro / 100.0)
    
    daily_gross_sol = (daily_std_count * 0.50) + (daily_oct_count * 1.50) + (daily_nit_count * 4.50)
    daily_split = calculate_revenue_split(daily_gross_sol)

    days = list(range(1, 31))
    df_macro = pd.DataFrame({
        "Day": days,
        "Cumulative Gross SOL": [daily_gross_sol * d for d in days],
        "Cumulative AMM Buyback (SOL)": [daily_split["amm_buyback"] * d for d in days],
        "Cumulative JitoSOL Reserve (SOL)": [daily_split["jito_reserve"] * d for d in days],
        "Cumulative Net Operator Profit ($)": [daily_split["operator_profit"] * d * sol_price for d in days]
    })

    fig_macro = px.line(
        df_macro,
        x="Day",
        y=["Cumulative AMM Buyback (SOL)", "Cumulative JitoSOL Reserve (SOL)"],
        title="Protocol Liquidity & Reserve Pool Accumulation Over 30 Days",
        labels={"value": "SOL Amount", "variable": "Pool"}
    )
    st.plotly_chart(fig_macro, use_container_width=True)

    st.markdown("---")
    
    # --- MODULE 2A: DYNAMIC BONDING CURVE MODEL ---
    st.subheader("2A. Dynamic Token Bonding Curve Model")
    st.markdown("Simulating token price discovery based on circulating supply ($P = k \cdot S^\\gamma$).")

    col_bc1, col_bc2, col_bc3 = st.columns(3)
    with col_bc1:
        base_price = st.number_input("Base Initial Price ($)", value=0.001, format="%.4f")
    with col_bc2:
        exponent_gamma = st.slider("Curve Exponent (γ)", 1.0, 2.5, 1.5, step=0.1, help="Higher values increase exponential price scaling as supply grows.")
    with col_bc3:
        max_supply_mil = st.slider("Simulated Circulating Supply (M Tokens)", 1, 100, 50, step=1)

    supply_points = np.linspace(0.1, max_supply_mil * 1_000_000, 100)
    k_constant = base_price / (1_000_000 ** (exponent_gamma - 1))
    price_curve = k_constant * (supply_points ** exponent_gamma) / supply_points
    market_cap = price_curve * supply_points

    df_curve = pd.DataFrame({
        "Circulating Supply": supply_points / 1_000_000,
        "Token Price ($)": price_curve,
        "Market Cap ($)": market_cap
    })

    fig_curve = go.Figure()
    fig_curve.add_trace(go.Scatter(x=df_curve["Circulating Supply"], y=df_curve["Token Price ($)"], name="Token Price ($)", line=dict(color="#00FFA3", width=3)))
    fig_curve.add_trace(go.Scatter(x=df_curve["Circulating Supply"], y=df_curve["Market Cap ($)"], name="Market Cap ($)", yaxis="y2", line=dict(color="#00B2FF", width=2, dash="dash")))

    fig_curve.update_layout(
        title="Token Bonding Curve & Market Cap Scaling",
        xaxis=dict(title="Circulating Supply (Millions)"),
        yaxis=dict(title=dict(text="Token Price ($)", font=dict(color="#00FFA3"))),
        yaxis2=dict(title=dict(text="Market Cap ($)", font=dict(color="#00B2FF")), overlaying="y", side="right")
    )
    st.plotly_chart(fig_curve, use_container_width=True)

    st.markdown("---")

    # --- MODULE 2B: TOKEN INFLATION VS. BURN SINKS ---
    st.subheader("2B. Daily Token Emissions vs. Burn Sinks (Net Net Sink Calculator)")
    st.markdown("Evaluating economic equilibrium: Net Daily Emissions = Base Reward Mint - (Fuel Buyback Burn + Prestige Upgrade Sinks).")

    col_sink1, col_sink2, col_sink3 = st.columns(3)
    with col_sink1:
        daily_emission_tokens = st.number_input("Base Daily Token Emissions (Mint)", value=500000, step=50000)
    with col_sink2:
        upgrade_burn_pct = st.slider("% Users Reinvesting in Prestige Upgrades Daily", 5, 50, 20)
    with col_sink3:
        avg_token_price = st.number_input("Assumed Token Price ($)", value=0.05, step=0.01)

    # Calculation logic for burn sinks
    sol_buyback_daily = daily_split["amm_buyback"]
    usd_buyback_daily = sol_buyback_daily * sol_price
    tokens_burned_via_buyback = usd_buyback_daily / avg_token_price if avg_token_price > 0 else 0

    # Prestige burn estimate (approx. 2000 tokens spent per upgrade attempt)
    upgrade_burn_tokens = (active_users * (upgrade_burn_pct / 100.0)) * 2500
    total_daily_burn = tokens_burned_via_buyback + upgrade_burn_tokens
    net_daily_change = daily_emission_tokens - total_daily_burn

    c_m1, c_m2, c_m3 = st.columns(3)
    c_m1.metric("Daily Emissions (Mint)", f"{daily_emission_tokens:,.0f} Tokens")
    c_m2.metric("Daily Protocol Burn (Sinks)", f"{total_daily_burn:,.0f} Tokens", f"Burn Rate: {(total_daily_burn / daily_emission_tokens) * 100:.1f}%")
    
    if net_daily_change <= 0:
        c_m3.metric("Net Daily Token Change", f"{net_daily_change:,.0f} Tokens", "DEFLATIONARY 🟢", delta_color="normal")
    else:
        c_m3.metric("Net Daily Token Change", f"+{net_daily_change:,.0f} Tokens", "INFLATIONARY 🔴", delta_color="inverse")

    st.caption(f" breakdown: AMM Buyback Burn: **{tokens_burned_via_buyback:,.0f}** tokens/day | Prestige Fee Sinks: **{upgrade_burn_tokens:,.0f}** tokens/day.")

# ==========================================
# TAB 3: MINNOW VS. WHALE PROGRESSION
# ==========================================
with tab3:
    st.subheader("3. Diligent Minnow Progression Model")
    st.write("Modeling progression time for a daily athlete utilizing Standard Fuel (0.50 SOL) and re-investing epoch payouts.")

    sessions_per_day = st.number_input("Sessions per Day", value=1.0, min_value=0.5, max_value=3.0, step=0.5)
    minnow_weighted_mult = simulate_prestige_progression(fuel_grade="Standard", sessions_per_day=sessions_per_day, voice_stations=3)
    
    st.metric("Effective Daily Yield Multiplier", f"{minnow_weighted_mult:.2f}x")
    
    # Timeline estimates table
    progression_data = pd.DataFrame({
        "Target Prestige Tier": ["Gold", "Platinum", "Ruby", "Diamond"],
        "Multiplier Benefit": ["1.25x (+25%)", "2.50x (+150%)", "6.00x (+500%)", "11.00x (+1000% + JitoSOL Yield)"],
        "Est. Days with 100% Token Re-investment": [30, 90, 210, 450],
        "Required Daily Standard Fuel (SOL)": [0.50 * d for d in [30, 90, 210, 450]]
    })
    st.table(progression_data)