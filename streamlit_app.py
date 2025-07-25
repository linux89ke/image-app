import streamlit as st
from PIL import Image, ImageColor
import requests
import io
import os

st.set_page_config(page_title="Color Key Background Remover", layout="wide")
st.title("🎯 White Background Remover (Keeps All Text & Tags)")

def remove_white_bg(image: Image.Image, threshold=240, replace_color="#F2F2F2") -> Image.Image:
    image = image.convert("RGBA")
    datas = image.getdata()
    newData = []

    bg_rgb = ImageColor.getrgb(replace_color)

    for item in datas:
        r, g, b, a = item
        if r > threshold and g > threshold and b > threshold:
            newData.append(bg_rgb + (255,))
        else:
            newData.append((r, g, b, a))

    image.putdata(newData)
    return image.convert("RGB")

# Handle image uploads
uploaded_files = st.file_uploader("📤 Upload images", type=["jpg", "jpeg", "png", "webp"], accept_multiple_files=True)

# Handle Jumia or image links
url = st.text_input("🔗 Or paste an image URL (Jumia allowed)")
image_queue = []

if url:
    try:
        headers = {
            "User-Agent": "Mozilla/5.0",
            "Referer": "https://www.jumia.co.ke/"
        }
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            img = Image.open(io.BytesIO(response.content)).convert("RGBA")
            image_queue.append(("linked_image", img))
        else:
            st.error(f"Error loading image: {response.status_code}")
    except Exception as e:
        st.error(f"⚠️ Could not fetch image: {e}")

# Add uploaded images to queue
if uploaded_files:
    for file in uploaded_files:
        try:
            image = Image.open(file).convert("RGBA")
            image_queue.append((file.name, image))
        except:
            st.warning(f"{file.name} is not a valid image.")

# Process all images
if image_queue:
    st.subheader("🧽 Cleaned Images")
    for name, image in image_queue:
        st.markdown(f"**🖼️ {name}**")
        st.image(image, caption="Original", use_column_width=True)

        cleaned = remove_white_bg(image)
        st.image(cleaned, caption="Cleaned (Text/Tags Preserved)", use_column_width=True)

        buf = io.BytesIO()
        cleaned.save(buf, format="JPEG")
        st.download_button("📥 Download Cleaned Image", data=buf.getvalue(),
                           file_name=f"{os.path.splitext(name)[0]}_cleaned.jpg", mime="image/jpeg")
