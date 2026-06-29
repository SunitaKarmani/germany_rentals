import streamlit as st
import pandas as pd
import plotly.express as px
import requests
import io

# Page configuration
st.set_page_config(
    page_title="German Rental Market Analysis",
    layout="wide"
)

# Title
st.title("German Rental Market Analysis")

# Data loading function
@st.cache_data
def load_data():
    file_id = "1_pJo6fWPcphqKBmKWqLi2huc3Zdy14ep"
    url = f"https://drive.google.com/uc?export=download&id={file_id}"
    
    response = requests.get(url)
    response.raise_for_status()
    
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
    st.success()
except Exception as e:
    st.error(f"Error loading data: {e}")
    st.stop()

# Sidebar filters
st.sidebar.header("🔍 Filter Data")

states = ['All States'] + sorted(df['regio1'].unique().tolist())
selected_state = st.sidebar.selectbox('Select Federal State', states)

segments = ['All Segments'] + sorted(df['price_category'].unique().tolist())
selected_segment = st.sidebar.selectbox('Select Price Segment', segments)

# Apply filters
filtered_df = df.copy()
if selected_state != 'All States':
    filtered_df = filtered_df[filtered_df['regio1'] == selected_state]
if selected_segment != 'All Segments':
    filtered_df = filtered_df[filtered_df['price_category'] == selected_segment]

# Check if filtered_df is empty
if len(filtered_df) == 0:
    st.warning("⚠️ No data available for the selected filters. Please adjust your selection.")
    st.stop()

# Key metrics
st.subheader("Key Metrics")
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


# TABS

tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs([
    "Market Segments",
    "Geography",
    "Amenities",
    "Relationships",
    "Property Condition",
    "Property Characteristics",
    "Price per m²",
    "Overview"
])


# TAB 1: MARKET SEGMENTS

with tab1:
    st.subheader("Market Segments Analysis")
    
    segment_data = filtered_df.groupby('price_category').agg({
        'totalRent': ['mean', 'count'],
        'livingSpace': 'mean'
    }).round(1)
    segment_data.columns = ['avg_rent', 'count', 'avg_space']
    segment_data = segment_data.reset_index()
    
    col1, col2 = st.columns(2)
    
    with col1:
        fig1 = px.pie(segment_data, values='count', names='price_category', 
                     title='Market Share by Price Segment')
        fig1.update_traces(textinfo='percent+label')
        st.plotly_chart(fig1, use_container_width=True)
    
    with col2:
        fig2 = px.bar(segment_data, x='price_category', y='avg_rent',
                     title='Average Rent by Segment', text='avg_rent')
        fig2.update_traces(texttemplate='€%{text:.0f}', textposition='outside')
        st.plotly_chart(fig2, use_container_width=True)
    
    fig3 = px.scatter(filtered_df.sample(min(1000, len(filtered_df))),
                     x='livingSpace', y='totalRent', color='price_category',
                     title='Living Space vs Rent Relationship', 
                     labels={'livingSpace': 'Space (m²)', 'totalRent': 'Rent (€)'})
    st.plotly_chart(fig3, use_container_width=True)


# TAB 2: GEOGRAPHY

with tab2:
    st.subheader("Geographic Analysis")
    
    state_data = filtered_df.groupby('regio1').agg({
        'totalRent': ['mean', 'count'],
        'livingSpace': 'mean'
    }).round(1)
    state_data.columns = ['avg_rent', 'count', 'avg_space']
    state_data = state_data.reset_index().sort_values('avg_rent', ascending=False)
    
    col1, col2 = st.columns(2)
    
    with col1:
        fig4 = px.bar(state_data, x='regio1', y='avg_rent', 
                     title='Average Rent by State', text='avg_rent')
        fig4.update_traces(texttemplate='€%{text:.0f}', textposition='outside')
        fig4.update_xaxes(tickangle=45)
        st.plotly_chart(fig4, use_container_width=True)
    
    with col2:
        fig5 = px.pie(state_data, values='count', names='regio1',
                     title='Listings Distribution by State')
        st.plotly_chart(fig5, use_container_width=True)


# TAB 3: AMENITIES

with tab3:
    st.subheader("Amenities Analysis")
    
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


# TAB 4: RELATIONSHIPS

with tab4:
    st.subheader("Relationship Analysis")
    
    segment_state = pd.crosstab(filtered_df['regio1'], filtered_df['price_category'], 
                               normalize='index') * 100
    fig9 = px.imshow(segment_state, title='Price Segments by State (%)',
                    color_continuous_scale='Blues')
    st.plotly_chart(fig9, use_container_width=True)


# TAB 5: PROPERTY CONDITION

