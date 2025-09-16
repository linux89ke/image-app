import streamlit as st
from PIL import Image
from rembg import remove
import io
import zipfile

st.set_page_config(page_title="Background Remover", layout="wide")
st.title("🧼 Remove Background (Local AI - rembg)")

# --------------------------
# Settings
# --------------------------
replace_color = st.color_picker("🎨 Background color", "#F2F2F2")
bg_choice = st.radio("Background type", ["Transparent", "White", "Custom Color"])

# --------------------------
# Upload Images (drag & drop supported)
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

                # Remove background
                output = remove(image)

                # Handle background options
                if bg_choice == "White":
                    bg = Image.new("RGBA", output.size, (255, 255, 255, 255))
                    output = Image.alpha_composite(bg, output)
                elif bg_choice == "Custom Color":
                    rgb = tuple(int(replace_color.lstrip("#")[i:i+2], 16) for i in (0, 2, 4))
                    bg = Image.new("RGBA", output.size, rgb + (255,))
                    output = Image.alpha_composite(bg, output)

                # Force output to 1000x1000 px (centered, preserving aspect ratio)
                final_img = Image.new("RGBA", (1000, 1000), (0, 0, 0, 0))
                output.thumbnail((1000, 1000), Image.LANCZOS)
                x = (1000 - output.width) // 2
                y = (1000 - output.height) // 2
                final_img.paste(output, (x, y), output)

                # Preview (already 1000x1000)
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(f"**🖼️ {file.name} – Original**")
                    st.image(image, width=300)
                with col2:
                    st.markdown("**🧼 Cleaned (1000×1000)**")
                    st.image(final_img, width=300)

                # Save cleaned image
                img_io = io.BytesIO()
                final_img.save(img_io, format="PNG")
                out_name = f"{file.name.rsplit('.', 1)[0]}_cleaned.png"
                zipf.writestr(out_name, img_io.getvalue())

                # Download button
                st.download_button(
                    label=f"⬇️ Download {file.name}",
                    data=img_io.getvalue(),
                    file_name=out_name,
                    mime="image/png"
                )

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
