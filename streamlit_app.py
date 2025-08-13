import streamlit as st
from PIL import Image, ImageColor
import requests
import io
import zipfile

st.set_page_config(page_title="Batch Background Remover", layout="wide")
st.title("🧼 Remove White Background (Keep Text, Tags & Labels)")

# ---------------------------
# Background removal function
# ---------------------------
def remove_white_bg(image: Image.Image, threshold=240, bg_choice="f2f2f2", size=(1000, 1000)) -> Image.Image:
    image = image.convert("RGBA")
    datas = image.getdata()
    newData = []

    if bg_choice == "white":
        bg_rgb = (255, 255, 255)
    else:
        bg_rgb = ImageColor.getrgb("#F2F2F2")

    for item in datas:
        r, g, b, a = item
        if r > threshold and g > threshold and b > threshold:
            newData.append(bg_rgb + (255,))
        else:
            newData.append((r, g, b, a))

    image.putdata(newData)
    image = image.convert("RGB")
    image = image.resize(size)  # Resize based on user input
    return image

# --------------------------
# Upload section and inputs
# --------------------------
uploaded_files = st.file_uploader("📤 Upload image(s)", type=["jpg", "jpeg", "png", "webp"], accept_multiple_files=True)
url = st.text_input("🔗 Or paste image URL (e.g. Jumia product image)")

bg_choice = st.radio("🎨 Background Replacement", ["white", "#F2F2F2"])
threshold = st.slider("🔍 White detection threshold", 200, 255, 240)

resize_width = st.number_input("📏 Resize Width (px)", min_value=100, max_value=5000, value=1000, step=50)
resize_height = st.number_input("📐 Resize Height (px)", min_value=100, max_value=5000, value=1000, step=50)

image_queue = []

# --------------------------
# Load image from URL
# --------------------------
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
processed_files = []

if image_queue:
    st.subheader("✅ Processed Images")
    with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED) as zipf:
        for name, image in image_queue:
            cleaned = remove_white_bg(image, threshold, bg_choice, (resize_width, resize_height))

            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"**🖼️ {name} – Original**")
                st.image(image, width=300)
            with col2:
                st.markdown("**🧼 Cleaned**")
                st.image(cleaned, width=300)

            # Save image to zip buffer
            img_io = io.BytesIO()
            cleaned.save(img_io, format="JPEG")
            cleaned_filename = name
            zipf.writestr(cleaned_filename, img_io.getvalue())

            processed_files.append((cleaned_filename, img_io.getvalue()))

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

