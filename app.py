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
st.markdown("Granular Session Profitability, Dynamic Repair/Station Wear, Level-Up Sinks & Level Maintenance Discounts")

# --- SIDEBAR GLOBAL CONSTANTS ---
st.sidebar.header("⚙️ Market & Protocol Baseline")
sol_price = st.sidebar.number_input("SOL Spot Price ($)", value=72.50, step=1.0)
token_price_sol = st.sidebar.number_input("Stride Token Price (in SOL)", value=0.005, format="%.5f")
token_price_usd = token_price_sol * sol_price
jito_apy = st.sidebar.slider("JitoSOL Reserve APY (%)", 4.0, 12.0, 7.2, step=0.1)

st.sidebar.caption(f"Calculated Token USD Price: **${token_price_usd:.4f}**")

# --- DATA STRUCTURES: ENERGY & LEVELING ---
ENERGY_TYPES = {
    "Standard": {"sol_cost": 0.50, "duration_mins": 30},
    "High-Octane": {"sol_cost": 1.50, "duration_mins": 45},
    "Nitro": {"sol_cost": 4.50, "duration_mins": 60}
}

# Level 1 to 30 Matrix Generation
levels = np.arange(1, 31)
level_upgrade_costs = np.round(15 * (levels ** 1.35)).astype(int)
level_efficiency_mults = 1.0 + ((levels - 1) * 0.08)

df_leveling = pd.DataFrame({
    "Level": levels,
    "Token Cost to Upgrade": level_upgrade_costs,
    "Cumulative Cost to Reach": np.cumsum(level_upgrade_costs),
    "Yield Efficiency Mult": level_efficiency_mults
})

# --- TAB NAVIGATION ---
tab1, tab2, tab3, tab4 = st.tabs([
    "🏃 Tab 1: Live Workout Session Simulator",
    "🎲 Tab 2: Overnight Game Theory & Level-Up Gamble",
    "👟 Tab 3: Shoe Leveling (1-30) & Repair Matrix",
    "🏦 Tab 4: JitoSOL Pool Yield Accumulator"
])

