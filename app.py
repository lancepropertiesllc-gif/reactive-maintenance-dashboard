import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Reactive Maintenance Risk Dashboard", layout="wide")

st.title("🔧 Reactive Maintenance Risk Dashboard")
st.markdown("**Built for real estate operators who wait until things break** — See how much surprise pain is coming to your cash flow")

st.info("""
**How to use this tool:**
1. Download the sample template below
2. Fill it out with your actual maintenance records (one row per repair)
3. Upload your completed CSV file
4. Review the highest risk items and upcoming cash flow hits
""")

# ==================== SAMPLE TEMPLATE DOWNLOAD ====================
st.subheader("📥 Download Sample Template")

sample_csv = """Property,Date,Issue_Type,Repair_Cost,Downtime_Days,Age_Years,Unit_Count,Description,Vendor,Preventive_Cost_Estimate,Notes
Building A - Chesterfield,2025-01-15,HVAC,2450,5,11,24,"Replaced blower motor","ABC Heating",1200,"Tenant complained about noise"
Building A - Chesterfield,2025-02-03,Water Heater,1850,8,9,24,"Tank started leaking","Quick Plumbing",950,"Emergency call on weekend"
Building B - St. Charles,2025-01-22,Plumbing,980,2,14,16,"Clogged main line","Local Plumber",650,""
Building B - St. Charles,2025-03-10,Electrical,3200,4,7,16,"Panel upgrade due to shorts","Electric Pros",1800,""
Building C - Wentzville,2025-02-18,Roof,6800,12,18,32,"Multiple leaks repaired","Roof Masters",4500,""
Building D - North County,2025-04-05,Appliances,650,1,12,20,"Refrigerator failed","Appliance Repair Co",400,""
Building E - Downtown,2025-03-01,Pest Control,450,0,5,12,"Rodent issue in basement","PestGuard",300,""
Building A - Chesterfield,2025-04-12,HVAC,3100,6,13,24,"Compressor failure","ABC Heating",2200,"Very hot day"
Building F - St. Peters,2025-02-25,Water Heater,2100,7,10,18,"Complete replacement","Quick Plumbing",1100,""
Building G - Ballwin,2025-01-30,Electrical,1450,3,8,28,"Breaker panel issues","Electric Pros",900,""
Building C - Wentzville,2025-05-01,Plumbing,850,4,15,32,"Pipe burst in unit 12","Local Plumber",600,""
Building D - North County,2025-04-20,Roof,1250,2,9,20,"Gutter damage after storm","Roof Masters",750,""
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
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Reactive Repair Costs", f"${filtered_df['Repair_Cost'].sum():,.0f}")
col2.metric("Avg Cost per Breakdown", f"${filtered_df['Repair_Cost'].mean():,.0f}")
col3.metric("Total Downtime Days", f"{filtered_df['Downtime_Days'].sum()}")
col4.metric("Est. Lost Rent Impact", f"${(filtered_df['Downtime_Days'] * 85).sum():,.0f}")

st.subheader("Highest Risk Items Right Now (Things That Will Probably Break Soon)")

risk_df = filtered_df.groupby(['Property', 'Issue_Type']).agg({
    'Age_Years': 'max',
    'Repair_Cost': ['mean', 'sum', 'count']
}).round(1)

risk_df.columns = ['Max_Age', 'Avg_Cost', 'Total_Cost', 'Breakdowns']
risk_df = risk_df.reset_index()

risk_df['Failure_Probability_Next_12mo'] = (risk_df['Max_Age'] / 15 * 100).clip(0, 95).round(0)
risk_df['Est_Emergency_Cost_If_It_Breaks'] = (risk_df['Failure_Probability_Next_12mo'] / 100 * risk_df['Total_Cost'] * 1.45).round(0)

risk_df = risk_df.sort_values('Failure_Probability_Next_12mo', ascending=False)

st.dataframe(risk_df.head(20), use_container_width=True)

# Charts (same as before)
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

st.subheader("🤖 Real Talk for Reactive Operators")
st.info("""
You’re going to keep waiting until things break — that’s how most operators run.  
Here’s approximately how much surprise pain you’re likely looking at in the next 12 months.
""")

high_risk = risk_df[risk_df['Failure_Probability_Next_12mo'] > 55]
if not high_risk.empty:
    st.dataframe(high_risk[['Property', 'Issue_Type', 'Max_Age', 'Failure_Probability_Next_12mo', 'Est_Emergency_Cost_If_It_Breaks']])

st.caption("Portfolio Tool by Tyler — Real Estate Ops & AI Consultant")