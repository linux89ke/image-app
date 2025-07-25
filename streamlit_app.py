import streamlit as st
from PIL import Image, ImageColor, ImageFilter, UnidentifiedImageError
import requests
import io

# rembg 2.x+
from rembg import remove
from rembg import new_session

st.title("🛒 Jumia Image Background Remover")
st.markdown("Paste a Jumia image link. We’ll remove the background, keep any labels, and add a new background color.")

url = st.text_input("🔗 Enter Jumia image URL:")

if url:
    try:
        headers = {
            "User-Agent": "Mozilla/5.0",
            "Referer": "https://www.jumia.co.ke/",
        }

        response = requests.get(url, headers=headers, timeout=10)

        if response.status_code == 200:
            image_bytes = io.BytesIO(response.content)
            image = Image.open(image_bytes).convert("RGBA")
            st.image(image, caption="📸 Original Image", use_column_width=True)

            if st.button("✨ Remove Background & Replace with #F2F2F2"):
                session = new_session("u2net")  # CORRECT usage, single positional arg
                cutout = remove(image, session=session)

                # Smooth the alpha edges
                alpha = cutout.split()[3].filter(ImageFilter.GaussianBlur(radius=1.0))
                cutout.putalpha(alpha)

                # Create new background
                bg_color = ImageColor.getrgb("#F2F2F2")
                background = Image.new("RGBA", cutout.size, bg_color + (255,))
                background.paste(cutout, mask=cutout.getchannel("A"))
                final = background.convert("RGB")

                st.image(final, caption="✅ Cleaned Image", use_column_width=True)

                # Downloadable file
                buf = io.BytesIO()
                final.save(buf, format="JPEG")
                st.download_button("📥 Download Image", data=buf.getvalue(),
                                   file_name="jumia_cleaned.jpg", mime="image/jpeg")
        else:
            st.error(f"❌ Could not fetch image. HTTP status code: {response.status_code}")

    except UnidentifiedImageError:
        st.error("⚠️ That file is not a valid image.")
    except Exception as e:
        st.error(f"⚠️ Error loading image: {e}")