# ==========================================
# TAB 1: WORKOUT SESSION SIMULATOR
# ==========================================
with tab1:
    st.subheader("1. Start-to-Finish Session Economics & Dynamic Sinks")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        energy_type = st.selectbox("Energy Type Input", list(ENERGY_TYPES.keys()), index=0)
        energy_sol = ENERGY_TYPES[energy_type]["sol_cost"]
        session_mins = ENERGY_TYPES[energy_type]["duration_mins"]
        shoe_level = st.slider("Shoe Level", 1, 30, 5)
        level_discount_per_lvl = st.slider("Base Repair Discount per Level (%)", 0.0, 2.0, 0.5, step=0.1, help="Reduces base repair % fee for each shoe level above Level 1.")
    with col2:
        target_margin_pct = st.slider("Target Initial ROI Margin (% Gain)", -20, 50, 15, help="Target potential gross return over input energy cost before wear & repair fees.")
        base_repair_pct = st.slider("Base Shoe Repair Fee (% of Gross Tokens)", 0.0, 30.0, 10.0, step=0.5, help="Base percentage of gross session tokens spent on standard repair.")
    with col3:
        voice_stations = st.slider("Voice Exercise Stations Completed", 0, 5, 3)
        station_wear_pct_per_station = st.slider("Additional Station Wear Fee (% per Station)", 0.0, 10.0, 2.0, step=0.5, help="Additional shoe wear fee per exercise station completed, as a % of gross tokens.")
        concurrent_users = st.number_input("Active Users in Daily Epoch Pool", value=1000, step=100)

    # 1. Calculate Effective Base Repair Fee % (Level Discount Applied)
    repair_level_reduction = (shoe_level - 1) * level_discount_per_lvl
    effective_base_repair_pct = max(0.0, base_repair_pct - repair_level_reduction)

    # 2. Gross Payout Calculation (Driven by Energy SOL + Target ROI Margin + Shoe Level Multiplier)
    level_mult = df_leveling.loc[df_leveling["Level"] == shoe_level, "Yield Efficiency Mult"].values[0]
    level_upgrade_cost_tokens = df_leveling.loc[df_leveling["Level"] == shoe_level, "Token Cost to Upgrade"].values[0]
    level_upgrade_cost_sol = level_upgrade_cost_tokens * token_price_sol

    gross_sol_target = energy_sol * (1.0 + (target_margin_pct / 100.0)) * level_mult
    gross_tokens_earned = gross_sol_target / token_price_sol if token_price_sol > 0 else 0
    gross_sol_payout = gross_tokens_earned * token_price_sol

    # 3. Dynamic Wear Deductions (% of Gross Tokens)
    base_repair_tokens = gross_tokens_earned * (effective_base_repair_pct / 100.0)
    station_wear_tokens = gross_tokens_earned * (station_wear_pct_per_station / 100.0) * voice_stations
    total_wear_tokens = base_repair_tokens + station_wear_tokens
    
    base_repair_sol = base_repair_tokens * token_price_sol
    station_wear_sol = station_wear_tokens * token_price_sol
    total_wear_sol = total_wear_tokens * token_price_sol

    # 4. Net Session Tokens & Immediate SOL Profitability
    net_tokens_earned = gross_tokens_earned - total_wear_tokens
    net_sol_payout = net_tokens_earned * token_price_sol

    # 5. Epoch Pool Claims (Only triggered if Voice Stations > 0)
    epoch_contribution_sol = energy_sol * 0.10
    total_epoch_pool_sol = epoch_contribution_sol * concurrent_users
    
    if voice_stations > 0:
        station_pool_bonus = 1.0 + (voice_stations * 0.05) # Base 1.0 + 5% per station
        user_epoch_share_pct = (station_pool_bonus / (concurrent_users * 1.0)) * 100
        user_epoch_claim_sol = total_epoch_pool_sol * (user_epoch_share_pct / 100.0)
    else:
        station_pool_bonus = 0.0
        user_epoch_share_pct = 0.0
        user_epoch_claim_sol = 0.0

    user_epoch_claim_tokens = user_epoch_claim_sol / token_price_sol if token_price_sol > 0 else 0

    # 6. Total 24-Hour Cycle Net Return (Including Level-Up Cost Sink)
    total_cycle_sol_return = net_sol_payout + user_epoch_claim_sol
    total_costs_and_sinks_sol = energy_sol + level_upgrade_cost_sol + total_wear_sol
    total_cycle_net_profit_sol = total_cycle_sol_return - (energy_sol + level_upgrade_cost_sol)
    total_cycle_net_roi_pct = (total_cycle_net_profit_sol / energy_sol) * 100 if energy_sol > 0 else 0

    st.markdown("---")
    st.markdown("### Session Financial Breakdown")

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Energy Cost", f"{energy_sol:.2f} SOL", f"${energy_sol * sol_price:.2f}")
    m2.metric("Gross Tokens Earned", f"{gross_tokens_earned:,.1f} Tokens", f"{gross_sol_payout:.3f} SOL (+{target_margin_pct}%)")
    m3.metric("Total Wear Fees", f"{total_wear_tokens:,.1f} Tokens", f"-{total_wear_sol:.3f} SOL ({((effective_base_repair_pct) + (station_wear_pct_per_station * voice_stations)):.1f}% Effective Fee)")
    m4.metric("Est. Epoch SOL Claim", f"{user_epoch_claim_sol:.4f} SOL", f"{user_epoch_share_pct:.3f}% of {total_epoch_pool_sol:.2f} SOL Pool" if voice_stations > 0 else "0 Stations = No Epoch Claim")

    st.markdown("---")
    st.markdown("### Cost Breakdown & Epoch Pool Trade-off (24-Hour Cycle)")
    
    col_b1, col_b2 = st.columns(2)
    with col_b1:
        st.write("**Itemized Session & Pool Earnings:**")
        st.write(f"• **1. Gross Tokens Earned:** `{gross_tokens_earned:,.1f}` Tokens (`{gross_sol_payout:.4f}` SOL)")
        st.write(f"• **2. Net Session Tokens (After Wear):** `{net_tokens_earned:,.1f}` Tokens (`{net_sol_payout:.4f}` SOL)")
        st.write(f"• **3. Est. Epoch Pool Payout:** `{user_epoch_claim_tokens:,.1f}` Tokens (`{user_epoch_claim_sol:.4f}` SOL)")
        
        st.markdown("---")
        st.write("**Total 24-Hour Cycle Returns:**")
        st.write(f"• **Total Revenue (Net Session + Epoch):** `{total_cycle_sol_return:.4f}` SOL (${total_cycle_sol_return * sol_price:.2f})")
        st.write(f"• **Net Profit / Loss:** `{total_cycle_net_profit_sol:+.4f}` SOL (${total_cycle_net_profit_sol * sol_price:+.2f})")
    
    with col_b2:
        st.write("**Maintenance, Station Wear & Level-Up Sinks:**")
        st.write(f"• **Base Repair Fee ({effective_base_repair_pct:.1f}%):** `{base_repair_tokens:,.1f}` Tokens ({base_repair_sol:.4f} SOL) *(Discounted from {base_repair_pct:.1f}% via Lvl {shoe_level})*")
        st.write(f"• **Station Wear ({station_wear_pct_per_station:.1f}% × {voice_stations}):** `{station_wear_tokens:,.1f}` Tokens ({station_wear_sol:.4f} SOL)")
        st.write(f"• **Level {shoe_level} Upgrade Cost:** `{level_upgrade_cost_tokens:,}` Tokens ({level_upgrade_cost_sol:.4f} SOL)")
        
        st.markdown("---")
        st.write("**Net 24-Hour Cycle ROI (vs Energy Input):**")
        if total_cycle_net_profit_sol >= 0:
            st.success(f"🟢 **Net 24h ROI:** **+{total_cycle_net_roi_pct:.2f}%** gain against input energy ({energy_sol:.2f} SOL)")
        else:
            st.error(f"🔴 **Net 24h ROI:** **{total_cycle_net_roi_pct:.2f}%** return against input energy ({energy_sol:.2f} SOL)")

