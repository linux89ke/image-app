import streamlit as st
from PIL import Image
from rembg import remove
from streamlit_cropper import st_cropper
import io, zipfile

st.set_page_config(page_title="Background Remover & Cropper", layout="wide")
st.title("🧼 Remove Background + ✂️ Crop & Resize (1000x1000)")

# --------------------------
# Settings
# --------------------------
if "custom_color" not in st.session_state:
    st.session_state.custom_color = "#F2F2F2"   # default custom background

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
# Process
# --------------------------
zip_buffer = io.BytesIO()

if uploaded_files:
    st.subheader("✅ Processed Images")

    with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED) as zipf:
        for file in uploaded_files:
            try:
                # Load original
                image = Image.open(file).convert("RGBA")

                # Step 1: Background removal
                output = remove(image)

                # Apply background option
                if bg_choice == "White":
                    bg = Image.new("RGBA", output.size, (255, 255, 255, 255))
                    output = Image.alpha_composite(bg, output)
                elif bg_choice == "Custom Color":
                    rgb = tuple(int(st.session_state.custom_color.lstrip("#")[i:i+2], 16) for i in (0, 2, 4))
                    bg = Image.new("RGBA", output.size, rgb + (255,))
                    output = Image.alpha_composite(bg, output)

                st.markdown(f"### ✂️ Crop {file.name}")
                st.info("Drag on the image below to crop. The result will be resized to 1000x1000 px.")

                # Step 2: Crop interactively
                cropped = st_cropper(output, aspect_ratio=(1, 1), return_type="pil", box_color="#FF0000")

                # Step 3: Resize to 1000x1000
                final_img = cropped.resize((1000, 1000), Image.LANCZOS)

                # Show result
                st.image(final_img, caption=f"{file.name} – Final (1000x1000)", use_container_width=True)

                # Save for download
                img_io = io.BytesIO()
                final_img.save(img_io, format="PNG")
                out_name = f"{file.name.rsplit('.', 1)[0]}_cleaned_cropped.png"
                zipf.writestr(out_name, img_io.getvalue())

                # Individual download
                st.download_button(
                    label=f"⬇️ Download {file.name}",
                    data=img_io.getvalue(),
                    file_name=out_name,
                    mime="image/png"
                )

                st.markdown("---")

            except Exception as e:
                st.error(f"⚠️ Failed to process {file.name}: {e}")

    # ZIP download
    zip_buffer.seek(0)
    st.download_button(
        label="📦 Download All as ZIP",
        data=zip_buffer,
        file_name="cleaned_images.zip",
        mime="application/zip"
    )