with tab5:
    st.subheader("Property Condition Analysis")
    
    if 'condition' in filtered_df.columns:
        
        if filtered_df['condition'].notna().sum() > 0:
            
            plot_df = filtered_df.dropna(subset=['condition']).copy()
            
            if len(plot_df) > 0:
                
                col1, col2 = st.columns(2)
                
                with col1:
                    condition_rent = plot_df.groupby('condition')['totalRent'].mean().reset_index()
                    condition_rent = condition_rent.sort_values('totalRent', ascending=True)
                    
                    fig_condition_rent = px.bar(
                        condition_rent,
                        x='totalRent',
                        y='condition',
                        orientation='h',
                        title='Average Rent by Property Condition',
                        labels={'totalRent': 'Average Rent (€)', 'condition': ''},
                        text='totalRent',
                        color='totalRent',
                        color_continuous_scale='Viridis'
                    )
                    fig_condition_rent.update_traces(texttemplate='€%{text:.0f}', textposition='outside')
                    fig_condition_rent.update_layout(height=400)
                    st.plotly_chart(fig_condition_rent, use_container_width=True)
                
                with col2:
                    condition_by_segment = pd.crosstab(
                        plot_df['price_category'], 
                        plot_df['condition'], 
                        normalize='index'
                    ) * 100
                    condition_by_segment = condition_by_segment.round(1)
                    
                    condition_plot = condition_by_segment.reset_index().melt(
                        id_vars='price_category', 
                        value_name='percentage', 
                        var_name='condition'
                    )
                    
                    fig_condition_segment = px.bar(
                        condition_plot,
                        x='price_category',
                        y='percentage',
                        color='condition',
                        title='Condition Distribution by Market Segment',
                        labels={'price_category': 'Market Segment', 'percentage': '%'},
                        color_discrete_sequence=px.colors.qualitative.Set3
                    )
                    fig_condition_segment.update_layout(
                        height=400,
                        barmode='stack',
                        yaxis=dict(range=[0, 100])
                    )
                    fig_condition_segment.update_traces(
                        texttemplate='%{text:.1f}%', 
                        textposition='inside',
                        textfont=dict(size=9)
                    )
                    st.plotly_chart(fig_condition_segment, use_container_width=True)
                
                # Price Trend by Condition
                if 'calculated_pricetrend' in plot_df.columns:
                    if plot_df['calculated_pricetrend'].notna().sum() > 0:
                        
                        st.subheader("Price Trend by Property Condition")
                        
                        fig_trend = px.box(
                            plot_df,
                            x='condition',
                            y='calculated_pricetrend',
                            title='Price Trend by Property Condition',
                            labels={'condition': '', 'calculated_pricetrend': 'Deviation from Regional Median (€/m²)'},
                            color='condition',
                            color_discrete_sequence=px.colors.qualitative.Set3
                        )
                        fig_trend.add_hline(y=0, line_dash="dash", line_color="red", opacity=0.5)
                        fig_trend.update_xaxes(tickangle=45)
                        fig_trend.update_layout(height=450)
                        st.plotly_chart(fig_trend, use_container_width=True)


# TAB 6: PROPERTY CHARACTERISTICS

with tab6:
    st.subheader("Property Characteristics Analysis")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if 'typeOfFlat' in filtered_df.columns and filtered_df['typeOfFlat'].notna().sum() > 0:
            type_rent = filtered_df.groupby('typeOfFlat')['totalRent'].mean().sort_values(ascending=False).reset_index()
            
            fig_type = px.bar(
                type_rent,
                x='typeOfFlat',
                y='totalRent',
                title='Average Rent by Property Type',
                labels={'typeOfFlat': '', 'totalRent': 'Average Rent (€)'},
                text='totalRent',
                color='totalRent',
                color_continuous_scale='Viridis'
            )
            fig_type.update_traces(texttemplate='€%{text:.0f}', textposition='outside')
            fig_type.update_xaxes(tickangle=45)
            fig_type.update_layout(height=400)
            st.plotly_chart(fig_type, use_container_width=True)
        else:
            st.info("No property type data available.")
    
    with col2:
        if 'heatingType' in filtered_df.columns and filtered_df['heatingType'].notna().sum() > 0:
            heating_rent = filtered_df.groupby('heatingType')['totalRent'].mean().sort_values(ascending=False).reset_index()
            
            fig_heating = px.bar(
                heating_rent.head(10),
                x='heatingType',
                y='totalRent',
                title='Average Rent by Heating Type (Top 10)',
                labels={'heatingType': '', 'totalRent': 'Average Rent (€)'},
                text='totalRent',
                color='totalRent',
                color_continuous_scale='Plasma'
            )
            fig_heating.update_traces(texttemplate='€%{text:.0f}', textposition='outside')
            fig_heating.update_xaxes(tickangle=45)
            fig_heating.update_layout(height=400)
            st.plotly_chart(fig_heating, use_container_width=True)
        else:
            st.info("No heating type data available.")
    
    col3, col4 = st.columns(2)
    
    with col3:
        if 'yearConstructed' in filtered_df.columns and filtered_df['yearConstructed'].notna().sum() > 0:
            year_rent = filtered_df.groupby('yearConstructed')['totalRent'].mean().reset_index()
            year_rent = year_rent[year_rent['yearConstructed'] > 1900]
            
            if len(year_rent) > 0:
                fig_year = px.line(
                    year_rent,
                    x='yearConstructed',
                    y='totalRent',
                    title='Average Rent by Construction Year',
                    labels={'yearConstructed': 'Construction Year', 'totalRent': 'Average Rent (€)'},
                    markers=True,
                    color_discrete_sequence=['#2E86AB']
                )
                fig_year.update_layout(height=400)
                st.plotly_chart(fig_year, use_container_width=True)
            else:
                st.info("No construction year data available.")
        else:
            st.info("No construction year data available.")


