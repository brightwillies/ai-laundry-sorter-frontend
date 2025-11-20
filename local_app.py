import streamlit as st
import requests
import json
from PIL import Image
import io
import base64

# ============================
# API CONFIGURATION
# ============================
CLOTH_API_URL = "http://localhost:8001/predict"
COLOR_API_URL = "http://localhost:8002/predict"
FABRIC_API_URL = "http://localhost:8003/predict"

# ============================
# WASHING RECOMMENDATIONS
# ============================
BRIGHT_WASHING = """
✨ **Bright Clothes Care:**
- Wash with other bright/pastel colors
- Avoid mixing with dark fabrics  
- Use cold or warm water (30-40°C)
- Turn inside out to preserve colors
"""

DARK_WASHING = """
🌑 **Dark Clothes Care:**
- Wash separately or with other dark clothes
- Use cold water to prevent fading
- Turn inside out before washing
- Avoid over-drying
"""

LEATHER_WASHING = """
🧥 **Leather Care:**
- Professional cleaning recommended
- Spot clean with damp cloth if needed
- Avoid machine washing
- Store in cool, dry place
"""

# ============================
# PAGE CONFIG
# ============================
st.set_page_config(
    page_title="AI Laundry Sorter",
    page_icon="🧺",
    layout="wide"
)

# ============================
# CUSTOM STYLING
# ============================
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .fabric-section {
        background-color: #f0f2f6;
        padding: 1.5rem;
        border-radius: 10px;
        margin: 1rem 0;
    }
    .bright-section {
        background-color: #fff2cc;
        padding: 1rem;
        border-radius: 8px;
        margin: 0.5rem 0;
        border-left: 4px solid #ffd700;
    }
    .dark-section {
        background-color: #333333;
        color: white;
        padding: 1rem;
        border-radius: 8px;
        margin: 0.5rem 0;
        border-left: 4px solid #666666;
    }
    .washing-tip {
        background-color: #d4edda;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #28a745;
    }
    .leather-tip {
        background-color: #f8d7da;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #dc3545;
    }
