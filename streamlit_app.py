import streamlit as st
from PIL import Image, ImageColor, ImageEnhance
import requests
import io
import zipfile
from rembg import remove  # AI background removal

st.set_page_config(page_title="Batch Background Remover", layout="wide")
st.title("🧼 AI Background Remover (Product Isolation with Tags Preserved)")

# ---------------------------
# Background removal + Tag preservation
# ---------------------------
def remove_bg_keep_tags(image: Image.Image, bg_choice="white", size=(1000, 1000), autocrop=True, border_ratio=0.05) -> Image.Image:
    """
    Removes background while preserving tags (e.g. 18+), sharpens edges,
    and centers product with border padding.
    """
    # Step 1: Remove background
    no_bg = remove(image).convert("RGBA")
    orig_rgba = image.convert("RGBA")

    pixels_no_bg = no_bg.getdata()
    pixels_orig = orig_rgba.getdata()

    new_pixels = []
    for p_clean, p_orig in zip(pixels_no_bg, pixels_orig):
        # If AI made transparent but original had strong colors (likely tag)
        if p_clean[3] == 0:
            if (p_orig[0] > 240 and p_orig[1] > 240 and p_orig[2] > 240):  # white
                new_pixels.append((255, 255, 255, 255))
            elif (p_orig[0] > 200 and p_orig[1] < 80 and p_orig[2] < 80):  # red
                new_pixels.append((p_orig[0], p_orig[1], p_orig[2], 255))
            elif (p_orig[0] < 50 and p_orig[1] < 50 and p_orig[2] < 50):  # black
                new_pixels.append((0, 0, 0, 255))
            else:
                new_pixels.append(p_clean)
        else:
            new_pixels.append(p_clean)

    restored = Image.new("RGBA", no_bg.size)
    restored.putdata(new_pixels)

    # Step 2: Auto-crop product
    if autocrop:
        bbox = restored.getbbox()
        if bbox:
            restored = restored.crop(bbox)

    # Step 3: Add padding (5% border by default)
    pad_x = int(size[0] * border_ratio)
    pad_y = int(size[1] * border_ratio)
    inner_size = (size[0] - 2 * pad_x, size[1] - 2 * pad_y)
    restored.thumbnail(inner_size, Image.LANCZOS)

    # Step 4: Sharpen edges
    restored = ImageEnhance.Sharpness(restored).enhance(1.5)

    # Step 5: Place on background
    if bg_choice == "transparent":
        canvas = Image.new("RGBA", size, (0, 0, 0, 0))
    else:
        bg_rgb = (255, 255, 255) if bg_choice == "white" else ImageColor.getrgb("#F2F2F2")
        canvas = Image.new("RGB", size, bg_rgb)

    x = (size[0] - restored.size[0]) // 2
    y = (size[1] - restored.size[1]) // 2
    canvas.paste(restored, (x, y), mask=restored.split()[3])

    return canvas


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
            cleaned = remove_bg_keep_tags(image, bg_choice, (resize_width, resize_height))

            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"**🖼️ {name} – Original**")
                st.image(image, width=300)
            with col2:
                st.markdown("**🧼 Cleaned (Tags Preserved)**")
                st.image(cleaned, width=300)

            # Save cleaned image individually
            img_io = io.BytesIO()
            if bg_choice == "transparent":
                cleaned.save(img_io, format="PNG")  # Keep transparency
            else:
                cleaned.save(img_io, format="JPEG")
            img_io.seek(0)

            st.download_button(
                label=f"⬇️ Download {name}",
                data=img_io,
                file_name=f"cleaned_{name}",
                mime="image/png" if bg_choice == "transparent" else "image/jpeg"
            )

            # Save to ZIP
            zipf.writestr(f"cleaned_{name}", img_io.getvalue())

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
