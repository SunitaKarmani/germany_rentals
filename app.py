import streamlit as st
import pandas as pd
import plotly.express as px
import requests
import io

# Page configuration
st.set_page_config(
    page_title="German Rental Market Analysis",
    page_icon="🏠",
    layout="wide"
)

# Title
st.title("🏠 German Rental Market Analysis")
st.markdown("**Thesis Dashboard - Interactive Analysis**")

# Data loading function
@st.cache_data
def load_data():
    file_id = "https://limewire.com/d/WmWYP#lscaC0eejP"
    url = f"https://drive.google.com/uc?export=download&id={file_id}"
    
    # Download the file
    response = requests.get(url)
    response.raise_for_status()  # Check for errors
    
    # Load into DataFrame
    df = pd.read_csv(io.StringIO(response.text))
   
    
    # Create price categories
    df['price_category'] = pd.cut(df['totalRent'], 
                                 bins=[0, 500, 1000, 1500, 3000],
                                 labels=['Budget', 'Economy', 'Mid-Range', 'Premium'])
    df = df[df['totalRent'] <= 3000].copy()
    
    return df

# Load the data
try:
    df = load_data()
    st.success("✅ Data loaded successfully!")
except Exception as e:
    st.error(f"Error loading data: {e}")
    st.stop()

# Sidebar filters
st.sidebar.header("🔍 Filter Data")

# State filter
states = ['All States'] + sorted(df['regio1'].unique().tolist())
selected_state = st.sidebar.selectbox('Select Federal State', states)

# Price segment filter
segments = ['All Segments'] + sorted(df['price_category'].unique().tolist())
selected_segment = st.sidebar.selectbox('Select Price Segment', segments)

# Apply filters
filtered_df = df.copy()
if selected_state != 'All States':
    filtered_df = filtered_df[filtered_df['regio1'] == selected_state]
if selected_segment != 'All Segments':
    filtered_df = filtered_df[filtered_df['price_category'] == selected_segment]

# Key metrics
st.subheader("📊 Key Metrics")
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Total Listings", f"{len(filtered_df):,}")

with col2:
    avg_rent = filtered_df['totalRent'].mean()
    st.metric("Average Rent", f"€{avg_rent:.0f}")

with col3:
    avg_space = filtered_df['livingSpace'].mean()
    st.metric("Average Space", f"{avg_space:.1f} m²")

with col4:
    price_per_sqm = (filtered_df['totalRent'] / filtered_df['livingSpace']).mean()
    st.metric("Price per m²", f"€{price_per_sqm:.1f}")

# Tabs for different analyses
tab1, tab2, tab3, tab4 = st.tabs(["🏘️ Market Segments", "🗺️ Geography", "💎 Amenities", "🔗 Relationships"])

with tab1:
    st.subheader("Market Segments Analysis")
    
    # Segment analysis
    segment_data = filtered_df.groupby('price_category').agg({
        'totalRent': ['mean', 'count'],
        'livingSpace': 'mean'
    }).round(1)
    segment_data.columns = ['avg_rent', 'count', 'avg_space']
    segment_data = segment_data.reset_index()
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Market share
        fig1 = px.pie(segment_data, values='count', names='price_category', 
                     title='Market Share by Price Segment')
        fig1.update_traces(textinfo='percent+label')
        st.plotly_chart(fig1, use_container_width=True)
    
    with col2:
        # Average rent
        fig2 = px.bar(segment_data, x='price_category', y='avg_rent',
                     title='Average Rent by Segment', text='avg_rent')
        fig2.update_traces(texttemplate='€%{text:.0f}', textposition='outside')
        st.plotly_chart(fig2, use_container_width=True)
    
    # Space vs Rent
    fig3 = px.scatter(filtered_df.sample(min(1000, len(filtered_df))),
                     x='livingSpace', y='totalRent', color='price_category',
                     title='Living Space vs Rent Relationship', 
                     labels={'livingSpace': 'Space (m²)', 'totalRent': 'Rent (€)'})
    st.plotly_chart(fig3, use_container_width=True)

with tab2:
    st.subheader("Geographic Analysis")
    
    # State analysis
    state_data = filtered_df.groupby('regio1').agg({
        'totalRent': ['mean', 'count'],
        'livingSpace': 'mean'
    }).round(1)
    state_data.columns = ['avg_rent', 'count', 'avg_space']
    state_data = state_data.reset_index().sort_values('avg_rent', ascending=False)
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Rent by state
        fig4 = px.bar(state_data, x='regio1', y='avg_rent', 
                     title='Average Rent by State', text='avg_rent')
        fig4.update_traces(texttemplate='€%{text:.0f}', textposition='outside')
        fig4.update_xaxes(tickangle=45)
        st.plotly_chart(fig4, use_container_width=True)
    
    with col2:
        # State distribution
        fig5 = px.pie(state_data, values='count', names='regio1',
                     title='Listings Distribution by State')
        st.plotly_chart(fig5, use_container_width=True)

with tab3:
    st.subheader("Amenities Analysis")
    
    # Analyze amenities
    amenities = ['balcony', 'hasKitchen', 'lift', 'garden', 'cellar']
    amenity_results = []
    
    for amenity in amenities:
        if amenity in filtered_df.columns:
            with_amenity = filtered_df[filtered_df[amenity] == True]['totalRent'].mean()
            without_amenity = filtered_df[filtered_df[amenity] == False]['totalRent'].mean()
            
            if without_amenity > 0:
                premium_pct = ((with_amenity - without_amenity) / without_amenity) * 100
                amenity_results.append({
                    'amenity': amenity,
                    'premium_%': premium_pct,
                    'prevalence': (filtered_df[amenity].sum() / len(filtered_df)) * 100
                })
    
    if amenity_results:
        amenity_df = pd.DataFrame(amenity_results).sort_values('premium_%', ascending=False)
        
        col1, col2 = st.columns(2)
        
        with col1:
            fig7 = px.bar(amenity_df, x='amenity', y='premium_%',
                         title='Price Premium for Amenities', text='premium_%')
            fig7.update_traces(texttemplate='%{text:+.1f}%', textposition='outside')
            st.plotly_chart(fig7, use_container_width=True)
        
        with col2:
            fig8 = px.bar(amenity_df, x='amenity', y='prevalence',
                         title='Amenity Prevalence', text='prevalence')
            fig8.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
            st.plotly_chart(fig8, use_container_width=True)

with tab4:
    st.subheader("Relationship Analysis")
    
    # Segments by state heatmap
    segment_state = pd.crosstab(filtered_df['regio1'], filtered_df['price_category'], 
                               normalize='index') * 100
    fig9 = px.imshow(segment_state, title='Price Segments by State (%)',
                    color_continuous_scale='Blues')
    st.plotly_chart(fig9, use_container_width=True)

# Footer
st.markdown("---")

st.markdown("**Thesis Research Dashboard** • Built with Streamlit")








