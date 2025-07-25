import streamlit as st
from PIL import Image, ImageColor, ImageFilter, UnidentifiedImageError
import requests
import io
import os

from rembg import remove, new_session

st.set_page_config(page_title="Image BG Remover", layout="wide")
st.title("🧼 Product Image Background Remover")
st.markdown("Upload or paste links — we’ll clean the background and keep text/tags intact.")

# Setup Rembg session with best quality model
session = new_session("isnet-general-use")  # 🧠 Best model for sharp edges & preserving tags

# Function to process image
def process_image(image: Image.Image, bg_hex="#F2F2F2") -> Image.Image:
    cutout = remove(image, session=session)

    # Feather edges for smoothness
    alpha = cutout.split()[3].filter(ImageFilter.GaussianBlur(radius=1.0))
    cutout.putalpha(alpha)

    # Replace background
    bg_color = ImageColor.getrgb(bg_hex)
    background = Image.new("RGBA", cutout.size, bg_color + (255,))
    background.paste(cutout, mask=cutout.getchannel("A"))
    final = background.convert("RGB")

    return final

# Section 1: Upload Images
st.subheader("📤 Upload Images")
uploaded_files = st.file_uploader("Upload one or more images", type=["jpg", "jpeg", "png", "webp"], accept_multiple_files=True)

# Section 2: Link Input
st.subheader("🔗 Paste an Image URL (e.g. Jumia)")
url = st.text_input("Paste image link")

image_queue = []

# Handle image links
if url:
    try:
        headers = {
            "User-Agent": "Mozilla/5.0",
            "Referer": "https://www.jumia.co.ke/"
        }
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            image_bytes = io.BytesIO(response.content)
            image = Image.open(image_bytes).convert("RGBA")
            image_queue.append(("linked_image", image))
        else:
            st.error(f"❌ Could not fetch image. Status code: {response.status_code}")
    except Exception as e:
        st.error(f"⚠️ Error loading image: {e}")

# Handle uploaded images
if uploaded_files:
    for file in uploaded_files:
        try:
            image = Image.open(file).convert("RGBA")
            image_queue.append((file.name, image))
        except UnidentifiedImageError:
            st.warning(f"⚠️ `{file.name}` is not a valid image.")

# Process all images
if image_queue:
    st.subheader("🖼️ Processed Images")
    for name, image in image_queue:
        st.markdown(f"**🖼️ {name}**")
        st.image(image, caption="Original", use_column_width=True)

        final = process_image(image)
        st.image(final, caption="Cleaned", use_column_width=True)

        buf = io.BytesIO()
        final.save(buf, format="JPEG")
        st.download_button("📥 Download Cleaned Image", data=buf.getvalue(),
                           file_name=f"{os.path.splitext(name)[0]}_cleaned.jpg", mime="image/jpeg")
