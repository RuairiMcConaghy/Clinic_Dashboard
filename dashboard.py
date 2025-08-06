#streamlit run dashboard.py

import streamlit as st
import pandas as pd
import plotly.express as px
from io import BytesIO
from PIL import Image
import base64
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode
from Model import run_scenario, scenarios, clinic_totals, weeks_open  # Added weeks_open for calculations

# ---------------------
# 1. Streamlit Config
# ---------------------
st.set_page_config(page_title="Clinic Profitability Dashboard", layout="wide")

# ---------------------
# 2. Logo & Title (Top-Right)
# ---------------------
logo_path = "Logo.webp"
with open(logo_path, "rb") as f:
    encoded_logo = base64.b64encode(f.read()).decode()

st.markdown(
    f"""
    <div style="display: flex; justify-content: space-between; align-items: center;">
        <h1>🏥 Clinic Profitability Dashboard</h1>
        <img src="data:image/webp;base64,{encoded_logo}" style="height:80px;">
    </div>
    """,
    unsafe_allow_html=True
)

# ---------------------
# 3. Sidebar Scenario Selection
# ---------------------
st.sidebar.header("Scenario Controls")
scenario = st.sidebar.selectbox("Select a Scenario", list(scenarios.keys()))
st.sidebar.markdown("Choose a scenario to update KPIs and charts in real-time.")

st.sidebar.markdown("### Weekly Patient Volumes")
dynamic_clinic_totals = {}

for clinic, default_total in clinic_totals.items():
    dynamic_clinic_totals[clinic] = st.sidebar.slider(
        f"{clinic} Patients/Week",
        min_value=0,
        max_value=50,
        value=default_total,
        step=1
    )

# ---------------------
# 4. Run Scenario
# ---------------------
with st.spinner(f"Running `{scenario}` scenario..."):
    results = run_scenario(
        scenario,
        export_excel=False,
        generate_plots=False,
        return_dataframes=True,
        clinic_totals_override=dynamic_clinic_totals  # ✅ Pass slider values
    )

df_services = results["services"]
df_summary = results["summary"]
df_growth = results["growth"]
df_cash_flow = results["cash_flow"]
df_price = results["price_sensitivity"]
df_utilization = results["utilization"]

st.success(f"Scenario `{scenario}` completed!")

# Prepare chart values
clinics = df_summary['Clinic']
actual_patients = [df_services[df_services["Clinic"] == c]["Patients/Week"].sum() for c in clinics]
break_even_patients = df_summary["Weekly Break-Even Patients"]

# ---------------------
# 5. Tabs (Added new tabs)
# ---------------------
tab_kpi, tab_charts, tab_tables, tab_comparison, tab_profitability, tab_multi, tab_download = st.tabs(
    ["📊 KPIs", "📈 Charts", "📄 Tables", "⚖ Scenario Comparison", "💹 Service Profitability", "📋 Multi-Scenario Summary", "💾 Download"]
)

# ---------------------
# TAB 1: KPIs
# ---------------------
with tab_kpi:
    st.subheader("Key Performance Indicators")

    # --- Scenario Variables Bar ---
    st.markdown("#### Scenario Variables")
    scenario_params = scenarios[scenario]  # Get the parameters for the selected scenario

    # Create one column per variable in the scenario
    cols = st.columns(len(scenario_params))
    for i, (param, value) in enumerate(scenario_params.items()):
        display_value = f"{value:.0%}" if "rate" in param else f"{value:.1f}x"
        cols[i].metric(label=param.replace("_", " ").title(), value=display_value)

    # --- Expanded KPI Metrics for Clinics ---
    for _, row in df_summary.iterrows():
        st.markdown(f"### 🏥 **{row['Clinic']}**")

        # First row: financial overview
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("💰 Annual Revenue", f"£{row['Annual Revenue']:,.0f}")
        col2.metric("📈 Net Profit", f"£{row['Net Profit']:,.0f}")
        col3.metric("📊 Net Margin", f"{row['Net Margin %']:.1f}%")
        col4.metric("🧮 Break-Even Patients", f"{row['Weekly Break-Even Patients']:.1f}")

        # Second row: cost breakdown & gross profit
        col5, col6, col7, col8 = st.columns(4)
        col5.metric("📦 Variable Costs", f"£{row['Variable Costs']:,.0f}")
        col6.metric("🏢 Fixed Costs", f"£{row['Fixed Costs']:,.0f}")
        col7.metric("💵 Gross Profit", f"£{row['Gross Profit']:,.0f}")
        col8.metric("💷 Total Tax", f"£{row['Total Tax']:,.0f}")

        # Third row: operational metrics
        col9, col10, col11, col12 = st.columns(4)
        col9.metric("⏱ Weekly Hours Avail.", f"{row['Weekly Hours Available']:.1f}h")
        col10.metric("🕒 Weekly Hours Booked", f"{row['Weekly Hours Booked']:.1f}h")
        col11.metric("📊 Utilization", f"{row['Utilization %']:.1f}%")
        col12.metric("⚡ Capacity Status", row['Capacity Status'])

        # --- Divider between clinics ---
        st.markdown("---")


