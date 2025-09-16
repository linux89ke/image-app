import streamlit as st
from PIL import Image
from rembg import remove
import io
import zipfile

st.set_page_config(page_title="Background Remover & Cropper", layout="wide")
st.title("🧼 Remove Background + ✂️ Crop & Resize (1000x1000)")

# --------------------------
# Settings
# --------------------------
if "custom_color" not in st.session_state:
    st.session_state.custom_color = "#F2F2F2"  # default custom background

col1, col2 = st.columns([3,1])
with col1:
    st.session_state.custom_color = st.color_picker(
        "🎨 Background color (for 'Custom Color' option)",
        value=st.session_state.custom_color,
        key="color_picker"
    )
with col2:
    if st.button("🔄 Reset Color"):
        st.session_state.custom_color = "#F2F2F2"
        st.experimental_rerun()

bg_choice = st.radio("Background type", ["Transparent", "White", "Custom Color"])

# --------------------------
# Upload Images
# --------------------------
uploaded_files = st.file_uploader(
    "📤 Drag & drop image(s) here or click to browse",
    type=["jpg", "jpeg", "png"],
    accept_multiple_files=True
)

# --------------------------
# Process Images
# --------------------------
zip_buffer = io.BytesIO()

if uploaded_files:
    st.subheader("✅ Processed Images")

    with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED) as zipf:
        for file in uploaded_files:
            try:
                # Load original
                image = Image.open(file).convert("RGBA")

                # Step 1: Remove background
                output = remove(image)

                # Step 2: Apply background color
                if bg_choice == "White":
                    bg = Image.new("RGBA", output.size, (255, 255, 255, 255))
                    output = Image.alpha_composite(bg, output)
                elif bg_choice == "Custom Color":
                    rgb = tuple(int(st.session_state.custom_color.lstrip("#")[i:i+2], 16) for i in (0, 2, 4))
                    bg = Image.new("RGBA", output.size, rgb + (255,))
                    output = Image.alpha_composite(bg, output)

                st.markdown(f"### ✂️ Crop {file.name}")
                st.info("Use sliders below to select crop area. The result will be resized to 1000x1000 px.")

                # --------------------------
                # Step 3: Crop with sliders
                w, h = output.size
                left = st.slider(f"{file.name} - Left", 0, w, 0)
                top = st.slider(f"{file.name} - Top", 0, h, 0)
                right = st.slider(f"{file.name} - Right", left+1, w, w)
                bottom = st.slider(f"{file.name} - Bottom", top+1, h, h)

                cropped = output.crop((left, top, right, bottom))

                # --------------------------
                # Step 4: Resize to 1000x1000
                final_img = cropped.resize((1000, 1000), Image.LANCZOS)

                # Show final image
                st.image(final_img, caption=f"{file.name} – Final (1000x1000)", use_container_width=True)

                # --------------------------
                # Save for download
                img_io = io.BytesIO()
                final_img.save(img_io, format="PNG")
                out_name = f"{file.name.rsplit('.', 1)[0]}_cleaned_cropped.png"
                zipf.writestr(out_name, img_io.getvalue())

                # Individual download button
                st.download_button(
                    label=f"⬇️ Download {file.name}",
                    data=img_io.getvalue(),
                    file_name=out_name,
                    mime="image/png"
                )

                st.markdown("---")

            except Exception as e:
                st.error(f"⚠️ Failed to process {file.name}: {e}")

    # --------------------------
    # ZIP download
    zip_buffer.seek(0)
    st.download_button(
        label="📦 Download All as ZIP",
        data=zip_buffer,
        file_name="cleaned_images.zip",
        mime="application/zip"
    )
