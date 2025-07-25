import streamlit as st
from PIL import Image, ImageColor, ImageFilter
import requests
import io
import zipfile

st.set_page_config(page_title="Batch Background Cleaner", layout="wide")
st.title("🧼 Background Cleaner + Shadow Adder")

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
    return image

def add_drop_shadow(img, offset=(15, 15), background_color="#F2F2F2", shadow_color="#aaaaaa", blur_radius=20):
    img = img.convert("RGBA")
    total_width = img.width + offset[0]
    total_height = img.height + offset[1]

    background = Image.new("RGBA", (total_width, total_height), background_color)

    # Create shadow from alpha
    alpha = img.getchannel("A")
    shadow = Image.new("RGBA", img.size, shadow_color)
    shadow.putalpha(alpha)

    # Paste and blur
    background.paste(shadow, offset, mask=alpha)
    background = background.filter(ImageFilter.GaussianBlur(blur_radius))

    # Paste the original image
    background.paste(img, (0, 0), img)
    return background.convert("RGB")

uploaded_files = st.file_uploader("📤 Upload image(s)", type=["jpg", "jpeg", "png", "webp"], accept_multiple_files=True)
url = st.text_input("🔗 Or paste direct image URL (e.g. Jumia)")

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
            image_queue.append(("linked_image.jpg", img))
        else:
            st.error(f"❌ Could not load image. HTTP {response.status_code}")
    except Exception as e:
        st.error(f"⚠️ Error loading image: {e}")

if uploaded_files:
    for file in uploaded_files:
        try:
            image = Image.open(file).convert("RGBA")
            image_queue.append((file.name, image))
        except:
            st.warning(f"{file.name} is not a valid image.")

zip_buffer = io.BytesIO()
processed_files = []

if image_queue:
    st.subheader("✅ Processed Results")
    with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED) as zipf:
        for name, image in image_queue:
            cleaned = remove_white_bg(image)
            shadowed = add_drop_shadow(cleaned)

            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"**Original: {name}**")
                st.image(image, width=300)
            with col2:
                st.markdown("**With Clean Background + Shadow**")
                st.image(shadowed, width=300)

            img_io = io.BytesIO()
            shadowed.save(img_io, format="JPEG")
            zipf.writestr(name, img_io.getvalue())
            processed_files.append((name, img_io.getvalue()))

    zip_buffer.seek(0)
    st.download_button(
        label="📦 Download All as ZIP",
        data=zip_buffer,
        file_name="cleaned_with_shadows.zip",
        mime="application/zip"
    )