# ---------------------
# TAB 2: Charts
# ---------------------
with tab_charts:
    # Break-even vs Actual Patients
    st.subheader("Break-Even vs Actual Patients")
    df_chart = pd.DataFrame({
        "Clinic": list(clinics) * 2,
        "Patients": actual_patients + list(break_even_patients),
        "Type": ["Actual"] * len(clinics) + ["Break-Even"] * len(clinics)
    })
    fig_bar = px.bar(
        df_chart, x="Clinic", y="Patients", color="Type", barmode="group",
        title=f"Break-Even vs Actual Patients ({scenario} scenario)",
        text_auto=True
    )
    st.plotly_chart(fig_bar, use_container_width=True)

    # Year-over-Year Projected Profit
    st.subheader("Year-over-Year Projected Profit")
    fig_growth = px.line(
        df_growth, x="Year", y="Projected Profit", color="Clinic",
        title="Year-over-Year Growth", markers=True
    )
    st.plotly_chart(fig_growth, use_container_width=True)

    # Cumulative Monthly Cash Flow
    st.subheader("Cumulative Monthly Cash Flow")
    fig_cash = px.line(
        df_cash_flow, x="Month", y="Cumulative Cash", color="Clinic",
        title="Cumulative Monthly Cash Flow", markers=True
    )
    st.plotly_chart(fig_cash, use_container_width=True)


