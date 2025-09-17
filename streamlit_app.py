import streamlit as st
from PIL import Image, ImageColor, ImageChops
import requests
import io
import zipfile
from rembg import remove  # AI background removal

st.set_page_config(page_title="Batch Background Remover", layout="wide")
st.title("🧼 AI Background Remover (Keep Tags & Labels)")

# ---------------------------
# Background removal (preserve tags/labels)
# ---------------------------
def remove_bg_keep_tags(image: Image.Image, bg_choice="white", size=(1000, 1000), autocrop=True) -> Image.Image:
    """
    Removes the background using an advanced masking technique to preserve sharp edges on tags.
    This avoids the "feathered" or "dirty" look from simpler pixel-replacement methods.
    """
    # Step 1: Get the AI-processed image and extract its alpha mask.
    # This mask has great, soft edges for the main subject but might miss tags.
    no_bg = remove(image).convert("RGBA")
    rembg_alpha_mask = no_bg.split()[3]

    # Step 2: Create a second, high-contrast mask from the original image.
    # This mask identifies all non-white areas, capturing tags and labels perfectly.
    orig_rgba = image.convert("RGBA")
    pixels_orig = orig_rgba.getdata()
    
    # Create a list of 255 (white) for non-background pixels, 0 (black) for background
    tag_mask_pixels = [255 if not (p[0] > 245 and p[1] > 245 and p[2] > 245) and p[3] > 0 else 0 for p in pixels_orig]
    tag_mask = Image.new("L", orig_rgba.size) # "L" mode is 8-bit grayscale
    tag_mask.putdata(tag_mask_pixels)

    # Step 3: Combine the two masks.
    # ImageChops.lighter takes the brightest pixel from both masks. This creates a final
    # mask that is the perfect union of the AI's subject detection and our tag detection.
    final_mask = ImageChops.lighter(rembg_alpha_mask, tag_mask)

    # Step 4: Apply the final, combined mask to the original image.
    # This cuts out the complete subject (product + tags) from the original source,
    # ensuring no quality is lost and all edges are as they should be.
    restored = Image.new("RGBA", orig_rgba.size, (0,0,0,0)) # Start with a transparent canvas
    restored.paste(orig_rgba, mask=final_mask)

    # Step 5: Crop to the content's bounding box.
    if autocrop:
        bbox = restored.getbbox()
        if bbox:
            restored = restored.crop(bbox)

    # Step 6: Create the final canvas with the chosen background and place the image.
    if bg_choice == "transparent":
        canvas = Image.new("RGBA", size, (0, 0, 0, 0))
    else:
        bg_rgb = (255, 255, 255) if bg_choice == "white" else ImageColor.getrgb("#F2F2F2")
        canvas = Image.new("RGB", size, bg_rgb)
    
    restored.thumbnail(size, Image.Resampling.LANCZOS)
    
    x = (size[0] - restored.size[0]) // 2
    y = (size[1] - restored.size[1]) // 2
    
    # The mask for pasting is the alpha channel of the restored image itself.
    canvas.paste(restored, (x, y), mask=restored.split()[3] if restored.mode == 'RGBA' else None)

    return canvas

# --------------------------
# UI: Upload section and inputs
# --------------------------
uploaded_files = st.file_uploader(
    "📤 Upload image(s)",
    type=["jpg", "jpeg", "png", "webp"],
    accept_multiple_files=True
)
url = st.text_input("🔗 Or paste image URL (e.g. from an e-commerce site)")

bg_choice = st.radio("🎨 Background Replacement", ["white", "#F2F2F2", "transparent"])
resize_width = st.number_input("📏 Resize Width (px)", min_value=100, max_value=5000, value=1000, step=50)
resize_height = st.number_input("📐 Resize Height (px)", min_value=100, max_value=5000, value=1000, step=50)
autocrop = st.checkbox("✂️ Auto-crop and center product", value=True)

image_queue = []

# --------------------------
# Load image from URL
# --------------------------
if url:
    try:
        headers = {"User-Agent": "Mozilla/5.0", "Referer": "https://www.google.com/"}
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            img = Image.open(io.BytesIO(response.content))
            image_queue.append(("linked_image.png", img))
        else:
            st.error(f"❌ Could not load image. HTTP Status: {response.status_code}")
    except Exception as e:
        st.error(f"⚠️ Error loading image from URL: {e}")

# --------------------------
# Load uploaded images
# --------------------------
if uploaded_files:
    for file in uploaded_files:
        try:
            image = Image.open(file)
            image_queue.append((file.name, image))
        except Exception as e:
            st.warning(f"Could not open {file.name}. Is it a valid image? Error: {e}")

# --------------------------
# Process images and display results
# --------------------------
if image_queue:
    zip_buffer = io.BytesIO()
    st.subheader("✅ Processed Images")
    
    with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zipf:
        with st.spinner('Removing backgrounds with advanced masking...'):
            for name, image in image_queue:
                cleaned = remove_bg_keep_tags(
                    image,
                    bg_choice,
                    (resize_width, resize_height),
                    autocrop=autocrop
                )

                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(f"**🖼️ {name} – Original**")
                    st.image(image)
                with col2:
                    st.markdown("**🧼 Cleaned (Tags Preserved)**")
                    st.image(cleaned)

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
                    label=f"⬇️ Download {cleaned_name}",
                    data=img_bytes,
                    file_name=cleaned_name,
                    mime=mime_type
                )
                st.divider()

    st.success("✅ All images processed successfully.")

    zip_buffer.seek(0)
    st.download_button(
        label="📦 Download All as ZIP",
        data=zip_buffer,
        file_name="cleaned_images.zip",
        mime="application/zip",
        use_container_width=True
    )
