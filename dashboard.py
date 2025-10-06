import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import os
st.set_page_config(page_title="Airline Delays Dashboard", layout="wide")
st.title("✈️ Airline Delays Dashboard")

PALETTE = ["#1f77b4", "#ff7f0e", "#2ca02c"]  
def extract_hour(value):
    if pd.isna(value):
        return np.nan
    try:
        v = int(value)
        return v // 100
    except Exception:
        return np.nan
DATA_PATH = r"C:\Users\dhars\Downloads\airline\flights.csv"
@st.cache_data
def load_data(path):
    df = pd.read_csv(path, low_memory=False)
    for col in ["dep_delay", "arr_delay", "sched_dep_time", "dep_time", "air_time", "distance", "month", "day"]:
        if col not in df.columns:
            df[col] = np.nan
    if "dep_hour" not in df.columns:
        time_col = "sched_dep_time" if "sched_dep_time" in df.columns else "dep_time"
        df["dep_hour"] = df[time_col].apply(extract_hour)
    df["origin"] = df["origin"].astype(str)
    df["dest"] = df["dest"].astype(str)
    df["route"] = df["origin"] + " → " + df["dest"]
    for ncol in ["dep_delay", "arr_delay", "air_time", "distance"]:
        df[ncol] = pd.to_numeric(df[ncol], errors="coerce")

    return df

if not os.path.exists(DATA_PATH):
    st.error(f"Dataset not found at: {DATA_PATH}")
    st.stop()

df = load_data(DATA_PATH)
st.sidebar.header("Filters")
airlines = st.sidebar.multiselect("Airlines", options=sorted(df['carrier'].dropna().unique()), default=sorted(df['carrier'].dropna().unique()))
origins = st.sidebar.multiselect("Origins", options=sorted(df['origin'].dropna().unique()), default=sorted(df['origin'].dropna().unique()))
dests = st.sidebar.multiselect("Destinations", options=sorted(df['dest'].dropna().unique()), default=sorted(df['dest'].dropna().unique()))
months = st.sidebar.multiselect("Months", options=sorted(df['month'].dropna().unique()), default=sorted(df['month'].dropna().unique()))

filtered = df[
    (df['carrier'].isin(airlines)) &
    (df['origin'].isin(origins)) &
    (df['dest'].isin(dests)) &
    (df['month'].isin(months))
].copy()

st.subheader("Filtered Data Preview")
st.dataframe(filtered.head(10))

if filtered.shape[0] == 0:
    st.warning("No rows match the selected filters.")
    st.stop()

col1, col2 = st.columns(2)

# 1. Avg Departure & Arrival Delay by Airline
with col1:
    delay_by_air = filtered.groupby('carrier')[['dep_delay', 'arr_delay']].mean().reset_index()
    fig1 = px.bar(delay_by_air.melt(id_vars='carrier', value_vars=['dep_delay', 'arr_delay']),
                  x='carrier', y='value', color='variable',
                  barmode='group', title="Avg Departure vs Arrival Delay by Airline",
                  color_discrete_sequence=PALETTE)
    st.plotly_chart(fig1, use_container_width=True)

    max_dep = delay_by_air['dep_delay'].max()
    worst_airline = delay_by_air.loc[delay_by_air['dep_delay'] == max_dep, 'carrier'].values[0]
    st.markdown(f"**Insight:** Airline with highest average departure delay is **{worst_airline}** ({max_dep:.2f} min).")

# 2. Flight Share by Airline
with col2:
    flights_share = filtered['carrier'].value_counts().reset_index()
    flights_share.columns = ['carrier', 'flights']
    fig2 = px.pie(flights_share, values='flights', names='carrier',
                  title="Flight Share by Airline", color_discrete_sequence=PALETTE)
    st.plotly_chart(fig2, use_container_width=True)

    top_airline = flights_share.iloc[0]
    st.markdown(f"**Insight:** **{top_airline['carrier']}** operates the most flights ({top_airline['flights']} flights, {top_airline['flights']/flights_share['flights'].sum()*100:.1f}%).")

# 3. Top 10 Busiest Routes
top_routes = filtered.groupby('route').size().sort_values(ascending=False).head(10).reset_index(name='flights')
fig3 = px.bar(top_routes, x='flights', y='route', orientation='h',
              title="Top 10 Busiest Routes", color='flights', color_discrete_sequence=PALETTE)
