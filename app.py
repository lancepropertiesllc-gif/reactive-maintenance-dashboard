import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Reactive Maintenance Risk Dashboard", layout="wide")

st.title("🔧 Reactive Maintenance Risk Dashboard")
st.markdown("**Identify emerging maintenance risks and quantify potential cash flow impact**")

st.info("""
**How to use this tool:**
1. Download the sample template below
2. Fill it out with your maintenance records (one row per repair)
3. Upload your completed CSV file
4. Review the risk analysis and projected exposure
""")

# ==================== SAMPLE TEMPLATE DOWNLOAD ====================
st.subheader("📥 Download Sample Template")

sample_csv = """Property,Date,Issue_Type,Repair_Cost,Downtime_Days,Age_Years,Unit_Count,Description,Vendor,Notes
Building A - Chesterfield,2025-01-15,HVAC,2450,5,11,24,"Replaced blower motor","ABC Heating","Tenant complained about noise"
Building A - Chesterfield,2025-02-03,Water Heater,1850,8,9,24,"Tank started leaking","Quick Plumbing","Emergency call on weekend"
Building B - St. Charles,2025-01-22,Plumbing,980,2,14,16,"Clogged main line","Local Plumber",""
Building B - St. Charles,2025-03-10,Electrical,3200,4,7,16,"Panel upgrade due to shorts","Electric Pros",""
Building C - Wentzville,2025-02-18,Roof,6800,12,18,32,"Multiple leaks repaired","Roof Masters",""
Building D - North County,2025-04-05,Appliances,650,1,12,20,"Refrigerator failed","Appliance Repair Co",""
Building E - Downtown,2025-03-01,Pest Control,450,0,5,12,"Rodent issue in basement","PestGuard",""
Building A - Chesterfield,2025-04-12,HVAC,3100,6,13,24,"Compressor failure","ABC Heating","Very hot day"
Building F - St. Peters,2025-02-25,Water Heater,2100,7,10,18,"Complete replacement","Quick Plumbing",""
Building G - Ballwin,2025-01-30,Electrical,1450,3,8,28,"Breaker panel issues","Electric Pros",""
Building C - Wentzville,2025-05-01,Plumbing,850,4,15,32,"Pipe burst in unit 12","Local Plumber",""
Building D - North County,2025-04-20,Roof,1250,2,9,20,"Gutter damage after storm","Roof Masters",""
"""

st.download_button(
    label="📥 Download Sample Template CSV",
    data=sample_csv,
    file_name="maintenance_data_template.csv",
    mime="text/csv",
)

st.divider()

# ==================== FILE UPLOADER ====================
uploaded_file = st.file_uploader("Upload your completed maintenance data CSV", type="csv")

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    st.success(f"✅ Successfully loaded {len(df)} maintenance records from {df['Property'].nunique()} properties")
else:
    st.warning("👆 Please upload your CSV file using the template above to see the analysis")
    st.stop()

# ==================== DASHBOARD ====================
st.sidebar.header("Portfolio Filters")
selected_properties = st.sidebar.multiselect(
    "Select Properties", 
    df['Property'].unique(), 
    default=df['Property'].unique()[:15]
)

filtered_df = df[df['Property'].isin(selected_properties)]

# Metrics
col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("Total Reactive Repair Costs", f"${filtered_df['Repair_Cost'].sum():,.0f}")
col2.metric("Avg Cost per Breakdown", f"${filtered_df['Repair_Cost'].mean():,.0f}")
col3.metric("Total Downtime Days", f"{filtered_df['Downtime_Days'].sum()}")
col4.metric("Est. Lost Rent Impact", f"${(filtered_df['Downtime_Days'] * 85).sum():,.0f}")

# Risk Calculation
risk_df = filtered_df.groupby(['Property', 'Issue_Type']).agg({
    'Age_Years': 'max',
    'Repair_Cost': ['mean', 'sum', 'count'],
    'Unit_Count': 'first'
}).round(1)

risk_df.columns = ['Max Age', 'Avg Cost', 'Total Cost', 'Breakdowns', 'Unit Count']
risk_df = risk_df.reset_index()

risk_df['Cost per Unit'] = (risk_df['Total Cost'] / risk_df['Unit Count']).round(2)
risk_df['Failure Probability Next 12mo'] = (risk_df['Max Age'] / 15 * 100).clip(0, 95).round(0)
risk_df['Est Emergency Cost If It Breaks'] = (risk_df['Failure Probability Next 12mo'] / 100 * risk_df['Total Cost'] * 1.45).round(0)

risk_df = risk_df.sort_values('Failure Probability Next 12mo', ascending=False)

# Total Estimated Emergency Cost
total_est_emergency = risk_df['Est Emergency Cost If It Breaks'].sum()
col5.metric("**Total Est. Emergency Costs**", f"${total_est_emergency:,.0f}")

st.subheader("Highest Risk Items Right Now")
st.dataframe(risk_df.head(20), use_container_width=True)

# Charts
colA, colB = st.columns(2)
with colA:
    st.subheader("Costs by Issue Type")
    fig1 = px.bar(filtered_df, x='Issue_Type', y='Repair_Cost', color='Issue_Type')
    st.plotly_chart(fig1, use_container_width=True)

with colB:
    st.subheader("Age vs Repair Cost")
    fig2 = px.scatter(filtered_df[filtered_df['Age_Years'] >= 7], 
                     x='Age_Years', y='Repair_Cost', 
                     color='Issue_Type', size='Repair_Cost')
    st.plotly_chart(fig2, use_container_width=True)

st.subheader("Key Insights")
st.info("""
This analysis highlights items with elevated failure probability based on age. 
Many operators defer replacement until failure occurs. The tool quantifies the potential financial exposure from that approach over the next 12 months.
""")

high_risk = risk_df[risk_df['Failure Probability Next 12mo'] > 55]
if not high_risk.empty:
    st.dataframe(high_risk[['Property', 'Issue_Type', 'Max Age', 'Unit Count', 'Cost per Unit', 
                           'Failure Probability Next 12mo', 'Est Emergency Cost If It Breaks']])

st.caption("Portfolio Tool by Tyler — Real Estate Ops & AI Consultant")