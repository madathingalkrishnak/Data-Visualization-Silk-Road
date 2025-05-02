#streamlit_appp.py
import pandas as pd
import numpy as np
import random
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(page_title="Travelling the Silk Road", layout="wide")

@st.cache_data
def load_data():
    return pd.read_csv('data.csv')


df = load_data()

#df= pd.read_csv('data.csv')

# Set up Streamlit page
st.title("Travelling the Silk Road: Dashboard")

###
st.subheader("Distribution of Daily Listings Across Sellers Over Time")

# Convert 'first_seen' to datetime
# Ensure datetime format
df['first_seen'] = pd.to_datetime(df['first_seen'], unit='s')

# Convert to daily date (drop time)
df['day'] = df['first_seen'].dt.date  # this is important!

# Count listings per seller per day
seller_activity = df.groupby(['day', 'seller']).size().reset_index(name='num_listings')

# Convert day to string so Plotly treats it as categorical
seller_activity['day'] = seller_activity['day'].astype(str)

# Sort by day
seller_activity = seller_activity.sort_values('day')

# Create box plot
fig = px.box(
    seller_activity,
    x='day',
    y='num_listings',
    title='Distribution of Daily Listings Across Sellers Over Time',
    labels={'day': 'Date', 'num_listings': 'Number of Listings'}
)

# Use log scale and improve layout
fig.update_layout(
    yaxis_type="log",
    xaxis_title="Date",
    yaxis_title="Number of Listings",
    margin=dict(t=60, b=120),
    xaxis_tickangle=-45
)

st.plotly_chart(fig)

#######

st.subheader("Shipping Flow: Sankey Diagram")

# Group and count
sankey_data = df.groupby(['ships_from', 'category_name', 'ships_to']).size().reset_index(name='count')

# Find top 20 categories by total flow
top_categories = sankey_data.groupby('category_name')['count'].sum().nlargest(20).index

# Filter the sankey data for only top 20 categories
sankey_data = sankey_data[sankey_data['category_name'].isin(top_categories)]

# Sankey Diagram (redone)
import plotly.colors as pc

# Step 1: Clean the data
# Filter to top values
top_origins = sankey_data['ships_from'].value_counts().nlargest(10).index
top_categories = sankey_data['category_name'].value_counts().nlargest(8).index
top_destinations = sankey_data['ships_to'].value_counts().nlargest(10).index

# Filter the data
filtered_df = sankey_data[
    (sankey_data['ships_from'].isin(top_origins)) &
    (sankey_data['category_name'].isin(top_categories)) &
    (sankey_data['ships_to'].isin(top_destinations))
].copy()

# Step 2: Create labels in fixed layers
origins = list(filtered_df['ships_from'].unique())
categories = list(filtered_df['category_name'].unique())
destinations = list(filtered_df['ships_to'].unique())
labels = origins + categories + destinations

# Index maps
label_map = {label: idx for idx, label in enumerate(labels)}

# Create connections
# Origins ➝ Categories
o2c = filtered_df.groupby(['ships_from', 'category_name'])['count'].sum().reset_index()
o2c['source'] = o2c['ships_from'].map(label_map)
o2c['target'] = o2c['category_name'].map(label_map)
o2c['value'] = o2c['count']

# Categories ➝ Destinations
c2d = filtered_df.groupby(['category_name', 'ships_to'])['count'].sum().reset_index()
c2d['source'] = c2d['category_name'].map(label_map)
c2d['target'] = c2d['ships_to'].map(label_map)
c2d['value'] = c2d['count']

# Combine links
links_df = pd.concat([o2c[['source', 'target', 'value']], c2d[['source', 'target', 'value']]])

