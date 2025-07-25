import streamlit as st
from PIL import Image, ImageColor, ImageFilter, UnidentifiedImageError
import requests
import io
from rembg import remove, new_session

st.set_page_config(page_title="Batch Image Cleaner", layout="wide")
st.title("🧼 Batch Product Image Background Remover")
st.markdown("Upload product images or paste **Jumia image URLs**. Background will be removed and replaced with a clean `#F2F2F2` backdrop.")

# Background color setup
bg_color = ImageColor.getrgb("#F2F2F2")

# Create rembg session once
session = new_session("u2net")


def process_image(image: Image.Image) -> Image.Image:
    image = image.convert("RGBA")
    cutout = remove(image, session=session)

    # Soften edges
    alpha = cutout.split()[3].filter(ImageFilter.GaussianBlur(radius=1.0))
    cutout.putalpha(alpha)

    # Composite on new background
    bg = Image.new("RGBA", cutout.size, bg_color + (255,))
    bg.paste(cutout, mask=cutout.getchannel("A"))

    return bg.convert("RGB")


# --- Upload Section ---
uploaded_files = st.file_uploader("📁 Upload one or more images", type=["jpg", "jpeg", "png", "webp"], accept_multiple_files=True)

# --- URL Section ---
url_input = st.text_area("🔗 Or paste image URLs (one per line):")

# --- Collect All Images ---
images_to_process = []

# Uploaded files
if uploaded_files:
    for file in uploaded_files:
        try:
            img = Image.open(file)
            images_to_process.append((file.name, img))
        except UnidentifiedImageError:
            st.warning(f"❌ Skipping invalid image: {file.name}")

# URLs
if url_input:
    urls = [u.strip() for u in url_input.splitlines() if u.strip()]
    for i, url in enumerate(urls):
        try:
            headers = {
                "User-Agent": "Mozilla/5.0",
                "Referer": "https://www.jumia.co.ke/",
            }
            r = requests.get(url, headers=headers, timeout=10)
            if r.status_code == 200:
                img = Image.open(io.BytesIO(r.content))
                filename = f"url_image_{i+1}.jpg"
                images_to_process.append((filename, img))
            else:
                st.warning(f"⚠️ Could not load: {url} (status {r.status_code})")
        except Exception as e:
            st.warning(f"⚠️ Error fetching {url}: {e}")

# --- Process Button ---
if images_to_process:
    st.subheader("✨ Processed Images")
    for name, img in images_to_process:
        try:
            cleaned = process_image(img)

            st.markdown(f"**🖼️ {name}**")
            st.image(cleaned, use_column_width=True)

            # Prepare download
            buf = io.BytesIO()
            cleaned.save(buf, format="JPEG")
            st.download_button("📥 Download", buf.getvalue(), file_name=f"cleaned_{name}", mime="image/jpeg")
            st.markdown("---")

        except Exception as e:
            st.error(f"Error processing {name}: {e}")
else:
    st.info("⬆️ Upload files or paste image URLs to begin.")

