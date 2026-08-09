import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="StrideFi Workout & Economy Simulator",
    page_icon="🏃",
    layout="wide"
)

st.title("🏃 StrideFi Workout & Economy Simulator")
st.markdown("Granular Session Profitability, Shoe Durability, 1–30 Leveling & JitoSOL Staking Accumulator")

# --- SIDEBAR GLOBAL CONSTANTS ---
st.sidebar.header("⚙️ Market & Protocol Baseline")
sol_price = st.sidebar.number_input("SOL Spot Price ($)", value=72.50, step=1.0)
token_price_sol = st.sidebar.number_input("Stride Token Price (in SOL)", value=0.005, format="%.5f")
token_price_usd = token_price_sol * sol_price
jito_apy = st.sidebar.slider("JitoSOL Reserve APY (%)", 4.0, 12.0, 7.2, step=0.1)

st.sidebar.caption(f"Calculated Token USD Price: **${token_price_usd:.4f}**")

# --- DATA STRUCTURES: ENERGY & LEVELING ---
ENERGY_TYPES = {
    "Standard": {"sol_cost": 0.50, "duration_mins": 30, "base_durability_loss": 10},
    "High-Octane": {"sol_cost": 1.50, "duration_mins": 45, "base_durability_loss": 20},
    "Nitro": {"sol_cost": 4.50, "duration_mins": 60, "base_durability_loss": 35}
}

# Level 1 to 30 Matrix Generation
levels = np.arange(1, 31)
# Exponential cost scaling for leveling
level_upgrade_costs = np.round(15 * (levels ** 1.35)).astype(int)
# Efficiency multiplier scaling with shoe level
level_efficiency_mults = 1.0 + ((levels - 1) * 0.08)

df_leveling = pd.DataFrame({
    "Level": levels,
    "Token Cost to Upgrade": level_upgrade_costs,
    "Cumulative Cost to Reach": np.cumsum(level_upgrade_costs),
    "Yield Efficiency Mult": level_efficiency_mults
})

# --- TAB NAVIGATION ---
tab1, tab2, tab3 = st.tabs([
    "🏃 Tab 1: Live Workout Session Simulator",
    "👟 Tab 2: Shoe Leveling (1-30) & Repair Costs",
    "🏦 Tab 3: JitoSOL Pool Yield Accumulator"
])

# ==========================================
# TAB 1: WORKOUT SESSION SIMULATOR
# ==========================================
with tab1:
    st.subheader("1. Start-to-Finish Session Economics")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        energy_type = st.selectbox("Energy Type Input", list(ENERGY_TYPES.keys()), index=0)
        energy_sol = ENERGY_TYPES[energy_type]["sol_cost"]
        session_mins = ENERGY_TYPES[energy_type]["duration_mins"]
    with col2:
        shoe_level = st.slider("Shoe Level", 1, 30, 5)
        target_margin_pct = st.slider("Target Initial ROI Margin (% Gain)", 0, 50, 15, help="Target potential return over input energy cost before repair fees.")
    with col3:
        voice_stations = st.slider("Voice Stations Completed", 0, 5, 3)
        concurrent_users = st.number_input("Active Users in Daily Epoch Pool", value=1000, step=100)

    # 1. Target payout calculation (Principal + Profit Margin)
    required_sol_payout = energy_sol * (1.0 + (target_margin_pct / 100.0))
    required_token_payout = required_sol_payout / token_price_sol if token_price_sol > 0 else 0
    
    # 2. Level and station modifiers
    level_mult = df_leveling.loc[df_leveling["Level"] == shoe_level, "Yield Efficiency Mult"].values[0]
    station_bonus = 1.0 + (voice_stations * 0.05) # 5% bonus per station
    
    effective_tokens_earned = required_token_payout * level_mult * station_bonus
    gross_sol_payout = effective_tokens_earned * token_price_sol

    # 3. Repair Costs
    base_durability_loss = ENERGY_TYPES[energy_type]["base_durability_loss"]
    repair_cost_per_pt_tokens = 2.5 * (1 + (shoe_level * 0.03))
    total_repair_token_cost = base_durability_loss * repair_cost_per_pt_tokens
    total_repair_sol_cost = total_repair_token_cost * token_price_sol

    # 4. Net Session Profitability
    net_sol_profit = gross_sol_payout - energy_sol - total_repair_sol_cost
    net_roi_pct = (net_sol_profit / energy_sol) * 100 if energy_sol > 0 else 0

    st.markdown("---")
    st.markdown("### Session Financial Breakdown")

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Energy Cost", f"{energy_sol:.2f} SOL", f"${energy_sol * sol_price:.2f}")
    m2.metric("Gross Tokens Earned", f"{effective_tokens_earned:,.1f} Tokens", f"{gross_sol_payout:.3f} SOL")
    m3.metric("Repair Cost", f"{total_repair_token_cost:,.1f} Tokens", f"-{total_repair_sol_cost:.3f} SOL")
    
    if net_sol_profit >= 0:
        m4.metric("Net Profit / Session", f"{net_sol_profit:,.3f} SOL", f"+{net_roi_pct:.1f}% ROI", delta_color="normal")
    else:
        m4.metric("Net Profit / Session", f"{net_sol_profit:,.3f} SOL", f"{net_roi_pct:.1f}% ROI", delta_color="inverse")

    st.markdown("---")
    st.markdown("### Epoch Pool Take Breakdown")
    epoch_contribution_sol = energy_sol * 0.10
    total_epoch_pool_sol = epoch_contribution_sol * concurrent_users
    user_epoch_share_pct = (station_bonus / (concurrent_users * 1.0)) * 100
    
    st.info(f"💡 **Epoch Pool Impact:** Total Daily Pool = **{total_epoch_pool_sol:,.2f} SOL**. Your completed **{voice_stations} Voice Stations** yield an estimated **{user_epoch_share_pct:.3f}%** claim of the daily pool against {concurrent_users:,} competing athletes.")