</style>
""", unsafe_allow_html=True)

# ============================
# MAIN APP
# ============================
st.markdown('<div class="main-header">🧺 AI Laundry Sorter</div>', unsafe_allow_html=True)
st.markdown("### Upload clothing images → Get fabric type, color, clothing category, and washing recommendations")

# File upload
uploaded_files = st.file_uploader(
    "Choose clothing images",
    type=["jpg", "jpeg", "png", "webp"],
    accept_multiple_files=True,
    help="Upload one or multiple clothing images"
)

if uploaded_files:
    for uploaded_file in uploaded_files:
        st.markdown("---")
        col1, col2 = st.columns([1, 2])
        
        with col1:
            # Display image
            image = Image.open(uploaded_file)
            st.image(image, caption=uploaded_file.name, use_container_width=True)
        
        with col2:
            with st.spinner("Analyzing clothing..."):
                try:
                    # Prepare image for API
                    img_bytes = io.BytesIO()
                    image.save(img_bytes, format='JPEG')
                    img_bytes.seek(0)
                    
                    # Call all three APIs
                    fabric_response = requests.post(
                        FABRIC_API_URL,
                        files={"file": (uploaded_file.name, img_bytes, "image/jpeg")}
                    )
                    img_bytes.seek(0)
                    
                    color_response = requests.post(
                        COLOR_API_URL,
                        files={"file": (uploaded_file.name, img_bytes, "image/jpeg")}
                    )
                    img_bytes.seek(0)
                    
                    cloth_response = requests.post(
                        CLOTH_API_URL,
                        files={"file": (uploaded_file.name, img_bytes, "image/jpeg")}
                    )
                    
                    if (fabric_response.status_code == 200 and 
                        color_response.status_code == 200 and 
                        cloth_response.status_code == 200):
                        
                        fabric_data = fabric_response.json()
                        color_data = color_response.json()
                        cloth_data = cloth_response.json()
                        
                        # Display results in hierarchy
                        st.markdown(f'<div class="fabric-section">', unsafe_allow_html=True)
                        st.markdown(f"### 🧵 **Fabric**: {fabric_data['fabric_type'].title()}")
                        st.metric("Confidence", f"{fabric_data['confidence']:.1f}%")
                        
                        # Check if it's clothing
                        if cloth_data.get('is_clothing', True) and cloth_data['cloth_type'] != 'Not Clothing':
                            cloth_type = cloth_data['cloth_type']
                            cloth_confidence = cloth_data['confidence']
                            
                            # For leather, show special washing (ignore color)
                            if fabric_data['fabric_type'] == 'leather':
                                st.markdown(f"#### 👕 **Clothing Type**: {cloth_type}")
                                st.markdown(f"**Confidence**: {cloth_confidence:.1%}")
                                st.markdown(f'<div class="leather-tip">{LEATHER_WASHING}</div>', unsafe_allow_html=True)
                            else:
                                # For other fabrics, show color classification
                                color_type = color_data['color']
                                color_confidence = color_data['confidence']
                                
                                st.markdown(f"#### 👕 **Clothing Type**: {cloth_type}")
                                st.markdown(f"**Confidence**: {cloth_confidence:.1%}")
                                
                                # Display color section with appropriate styling
                                if color_type == "bright":
                                    st.markdown('<div class="bright-section">', unsafe_allow_html=True)
                                    st.markdown(f"##### 🌟 **Color**: {color_type.title()} ({color_confidence:.1%})")
                                    st.markdown("</div>", unsafe_allow_html=True)
                                    washing_tip = BRIGHT_WASHING
                                else:
                                    st.markdown('<div class="dark-section">', unsafe_allow_html=True)
                                    st.markdown(f"##### 🌑 **Color**: {color_type.title()} ({color_confidence:.1%})")
                                    st.markdown("</div>", unsafe_allow_html=True)
                                    washing_tip = DARK_WASHING
                                
                                # Show combined washing advice
                                st.markdown(f'<div class="washing-tip">{washing_tip}</div>', unsafe_allow_html=True)
                                st.markdown(f"**Fabric Care**: {fabric_data['washing_advice']}")
                        else:
                            st.warning("🚫 **Not Clothing** - This item doesn't appear to be clothing")
                        
                        st.markdown("</div>", unsafe_allow_html=True)
                        
                        # Show detailed predictions
                        with st.expander("View detailed predictions"):
                            col_pred1, col_pred2, col_pred3 = st.columns(3)
                            
                            with col_pred1:
                                st.markdown("**Fabric Probabilities:**")
                                for fabric, prob in fabric_data['all_predictions'].items():
                                    st.progress(prob/100, text=f"{fabric}: {prob:.1f}%")
                            
                            with col_pred2:
                                st.markdown("**Clothing Type Probabilities:**")
                                for cloth, prob in cloth_data['all_predictions'].items():
                                    st.progress(prob, text=f"{cloth}: {prob:.1%}")
                            
                            with col_pred3:
                                st.markdown("**Color Analysis:**")
                                st.metric("Brightness", f"{color_data['brightness_L']:.1f}")
                                st.metric("Saturation", f"{color_data['saturation']:.1f}")
                                st.metric("Colorfulness", f"{color_data['colorfulness']:.1f}")
                    
                    else:
                        st.error("❌ Error calling APIs")
                        
                except Exception as e:
                    st.error(f"❌ Error processing image: {str(e)}")

# Sidebar information
with st.sidebar:
    st.markdown("### 📊 System Status")
    
    # Check API health
    try:
        cloth_health = requests.get("http://localhost:8001/health").status_code == 200
        color_health = requests.get("http://localhost:8002/health").status_code == 200
        fabric_health = requests.get("http://localhost:8003/health").status_code == 200
        
        st.success("✅ Cloth Type API: Online" if cloth_health else "❌ Cloth Type API: Offline")
        st.success("✅ Color API: Online" if color_health else "❌ Color API: Offline")
        st.success("✅ Fabric API: Online" if fabric_health else "❌ Fabric API: Offline")
        
    except:
        st.error("❌ Cannot connect to APIs")
    
    st.markdown("---")
    st.markdown("### 🧼 Supported Fabrics")
    st.markdown("- Cotton\n- Denim\n- Leather\n- Linen\n- Polyester\n- Silk")
    
    st.markdown("### 🎨 Color Analysis")
    st.markdown("- Bright Colors\n- Dark Colors")
    
    st.markdown("### 👕 Clothing Types")
    st.markdown("- Shirts/Blouses\n- Tops/T-shirts\n- Pants\n- Dresses\n- Jackets\n- And more...")

st.markdown("---")
st.caption("AI Laundry Sorter • Complete System: Fabric + Color + Clothing Type Detection")