# TAB 7: PRICE PER SQUARE METER

with tab7:
    st.subheader("Price per Square Meter Analysis")
    
    filtered_df['price_per_sqm'] = filtered_df['totalRent'] / filtered_df['livingSpace']
    
    col1, col2 = st.columns(2)
    
    with col1:
        sqm_plot_df = filtered_df[filtered_df['price_per_sqm'] < 30].copy()
        
        if len(sqm_plot_df) > 0:
            fig_sqm_dist = px.histogram(
                sqm_plot_df,
                x='price_per_sqm',
                nbins=50,
                title='Price per Square Meter Distribution',
                labels={'price_per_sqm': 'Price per m² (€)', 'count': 'Number of Listings'},
                color_discrete_sequence=['#F18F01']
            )
            fig_sqm_dist.update_layout(height=400)
            st.plotly_chart(fig_sqm_dist, use_container_width=True)
        else:
            st.info("No price per m² data available.")
    
    with col2:
        if 'condition' in filtered_df.columns and filtered_df['condition'].notna().sum() > 0:
            sqm_condition = filtered_df.groupby('condition')['price_per_sqm'].mean().sort_values(ascending=False).reset_index()
            
            fig_sqm_condition = px.bar(
                sqm_condition,
                x='condition',
                y='price_per_sqm',
                title='Price per m² by Property Condition',
                labels={'condition': '', 'price_per_sqm': 'Price per m² (€)'},
                text='price_per_sqm',
                color='price_per_sqm',
                color_continuous_scale='Viridis'
            )
            fig_sqm_condition.update_traces(texttemplate='€%{text:.2f}', textposition='outside')
            fig_sqm_condition.update_xaxes(tickangle=45)
            fig_sqm_condition.update_layout(height=400)
            st.plotly_chart(fig_sqm_condition, use_container_width=True)
        else:
            st.info("No condition data available for price per m² analysis.")
    
    col3, col4 = st.columns(2)
    
    with col3:
        if 'regio3' in filtered_df.columns and filtered_df['regio3'].notna().sum() > 0:
            sqm_city = filtered_df.groupby('regio3')['price_per_sqm'].mean().sort_values(ascending=False).head(10).reset_index()
            
            fig_sqm_city = px.bar(
                sqm_city,
                x='regio3',
                y='price_per_sqm',
                title='Top 10 Cities by Price per m²',
                labels={'regio3': '', 'price_per_sqm': 'Price per m² (€)'},
                text='price_per_sqm',
                color='price_per_sqm',
                color_continuous_scale='Reds'
            )
            fig_sqm_city.update_traces(texttemplate='€%{text:.2f}', textposition='outside')
            fig_sqm_city.update_xaxes(tickangle=45)
            fig_sqm_city.update_layout(height=400)
            st.plotly_chart(fig_sqm_city, use_container_width=True)
        else:
            st.info("No city data available for price per m² analysis.")


# TAB 8: OVERVIEW

with tab8:
    st.subheader("Overview")
    
    col1, col2 = st.columns(2)
    
    with col1:
        fig_rent = px.histogram(
            filtered_df,
            x='totalRent',
            nbins=100,
            title='Total Rent Distribution',
            labels={'totalRent': 'Total Rent (€)', 'count': 'Number of Listings'},
            color_discrete_sequence=['salmon']
        )
        st.plotly_chart(fig_rent, use_container_width=True)
    
    with col2:
        fig_space = px.histogram(
            filtered_df,
            x='livingSpace',
            nbins=50,
            title='Living Space Distribution',
            labels={'livingSpace': 'Living Space (m²)', 'count': 'Number of Listings'},
            color_discrete_sequence=['#2E86AB']
        )
        st.plotly_chart(fig_space, use_container_width=True)
    
    if 'date' in filtered_df.columns and filtered_df['date'].notna().sum() > 0:
        try:
            filtered_df['date_parsed'] = pd.to_datetime(filtered_df['date'], format='%b%y')
            monthly_count = filtered_df.groupby(filtered_df['date_parsed'].dt.to_period('M')).size().reset_index()
            monthly_count.columns = ['month', 'count']
            monthly_count['month'] = monthly_count['month'].dt.to_timestamp()
            
            fig_monthly = px.bar(
                monthly_count,
                x='month',
                y='count',
                title='Number of Listings by Month',
                labels={'month': 'Month', 'count': 'Number of Listings'},
                color_discrete_sequence=['green']
            )
            fig_monthly.update_xaxes(tickangle=45)
            st.plotly_chart(fig_monthly, use_container_width=True)
        except:
            st.info("Date data could not be parsed.")

# Footer
st.markdown("---")
st.caption("Data source: ImmobilienScout24 (2018-2020) | Built with Streamlit")