# Optional: color by category
category_colors = {
    cat: f'rgba({50+i*20}, {100+i*10}, {150+i*15}, 0.6)' for i, cat in enumerate(categories)
}
# Step 1: Choose a distinct color palette
color_list = pc.qualitative.Dark2  # You can also try: Set1, Bold, Dark2
color_cycle = color_list * ((len(categories) // len(color_list)) + 1)

# Step 2: Assign colors to each category
category_colors = {cat: color_cycle[i] for i, cat in enumerate(categories)}

# Step 3: Assign link colors based on the category in either source or target
link_colors = []
for _, row in links_df.iterrows():
    source_label = labels[row['source']]
    target_label = labels[row['target']]
    
    # Assign color based on the category node
    if source_label in categories:
        color = category_colors[source_label]
    elif target_label in categories:
        color = category_colors[target_label]
    else:
        color = 'rgba(180,180,180,0.4)'  # fallback light gray

    link_colors.append(color)

print(category_colors)  # Check if colors are being assigned correctly
print(link_colors[:10])  # Preview first 10 link colors

# Step 3: Plot
fig = go.Figure(data=[go.Sankey(
    arrangement="snap",
    node=dict(
        pad=15,
        thickness=20,
        line=dict(color="black", width=0.5),
        label=labels,
        color="rgba(50,50,50,0.9)"
    ),
    link=dict(
        source=links_df['source'],
        target=links_df['target'],
        value=links_df['value'],
        color=link_colors,
        hovertemplate='Source: %{source.label}<br>Target: %{target.label}<br>Count: %{value}<extra></extra>'
    )
)])

fig.update_layout(
    title_text="Shipping Flow: Origin → Product Category → Destination",
    font_size=12,
    height=600
)
st.plotly_chart(fig, use_container_width=True)

###
category_ratings = df.groupby('category_name')['feedback_rating'].mean().reset_index()
category_ratings = category_ratings.sort_values(by='feedback_rating', ascending=False)

st.subheader("Category Name vs Feedback Rating")

fig2 = px.line(
    category_ratings,
    x='feedback_rating',
    y='category_name',
    title='Average Feedback Rating by Category',
    labels={'feedback_rating': 'Average Rating', 'category_name': 'Category'},
    markers=True  # adds points at each category
)
fig2.update_xaxes(type='log')

#fig6.update_layout(xaxis_range=[4.4, 5])
st.plotly_chart(fig2)





#####


st.subheader("🌍 Shipping Network on a Globe")

# Static lat/lon mapping
country_coords = {
    'Canada': (56.1304, -106.3468),
    'Germany': (51.1657, 10.4515),
    'United States of America': (37.0902, -95.7129),
    'Netherlands': (52.1326, 5.2913),
    'Spain': (40.4637, -3.7492),
    'United Kingdom': (55.3781, -3.4360),
    'Switzerland': (46.8182, 8.2275),
    'Uzbekistan': (41.3775, 64.5853),
    'South Africa': (-30.5595, 22.9375),
    'Australia': (-25.2744, 133.7751),
    'American Samoa': (-14.2709, -170.1322),
    'Mexico': (23.6345, -102.5528),
    'Finland': (61.9241, 25.7482),
    'Norway': (60.4720, 8.4689)
}

# Aliases
aliases = {'USA': 'United States of America', 'US': 'United States of America',
           'UK': 'United Kingdom', 'The Netherlands': 'Netherlands'}

df['ships_from'] = df['ships_from'].replace(aliases)
df['ships_to'] = df['ships_to'].replace(aliases)

# Remove invalids
invalid_from = ['undeclared', 'Anywhere', 'My Inbox']
df = df[~df['ships_from'].isin(invalid_from)]

# Expand Worldwide
worldwide_targets = ['United States of America', 'Germany', 'United Kingdom', 'Australia']
worldwide_rows = df[df['ships_to'] == 'Worldwide']
expanded = pd.concat([
    worldwide_rows.assign(ships_to=target) for target in worldwide_targets
])
df = pd.concat([df[df['ships_to'] != 'Worldwide'], expanded])

# Keep only countries with coords
df = df[df['ships_from'].isin(country_coords) & df['ships_to'].isin(country_coords)]

# **NOW create your options**
country_options = sorted(list(set(country_coords.keys()) & set(df['ships_from'].unique())))

# UI filters
selected_from = st.selectbox('Filter by Origin Country (optional):', ["All"] + country_options)
selected_to = st.selectbox('Filter by Destination Country (optional):', ["All"] + sorted(list(country_coords.keys())))

if selected_from != "All":
    df = df[df['ships_from'] == selected_from]
if selected_to != "All":
    df = df[df['ships_to'] == selected_to]



# Flow data
flow_data = df.groupby(['ships_from', 'ships_to']).size().reset_index(name='count')

# All countries involved
all_countries = sorted(set(flow_data['ships_from']).union(set(flow_data['ships_to'])))

# Assign distinct colors using a large qualitative palette
#palette = pc.qualitative.Alphabet * ((len(all_countries) // 26) + 1)

#color_map = {country: palette[i] for i, country in enumerate(all_countries)}
custom_15_palette = [
    '#e6194b',  # red
    '#3cb44b',  # green
    '#ffe119',  # yellow
    '#4363d8',  # blue
    '#f58231',  # orange
    '#911eb4',  # purple
    '#46f0f0',  # cyan
    '#f032e6',  # magenta
    '#bcf60c',  # lime
    '#fabebe',  # light pink
    '#008080',  # teal
    '#e6beff',  # lavender
    '#9a6324',  # brown
    '#800000',  # maroon
    '#aaffc3',  # mint green
]
color_map = {country: custom_15_palette[i] for i, country in enumerate(all_countries)}

def interpolate_line(lat1, lon1, lat2, lon2, steps=10):
    lats = [lat1 + (lat2 - lat1) * i / steps for i in range(steps + 1)]
    lons = [lon1 + (lon2 - lon1) * i / steps for i in range(steps + 1)]
    return lats, lons

# Arrow traces
arrow_traces = []

for _, row in flow_data.iterrows():
    lat1, lon1 = country_coords[row['ships_from']]
    lat2, lon2 = country_coords[row['ships_to']]
    
    lats, lons = interpolate_line(lat1, lon1, lat2, lon2)

    arrow_traces.append(
        go.Scattergeo(
            lat=lats,
            lon=lons,
            mode='lines',
            line=dict(width=1.2, color=color_map[row['ships_from']]),
            opacity=0.6,
            hoverinfo='text',
            text=[f"{row['ships_from']} ➤ {row['ships_to']}<br>Count: {row['count']}"] * len(lats),
            showlegend=False
        )
    )

# Origin country bubbles
origin_counts = flow_data.groupby('ships_from')['count'].sum().reset_index()
origin_traces = []

for _, row in origin_counts.iterrows():
    country = row['ships_from']
    count = row['count']
    lat, lon = country_coords[country]
    origin_traces.append(
        go.Scattergeo(
            lon=[lon],
            lat=[lat],
            mode='markers',
            name=country,
            marker=dict(
                size=np.interp(np.log10(count), [1, 6], [6, 18]),
                color=color_map[country],
                line=dict(width=0.5, color='white')
            ),
            showlegend=True
        )
    )
    origin_traces.append(
        go.Scattergeo(
            lon=[lon],
            lat=[lat],
            mode='text',
            text=[country],
            textposition='top center',
            hoverinfo='skip',
            showlegend=False
        )
    )

# Destination bubbles
dest_counts = flow_data.groupby('ships_to')['count'].sum().reset_index()
dest_trace = go.Scattergeo(
    lon=[country_coords[c][1] for c in dest_counts['ships_to']],
    lat=[country_coords[c][0] for c in dest_counts['ships_to']],
    text=dest_counts['ships_to'],
    mode='markers',
    marker=dict(
        size=[np.interp(np.log10(c), [1, 6], [5, 16]) for c in dest_counts['count']],
        color=[color_map[c] for c in dest_counts['ships_to']],
        opacity=0.7,
        line=dict(width=0.5, color='white')
    ),
    name='Destinations',
    showlegend=False
)

# Layout
layout = go.Layout(
    title='🌍 Shipping Network on a Globe',
    geo=dict(
        projection_type='orthographic',
        showland=True,
        landcolor='rgb(217, 217, 217)',
        showcountries=True,
        countrycolor='rgb(204, 204, 204)',
        lakecolor='#0F1117',  # Set the water background to black
        bgcolor='#0F1117',    # Set the background color behind the globe to black
        showcoastlines=True, # Optional: Show coastlines
        showocean=True,      # Optional: Show oceans
        domain=dict(x=[0, 1], y=[0, 1])
    ),
    plot_bgcolor='#0F1117',   # Set the plot background to black (behind the globe)
    font=dict(color='white'),  # Set the text color to white for better contrast
    title_font=dict(color='white'),  # Set the title font color to white
    showlegend=True,
    legend=dict(font=dict(color='white')),  # Set the legend font color to white
    autosize=True
)



# Final figure
fig3 = go.Figure(data=origin_traces + [dest_trace] + arrow_traces, layout=layout)
fig3.update_layout(height=800)

# Plot
st.plotly_chart(fig3, use_container_width=True)

##
st.subheader("Top Shipping Origins and Destinations per Category")

top_categories = df['category_name'].value_counts().head(10).index.tolist()
filtered_df = df[df['category_name'].isin(top_categories)]

ships_from_counts = filtered_df.groupby('category_name')['ships_from'].value_counts()\
    .groupby(level=0, group_keys=False).nlargest(3).reset_index(name='count')
ships_to_counts = filtered_df.groupby('category_name')['ships_to'].value_counts()\
    .groupby(level=0, group_keys=False).nlargest(3).reset_index(name='count')

# Shipping Origins

# OPTION 1: Remove 0 counts
#ships_from_counts = ships_from_counts[ships_from_counts['count'] > 0]

fig4 = px.bar(
    ships_from_counts,
    x='category_name',        # one bar-group per category
    y='count',
    color='ships_from',       # bars within each group are colored by origin
    barmode='group',          # show them side-by-side
    title='Top Shipping Origins per Top 10 Categories',
    labels={'category_name': 'Category', 'count': 'Count', 'ships_from': 'Ships From'}
)

# log scale
fig4.update_yaxes(type='log')

# rotate x-labels so they don't overlap
fig4.update_xaxes(tickangle=-45)

fig4.update_layout(
    legend_title_text='Ships From',
    margin=dict(t=80, b=100),
    height=500
)

st.plotly_chart(fig4)

###
fig5 = px.bar(
    ships_to_counts,
    x='category_name',        # one bar-group per category
    y='count',
    color='ships_to',       # bars within each group are colored by origin
    barmode='group',          # show them side-by-side
    title='Top Shipping Destinations per Top 10 Categories',
    labels={'category_name': 'Category', 'count': 'Count', 'ships_to': 'Ships To'}
)

# log scale if you still want it
fig5.update_yaxes(type='log')

# rotate x-labels so they don't overlap
fig5.update_xaxes(tickangle=-45)

fig5.update_layout(
    legend_title_text='Ships From',
    margin=dict(t=80, b=100),
    height=500
)

st.plotly_chart(fig5)
