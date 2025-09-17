import streamlit as st
from PIL import Image, ImageOps
from rembg import remove
import io
import zipfile

st.set_page_config(page_title="Batch Background Remover", layout="wide")
st.title("🛍️ E-Commerce Product Background Remover")

# ---------------------------
# Background removal that keeps ALL tags/labels intact
# ---------------------------
def remove_bg_keep_all(image: Image.Image, bg_choice="white", size=(1000, 1000), border_ratio=0.05) -> Image.Image:
    # Step 1: Remove background
    no_bg = remove(image).convert("RGBA")
    orig_rgba = image.convert("RGBA")

    # Step 2: Restore ALL original pixels where rembg made transparent holes
    restored = Image.new("RGBA", orig_rgba.size)
    pixels_no_bg = no_bg.getdata()
    pixels_orig = orig_rgba.getdata()
    new_pixels = []
    for p_clean, p_orig in zip(pixels_no_bg, pixels_orig):
        if p_clean[3] == 0:  # transparent pixel
            new_pixels.append(p_orig)  # keep original
        else:
            new_pixels.append(p_clean)
    restored.putdata(new_pixels)

    # Step 3: Fit into square canvas with border
    w, h = size
    border_x, border_y = int(w * border_ratio), int(h * border_ratio)
    canvas = Image.new("RGBA", (w, h), (255, 255, 255, 0))

    # Resize product with margin
    max_w, max_h = w - 2 * border_x, h - 2 * border_y
    restored.thumbnail((max_w, max_h), Image.LANCZOS)

    # Paste centered
    pos_x = (w - restored.width) // 2
    pos_y = (h - restored.height) // 2
    canvas.paste(restored, (pos_x, pos_y), restored)

    # Step 4: Replace transparent with chosen background
    if bg_choice == "white":
        bg_color = (255, 255, 255)
    else:
        bg_color = (242, 242, 242)  # encoded color
    final = Image.new("RGB", (w, h), bg_color)
    final.paste(canvas, mask=canvas.split()[3])  # keep alpha
    return final


# ---------------------------
# Streamlit App
# ---------------------------
uploaded_files = st.file_uploader("Upload product images", type=["jpg", "jpeg", "png"], accept_multiple_files=True)

bg_choice = st.radio("Background color", ["white", "encoded (#F2F2F2)"])

if uploaded_files:
    processed_images = []
    for file in uploaded_files:
        img = Image.open(file).convert("RGBA")
        processed = remove_bg_keep_all(img, bg_choice="white" if bg_choice == "white" else "encoded")
        processed_images.append((file.name, processed))

        st.image(processed, caption=f"Processed: {file.name}", use_column_width=True)

    # Download buttons
    st.subheader("Download Options")
    for fname, img in processed_images:
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        st.download_button(f"⬇️ Download {fname}", buf.getvalue(), file_name=f"processed_{fname}", mime="image/png")

    # Download all as ZIP
    zip_buf = io.BytesIO()
    with zipfile.ZipFile(zip_buf, "w") as zf:
        for fname, img in processed_images:
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            zf.writestr(f"processed_{fname}", buf.getvalue())
    st.download_button("⬇️ Download All (ZIP)", zip_buf.getvalue(), file_name="processed_images.zip", mime="application/zip")
