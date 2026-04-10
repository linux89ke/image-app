import streamlit as st
from PIL import Image, ImageColor, ImageChops
import requests
import io
import zipfile
from rembg import remove  

# Configuration
st.set_page_config(page_title="Batch Background Remover", layout="wide")

# Custom CSS for a professional look
st.markdown("""
    <style>
    .main-title {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1E1E1E;
        margin-bottom: 20px;
    }
    .status-text {
        font-size: 0.9rem;
        color: #666;
    }
    </style>
    """, unsafe_allow_html=True)

st.markdown('<p class="main-title">AI Background Remover</p>', unsafe_allow_html=True)

def remove_bg_keep_tags(image: Image.Image, bg_choice="white", size=(1000, 1000), autocrop=True) -> Image.Image:
    """
    Removes the background using advanced masking to preserve product tags.
    """
    no_bg = remove(image).convert("RGBA")
    rembg_alpha_mask = no_bg.split()[3]

    orig_rgba = image.convert("RGBA")
    pixels_orig = orig_rgba.getdata()
    
    # Logic to capture tags/labels by identifying non-white pixels
    tag_mask_pixels = [255 if not (p[0] > 245 and p[1] > 245 and p[2] > 245) and p[3] > 0 else 0 for p in pixels_orig]
    tag_mask = Image.new("L", orig_rgba.size) 
    tag_mask.putdata(tag_mask_pixels)

    final_mask = ImageChops.lighter(rembg_alpha_mask, tag_mask)

    restored = Image.new("RGBA", orig_rgba.size, (0,0,0,0))
    restored.paste(orig_rgba, mask=final_mask)

    if autocrop:
        bbox = restored.getbbox()
        if bbox:
            restored = restored.crop(bbox)

    if bg_choice == "transparent":
        canvas = Image.new("RGBA", size, (0, 0, 0, 0))
    else:
        bg_rgb = (255, 255, 255) if bg_choice == "white" else ImageColor.getrgb("#F2F2F2")
        canvas = Image.new("RGB", size, bg_rgb)
    
    restored.thumbnail(size, Image.Resampling.LANCZOS)
    
    x = (size[0] - restored.size[0]) // 2
    y = (size[1] - restored.size[1]) // 2
    
    canvas.paste(restored, (x, y), mask=restored.split()[3] if restored.mode == 'RGBA' else None)

    return canvas

# --------------------------
# Sidebar / Settings Section
# --------------------------
with st.sidebar:
    st.header("Settings")
    bg_choice = st.radio("Background Canvas", ["white", "#F2F2F2", "transparent"])
    resize_width = st.number_input("Width (px)", min_value=100, max_value=5000, value=1000, step=50)
    resize_height = st.number_input("Height (px)", min_value=100, max_value=5000, value=1000, step=50)
    autocrop = st.checkbox("Enable Auto-crop", value=True)

# --------------------------
# Main Input Section
# --------------------------
uploaded_files = st.file_uploader(
    "Upload Image Files",
    type=["jpg", "jpeg", "png", "webp"],
    accept_multiple_files=True
)
url = st.text_input("Source URL", placeholder="https://example.com/product.jpg")

image_queue = []

if url:
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            img = Image.open(io.BytesIO(response.content))
            image_queue.append(("linked_image.png", img))
        else:
            st.error(f"Error: Connection failed (Status {response.status_code})")
    except Exception as e:
        st.error(f"Error: {e}")

if uploaded_files:
    for file in uploaded_files:
        try:
            image = Image.open(file)
            image_queue.append((file.name, image))
        except Exception as e:
            st.warning(f"Could not open {file.name}: {e}")

# --------------------------
# Processing Engine
# --------------------------
if image_queue:
    zip_buffer = io.BytesIO()
    st.markdown("### Output Gallery")
    
    with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zipf:
        with st.spinner('Processing images...'):
            for name, image in image_queue:
                cleaned = remove_bg_keep_tags(
                    image,
                    bg_choice,
                    (resize_width, resize_height),
                    autocrop=autocrop
                )

                col1, col2 = st.columns(2)
                with col1:
                    st.caption(f"Original: {name}")
                    st.image(image, use_container_width=True)
                with col2:
                    st.caption("Processed Subject")
                    st.image(cleaned, use_container_width=True)

                img_io = io.BytesIO()
                if bg_choice == "transparent":
                    cleaned.save(img_io, format="PNG")
                    file_ext, mime_type = (".png", "image/png")
                else:
                    if cleaned.mode == 'RGBA':
                        cleaned = cleaned.convert('RGB')
                    cleaned.save(img_io, format="JPEG")
                    file_ext, mime_type = (".jpg", "image/jpeg")
                
                img_bytes = img_io.getvalue()
                cleaned_name = name.rsplit(".", 1)[0] + "_cleaned" + file_ext
                zipf.writestr(cleaned_name, img_bytes)

                st.download_button(
                    label=f"Download {cleaned_name}",
                    data=img_bytes,
                    file_name=cleaned_name,
                    mime=mime_type
                )
                st.divider()

    zip_buffer.seek(0)
    st.download_button(
        label="Download All Assets (ZIP)",
        data=zip_buffer,
        file_name="cleaned_images.zip",
        mime="application/zip",
        use_container_width=True
    )
