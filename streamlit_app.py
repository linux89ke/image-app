import streamlit as st
from PIL import Image, ImageColor
import requests
import io
import os
import zipfile

st.set_page_config(page_title="Batch Background Remover", layout="wide")
st.title("🧼 Remove White Background (Keep Text & Tags)")

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

# Upload section
uploaded_files = st.file_uploader("📤 Upload image(s)", type=["jpg", "jpeg", "png", "webp"], accept_multiple_files=True)
url = st.text_input("🔗 Or paste image URL (e.g. Jumia product image)")

image_queue = []

# Add image from URL
if url:
    try:
        headers = {
            "User-Agent": "Mozilla/5.0",
            "Referer": "https://www.jumia.co.ke/"
        }
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            img = Image.open(io.BytesIO(response.content)).convert("RGBA")
            image_queue.append(("linked_image.jpg", img))
        else:
            st.error(f"❌ Could not load image. HTTP {response.status_code}")
    except Exception as e:
        st.error(f"⚠️ Error loading image: {e}")

# Add uploaded images
if uploaded_files:
    for file in uploaded_files:
        try:
            image = Image.open(file).convert("RGBA")
            image_queue.append((file.name, image))
        except:
            st.warning(f"{file.name} is not a valid image.")

# Process and store in memory for zip
zip_buffer = io.BytesIO()
processed_files = []

if image_queue:
    st.subheader("✅ Processed Images")

    with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED) as zipf:
        for name, image in image_queue:
            st.markdown(f"**🖼️ {name}**")
            st.image(image, caption="Original", use_column_width=True)

            cleaned = remove_white_bg(image)
            st.image(cleaned, caption="Cleaned", use_column_width=True)

            img_io = io.BytesIO()
            cleaned.save(img_io, format="JPEG")
            cleaned_filename = f"{os.path.splitext(name)[0]}_cleaned.jpg"
            zipf.writestr(cleaned_filename, img_io.getvalue())

            processed_files.append((cleaned_filename, img_io.getvalue()))

    st.success("✅ All images processed successfully.")

    # Download ZIP
    zip_buffer.seek(0)
    st.download_button(
        label="📦 Download All as ZIP",
        data=zip_buffer,
        file_name="cleaned_images.zip",
        mime="application/zip"
    )
