import streamlit as st
from PIL import Image, ImageColor
from rembg import remove
import io
import requests

st.title("Background Remover & Color Replacer")

# Choose method
method = st.radio("Select Image Source", ["Upload Image", "Paste Image URL"])

# Load image from file or URL
image = None

if method == "Upload Image":
    uploaded_file = st.file_uploader("Upload an image", type=["png", "jpg", "jpeg"])
    if uploaded_file:
        image = Image.open(uploaded_file).convert("RGBA")
elif method == "Paste Image URL":
    url = st.text_input("Enter image URL:")
    if url:
        try:
            response = requests.get(url)
            image = Image.open(io.BytesIO(response.content)).convert("RGBA")
        except Exception as e:
            st.error(f"Failed to load image: {e}")

# Show and process
if image:
    st.image(image, caption="Original Image", use_column_width=True)

    if st.button("Remove Background and Add Color #F2F2F2"):
        # Remove background
        output = remove(image)

        # Create new solid background
        bg_color = ImageColor.getrgb("#F2F2F2")
        background = Image.new("RGBA", output.size, bg_color + (255,))
        background.paste(output, mask=output.split()[3])  # Use alpha channel

        final_image = background.convert("RGB")
        st.image(final_image, caption="Background Replaced", use_column_width=True)

        # Download button
        buf = io.BytesIO()
        final_image.save(buf, format="JPEG")
        byte_im = buf.getvalue()
        st.download_button("Download Image", data=byte_im, file_name="replaced-bg.jpg", mime="image/jpeg")