# ==========================================
# TAB 2: SHOE LEVELING (1 TO 30)
# ==========================================
with tab2:
    st.subheader("2. Shoe Leveling Matrix (Level 1 to 30)")
    st.write("Inspect upgrade costs, cumulative token sinks, and yield multipliers per shoe level.")

    st.dataframe(df_leveling, use_container_width=True)

    fig_leveling = px.line(
        df_leveling,
        x="Level",
        y=["Token Cost to Upgrade", "Cumulative Cost to Reach"],
        title="Token Upgrade Sink Trajectory across 30 Levels",
        labels={"value": "Tokens", "variable": "Cost Metric"}
    )
    st.plotly_chart(fig_leveling, use_container_width=True)

# ==========================================
# TAB 3: JITOSOL POOL ACCUMULATOR
# ==========================================
with tab3:
    st.subheader("3. JitoSOL Reserve Pool Accumulator")
    st.write("Simulates the 20% SOL revenue reserve compounding with JitoSOL staking yields over time.")

    col_j1, col_j2, col_j3 = st.columns(3)
    with col_j1:
        daily_sessions = st.slider("Daily Protocol Workout Sessions", 100, 20000, 2500, step=500)
    with col_j2:
        avg_energy_sol = st.selectbox("Average Energy Used per Session", [0.50, 1.50, 4.50], index=0)
    with col_j3:
        simulation_days = st.slider("Simulation Timeline (Days)", 30, 365, 180, step=30)

    daily_sol_intake = daily_sessions * avg_energy_sol
    daily_jito_reserve_input = daily_sol_intake * 0.20
    daily_jito_rate = (jito_apy / 100.0) / 365.0

    accumulated_sol = []
    yield_earned = []
    current_principal = 0.0
    total_yield = 0.0

    for day in range(1, simulation_days + 1):
        current_principal += daily_jito_reserve_input
        day_yield = current_principal * daily_jito_rate
        total_yield += day_yield
        current_principal += day_yield
        accumulated_sol.append(current_principal)
        yield_earned.append(total_yield)

    df_jito = pd.DataFrame({
        "Day": list(range(1, simulation_days + 1)),
        "Total JitoSOL Reserve (SOL)": accumulated_sol,
        "Cumulative Staking Yield (SOL)": yield_earned
    })

    f1, f2, f3 = st.columns(3)
    f1.metric("Total Reserve Pool Accumulated", f"{current_principal:,.1f} SOL", f"${current_principal * sol_price:,.2f}")
    f2.metric("Cumulative Jito Yield Earned", f"{total_yield:,.1f} SOL", f"${total_yield * sol_price:,.2f}")
    f3.metric("Daily Jito Reserve Deposit", f"{daily_jito_reserve_input:,.1f} SOL/day")

    fig_jito = px.area(
        df_jito,
        x="Day",
        y="Total JitoSOL Reserve (SOL)",
        title=f"JitoSOL Reserve Growth ({simulation_days} Days at {jito_apy}% APY)",
        labels={"Total JitoSOL Reserve (SOL)": "Reserve (SOL)"}
    )
    st.plotly_chart(fig_jito, use_container_width=True)