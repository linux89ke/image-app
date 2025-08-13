import streamlit as st
from PIL import Image, ImageColor
import requests
import io
import zipfile

# ---------------------------
# CONFIG
# ---------------------------
REMOVE_BG_API_KEY = st.secrets.get("REMOVE_BG_API_KEY", "")  # Store in Streamlit secrets

st.set_page_config(page_title="Batch Background Remover", layout="wide")
st.title("🧼 remove.bg Product Background Remover")

# ---------------------------
# Remove background using remove.bg API
# ---------------------------
def remove_bg_api(image_bytes, bg_choice="transparent", size=(1000, 1000)):
    url = "https://api.remove.bg/v1.0/removebg"
    
    # API parameters
    params = {"size": "auto"}
    if bg_choice == "white":
        params["bg_color"] = "ffffff"
    elif bg_choice == "#F2F2F2":
        params["bg_color"] = "f2f2f2"
    # transparent = default, so no bg_color param

    headers = {"X-Api-Key": REMOVE_BG_API_KEY}
    files = {"image_file": ("image.png", image_bytes, "image/png")}

    response = requests.post(url, headers=headers, files=files, data=params)
    
    if response.status_code == 200:
        result_img = Image.open(io.BytesIO(response.content))
        result_img = result_img.resize(size)
        return result_img
    else:
        st.error(f"API error {response.status_code}: {response.text}")
        return None

# ---------------------------
# UI inputs
# ---------------------------
uploaded_files = st.file_uploader("📤 Upload image(s)", type=["jpg", "jpeg", "png", "webp"], accept_multiple_files=True)
url_input = st.text_input("🔗 Or paste image URL (e.g. Jumia product image)")

bg_choice = st.radio("🎨 Background Replacement", ["white", "#F2F2F2", "transparent"])
resize_width = st.number_input("📏 Resize Width (px)", min_value=100, max_value=5000, value=1000, step=50)
resize_height = st.number_input("📐 Resize Height (px)", min_value=100, max_value=5000, value=1000, step=50)

if not REMOVE_BG_API_KEY:
    st.warning("⚠️ Please set your remove.bg API key in Streamlit secrets as 'REMOVE_BG_API_KEY'")
    st.stop()

# ---------------------------
# Collect images
# ---------------------------
image_queue = []

if url_input:
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(url_input, headers=headers)
        if r.status_code == 200:
            img = Image.open(io.BytesIO(r.content)).convert("RGBA")
            img_bytes = io.BytesIO()
            img.save(img_bytes, format="PNG")
            img_bytes.seek(0)
            image_queue.append(("linked_image.png", img_bytes))
        else:
            st.error(f"❌ Could not load image. HTTP {r.status_code}")
    except Exception as e:
        st.error(f"⚠️ Error loading image: {e}")

if uploaded_files:
    for file in uploaded_files:
        try:
            img = Image.open(file).convert("RGBA")
            img_bytes = io.BytesIO()
            img.save(img_bytes, format="PNG")
            img_bytes.seek(0)
            image_queue.append((file.name, img_bytes))
        except:
            st.warning(f"{file.name} is not a valid image.")

# ---------------------------
# Process images
# ---------------------------
zip_buffer = io.BytesIO()

if image_queue:
    st.subheader("✅ Processed Images")
    with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED) as zipf:
        progress = st.progress(0)
        for i, (name, img_bytes) in enumerate(image_queue):
            cleaned = remove_bg_api(img_bytes, bg_choice, (resize_width, resize_height))
            if cleaned:
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(f"**🖼️ {name} – Original**")
                    st.image(Image.open(img_bytes), width=300)
                with col2:
                    st.markdown("**🧼 Cleaned**")
                    st.image(cleaned, width=300)

                img_io = io.BytesIO()
                if bg_choice == "transparent":
                    cleaned.save(img_io, format="PNG")
                else:
                    cleaned.save(img_io, format="JPEG")
                zipf.writestr(name, img_io.getvalue())

            progress.progress((i+1) / len(image_queue))

    st.success("✅ All images processed successfully.")

    zip_buffer.seek(0)
    st.download_button(
        label="📦 Download All as ZIP",
        data=zip_buffer,
        file_name="cleaned_images.zip",
        mime="application/zip"
    )
