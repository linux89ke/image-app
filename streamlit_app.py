import streamlit as st
from PIL import Image, ImageColor, ImageFilter
from rembg import remove
import requests
import io

st.title("Jumia Product Background Remover (Preserve Tags/Text)")

url = st.text_input("Paste Jumia image URL")

if url:
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=10)

        if response.status_code == 200:
            image_bytes = io.BytesIO(response.content)
            image = Image.open(image_bytes).convert("RGBA")
            st.image(image, caption="Original Image", use_column_width=True)

            if st.button("Remove Background but Keep Text & Tags"):
                # Remove background using rembg
                cutout = remove(image, model_name='u2net')  # or 'isnet-general-use' for better edges

                # Feather the alpha mask a bit for smoother edges
                alpha = cutout.split()[3].filter(ImageFilter.GaussianBlur(radius=1.0))
                cutout.putalpha(alpha)

                # Create new solid background
                bg_color = ImageColor.getrgb("#F2F2F2")
                background = Image.new("RGBA", cutout.size, bg_color + (255,))
                background.paste(cutout, mask=cutout.getchannel("A"))  # only paste non-transparent parts

                final = background.convert("RGB")
                st.image(final, caption="Processed Image with Text Preserved", use_column_width=True)

                buf = io.BytesIO()
                final.save(buf, format="JPEG")
                st.download_button("Download", data=buf.getvalue(), file_name="jumia-product.jpg", mime="image/jpeg")

        else:
            st.error(f"Could not fetch image. HTTP {response.status_code}")

    except Exception as e:
        st.error(f"Failed to load image: {e}")
