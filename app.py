import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Reactive Maintenance Risk Dashboard", layout="wide")
st.title("🔧 Reactive Maintenance Risk Dashboard")
st.markdown("**Built for operators who wait until it breaks** — Upload your data and see the coming pain")

# File uploader
uploaded_file = st.file_uploader("Upload your maintenance data CSV", type="csv")

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    st.success(f"✅ Loaded {len(df)} records for {df['Property'].nunique()} properties")
else:
    st.warning("Please upload a maintenance_data.csv file to begin")
    st.stop()

# Sidebar filters
st.sidebar.header("Filters")
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

st.subheader("🤖 Real Talk for Reactive Operators")
st.info("""
You’re going to keep waiting until things break.  
Here’s approximately how much surprise pain you’re likely looking at in the next 12 months.
""")

high_risk = risk_df[risk_df['Failure_Probability_Next_12mo'] > 55]
if not high_risk.empty:
    st.dataframe(high_risk[['Property', 'Issue_Type', 'Max_Age', 'Failure_Probability_Next_12mo', 'Est_Emergency_Cost_If_It_Breaks']])

st.caption("Portfolio Tool by Tyler — Real Estate Ops & AI Consultant")