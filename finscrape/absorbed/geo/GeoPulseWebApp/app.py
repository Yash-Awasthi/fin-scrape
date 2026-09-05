import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import json
import re
from openai import OpenAI
from datetime import datetime
import os
import time
import tempfile
from pyvis.network import Network
from collections import Counter


from src.utils import get_color, create_gauge
from src.api import fetch_analysis, fetch_global_rankings, fetch_market_risk, generate_dynamic_graph_data, expand_dynamic_graph_data, run_oasis_panic_simulation, CAMEL_AVAILABLE
from src.graph import generate_impact_network


# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="GeoPulse | Strategic Intelligence",
    page_icon="📡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CSS STYLING ---
st.markdown("""
    <style>
    .metric-card {
        background-color: #ffffff;
        border: 1px solid #e0e0e0;
        border-radius: 12px;
        padding: 20px;
        text-align: center;
        box-shadow: 0px 4px 12px rgba(0,0,0,0.05);
        height: 100%;
        transition: transform 0.2s;
    }
    .metric-card:hover { transform: translateY(-2px); }
    
    .big-stat { font-size: 32px; font-weight: 700; margin-bottom: 0px; color: #2c3e50; }
    .sub-stat { font-size: 14px; font-weight: 600; margin-bottom: 5px; }
    .stat-label { font-size: 12px; color: #7f8c8d; text-transform: uppercase; letter-spacing: 1px; font-weight: 600; margin-top: 5px;}
    
    .trend-bad { color: #c0392b; }
    .trend-good { color: #27ae60; }
    .trend-neutral { color: #7f8c8d; }
    
    .news-item { padding: 12px 0; border-bottom: 1px solid #f1f1f1; }
    .news-title { font-weight: 600; font-size: 15px; color: #2c3e50; margin-bottom: 4px; }
    .news-date { font-size: 11px; color: #95a5a6; }
    
    .risk-high { background-color: #ffebee; color: #c62828; padding: 2px 6px; border-radius: 4px; font-weight: bold; }
    .risk-med { background-color: #fff3e0; color: #ef6c00; padding: 2px 6px; border-radius: 4px; font-weight: bold; }
    .risk-low { background-color: #e8f5e9; color: #2e7d32; padding: 2px 6px; border-radius: 4px; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- HELPER FUNCTIONS ---

# --- SIDEBAR ---
with st.sidebar:
    col1, col2 = st.columns([1, 2.5])
    with col1: st.image("assets/logo.png", width=70)
    with col2: st.markdown("<h2 style='margin:0; padding-top:10px; font-size:1.8em;'>GeoPulse</h2><div style='color:gray; font-size:0.8em; margin-top:-5px;'>Strategic Intelligence</div>", unsafe_allow_html=True)
    
    st.markdown("<div style='margin-top: 15px; margin-bottom: 5px; font-weight: 600;'>⚙️ Model Configuration</div>", unsafe_allow_html=True)
    provider = st.selectbox("LLM Provider", ["Perplexity", "Google", "OpenAI", "DeepSeek"], label_visibility="collapsed")
    
    if provider == "Perplexity":
        model_options = ["sonar-pro", "sonar"]
        base_url = "https://api.perplexity.ai"
    elif provider == "Google":
        model_options = ["gemini-2.5-flash", "gemini-2.5-pro", "gemini-1.5-flash", "gemini-1.5-pro"]
        base_url = "https://generativelanguage.googleapis.com/v1beta/openai/"
    elif provider == "OpenAI":
        model_options = ["gpt-4o", "gpt-4o-mini", "o1-mini"]
        base_url = None
    elif provider == "DeepSeek":
        model_options = ["deepseek-chat", "deepseek-reasoner"]
        base_url = "https://api.deepseek.com"
        
    selected_model = st.selectbox("Model", model_options, label_visibility="collapsed")
    
    online_models = ["sonar-pro", "sonar"]
    if selected_model not in online_models:
        st.markdown("<div style='font-size: 0.75em; color: #d35400; background-color: #fcf3cf; padding: 6px; border-radius: 4px; margin-bottom: 5px; margin-top: -5px;'>⚠️ <b>Offline Model:</b> Analysis relies on last training data cutoff.</div>", unsafe_allow_html=True)
        
    api_key = st.text_input(f"API Key", type="password", placeholder=f"{provider} API Key")
    st.markdown("<div style='font-size: 0.7em; color: #7f8c8d; margin-top: -10px; margin-bottom: 15px; line-height: 1.2;'>🔒 <b>Privacy:</b> Key is kept in local session memory. We do not store or log it.</div>", unsafe_allow_html=True)
    
    page = st.radio("Module", ["📡 Regional Monitor", "📊 Global Heatmap", "📈 Market Watchdog", "🦢 Black Swan Events"], label_visibility="collapsed")

    st.markdown("""
        <div style="padding: 10px; border-radius: 10px; background-color: #f0f2f6; border: 1px solid #e0e0e0;">
            <p style="margin-bottom: 5px; font-size: 0.85em; color: #7f8c8d; font-weight: 700;">DEVELOPER</p>
            <p style="margin-bottom: 10px; font-weight: 600; color: #2c3e50;">Jayshil Jain</p>
            <div style="display: flex; gap: 10px;">
                <a href="https://github.com/jayshilj/GeoPulseWebApp" target="_blank"><img src="https://img.icons8.com/material-outlined/24/000000/github.png"/></a>
                <a href="https://www.linkedin.com/in/jayshiljain/" target="_blank"><img src="https://img.icons8.com/material-outlined/24/000000/linkedin--v1.png"/></a>
                <a href="https://www.jayshil.com/" target="_blank"><img src="https://img.icons8.com/material-outlined/24/000000/globe.png"/></a>
            </div>
        </div>
    """, unsafe_allow_html=True)

# --- PAGE 1: REGIONAL MONITOR ---
if page == "📡 Regional Monitor":
    st.title("📡 Regional Analysis")
    st.markdown("Real-time diplomatic assessment with historical comparison.")
    
    with st.container():
        c1, c2, c3 = st.columns([2, 2, 1])
        with c1: country_a = st.text_input("Entity A", "USA")
        with c2: country_b = st.text_input("Entity B", "India")
        with c3: 
            st.markdown("---")
            btn = st.button("Initialize Scan", type="primary", width="stretch")

    if 'regional_scan_data' not in st.session_state:
        st.session_state['regional_scan_data'] = None
    if 'regional_scan_entities' not in st.session_state:
        st.session_state['regional_scan_entities'] = None

    if btn:
        if not api_key:
            st.warning("Please enter your API Key in the sidebar.")
        else:
            with st.spinner("Retrieving historical cables & current intel..."):
                data = fetch_analysis(country_a, country_b, api_key, base_url, selected_model)
            
            if "error" in data:
                st.error(f"Error: {data['error']}")
                st.session_state['regional_scan_data'] = None
                st.session_state['regional_scan_entities'] = None
            else:
                st.session_state['regional_scan_data'] = data
                st.session_state['regional_scan_entities'] = (country_a, country_b)

    if st.session_state['regional_scan_data']:
        data = st.session_state['regional_scan_data']
        scanned_a, scanned_b = st.session_state['regional_scan_entities']
        
        # Extract Data
        flag1 = data.get('c1_flag', '')
        flag2 = data.get('c2_flag', '')
        curr = data.get('score_current', 0)
        past = data.get('score_past', 0)
        
        # Calculate Change
        diff = curr - past
        if diff > 0:
            trend_str = f"⬆ +{diff} (Worsening)"
            trend_cls = "trend-bad"
        elif diff < 0:
            trend_str = f"⬇ {diff} (Improving)"
            trend_cls = "trend-good"
        else:
            trend_str = "No Change"
            trend_cls = "trend-neutral"

        # 1. Header
        st.markdown(f"""
        <div style="text-align: center; margin-bottom: 25px;">
            <h1 style="margin:0; font-size: 2.5rem;">{flag1} {scanned_a.upper()} <span style="color:#bdc3c7;">&</span> {scanned_b.upper()} {flag2}</h1>
        </div>
        """, unsafe_allow_html=True)
        
        # 2. Main Dashboard
        col_left, col_mid, col_right = st.columns([1.5, 1, 1])
        
        with col_left:
            # Gauge now shows Delta automatically via Plotly
            st.plotly_chart(create_gauge(curr, past), width="stretch")
        
        with col_mid:
            st.markdown(f"""
            <div class="metric-card">
                <div class="stat-label">YoY Change (1 Year)</div>
                <div class="sub-stat {trend_cls}">{trend_str}</div>
                <div style="font-size: 13px; color: #555; margin-top: 5px;">
                    <i>"{data.get('change_reason', 'N/A')}"</i>
                </div>
                <hr style="margin: 10px 0; opacity: 0.3;">
                <div class="stat-label">Primary Driver</div>
                <div style="font-weight: 600; color: #2c3e50;">{data.get('main_driver', 'N/A')}</div>
            </div>
            """, unsafe_allow_html=True)
            
        with col_right:
            # Trade
            def_raw = data.get('trade_deficit', 'N/A')
            if isinstance(def_raw, (int, float)): val = f"${def_raw} B"
            else: val = str(def_raw).replace(" billion", "B")
            
            st.markdown(f"""
            <div class="metric-card">
                <div class="stat-label">Est. Trade Deficit</div>
                <div class="big-stat">{val}</div>
                <div class="stat-label" style="margin-top:0;">{data.get('trade_context', '')}</div>
                <div style="font-size: 10px; color: #95a5a6; margin-top: 8px;">⚠️ Estimated by AI - Verify with World Bank</div>
            </div>
            """, unsafe_allow_html=True)

        # 3. Summary & News
        st.divider()
        col_sum, col_news = st.columns([1.2, 1])
        
        with col_sum:
            st.subheader("📝 Strategic Assessment")
            st.info(data.get('summary', ''))
            st.caption(f"Historical comparison baseline: {datetime.now().year - 1}")

        with col_news:
            st.subheader("📰 Intelligence Feed")
            for item in data.get('news', []):
                st.markdown(f"""
                <div class="news-item">
                    <div class="news-title">🔹 {item.get('title')}</div>
                    <div class="news-date">{item.get('source')} • {item.get('date')}</div>
                </div>
                """, unsafe_allow_html=True)

# --- PAGE 2: GLOBAL HEATMAP ---
elif page == "📊 Global Heatmap":
    st.title("📊 Global Heatmap")
    
    if not api_key:
        st.warning("API Key required.")
    else:
        # Refresh logic
        col_r1, col_r2 = st.columns([4, 1])
        with col_r2:
            if st.button("🔄 Refresh Data"):
                st.session_state.pop('rankings', None)
                st.rerun()
        
        if "rankings" not in st.session_state:
            with st.spinner("Scanning global datasets..."):
                st.session_state.rankings = fetch_global_rankings(api_key, base_url, selected_model)
        
        ranks = st.session_state.rankings
        if ranks:
            tab1, tab2 = st.tabs(["🔥 Flashpoints (High Tension)", "🕊️ Stable Zones"])
            
            with tab1:
                st.dataframe(pd.DataFrame(ranks.get('highest_pressure', [])), 
                             column_config={"score": st.column_config.ProgressColumn("Tension", min_value=0, max_value=100, format="%d")},
                             hide_index=True, width="stretch")
            with tab2:
                st.dataframe(pd.DataFrame(ranks.get('lowest_pressure', [])),
                             column_config={"score": st.column_config.ProgressColumn("Tension", min_value=0, max_value=100, format="%d")},
                             hide_index=True, width="stretch")

# --- PAGE 3: MARKET WATCHDOG (NEW) ---
elif page == "📈 Market Watchdog":
    st.title("📈 Commodity Risk Watchdog")
    st.markdown("Analyze how geopolitical tension in top producing nations impacts commodity prices.")
    
    if not api_key:
        st.warning("Please enter your API Key in the sidebar.")
    else:
        # 1. Selection Controls
        col_input, col_btn = st.columns([3, 1])
        with col_input:
            commodity_choice = st.selectbox(
                "Select Commodity to Track:", 
                ["Crude Oil", "Natural Gas", "Gold", "Silver", "Semiconductors (Chips)", "Lithium"]
            )
        with col_btn:
            st.markdown("---")
            scan_market = st.button("Analyze Risk", type="primary", width="stretch")
            
        if scan_market:
            with st.spinner(f"Analyzing supply chains for {commodity_choice}..."):
                market_data = fetch_market_risk(commodity_choice, api_key, base_url, selected_model)
                
            if "error" in market_data:
                st.error(market_data['error'])
            else:
                # 2. Key Metrics Row
                m1, m2, m3 = st.columns(3)
                
                # Risk Score Coloring
                risk_score = market_data.get('global_risk_score', 0)
                risk_color = "green" if risk_score < 40 else "orange" if risk_score < 70 else "red"
                
                # Outlook Coloring
                outlook = market_data.get('price_outlook', 'Neutral')
                outlook_color = "red" if "Bullish" in outlook else "green" # Bullish usually means prices up (bad for buyers)
                
                with m1:
                    st.metric(label="Global Supply Chain Risk", value=f"{risk_score}/100")
                    st.progress(risk_score)
                with m2:
                    st.metric(label="Price Outlook (Geopolitical)", value=outlook)
                with m3:
                    st.caption("Analyst Note:")
                    st.write(f"_{market_data.get('outlook_reason', 'No data')}_")
                
                st.divider()
                
                # 3. Tabbed Detail View
                tab_prod, tab_refin, tab_choke = st.tabs(["🌍 Top Producers", "🏭 Top Refiners", "🚢 Logistical Choke Points"])
                
                with tab_prod:
                    st.subheader("🌍 Key Producers & Tension Levels")
                    producer_source = market_data.get('producer_source', 'Unknown Source')
                    if producer_source != "Unknown Source":
                        st.caption(f"**Data Source:** {producer_source}")
                        
                    producers = market_data.get('top_producers', [])
                    if producers:
                        for p in producers:
                            t_score = p.get('tension_index', 0)
                            if t_score > 75: badge = "🔴 CRITICAL"
                            elif t_score > 50: badge = "🟠 HIGH"
                            else: badge = "🟢 STABLE"
                            st.markdown(f"""
                            <div style="background-color: #f8f9fa; padding: 15px; border-radius: 10px; margin-bottom: 10px; border-left: 5px solid {get_color(t_score)}">
                                <div style="display:flex; justify-content:space-between; align-items:center;">
                                    <h4 style="margin:0;">{p.get('country')}</h4>
                                    <span style="font-size:0.9em; background:#eee; padding:3px 8px; border-radius:5px;">Share: {p.get('production_share')}</span>
                                </div>
                                <div style="margin-top: 8px; font-size: 0.95em;">
                                    <b>Tension Score:</b> {t_score} &nbsp;|&nbsp; <b>Status:</b> {badge}
                                </div>
                                <div style="margin-top: 5px; color: #666; font-size: 0.9em;">
                                    ⚠️ <i>Risk Factor: {p.get('risk_note')}</i>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                    else:
                        st.info("No producer data found.")
                        
                with tab_refin:
                    st.subheader("🏭 Key Refiners/Processors & Tension Levels")
                    refiner_source = market_data.get('refiner_source', 'Unknown Source')
                    if refiner_source != "Unknown Source":
                        st.caption(f"**Data Source:** {refiner_source}")
                        
                    refiners = market_data.get('top_refiners', [])
                    if refiners:
                        for r in refiners:
                            t_score = r.get('tension_index', 0)
                            if t_score > 75: badge = "🔴 CRITICAL"
                            elif t_score > 50: badge = "🟠 HIGH"
                            else: badge = "🟢 STABLE"
                            st.markdown(f"""
                            <div style="background-color: #f8f9fa; padding: 15px; border-radius: 10px; margin-bottom: 10px; border-left: 5px solid {get_color(t_score)}">
                                <div style="display:flex; justify-content:space-between; align-items:center;">
                                    <h4 style="margin:0;">{r.get('country')}</h4>
                                    <span style="font-size:0.9em; background:#eee; padding:3px 8px; border-radius:5px;">Share: {r.get('production_share')}</span>
                                </div>
                                <div style="margin-top: 8px; font-size: 0.95em;">
                                    <b>Tension Score:</b> {t_score} &nbsp;|&nbsp; <b>Status:</b> {badge}
                                </div>
                                <div style="margin-top: 5px; color: #666; font-size: 0.9em;">
                                    ⚠️ <i>Risk Factor: {r.get('risk_note')}</i>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                    else:
                        st.info("No refiner data found.")
                
                with tab_choke:
                    st.subheader("🚢 Global Choke Point Analysis")
                    choke_point_source = market_data.get('choke_point_source', 'Unknown Source')
                    if choke_point_source != "Unknown Source":
                        st.caption(f"**Data Source:** {choke_point_source}")
                        
                    choke_points = market_data.get('choke_points', [])
                    if choke_points:
                        for cp in choke_points:
                            c_score = cp.get('threat_score', 0)
                            vol = cp.get('volume_flow', 'N/A')
                            if cp.get('reliance_level') == 'High': rel_color = '#c0392b'
                            elif cp.get('reliance_level') == 'Medium': rel_color = '#f39c12'
                            else: rel_color = '#27ae60'
                            st.markdown(f"""
                            <div class="metric-card" style="margin-bottom: 15px; text-align: left; border-left: 5px solid {get_color(c_score)};">
                                <div style="display:flex; justify-content:space-between; align-items:flex-start;">
                                    <h4 style="margin-top: 0; margin-bottom: 8px;">{cp.get('name')}</h4>
                                    <span style="background: #eef2ff; color: #3b5bdb; font-size: 0.85em; font-weight: 700; padding: 3px 10px; border-radius: 20px; white-space: nowrap;">📦 {vol}</span>
                                </div>
                                <div style="font-size: 0.9em; margin-bottom: 10px;">
                                    <b>Reliance:</b> <span style="color: {rel_color}; font-weight: 700;">{cp.get('reliance_level')}</span>
                                    &nbsp;|&nbsp;
                                    <b>Threat Score:</b> {c_score}/100
                                </div>
                                <p style="color: #555; font-size: 0.9em; margin-bottom: 0;">{cp.get('current_threat')}</p>
                            </div>
                            """, unsafe_allow_html=True)
                    else:
                        st.info("No choke point data analyzed.")

# --- PAGE 4: BLACK SWAN EVENTS (NEW) ---
elif page == "🦢 Black Swan Events":
    st.title("🦢 Black Swan Simulator")
    st.markdown("Visualize the impact of catastrophic geopolitical shocks on global trade routes and logistical flows.")

    # Layout Setup
    col_controls = st.container()
    
    # 1. Simulator Controls
    with col_controls:
        st.markdown("""
        <div style="background-color: #f8f9fa; border: 1px solid #e0e0e0; border-radius: 12px; padding: 20px; box-shadow: 0px 4px 12px rgba(0,0,0,0.05); margin-bottom: 15px;">
            <h3 style="margin-top:0; color:#2c3e50; font-size: 1.25rem;">🛠️ Scenario Config</h3>
            <p style="font-size: 0.9em; color: #7f8c8d; margin-bottom: 5px;">Select a global choke point to disrupt and simulate the cascading impacts.</p>
        </div>
        """, unsafe_allow_html=True)
        
        scenario = st.selectbox(
            "Select Global Shock:",
            [
                "Baseline (Clear Skies)",
                "Suez Canal Total Blockage",
                "Strait of Hormuz Closure",
                "Malacca Strait Conflict",
                "Panama Canal Drought/Shutdown",
                "Custom Event"
            ],
            label_visibility="collapsed"
        )
        
        custom_scenario_text = ""
        if scenario == "Custom Event":
            custom_scenario_text = st.text_input("Enter Custom Event:", placeholder="e.g. Global Internet Outage")
        
        # We define a variable to hold the effective scenario name
        effective_scenario = custom_scenario_text if scenario == "Custom Event" and custom_scenario_text else scenario
        
        st.markdown("---")
        run_sim = st.button("🚀 Execute Scenario", type="primary", width='stretch')
        
        # Initialize graph session state
        if 'bs_graph_data' not in st.session_state:
            st.session_state['bs_graph_data'] = None
        if 'bs_graph_iterations' not in st.session_state:
            st.session_state['bs_graph_iterations'] = 0
        if 'bs_scenario' not in st.session_state:
            st.session_state['bs_scenario'] = None
        if 'bs_model_key' not in st.session_state:
            st.session_state['bs_model_key'] = None
        
        # Invalidate graph if scenario, provider, or model changes
        current_model_key = f"{provider}:{selected_model}"
        if (run_sim
                or st.session_state['bs_scenario'] != effective_scenario
                or st.session_state['bs_model_key'] != current_model_key):
            st.session_state['bs_graph_data'] = None
            st.session_state['bs_graph_iterations'] = 0
            st.session_state['bs_scenario'] = effective_scenario
            st.session_state['bs_model_key'] = current_model_key
        
        st.markdown("""
        <div style="margin-top: 20px; padding: 15px; background-color: #fff3e0; border-left: 4px solid #ef6c00; border-radius: 4px;">
            <span style="color: #e65100; font-weight: bold; font-size: 0.9em;">Simulation Engine Active</span><br>
            <span style="color: #555; font-size: 0.8em;">Powered by GeoPulse & CAMEL-AI</span>
        </div>
        """, unsafe_allow_html=True)
        
    # 2. Disruption Logic
    blocked_cp = None
    if scenario == "Suez Canal Total Blockage": blocked_cp = "Suez Canal"
    elif scenario == "Strait of Hormuz Closure": blocked_cp = "Strait of Hormuz"
    elif scenario == "Malacca Strait Conflict": blocked_cp = "Strait of Malacca"
    elif scenario == "Panama Canal Drought/Shutdown": blocked_cp = "Panama Canal"

    # 3. Interactive Network Graph ---
    st.markdown("---")
    st.markdown("#### 🔗 Interactive Relationship Graph")
    if effective_scenario and effective_scenario != "Baseline (Clear Skies)":
        # Guard: require API key before attempting any graph generation
        if not api_key:
            st.warning("⚠️ **API Key Required** — Please configure your API key in the sidebar (⚙️ Model Configuration) to generate the interactive supply chain graph.")
        else:
            # 1. Ensure Initial Data Exists
            if run_sim and not st.session_state.get('bs_graph_data'):
                with st.spinner(f"AI is modeling initial supply chain reactions..."):
                    st.session_state['bs_graph_data'] = generate_dynamic_graph_data(effective_scenario, api_key, base_url, selected_model)

            # 2. Render UI Controls
            col_title, col_btn = st.columns([3, 1])
            expand_clicked = False
            with col_btn:
                iters = st.session_state.get('bs_graph_iterations', 0)
                if iters < 3 and st.session_state.get('bs_graph_data') and "error" not in st.session_state.get('bs_graph_data'):
                    expand_clicked = st.button(f"🕸️ Expand Reactions ({iters}/3)", width='stretch')
                elif iters >= 3:
                    st.button("Max Expansions Reached", disabled=True, width='stretch')
            
            # 3. Handle Expansion Logic
            if expand_clicked:
                with st.spinner("AI is calculating deeper consequences..."):
                    new_data = expand_dynamic_graph_data(st.session_state['bs_graph_data'], api_key, base_url, selected_model)
                    if "error" not in new_data:
                        # Deduplicate nodes by id before merging (LLM may repeat existing nodes)
                        existing_ids = {n["id"] for n in st.session_state['bs_graph_data']['nodes']}
                        unique_new_nodes = [n for n in new_data.get('nodes', []) if n.get("id") not in existing_ids]
                        
                        # Deduplicate edges by (source, target) pair
                        existing_edges = {
                            (e["source"], e["target"])
                            for e in st.session_state['bs_graph_data']['edges']
                        }
                        unique_new_edges = [
                            e for e in new_data.get('edges', [])
                            if (e.get("source"), e.get("target")) not in existing_edges
                        ]
                        
                        st.session_state['bs_graph_data']['nodes'].extend(unique_new_nodes)
                        st.session_state['bs_graph_data']['edges'].extend(unique_new_edges)
                        st.session_state['bs_graph_iterations'] += 1
                    else:
                        st.error(f"Expansion Error: {new_data['error']}")
            
            # 4. Render Graph Stats & Pyvis Graph
            graph_data = st.session_state.get('bs_graph_data')
            if graph_data and "error" in graph_data:
                st.error(f"AI Generation Error: {graph_data['error']}")
            elif graph_data:
                # Render Stats
                nodes_count = len(graph_data.get('nodes', []))
                edges_count = len(graph_data.get('edges', []))
                
                groups = [n.get('group', 'Unknown') for n in graph_data.get('nodes', []) if n.get('group') != 'Event']
                most_impacted = Counter(groups).most_common(1)[0][0] if groups else "N/A"
                
                st.markdown(f"""
                <div style="display: flex; gap: 20px; margin-bottom: 20px;">
                    <div style="flex: 1; background-color: #ffffff; padding: 15px; border-radius: 8px; border: 1px solid #e0e0e0; border-left: 4px solid #e74c3c;">
                        <p style="margin: 0; color: #7f8c8d; font-size: 0.85em; text-transform: uppercase;">Total Entities Affected</p>
                        <h3 style="margin: 5px 0 0 0; color: #2c3e50;">{nodes_count}</h3>
                    </div>
                    <div style="flex: 1; background-color: #ffffff; padding: 15px; border-radius: 8px; border: 1px solid #e0e0e0; border-left: 4px solid #2980b9;">
                        <p style="margin: 0; color: #7f8c8d; font-size: 0.85em; text-transform: uppercase;">Cascading Reactions</p>
                        <h3 style="margin: 5px 0 0 0; color: #2c3e50;">{edges_count}</h3>
                    </div>
                    <div style="flex: 1; background-color: #ffffff; padding: 15px; border-radius: 8px; border: 1px solid #e0e0e0; border-left: 4px solid #f39c12;">
                        <p style="margin: 0; color: #7f8c8d; font-size: 0.85em; text-transform: uppercase;">Most Impacted Sector</p>
                        <h3 style="margin: 5px 0 0 0; color: #2c3e50;">{most_impacted}</h3>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # Render Graph via st.components.v1.html (st.html cannot render full HTML documents with physics scripts)
                try:
                    html_data = generate_impact_network(effective_scenario, graph_data)
                    st.components.v1.html(html_data, height=850, scrolling=True)
                except Exception as e:
                    st.error(f"Failed to generate network graph: {e}")

    # 7. Analysis Context
    if blocked_cp:
        st.error(f"### 🚨 Strategic Alert: {blocked_cp} is currently non-operational.")
        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown(f"""
            **Immediate Impact:**
            - Total cessation of through-traffic for the `{blocked_cp}`.
            - Massive backlog accumulating at entry ports.
            - Insurance premiums for regional transit expected to spike by 300%.
            """)
        with col_b:
            st.markdown(f"""
            **Recommended Actions:**
            - Reroute vessels around alternative corridors (e.g., Cape of Good Hope).
            - Engage strategic reserves for critical commodities (Oil/Semiconductors).
            - Activate diplomatic emergency protocols.
            """)
    else:
        st.success("### ✅ Global Trade Status: Nominal")
        st.info("Select a scenario from the sidebar to simulate a Black Swan event and observe cascading logistical failures.")

    # 8. Oasis Social Dynamics Simulation
    st.divider()
    st.subheader("👥 Social Dynamics Simulation (Oasis/CAMEL-AI)")
    st.markdown("Run a small-scale multi-agent simulation to observe emergent human behavior, such as localized panic buying.")
    
    if st.button("Run Panic Buying Simulation", type="secondary", width='stretch'):
        if not api_key:
            st.warning("Please enter your API Key in the sidebar to run the simulation.")
        elif scenario == "Baseline (Clear Skies)":
            st.info("Select a disruptive scenario to trigger panic.")
        else:
            with st.spinner("Simulating localized retail panic using CAMEL-AI..."):
                chat_log = run_oasis_panic_simulation(scenario, api_key, selected_model, base_url)
                
            if chat_log and isinstance(chat_log, list):
                if "error" in str(chat_log[0]).lower() or "not installed" in str(chat_log[0]).lower():
                    st.error(chat_log[0].get('content', 'Error'))
                else:
                    st.success("Simulation Complete. Showing emergent dialogue:")
                    for msg in chat_log:
                        role = msg.get("role", "")
                        content = msg.get("content", "")
                        if role == "Consumer":
                            st.chat_message("user", avatar="🛒").write(f"**Anxious Consumer:** {content}")
                        elif role == "Manager":
                            st.chat_message("assistant", avatar="🏪").write(f"**Store Manager:** {content}")
                        else:
                            st.write(content)
            else:
                st.error("Failed to generate simulation.")