# ---------------------
# TAB 3: Tables (Dark Mode)
# ---------------------
with tab_tables:
    st.subheader("Service-Level Profitability (Excel-style Filtering)")

    dark_css = {
        ".ag-root-wrapper": {"background-color": "#1e1e1e !important", "color": "#f5f5f5 !important"},
        ".ag-header": {"background-color": "#2a2a2a !important", "color": "#f5f5f5 !important", "font-weight": "bold"},
        ".ag-header-cell": {"background-color": "#2a2a2a !important", "color": "#f5f5f5 !important", "font-weight": "bold"},
        ".ag-row": {"background-color": "#1e1e1e !important", "color": "#f5f5f5 !important"},
        ".ag-row-hover": {"background-color": "#333333 !important"},
        ".ag-cell": {"background-color": "#1e1e1e !important", "color": "#f5f5f5 !important"},
        ".ag-paging-panel": {"background-color": "#1e1e1e !important", "color": "#f5f5f5 !important"},
    }

    # --- Service Table ---
    st.subheader("Service-Level Profitability")
    gb_services = GridOptionsBuilder.from_dataframe(df_services)
    gb_services.configure_default_column(filter=True, sortable=True, resizable=True)
    gb_services.configure_side_bar()
    gb_services.configure_pagination(enabled=True, paginationAutoPageSize=False, paginationPageSize=20)
    grid_options_services = gb_services.build()

    AgGrid(
        df_services,
        gridOptions=grid_options_services,
        update_mode=GridUpdateMode.NO_UPDATE,
        theme='alpine',
        fit_columns_on_grid_load=True,
        custom_css=dark_css
    )

    st.markdown("---")

    # --- Clinic Summary Table ---
    st.subheader("Clinic Summary")
    gb_summary = GridOptionsBuilder.from_dataframe(df_summary)
    gb_summary.configure_default_column(filter=True, sortable=True, resizable=True)
    gb_summary.configure_side_bar()
    gb_summary.configure_pagination(enabled=True, paginationAutoPageSize=False, paginationPageSize=20)
    grid_options_summary = gb_summary.build()

    AgGrid(
        df_summary,
        gridOptions=grid_options_summary,
        update_mode=GridUpdateMode.NO_UPDATE,
        theme='alpine',
        fit_columns_on_grid_load=True,
        custom_css=dark_css
    )

    st.markdown("---")

    # --- Price Sensitivity Impact Table ---
    st.subheader("Price Sensitivity Impact")
    gb_price = GridOptionsBuilder.from_dataframe(df_price)
    gb_price.configure_default_column(filter=True, sortable=True, resizable=True)
    gb_price.configure_side_bar()
    gb_price.configure_pagination(enabled=True, paginationAutoPageSize=False, paginationPageSize=20)
    grid_options_price = gb_price.build()

    AgGrid(
        df_price,
        gridOptions=grid_options_price,
        update_mode=GridUpdateMode.NO_UPDATE,
        theme='alpine',
        fit_columns_on_grid_load=True,
        custom_css=dark_css
    )

    st.markdown("---")

    # --- Utilization & Capacity Table ---
    st.subheader("Utilization & Capacity")
    gb_util = GridOptionsBuilder.from_dataframe(df_utilization)
    gb_util.configure_default_column(filter=True, sortable=True, resizable=True)
    gb_util.configure_side_bar()
    gb_util.configure_pagination(enabled=True, paginationAutoPageSize=False, paginationPageSize=20)
    grid_options_util = gb_util.build()

    AgGrid(
        df_utilization,
        gridOptions=grid_options_util,
        update_mode=GridUpdateMode.NO_UPDATE,
        theme='alpine',
        fit_columns_on_grid_load=True,
        custom_css=dark_css
    )

    st.markdown("---")

    # --- Year-over-Year (YoY) Growth Table ---
    st.subheader("Year-over-Year (YoY) Growth")
    gb_growth = GridOptionsBuilder.from_dataframe(df_growth)
    gb_growth.configure_default_column(filter=True, sortable=True, resizable=True)
    gb_growth.configure_side_bar()
    gb_growth.configure_pagination(enabled=True, paginationAutoPageSize=False, paginationPageSize=20)
    grid_options_growth = gb_growth.build()

    AgGrid(
        df_growth,
        gridOptions=grid_options_growth,
        update_mode=GridUpdateMode.NO_UPDATE,
        theme='alpine',
        fit_columns_on_grid_load=True,
        custom_css=dark_css
    )

    st.markdown("---")

    # --- Cash Flow (Cumulative) Table ---
    st.subheader("Cumulative Monthly Cash Flow")
    gb_cash = GridOptionsBuilder.from_dataframe(df_cash_flow)
    gb_cash.configure_default_column(filter=True, sortable=True, resizable=True)
    gb_cash.configure_side_bar()
    gb_cash.configure_pagination(enabled=True, paginationAutoPageSize=False, paginationPageSize=20)
    grid_options_cash = gb_cash.build()

    AgGrid(
        df_cash_flow,
        gridOptions=grid_options_cash,
        update_mode=GridUpdateMode.NO_UPDATE,
        theme='alpine',
        fit_columns_on_grid_load=True,
        custom_css=dark_css
    )

    # ---------------------
    # Download Buttons
    # ---------------------
    st.markdown("### 📥 Download Tables")
    col1, col2, col3 = st.columns(3)
    col1.download_button(
        "⬇ Download Services Table (CSV)",
        df_services.to_csv(index=False).encode('utf-8'),
        "services_table.csv",
        "text/csv"
    )
    col2.download_button(
        "⬇ Download Summary Table (CSV)",
        df_summary.to_csv(index=False).encode('utf-8'),
        "summary_table.csv",
        "text/csv"
    )
    col3.download_button(
        "⬇ Download Price Sensitivity Table (CSV)",
        df_price.to_csv(index=False).encode('utf-8'),
        "price_sensitivity_table.csv",
        "text/csv"
    )

    st.markdown("### 📥 Download New Tables")
    col4, col5, col6 = st.columns(3)
    col4.download_button(
        "⬇ Download Utilization Table (CSV)",
        df_utilization.to_csv(index=False).encode('utf-8'),
        "utilization_table.csv",
        "text/csv"
    )
    col5.download_button(
        "⬇ Download YoY Growth Table (CSV)",
        df_growth.to_csv(index=False).encode('utf-8'),
        "yoy_growth_table.csv",
        "text/csv"
    )
    col6.download_button(
        "⬇ Download Cash Flow Table (CSV)",
        df_cash_flow.to_csv(index=False).encode('utf-8'),
        "cash_flow_table.csv",
        "text/csv"
    )

