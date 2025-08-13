import streamlit as st
from PIL import Image, ImageColor
import requests
import io
import zipfile
from rembg import remove  # AI background removal

st.set_page_config(page_title="Batch Background Remover", layout="wide")
st.title("🧼 AI Background Remover (Product Isolation)")

# ---------------------------
# Background replacement function
# ---------------------------
def remove_any_bg(image: Image.Image, bg_choice="white", size=(1000, 1000)) -> Image.Image:
    # Remove background (returns transparent PNG)
    no_bg = remove(image)

    if bg_choice == "transparent":
        # Keep transparency and resize
        return no_bg.resize(size)

    # Convert choice to RGB
    if bg_choice == "white":
        bg_rgb = (255, 255, 255)
    else:
        bg_rgb = ImageColor.getrgb("#F2F2F2")

    # Create background
    bg_layer = Image.new("RGB", no_bg.size, bg_rgb)
    
    # Paste subject on background
    bg_layer.paste(no_bg, mask=no_bg.split()[3])  # Use alpha channel as mask

    # Resize if needed
    bg_layer = bg_layer.resize(size)
    return bg_layer

# --------------------------
# Upload section and inputs
# --------------------------
uploaded_files = st.file_uploader("📤 Upload image(s)", type=["jpg", "jpeg", "png", "webp"], accept_multiple_files=True)
url = st.text_input("🔗 Or paste image URL (e.g. Jumia product image)")

bg_choice = st.radio("🎨 Background Replacement", ["white", "#F2F2F2", "transparent"])
resize_width = st.number_input("📏 Resize Width (px)", min_value=100, max_value=5000, value=1000, step=50)
resize_height = st.number_input("📐 Resize Height (px)", min_value=100, max_value=5000, value=1000, step=50)

image_queue = []

# --------------------------
# Load image from URL
# --------------------------
if url:
    try:
        headers = {"User-Agent": "Mozilla/5.0", "Referer": "https://www.jumia.co.ke/"}
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            img = Image.open(io.BytesIO(response.content)).convert("RGBA")
            image_queue.append(("linked_image.png", img))
        else:
            st.error(f"❌ Could not load image. HTTP {response.status_code}")
    except Exception as e:
        st.error(f"⚠️ Error loading image: {e}")

# --------------------------
# Load uploaded images
# --------------------------
if uploaded_files:
    for file in uploaded_files:
        try:
            image = Image.open(file).convert("RGBA")
            image_queue.append((file.name, image))
        except:
            st.warning(f"{file.name} is not a valid image.")

# --------------------------
# Process images
# --------------------------
zip_buffer = io.BytesIO()

if image_queue:
    st.subheader("✅ Processed Images")
    with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED) as zipf:
        for name, image in image_queue:
            cleaned = remove_any_bg(image, bg_choice, (resize_width, resize_height))

            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"**🖼️ {name} – Original**")
                st.image(image, width=300)
            with col2:
                st.markdown("**🧼 Cleaned**")
                st.image(cleaned, width=300)

            # Save cleaned image to ZIP
            img_io = io.BytesIO()
            if bg_choice == "transparent":
                cleaned.save(img_io, format="PNG")  # Keep transparency
            else:
                cleaned.save(img_io, format="JPEG")
            zipf.writestr(name, img_io.getvalue())

    st.success("✅ All images processed successfully.")

    # --------------------------
    # Download ZIP
    # --------------------------
    zip_buffer.seek(0)
    st.download_button(
        label="📦 Download All as ZIP",
        data=zip_buffer,
        file_name="cleaned_images.zip",
        mime="application/zip"
    )

