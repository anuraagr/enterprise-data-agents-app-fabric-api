import streamlit as st

# Page setup
st.set_page_config(
    page_title="Enterprise AI Agents | Microsoft", 
    page_icon="🏥", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for professional styling
st.markdown("""
<style>
    /* Main theme colors */
    :root {
        --primary-color: #0078D4;
        --secondary-color: #50E6FF;
        --accent-color: #00BCF2;
        --dark-bg: #1a1a2e;
        --card-bg: #16213e;
    }
    
    /* Hide default Streamlit elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Hero section styling */
    .hero-container {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 3rem 2rem;
        border-radius: 20px;
        margin-bottom: 2rem;
        text-align: center;
        box-shadow: 0 10px 40px rgba(102, 126, 234, 0.3);
    }
    
    .hero-title {
        font-size: 3rem;
        font-weight: 700;
        color: white;
        margin-bottom: 0.5rem;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
    }
    
    .hero-subtitle {
        font-size: 1.3rem;
        color: rgba(255,255,255,0.9);
        margin-bottom: 1rem;
    }
    
    .hero-badge {
        display: inline-block;
        background: rgba(255,255,255,0.2);
        padding: 0.5rem 1rem;
        border-radius: 20px;
        font-size: 0.9rem;
        color: white;
        backdrop-filter: blur(10px);
    }
    
    /* Feature cards */
    .feature-card {
        background: linear-gradient(145deg, #ffffff 0%, #f8f9fa 100%);
        border-radius: 16px;
        padding: 2rem;
        height: 100%;
        border: 1px solid #e9ecef;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(0,0,0,0.05);
    }
    
    .feature-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 30px rgba(0,0,0,0.12);
    }
    
    .feature-icon {
        font-size: 2.5rem;
        margin-bottom: 1rem;
    }
    
    .feature-title {
        font-size: 1.4rem;
        font-weight: 600;
        color: #1a1a2e;
        margin-bottom: 0.75rem;
    }
    
    .feature-description {
        color: #6c757d;
        font-size: 1rem;
        line-height: 1.6;
    }
    
    /* Stats section */
    .stats-container {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        border-radius: 16px;
        padding: 2rem;
        margin: 2rem 0;
    }
    
    .stat-value {
        font-size: 2.5rem;
        font-weight: 700;
        color: #50E6FF;
    }
    
    .stat-label {
        color: rgba(255,255,255,0.7);
        font-size: 0.9rem;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    /* CTA Button */
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        padding: 0.75rem 2rem;
        font-size: 1.1rem;
        font-weight: 600;
        border-radius: 30px;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(102, 126, 234, 0.6);
    }
    
    /* Footer styling */
    .footer {
        text-align: center;
        padding: 2rem;
        color: #6c757d;
        border-top: 1px solid #e9ecef;
        margin-top: 3rem;
    }
    
    .footer-logo {
        font-size: 1.5rem;
        margin-bottom: 0.5rem;
    }
    
    /* Capability tags */
    .capability-tag {
        display: inline-block;
        background: linear-gradient(135deg, #e8f4f8 0%, #d4edda 100%);
        padding: 0.4rem 1rem;
        border-radius: 20px;
        font-size: 0.85rem;
        color: #155724;
        margin: 0.25rem;
        font-weight: 500;
    }
    
    /* Section headers */
    .section-header {
        text-align: center;
        margin: 3rem 0 2rem 0;
    }
    
    .section-title {
        font-size: 2rem;
        font-weight: 700;
        color: #1a1a2e;
        margin-bottom: 0.5rem;
    }
    
    .section-subtitle {
        color: #6c757d;
        font-size: 1.1rem;
    }
</style>
""", unsafe_allow_html=True)

# Hero Section
st.markdown("""
<div class="hero-container">
    <div class="hero-title">🏥 Enterprise Healthcare AI</div>
    <div class="hero-subtitle">Intelligent Data Agents powered by Microsoft Fabric</div>
    <div class="hero-badge">✨ Synthea Healthcare Dataset • Natural Language SQL • Real-time Analytics</div>
</div>
""", unsafe_allow_html=True)

# Quick stats row
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric(label="🔬 Data Tables", value="19", delta="Silver + Gold")
with col2:
    st.metric(label="👥 Patients", value="115", delta="Synthetic")
with col3:
    st.metric(label="📋 Records", value="150K+", delta="Healthcare")
with col4:
    st.metric(label="🔒 Security", value="Azure AD", delta="Enterprise")

st.markdown("<br>", unsafe_allow_html=True)

# Section Header
st.markdown("""
<div class="section-header">
    <div class="section-title">What Can This Agent Do?</div>
    <div class="section-subtitle">Explore the capabilities of your healthcare AI assistant</div>
</div>
""", unsafe_allow_html=True)

# Feature Cards
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    <div class="feature-card">
        <div class="feature-icon">💬</div>
        <div class="feature-title">Natural Language to SQL</div>
        <div class="feature-description">
            Ask questions in plain English. The Fabric Data Agent automatically converts your queries to SQL 
            and retrieves results from the lakehouse.
        </div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="feature-card">
        <div class="feature-icon">⚡</div>
        <div class="feature-title">Real-time Analytics</div>
        <div class="feature-description">
            Query live data from Microsoft Fabric lakehouse with sub-second response times. 
            Silver and Gold data layers for optimal performance.
        </div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("""
    <div class="feature-card">
        <div class="feature-icon">📁</div>
        <div class="feature-title">File Upload & Analysis</div>
        <div class="feature-description">
            Upload CSV or Excel files for instant analysis. Combine your data with 
            the Synthea healthcare database for comprehensive insights.
        </div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# Capabilities Section
st.markdown("""
<div class="section-header">
    <div class="section-title">Synthea Database Schema</div>
    <div class="section-subtitle">Access comprehensive synthetic healthcare data</div>
</div>
""", unsafe_allow_html=True)

# Database tables in a nice grid
tables_col1, tables_col2, tables_col3 = st.columns(3)

with tables_col1:
    st.markdown("**👤 Patient Data**")
    st.markdown("""
    - `patients` - Demographics & coverage
    - `allergies` - Patient allergies
    - `careplans` - Care plan records
    - `immunizations` - Vaccination history
    """)

with tables_col2:
    st.markdown("**🏥 Clinical Data**")
    st.markdown("""
    - `conditions` - Diagnoses & diseases
    - `medications` - Prescriptions & costs
    - `procedures` - Medical procedures
    - `observations` - Vitals & lab results
    """)

with tables_col3:
    st.markdown("**🏢 Administrative**")
    st.markdown("""
    - `encounters` - Healthcare visits
    - `organizations` - Healthcare facilities
    - `providers` - Doctors & specialists
    - `payers` - Insurance information
    """)

st.markdown("<br><br>", unsafe_allow_html=True)

# CTA Section
cta_col1, cta_col2, cta_col3 = st.columns([1, 2, 1])
with cta_col2:
    st.markdown("<div style='text-align: center;'>", unsafe_allow_html=True)
    if st.button("🚀 Launch Healthcare Agent", use_container_width=True):
        st.switch_page("pages/01-Healthcare_Agent.py")
    st.markdown("</div>", unsafe_allow_html=True)

# Advanced Features Expander
with st.expander("🔧 Advanced Features & Architecture"):
    adv_col1, adv_col2 = st.columns(2)
    
    with adv_col1:
        st.markdown("**🛠️ Technical Stack**")
        st.markdown("""
        - **AI Backend**: Microsoft Fabric Data Agent
        - **Data Platform**: Fabric Lakehouse (Silver + Gold layers)
        - **Authentication**: Azure AD Service Principal
        - **Deployment**: Azure Container Apps
        - **Framework**: Streamlit + Python 3.11
        """)
    
    with adv_col2:
        st.markdown("**🎯 Use Cases**")
        st.markdown("""
        - Patient cohort analysis
        - Healthcare cost optimization
        - Treatment pattern discovery
        - Population health insights
        - Clinical operations reporting
        """)

# Footer
st.markdown("""
<div class="footer">
    <div class="footer-logo">🏥 Microsoft Healthcare AI</div>
    <div>Built with Azure AI Foundry • Microsoft Fabric • Streamlit</div>
    <div style="margin-top: 0.5rem; font-size: 0.85rem;">© 2026 Microsoft Corporation</div>
</div>
""", unsafe_allow_html=True)
