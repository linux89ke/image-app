import streamlit as st
from PIL import Image, ImageColor
import requests
import io
import zipfile
from rembg import remove  # AI background removal

st.set_page_config(page_title="Batch Background Remover", layout="wide")
st.title("Background Remover")

# ---------------------------
# Background removal (preserve tags/labels)
# ---------------------------
def remove_bg_keep_tags(image: Image.Image, bg_choice="white", size=(1000, 1000), autocrop=True) -> Image.Image:
    """
    Removes the background from an image while attempting to preserve non-white elements
    like tags and labels that the AI might otherwise remove.
    """
    # Step 1: Remove background using rembg
    no_bg = remove(image).convert("RGBA")

    # Step 2: Compare with original to restore tags/labels
    orig_rgba = image.convert("RGBA")
    pixels_no_bg = no_bg.getdata()
    pixels_orig = orig_rgba.getdata()

    new_pixels = []
    for p_clean, p_orig in zip(pixels_no_bg, pixels_orig):
        # If the AI-cleaned pixel is transparent, but the original pixel was NOT pure white,
        # it's likely a tag or label that should be restored.
        
        # --- IMPROVEMENT ---
        # The threshold is now stricter (245 instead of 240) to better capture
        # the anti-aliased edges of tags, resulting in a cleaner look.
        is_transparent_in_cleaned = p_clean[3] == 0
        is_not_white_in_original = not (p_orig[0] > 245 and p_orig[1] > 245 and p_orig[2] > 245)

        if is_transparent_in_cleaned and is_not_white_in_original:
            new_pixels.append(p_orig)  # Restore the original pixel (tag/label)
        else:
            new_pixels.append(p_clean) # Keep the AI-cleaned pixel

    restored = Image.new("RGBA", no_bg.size)
    restored.putdata(new_pixels)

    # Step 3: Crop to product bounding box
    if autocrop:
        bbox = restored.getbbox()
        if bbox:
            restored = restored.crop(bbox)

    # Step 4: Handle background choice and resize
    if bg_choice == "transparent":
        # Create a transparent canvas
        canvas = Image.new("RGBA", size, (0, 0, 0, 0))
    else:
        # Create a solid color canvas
        bg_rgb = (255, 255, 255) if bg_choice == "white" else ImageColor.getrgb("#F2F2F2")
        canvas = Image.new("RGB", size, bg_rgb)
    
    # Resize the restored image to fit within the canvas while maintaining aspect ratio
    restored.thumbnail(size, Image.Resampling.LANCZOS)
    
    # Calculate position to center the image
    x = (size[0] - restored.size[0]) // 2
    y = (size[1] - restored.size[1]) // 2
    
    # Paste the restored image onto the canvas using its alpha channel as a mask
    # For RGB canvas, we need to convert the restored image to RGBA to get the mask
    paste_image = restored if restored.mode == 'RGBA' else restored.convert('RGBA')
    canvas.paste(paste_image, (x, y), mask=paste_image.split()[3])

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
        # Use headers to mimic a browser and avoid being blocked
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
        # Add a spinner to show progress during processing
        with st.spinner('Removing backgrounds... please wait.'):
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

                # Save cleaned image to an in-memory buffer
                img_io = io.BytesIO()
                if bg_choice == "transparent":
                    cleaned.save(img_io, format="PNG")
                    file_ext = ".png"
                    mime_type = "image/png"
                else:
                    # If the canvas has an alpha channel, convert to RGB before saving as JPEG
                    if cleaned.mode == 'RGBA':
                        cleaned = cleaned.convert('RGB')
                    cleaned.save(img_io, format="JPEG")
                    file_ext = ".jpg"
                    mime_type = "image/jpeg"
                
                img_bytes = img_io.getvalue()
                cleaned_name = name.rsplit(".", 1)[0] + "_cleaned" + file_ext

                # Add the processed image to the ZIP archive
                zipf.writestr(cleaned_name, img_bytes)

                # Individual download button
                st.download_button(
                    label=f"⬇️ Download {cleaned_name}",
                    data=img_bytes,
                    file_name=cleaned_name,
                    mime=mime_type
                )
                st.divider()

    st.success("✅ All images processed successfully.")

    # --------------------------
    # Download All as ZIP
    # --------------------------
    zip_buffer.seek(0)
    st.download_button(
        label="📦 Download All as ZIP",
        data=zip_buffer,
        file_name="cleaned_images.zip",
        mime="application/zip",
        use_container_width=True
    )