# ==========================================
# TAB 2: OVERNIGHT GAME THEORY & GAMBLE
# ==========================================
with tab2:
    st.subheader("2. Athlete Decision Mechanics: Exercise & Level-Up Gambles")
    st.markdown("Athletes face two core strategic choices each day:")
    
    st.markdown("#### Choice 1: The Exercise Station Choice")
    st.write("Incur additional station wear fee today to boost claim on midnight pool reward.")
    
    g_col1, g_col2 = st.columns(2)
    with g_col1:
        st.metric("Up-Front Station Cost (Tokens)", f"{station_wear_tokens:,.1f} Tokens", f"-{station_wear_pct_per_station * voice_stations:.1f}% of gross tokens")
    with g_col2:
        st.metric("Midnight Epoch Pool Share", f"{user_epoch_claim_sol:.4f} SOL", f"{user_epoch_share_pct:.3f}% Pool Claim (+{voice_stations * 5}%)" if voice_stations > 0 else "No Stations = 0% Pool Claim")
        
    st.markdown("---")
    st.markdown("#### Choice 2: The Level-Up Timing Gamble")
    st.write("Upgrade today at current token price vs. hold tokens overnight and gamble on token price movement before upgrading tomorrow.")
    
    c_g1, c_g2, c_g3 = st.columns(3)
    with c_g1:
        target_upgrade_level = st.selectbox("Select Target Upgrade Level", np.arange(2, 31), index=4)
        tokens_required = df_leveling.loc[df_leveling["Level"] == target_upgrade_level, "Token Cost to Upgrade"].values[0]
    with c_g2:
        overnight_price_change_pct = st.slider("Simulated Overnight Token Price Change (%)", -50, 50, 10, step=5)
    with c_g3:
        st.write(f"**Tokens Required:** `{tokens_required:,}` Tokens")
    
    cost_today_sol = tokens_required * token_price_sol
    cost_today_usd = cost_today_sol * sol_price
    
    tomorrow_token_price_sol = token_price_sol * (1.0 + (overnight_price_change_pct / 100.0))
    cost_tomorrow_sol = tokens_required * tomorrow_token_price_sol
    cost_tomorrow_usd = cost_tomorrow_sol * sol_price
    
    diff_sol = cost_tomorrow_sol - cost_today_sol
    diff_usd = cost_tomorrow_usd - cost_today_usd

    m_u1, m_u2, m_u3 = st.columns(3)
    m_u1.metric("Upgrade Today Cost", f"{cost_today_sol:.3f} SOL", f"${cost_today_usd:.2f}")
    m_u2.metric(f"Upgrade Tomorrow Cost ({overnight_price_change_pct:+d}%)", f"{cost_tomorrow_sol:.3f} SOL", f"${cost_tomorrow_usd:.2f}")
    
    if diff_sol < 0:
        m_u3.metric("Gamble Outcome (Waiting)", f"{diff_sol:+.3f} SOL", f"Cheaper tomorrow by ${abs(diff_usd):.2f} (Tokens depreciated)", delta_color="normal")
    else:
        m_u3.metric("Gamble Outcome (Waiting)", f"{diff_sol:+.3f} SOL", f"More expensive by ${diff_usd:.2f} (Tokens appreciated)", delta_color="inverse")

    st.info("💡 **Strategy Insight:** If an athlete expects token prices to rise overnight, upgrading **today** locks in a lower SOL cost. If they expect token prices to drop, holding tokens and waiting until tomorrow lowers the relative SOL cost of leveling up.")

# ==========================================
# TAB 3: SHOE LEVELING (1 TO 30)
# ==========================================
with tab3:
    st.subheader("3. Shoe Leveling Matrix (Level 1 to 30)")
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
# TAB 4: JITOSOL POOL ACCUMULATOR
# ==========================================
with tab4:
    st.subheader("4. JitoSOL Reserve Pool Accumulator")
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