st.plotly_chart(fig3, use_container_width=True)
st.markdown(f"**Insight:** Busiest route is **{top_routes.iloc[0]['route']}** with **{top_routes.iloc[0]['flights']} flights**.")

# 4. Monthly Avg Departure Delay
monthly_delays = filtered.groupby('month')['dep_delay'].mean().reset_index()
fig4 = px.line(monthly_delays, x='month', y='dep_delay', markers=True,
               title="Monthly Avg Departure Delay", color_discrete_sequence=PALETTE)
st.plotly_chart(fig4, use_container_width=True)
max_month = monthly_delays.loc[monthly_delays['dep_delay'].idxmax()]['month']
st.markdown(f"**Insight:** Month with highest avg departure delay is **{int(max_month)}**.")

# 5. Avg Departure Delay by Origin Airport
airport_delays = filtered.groupby('origin')['dep_delay'].mean().reset_index()
fig5 = px.bar(airport_delays, x='origin', y='dep_delay',
              title="Avg Departure Delay by Origin Airport", color_discrete_sequence=PALETTE)
st.plotly_chart(fig5, use_container_width=True)
worst_origin = airport_delays.loc[airport_delays['dep_delay'].idxmax()]['origin']
st.markdown(f"**Insight:** Airport with highest avg departure delay is **{worst_origin}**.")

# 6. Avg Flight Distance by Airline
dist_airline = filtered.groupby('carrier')['distance'].mean().reset_index()
fig6 = px.bar(dist_airline, x='carrier', y='distance',
              title="Avg Flight Distance by Airline", color_discrete_sequence=PALETTE)
st.plotly_chart(fig6, use_container_width=True)
longest_airline = dist_airline.loc[dist_airline['distance'].idxmax()]['carrier']
st.markdown(f"**Insight:** Airline with longest avg flight distance is **{longest_airline}**.")

# 7. Top 10 Routes by Avg Air Time
route_airtime = filtered.groupby('route')['air_time'].mean().reset_index().dropna().sort_values(by='air_time', ascending=False).head(10)
fig7 = px.bar(route_airtime, x='air_time', y='route', orientation='h',
              title="Top 10 Routes by Avg Air Time", color='air_time', color_discrete_sequence=PALETTE)
st.plotly_chart(fig7, use_container_width=True)
st.markdown(f"**Insight:** Route with longest avg air time is **{route_airtime.iloc[0]['route']}** ({route_airtime.iloc[0]['air_time']:.2f} min).")

# 8. Hourly Avg Departure Delay
hourly_delay = filtered.groupby('dep_hour')['dep_delay'].mean().reset_index().dropna()
fig8 = px.line(hourly_delay, x='dep_hour', y='dep_delay', markers=True,
               title="Hourly Avg Departure Delay", color_discrete_sequence=PALETTE)
st.plotly_chart(fig8, use_container_width=True)
peak_hour = hourly_delay.loc[hourly_delay['dep_delay'].idxmax()]['dep_hour']
st.markdown(f"**Insight:** Hour with highest avg departure delay is **{int(peak_hour)}:00**.")

# 9. Daily Avg Departure Delay
daily_delay = filtered.groupby('day')['dep_delay'].mean().reset_index().dropna()
fig9 = px.line(daily_delay, x='day', y='dep_delay', markers=True,
               title="Daily Avg Departure Delay", color_discrete_sequence=PALETTE)
st.plotly_chart(fig9, use_container_width=True)
worst_day = daily_delay.loc[daily_delay['dep_delay'].idxmax()]['day']
st.markdown(f"**Insight:** Day with highest avg departure delay is **{int(worst_day)}**.")

# 10. Departure Delay Distribution
fig10 = px.histogram(filtered, x='dep_delay', nbins=40,
                     title="Departure Delay Distribution", color_discrete_sequence=PALETTE)
st.plotly_chart(fig10, use_container_width=True)
avg_delay = filtered['dep_delay'].mean()
st.markdown(f"**Insight:** Average departure delay across all flights is **{avg_delay:.2f} minutes**.")