# ---------------------
# TAB 4: Scenario Comparison
# ---------------------
with tab_comparison:
    st.subheader("⚖ Scenario Comparison")
    scenario_a = st.selectbox("Select Scenario A", list(scenarios.keys()), index=0)
    scenario_b = st.selectbox("Select Scenario B", list(scenarios.keys()), index=1)

    results_a = run_scenario(scenario_a, export_excel=False, generate_plots=False, return_dataframes=True, clinic_totals_override=dynamic_clinic_totals)
    results_b = run_scenario(scenario_b, export_excel=False, generate_plots=False, return_dataframes=True, clinic_totals_override=dynamic_clinic_totals)

    summary_a = results_a["summary"]
    summary_b = results_b["summary"]

    comparison_list = []
    for clinic in summary_a['Clinic']:
        row_a = summary_a[summary_a['Clinic'] == clinic].iloc[0]
        row_b = summary_b[summary_b['Clinic'] == clinic].iloc[0]

        def pct_change(a, b):
            return (b - a) / a * 100 if a != 0 else None

        comparison_list.append({'Clinic': clinic, 'Metric': 'Annual Revenue', 'Scenario A': row_a['Annual Revenue'], 'Scenario B': row_b['Annual Revenue'], 'Δ %': pct_change(row_a['Annual Revenue'], row_b['Annual Revenue'])})
        comparison_list.append({'Clinic': clinic, 'Metric': 'Net Profit', 'Scenario A': row_a['Net Profit'], 'Scenario B': row_b['Net Profit'], 'Δ %': pct_change(row_a['Net Profit'], row_b['Net Profit'])})
        comparison_list.append({'Clinic': clinic, 'Metric': 'Break-even Patients', 'Scenario A': row_a['Weekly Break-Even Patients'], 'Scenario B': row_b['Weekly Break-Even Patients'], 'Δ %': pct_change(row_a['Weekly Break-Even Patients'], row_b['Weekly Break-Even Patients'])})
        comparison_list.append({'Clinic': clinic, 'Metric': 'Utilization %', 'Scenario A': row_a['Utilization %'], 'Scenario B': row_b['Utilization %'], 'Δ %': pct_change(row_a['Utilization %'], row_b['Utilization %'])})

    df_comparison = pd.DataFrame(comparison_list)
    st.dataframe(df_comparison.style.format({"Scenario A":"£{:.0f}", "Scenario B":"£{:.0f}", "Δ %":"{:+.1f}%"}))

# ---------------------
# TAB 5: Profitability per Service & Client Cohort
# ---------------------
with tab_profitability:
    st.subheader("💹 Service Profitability Analysis")

    df_services['Profit per Hour'] = df_services['Profit'] / (df_services['Patients/Week'] * df_services['Duration (min)'] / 60 * weeks_open)
    # 'Revenue per Client' is already in df_services

    top3 = df_services.sort_values('Profit per Hour', ascending=False).head(3)
    st.markdown(f"**Top 3 Services by Profit per Hour:** {', '.join(top3['Service'])}")

    fig_profit = px.bar(
        df_services.sort_values('Profit per Hour', ascending=False),
        x='Profit per Hour', y='Service', color='Clinic', orientation='h',
        title='Profit per Service per Hour'
    )
    st.plotly_chart(fig_profit, use_container_width=True)

    fig_client = px.scatter(
        df_services,
        x='Revenue per Client', y='Service', color='Clinic', size='Profit',
        title='Revenue per Client vs Service'
    )
    st.plotly_chart(fig_client, use_container_width=True)

# ---------------------
# TAB 6: Multi-Scenario Summary
# ---------------------
with tab_multi:
    st.subheader("📋 Multi-Scenario Simulation Summary")

    multi_summary = []
    for scenario_name in scenarios.keys():
        res = run_scenario(scenario_name, export_excel=False, generate_plots=False, return_dataframes=True, clinic_totals_override=dynamic_clinic_totals)
        df_sum = res['summary']
        multi_summary.append({
            'Scenario': scenario_name,
            'Total Revenue (£)': df_sum['Annual Revenue'].sum(),
            'Total Net Profit (£)': df_sum['Net Profit'].sum(),
            'Avg Break-even Patients': df_sum['Weekly Break-Even Patients'].mean(),
            'Avg Utilization %': df_sum['Utilization %'].mean()
        })

    df_multi = pd.DataFrame(multi_summary).sort_values('Total Net Profit (£)', ascending=False)
    st.dataframe(df_multi.style.format({"Total Revenue (£)":"£{:.0f}", "Total Net Profit (£)":"£{:.0f}", "Avg Break-even Patients":"{:.1f}", "Avg Utilization %":"{:.1f}%"}))

# ---------------------
# TAB 7: Download Excel
# ---------------------
with tab_download:
    st.subheader("Download Scenario Results")
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        df_services.to_excel(writer, sheet_name='Services', index=False)
        df_summary.to_excel(writer, sheet_name='Summary', index=False)
        df_growth.to_excel(writer, sheet_name='YoY Growth', index=False)
        df_cash_flow.to_excel(writer, sheet_name='Cash Flow', index=False)
        df_price.to_excel(writer, sheet_name='Price Sensitivity', index=False)
        df_utilization.to_excel(writer, sheet_name='Utilization', index=False)

    st.download_button(
        label="💾 Download Full Report (Excel)",
        data=buffer.getvalue(),
        file_name=f"clinic_profitability_{scenario}.xlsx",
        mime="application/vnd.ms-excel"
    )

#streamlit run dashboard.py
