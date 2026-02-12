import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, date, time
from database import (
    init_db, insert_trade, get_all_trades, get_metrics, delete_trade,
    create_user, authenticate_user,
)
import io

init_db()

COMMANDMENTS = [
    "1. Only trade within the first 2 hours of market open",
    "2. Never risk more than 2% of account per trade",
    "3. Always wait for VWAP confirmation",
    "4. Respect the EMA alignment before entry",
    "5. Validate volume before pulling the trigger",
    "6. Honor your stop loss — no moving it",
    "7. Take profits at predetermined levels",
    "8. No revenge trading after a loss",
    "9. Walk away after 3 consecutive losses",
    "10. Review every trade before the next session",
]

NEON_GREEN = "#00FF7F"
ELECTRIC_BLUE = "#00D4FF"
CRIMSON_RED = "#FF3B3B"
DARK_BG = "#0E1117"
CARD_BG = "#1A1D23"

st.set_page_config(
    page_title="LUMAR Trading Journal",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(f"""
<style>
    .main .block-container {{
        padding-top: 1rem;
        max-width: 1400px;
    }}
    .metric-card {{
        background: {CARD_BG};
        border-radius: 12px;
        padding: 1.2rem;
        border: 1px solid #2A2D35;
        text-align: center;
    }}
    .metric-value {{
        font-size: 2rem;
        font-weight: 700;
        margin: 0.3rem 0;
    }}
    .metric-label {{
        font-size: 0.85rem;
        color: #888;
        text-transform: uppercase;
        letter-spacing: 1px;
    }}
    .green {{ color: {NEON_GREEN}; }}
    .blue {{ color: {ELECTRIC_BLUE}; }}
    .red {{ color: {CRIMSON_RED}; }}
    .header-title {{
        font-size: 2.2rem;
        font-weight: 800;
        background: linear-gradient(90deg, {NEON_GREEN}, {ELECTRIC_BLUE});
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0;
    }}
    .header-sub {{
        color: #666;
        font-size: 0.9rem;
        margin-top: 0;
    }}
    div[data-testid="stSidebar"] {{
        background: #0A0D12;
    }}
    .stTabs [data-baseweb="tab-list"] {{
        gap: 8px;
    }}
    .stTabs [data-baseweb="tab"] {{
        border-radius: 8px;
        padding: 8px 20px;
    }}
    .trade-win {{
        border-left: 3px solid {NEON_GREEN};
        padding-left: 10px;
    }}
    .trade-loss {{
        border-left: 3px solid {CRIMSON_RED};
        padding-left: 10px;
    }}
</style>
""", unsafe_allow_html=True)

if "user_id" not in st.session_state:
    st.session_state.user_id = None
if "username" not in st.session_state:
    st.session_state.username = None


def show_login_page():
    col_spacer1, col_center, col_spacer2 = st.columns([1, 2, 1])

    with col_center:
        st.markdown("<div style='text-align:center;'>", unsafe_allow_html=True)
        st.image("attached_assets/LOGO_LUMAR1-02_1770923649384.png", use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown(f"""
        <div style="text-align:center;margin-bottom:2rem;">
            <p class="header-title" style="font-size:1.8rem;">Welcome to Lumar Trading</p>
            <p class="header-sub">Your Professional NQ Futures Trading Journal</p>
        </div>
        """, unsafe_allow_html=True)

        login_tab, signup_tab = st.tabs(["Login", "Sign Up"])

        with login_tab:
            with st.form("login_form"):
                username = st.text_input("Username", key="login_user")
                password = st.text_input("Password", type="password", key="login_pass")
                submitted = st.form_submit_button("Login", type="primary", use_container_width=True)

                if submitted:
                    if not username or not password:
                        st.error("Please enter both username and password.")
                    else:
                        user_id = authenticate_user(username, password)
                        if user_id:
                            st.session_state.user_id = user_id
                            st.session_state.username = username
                            st.rerun()
                        else:
                            st.error("Invalid username or password.")

        with signup_tab:
            with st.form("signup_form"):
                new_username = st.text_input("Choose a Username", key="signup_user")
                new_password = st.text_input("Choose a Password", type="password", key="signup_pass")
                confirm_password = st.text_input("Confirm Password", type="password", key="signup_confirm")
                submitted = st.form_submit_button("Create Account", type="primary", use_container_width=True)

                if submitted:
                    if not new_username or not new_password:
                        st.error("Please fill in all fields.")
                    elif len(new_password) < 6:
                        st.error("Password must be at least 6 characters.")
                    elif new_password != confirm_password:
                        st.error("Passwords do not match.")
                    else:
                        user_id, error = create_user(new_username, new_password)
                        if user_id:
                            st.session_state.user_id = user_id
                            st.session_state.username = new_username
                            st.rerun()
                        else:
                            st.error(error)

        st.markdown("---")
        st.markdown(f"""
        <div style="text-align:center;">
            <a href="https://www.youtube.com/@lumartrading" target="_blank" style="text-decoration:none;">
                <span style="background:#FF0000;color:white;font-weight:600;font-size:0.9rem;padding:0.4rem 1rem;border-radius:6px;">📺 Join Lumar Trading Live</span>
            </a>
            &nbsp;&nbsp;
            <a href="https://www.lumartraders.com" target="_blank" style="text-decoration:none;">
                <span style="color:{ELECTRIC_BLUE};font-weight:600;font-size:0.9rem;padding:0.4rem 1rem;border-radius:6px;border:1px solid {ELECTRIC_BLUE};">🌐 Visit Official Website</span>
            </a>
        </div>
        """, unsafe_allow_html=True)

        st.markdown(f"""
        <div style="text-align:center;padding:1.5rem 0 0.5rem 0;">
            <span style="font-size:0.8rem;color:#555;">Powered by <strong style="color:{NEON_GREEN};">LUMAR Trading</strong> | Success is a Discipline</span>
        </div>
        """, unsafe_allow_html=True)


def show_main_app():
    user_id = st.session_state.user_id
    username = st.session_state.username

    st.markdown('<p class="header-title">LUMAR Trading Journal</p>', unsafe_allow_html=True)
    st.markdown('<p class="header-sub">Nasdaq NQ Futures — Strategy Tracker & Discipline Monitor</p>', unsafe_allow_html=True)
    st.markdown("---")

    tab_dashboard, tab_entry, tab_history, tab_export = st.tabs([
        "Dashboard", "New Trade", "Trade History", "Export Data"
    ])

    df = get_all_trades(user_id)
    metrics = get_metrics(df)

    with tab_dashboard:
        col1, col2, col3, col4 = st.columns(4)

        pnl_color = "green" if metrics["total_pnl"] >= 0 else "red"
        with col1:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Total Net P&L</div>
                <div class="metric-value {pnl_color}">${metrics['total_pnl']:,.2f}</div>
                <div style="color:#666;font-size:0.8rem;">{metrics['total_trades']} trades</div>
            </div>
            """, unsafe_allow_html=True)

        wr_color = "green" if metrics["win_rate"] >= 50 else "red"
        with col2:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Win Rate</div>
                <div class="metric-value {wr_color}">{metrics['win_rate']:.1f}%</div>
                <div style="color:#666;font-size:0.8rem;">{metrics['winning_trades']}W / {metrics['losing_trades']}L</div>
            </div>
            """, unsafe_allow_html=True)

        pf_val = metrics["profit_factor"]
        pf_display = f"{pf_val:.2f}" if pf_val != float("inf") else "∞"
        pf_color = "green" if pf_val >= 1 else "red"
        with col3:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Profit Factor</div>
                <div class="metric-value {pf_color}">{pf_display}</div>
                <div style="color:#666;font-size:0.8rem;">{"Good" if pf_val >= 1.5 else "Needs Work"}</div>
            </div>
            """, unsafe_allow_html=True)

        ds_color = "green" if metrics["discipline_score"] >= 70 else "blue" if metrics["discipline_score"] >= 50 else "red"
        with col4:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Discipline Score</div>
                <div class="metric-value {ds_color}">{metrics['discipline_score']:.1f}%</div>
                <div style="color:#666;font-size:0.8rem;">Commandments adherence</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("###")

        if not df.empty:
            col_chart1, col_chart2 = st.columns([2, 1])

            with col_chart1:
                st.markdown(f"#### Equity Curve")
                df_sorted = df.sort_values("timestamp")
                df_sorted["cumulative_pnl"] = df_sorted["pnl"].cumsum()

                fig_equity = go.Figure()
                fig_equity.add_trace(go.Scatter(
                    x=pd.to_datetime(df_sorted["timestamp"]),
                    y=df_sorted["cumulative_pnl"],
                    mode="lines+markers",
                    line=dict(color=NEON_GREEN, width=2),
                    marker=dict(size=6, color=ELECTRIC_BLUE),
                    fill="tozeroy",
                    fillcolor="rgba(0, 255, 127, 0.05)",
                    name="Equity",
                ))
                fig_equity.update_layout(
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                    font_color="#FAFAFA",
                    xaxis=dict(gridcolor="#1E2229", title="Date"),
                    yaxis=dict(gridcolor="#1E2229", title="Cumulative P&L ($)", tickprefix="$"),
                    margin=dict(l=20, r=20, t=20, b=20),
                    height=350,
                    hovermode="x unified",
                )
                st.plotly_chart(fig_equity, use_container_width=True)

            with col_chart2:
                st.markdown(f"#### P&L Distribution")
                colors = [NEON_GREEN if x > 0 else CRIMSON_RED for x in df_sorted["pnl"]]
                fig_bar = go.Figure()
                fig_bar.add_trace(go.Bar(
                    x=list(range(1, len(df_sorted) + 1)),
                    y=df_sorted["pnl"],
                    marker_color=colors,
                    name="P&L",
                ))
                fig_bar.update_layout(
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                    font_color="#FAFAFA",
                    xaxis=dict(gridcolor="#1E2229", title="Trade #"),
                    yaxis=dict(gridcolor="#1E2229", title="P&L ($)", tickprefix="$"),
                    margin=dict(l=20, r=20, t=20, b=20),
                    height=350,
                )
                st.plotly_chart(fig_bar, use_container_width=True)

            col_d1, col_d2 = st.columns(2)
            with col_d1:
                st.markdown(f"#### Discipline Over Time")
                fig_disc = go.Figure()
                fig_disc.add_trace(go.Scatter(
                    x=pd.to_datetime(df_sorted["timestamp"]),
                    y=df_sorted["discipline_score"],
                    mode="lines+markers",
                    line=dict(color=ELECTRIC_BLUE, width=2),
                    marker=dict(size=6),
                    name="Discipline",
                ))
                fig_disc.add_hline(y=70, line_dash="dash", line_color=NEON_GREEN, annotation_text="Target: 70%")
                fig_disc.update_layout(
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                    font_color="#FAFAFA",
                    xaxis=dict(gridcolor="#1E2229"),
                    yaxis=dict(gridcolor="#1E2229", title="Score (%)", range=[0, 105]),
                    margin=dict(l=20, r=20, t=20, b=20),
                    height=300,
                )
                st.plotly_chart(fig_disc, use_container_width=True)

            with col_d2:
                st.markdown(f"#### Win/Loss by Direction")
                dir_stats = df.groupby("direction").agg(
                    wins=("pnl", lambda x: (x > 0).sum()),
                    losses=("pnl", lambda x: (x <= 0).sum()),
                ).reset_index()

                fig_dir = go.Figure()
                fig_dir.add_trace(go.Bar(name="Wins", x=dir_stats["direction"], y=dir_stats["wins"], marker_color=NEON_GREEN))
                fig_dir.add_trace(go.Bar(name="Losses", x=dir_stats["direction"], y=dir_stats["losses"], marker_color=CRIMSON_RED))
                fig_dir.update_layout(
                    barmode="group",
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                    font_color="#FAFAFA",
                    xaxis=dict(gridcolor="#1E2229"),
                    yaxis=dict(gridcolor="#1E2229", title="Count"),
                    margin=dict(l=20, r=20, t=20, b=20),
                    height=300,
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                )
                st.plotly_chart(fig_dir, use_container_width=True)
        else:
            st.info("No trades recorded yet. Go to the **New Trade** tab to log your first trade.")

    with tab_entry:
        st.markdown("### Log a New Trade — *El Gatillo*")

        col_left, col_right = st.columns([1, 1])

        with col_left:
            st.markdown("#### Trade Details")
            trade_date = st.date_input("Date", value=date.today(), key="trade_date")
            trade_time = st.time_input("Time", value=datetime.now().time(), key="trade_time")

            col_a, col_b = st.columns(2)
            with col_a:
                asset = st.text_input("Asset", value="NQ", key="asset")
            with col_b:
                direction = st.selectbox("Direction", ["Long", "Short"], key="direction")

            st.markdown("#### LUMAR Strategy Checklist")
            vwap = st.selectbox("Price relative to VWAP", ["Above", "Below"], key="vwap")
            ema = st.selectbox("EMA Alignment", ["Confirmed", "Not Confirmed"], key="ema")
            volume = st.selectbox("Volume Validation", ["High", "Low"], key="volume")
            orb = st.selectbox("ORB Level", ["Inside", "Breakout"], key="orb")

        with col_right:
            st.markdown("#### Financials")
            col_e, col_x = st.columns(2)
            with col_e:
                entry_price = st.number_input("Entry Price", min_value=0.0, step=0.25, format="%.2f", key="entry_price")
            with col_x:
                exit_price = st.number_input("Exit Price", min_value=0.0, step=0.25, format="%.2f", key="exit_price")

            col_s, col_q = st.columns(2)
            with col_s:
                stop_loss = st.number_input("Stop Loss (points)", min_value=0.0, step=0.25, format="%.2f", key="stop_loss")
            with col_q:
                quantity = st.number_input("Quantity (contracts)", min_value=1, step=1, value=1, key="quantity")

            if entry_price > 0 and exit_price > 0:
                if direction == "Long":
                    preview_pnl = (exit_price - entry_price) * quantity
                else:
                    preview_pnl = (entry_price - exit_price) * quantity

                pnl_cls = "green" if preview_pnl >= 0 else "red"
                st.markdown(f"""
                <div class="metric-card" style="margin-top:0.5rem;">
                    <div class="metric-label">Estimated P&L</div>
                    <div class="metric-value {pnl_cls}">${preview_pnl:,.2f}</div>
                </div>
                """, unsafe_allow_html=True)

            st.markdown("#### Daily Reflection — The 10 Commandments")
            st.caption("Check the commandments that apply to this trade, then mark as Followed or Broken.")
            followed = []
            broken = []
            for cmd in COMMANDMENTS:
                col_check, col_cmd, col_status = st.columns([0.3, 2.7, 1])
                with col_check:
                    applies = st.checkbox("", key=f"chk_{cmd[:5]}", label_visibility="collapsed")
                with col_cmd:
                    st.markdown(f"<span style='font-size:0.85rem;'>{cmd}</span>", unsafe_allow_html=True)
                with col_status:
                    if applies:
                        status = st.selectbox("", ["Followed", "Broken"], key=f"cmd_{cmd[:5]}", label_visibility="collapsed")
                        if status == "Followed":
                            followed.append(cmd)
                        else:
                            broken.append(cmd)
                    else:
                        st.markdown("<span style='color:#555;font-size:0.8rem;'>N/A</span>", unsafe_allow_html=True)

            emotional_notes = st.text_area(
                "Notes on Emotional State",
                placeholder="How did you feel? E.g., 'I felt anxious before entry but stayed disciplined...'",
                key="emotional_notes",
            )

        st.markdown("---")

        checklist_valid = all([
            vwap in ["Above", "Below"],
            ema in ["Confirmed", "Not Confirmed"],
            volume in ["High", "Low"],
            orb in ["Inside", "Breakout"],
        ])

        if st.button("Save Trade", type="primary", use_container_width=True):
            if entry_price <= 0 or exit_price <= 0:
                st.error("Entry and Exit prices must be greater than 0.")
            elif stop_loss <= 0:
                st.error("Stop Loss must be greater than 0.")
            elif not checklist_valid:
                st.error("Please complete the LUMAR Strategy Checklist before saving.")
            else:
                timestamp = datetime.combine(trade_date, trade_time).isoformat()
                trade_data = {
                    "timestamp": timestamp,
                    "asset": asset,
                    "direction": direction,
                    "entry_price": entry_price,
                    "exit_price": exit_price,
                    "stop_loss": stop_loss,
                    "quantity": quantity,
                    "vwap_position": vwap,
                    "ema_alignment": ema,
                    "volume_validation": volume,
                    "orb_level": orb,
                    "commandments_followed": followed,
                    "commandments_broken": broken,
                    "emotional_notes": emotional_notes,
                }
                pnl, disc = insert_trade(user_id, trade_data)
                pnl_label = f"${pnl:,.2f}"
                if pnl >= 0:
                    st.success(f"Trade saved! P&L: **{pnl_label}** | Discipline: **{disc:.1f}%**")
                else:
                    st.warning(f"Trade saved. P&L: **{pnl_label}** | Discipline: **{disc:.1f}%**")
                st.rerun()

    with tab_history:
        st.markdown("### Trade History")

        if not df.empty:
            col_filter1, col_filter2, col_filter3 = st.columns(3)
            with col_filter1:
                dir_filter = st.selectbox("Filter by Direction", ["All", "Long", "Short"], key="dir_filter")
            with col_filter2:
                result_filter = st.selectbox("Filter by Result", ["All", "Winners", "Losers"], key="result_filter")
            with col_filter3:
                sort_by = st.selectbox("Sort by", ["Date (Newest)", "Date (Oldest)", "P&L (High)", "P&L (Low)"], key="sort_by")

            filtered = df.copy()
            if dir_filter != "All":
                filtered = filtered[filtered["direction"] == dir_filter]
            if result_filter == "Winners":
                filtered = filtered[filtered["pnl"] > 0]
            elif result_filter == "Losers":
                filtered = filtered[filtered["pnl"] <= 0]

            if sort_by == "Date (Newest)":
                filtered = filtered.sort_values("timestamp", ascending=False)
            elif sort_by == "Date (Oldest)":
                filtered = filtered.sort_values("timestamp", ascending=True)
            elif sort_by == "P&L (High)":
                filtered = filtered.sort_values("pnl", ascending=False)
            else:
                filtered = filtered.sort_values("pnl", ascending=True)

            st.markdown(f"Showing **{len(filtered)}** of **{len(df)}** trades")

            for _, row in filtered.iterrows():
                pnl_val = row["pnl"]
                icon = "▲" if row["direction"] == "Long" else "▼"
                border_color = NEON_GREEN if pnl_val > 0 else CRIMSON_RED

                st.markdown(f'<div style="border-left:3px solid {border_color};padding-left:4px;margin-bottom:2px;">', unsafe_allow_html=True)
                with st.expander(
                    f"{icon} {row['asset']} {row['direction']} — "
                    f"P&L: ${pnl_val:,.2f} — "
                    f"{row['timestamp'][:16]}"
                ):
                    c1, c2, c3, c4 = st.columns(4)
                    c1.metric("Entry", f"${row['entry_price']:,.2f}")
                    c2.metric("Exit", f"${row['exit_price']:,.2f}")
                    c3.metric("Stop Loss", f"{row['stop_loss']:.2f} pts")
                    c4.metric("Qty", row["quantity"])

                    c5, c6, c7, c8 = st.columns(4)
                    c5.markdown(f"**VWAP:** {row['vwap_position']}")
                    c6.markdown(f"**EMA:** {row['ema_alignment']}")
                    c7.markdown(f"**Volume:** {row['volume_validation']}")
                    c8.markdown(f"**ORB:** {row['orb_level']}")

                    disc_val = row.get("discipline_score", 0)
                    st.progress(min(disc_val / 100, 1.0), text=f"Discipline Score: {disc_val:.1f}%")

                    if row.get("commandments_followed"):
                        st.markdown(f"**Followed:** {row['commandments_followed']}")
                    if row.get("commandments_broken"):
                        st.markdown(f"**Broken:** <span style='color:{CRIMSON_RED}'>{row['commandments_broken']}</span>", unsafe_allow_html=True)
                    if row.get("emotional_notes"):
                        st.markdown(f"**Notes:** _{row['emotional_notes']}_")

                    if st.button(f"Delete Trade", key=f"del_{row['id']}"):
                        delete_trade(row["id"], user_id)
                        st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.info("No trades to display. Start logging trades in the **New Trade** tab.")

    with tab_export:
        st.markdown("### Export & Backup")

        if not df.empty:
            col_exp1, col_exp2 = st.columns(2)

            with col_exp1:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-label">Total Records</div>
                    <div class="metric-value blue">{len(df)}</div>
                </div>
                """, unsafe_allow_html=True)

            with col_exp2:
                date_range = ""
                if not df.empty:
                    dates = pd.to_datetime(df["timestamp"])
                    date_range = f"{dates.min().strftime('%b %d, %Y')} — {dates.max().strftime('%b %d, %Y')}"
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-label">Date Range</div>
                    <div class="metric-value blue" style="font-size:1.2rem;">{date_range}</div>
                </div>
                """, unsafe_allow_html=True)

            st.markdown("###")

            csv_buffer = io.StringIO()
            export_df = df.drop(columns=["id", "user_id"], errors="ignore")
            export_df.to_csv(csv_buffer, index=False)
            csv_data = csv_buffer.getvalue()

            st.download_button(
                label="Export to CSV",
                data=csv_data,
                file_name=f"lumar_trades_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
                type="primary",
                use_container_width=True,
            )

            st.markdown("###")
            st.markdown("#### Data Preview")
            preview_df = df[["timestamp", "asset", "direction", "entry_price", "exit_price", "pnl", "discipline_score"]].copy()
            preview_df.columns = ["Date/Time", "Asset", "Direction", "Entry", "Exit", "P&L", "Discipline %"]
            st.dataframe(preview_df, use_container_width=True, hide_index=True)
        else:
            st.info("No data to export. Start logging trades first.")

    st.markdown("---")
    st.markdown(f"""
    <div style="text-align:center;padding:1rem 0 0.5rem 0;">
        <span style="font-size:0.8rem;color:#555;">Powered by <strong style="color:{NEON_GREEN};">LUMAR Trading</strong> | Success is a Discipline</span>
    </div>
    """, unsafe_allow_html=True)

    with st.sidebar:
        # REPLACE WITH LUMAR LOGO URL
        st.image("attached_assets/LOGO_LUMAR1-17_1770923340855.png", use_container_width=True)

        st.markdown(f"""
        <div style="background:{CARD_BG};border-radius:8px;padding:0.8rem;margin-bottom:0.8rem;text-align:center;">
            <span style="color:#888;font-size:0.75rem;">Logged in as</span><br>
            <span style="color:{NEON_GREEN};font-weight:700;font-size:1.1rem;">{username}</span>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div style="background:#1A1D23;border:2px solid #FF0000;border-radius:10px;padding:1rem;margin-bottom:0.5rem;text-align:center;">
            <p style="font-size:0.8rem;color:#888;margin:0 0 0.5rem 0;text-transform:uppercase;letter-spacing:1px;">Community & Live Sessions</p>
            <a href="https://www.youtube.com/@lumartrading" target="_blank" style="text-decoration:none;">
                <div style="background:#FF0000;color:white;font-weight:700;font-size:1rem;padding:0.6rem 1rem;border-radius:8px;cursor:pointer;transition:opacity 0.2s;">
                    📺 Join Lumar Trading Live
                </div>
            </a>
            <p style="font-size:0.75rem;color:#AAA;margin:0.5rem 0 0 0;font-style:italic;">Trade NQ futures live with Marcio and the team!</p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown(f"""
        <div style="text-align:center;margin-bottom:1rem;">
            <a href="https://www.lumartraders.com" target="_blank" style="text-decoration:none;">
                <div style="background:transparent;color:{ELECTRIC_BLUE};font-weight:600;font-size:0.95rem;padding:0.5rem 1rem;border-radius:8px;border:2px solid {ELECTRIC_BLUE};cursor:pointer;">
                    🌐 Visit Official Website
                </div>
            </a>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("---")

        st.markdown("##### Quick Stats")
        if not df.empty:
            st.markdown(f"Total Trades: **{metrics['total_trades']}**")
            pnl_display = f"${metrics['total_pnl']:,.2f}"
            st.markdown(f"Net P&L: **{pnl_display}**")
            st.markdown(f"Win Rate: **{metrics['win_rate']:.1f}%**")
            st.markdown(f"Discipline: **{metrics['discipline_score']:.1f}%**")

            st.markdown("---")
            st.markdown("##### Recent Trades")
            recent = df.head(5)
            for _, r in recent.iterrows():
                icon = "🟢" if r["pnl"] > 0 else "🔴"
                st.markdown(f"{icon} {r['direction']} ${r['pnl']:,.2f}")
        else:
            st.markdown("*No trades yet*")

        st.markdown("---")
        st.markdown("##### The 10 Commandments")
        for i, cmd in enumerate(COMMANDMENTS, 1):
            st.markdown(f"<span style='font-size:0.75rem;color:#888;'>{cmd}</span>", unsafe_allow_html=True)

        st.markdown("---")
        if st.button("Logout", use_container_width=True):
            st.session_state.user_id = None
            st.session_state.username = None
            st.rerun()


if st.session_state.user_id is None:
    show_login_page()
else:
    show_main_app()
