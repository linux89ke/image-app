import streamlit as st
from PIL import Image
from rembg import remove
import io
import zipfile

st.set_page_config(page_title="Background Remover", layout="wide")
st.title("🧼 Remove Background & Resize to 1000x1000 px")

# --------------------------
# Background settings
# --------------------------
if "custom_color" not in st.session_state:
    st.session_state.custom_color = "#F2F2F2"  # default custom background

col1, col2 = st.columns([3,1])
with col1:
    st.session_state.custom_color = st.color_picker(
        "🎨 Background color (for 'Custom Color' option)",
        value=st.session_state.custom_color
    )
with col2:
    if st.button("🔄 Reset Color"):
        st.session_state.custom_color = "#F2F2F2"
        st.experimental_rerun()

bg_choice = st.radio("Background type", ["Transparent", "White", "Custom Color"])

# --------------------------
# Upload images
# --------------------------
uploaded_files = st.file_uploader(
    "📤 Drag & drop image(s) here or click to browse",
    type=["jpg", "jpeg", "png"],
    accept_multiple_files=True
)

# --------------------------
# Process images
# --------------------------
zip_buffer = io.BytesIO()

if uploaded_files:
    st.subheader("✅ Processed Images")

    with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED) as zipf:
        for file in uploaded_files:
            try:
                # Load image
                image = Image.open(file).convert("RGBA")

                # Remove background
                output = remove(image)

                # Apply background color
                if bg_choice == "White":
                    bg = Image.new("RGBA", output.size, (255, 255, 255, 255))
                    output = Image.alpha_composite(bg, output)
                elif bg_choice == "Custom Color":
                    rgb = tuple(int(st.session_state.custom_color.lstrip("#")[i:i+2], 16) for i in (0, 2, 4))
                    bg = Image.new("RGBA", output.size, rgb + (255,))
                    output = Image.alpha_composite(bg, output)

                # Resize to 1000x1000 and center
                final_img = Image.new("RGBA", (1000, 1000), (0, 0, 0, 0))
                output.thumbnail((1000, 1000), Image.LANCZOS)
                x = (1000 - output.width) // 2
                y = (1000 - output.height) // 2
                final_img.paste(output, (x, y), output)

                # Show result
                st.image(final_img, caption=f"{file.name} – 1000x1000", use_container_width=True)

                # Save for download
                img_io = io.BytesIO()
                final_img.save(img_io, format="PNG")
                out_name = f"{file.name.rsplit('.', 1)[0]}_cleaned.png"
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

    # ZIP download
    zip_buffer.seek(0)
    st.download_button(
        label="📦 Download All as ZIP",
        data=zip_buffer,
        file_name="cleaned_images.zip",
        mime="application/zip"
    )
