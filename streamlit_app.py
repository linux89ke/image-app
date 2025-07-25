import streamlit as st
from PIL import Image, ImageColor, ImageFilter
from rembg import remove
import requests
import io

st.title("🛒 Jumia Image Background Remover")
st.write("Paste a Jumia image URL (with price tags or labels) and get a cleaned version with a solid background.")

url = st.text_input("🔗 Paste Jumia image URL below:")

if url:
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                          "(KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
            "Referer": "https://www.jumia.co.ke/",
            "Accept": "image/webp,image/apng,image/*,*/*;q=0.8",
        }

        response = requests.get(url, headers=headers, timeout=10)

        if response.status_code == 200:
            image_bytes = io.BytesIO(response.content)
            image = Image.open(image_bytes).convert("RGBA")
            st.image(image, caption="🖼️ Original Image", use_column_width=True)

            if st.button("✨ Remove Background & Preserve Tags"):
                # Remove background
                cutout = remove(image, model_name='u2net')  # or 'isnet-general-use' for higher quality

                # Feather the alpha mask for smoother edges
                alpha = cutout.split()[3].filter(ImageFilter.GaussianBlur(radius=1.0))
                cutout.putalpha(alpha)

                # Replace background with solid #F2F2F2
                bg_color = ImageColor.getrgb("#F2F2F2")
                background = Image.new("RGBA", cutout.size, bg_color + (255,))
                background.paste(cutout, mask=cutout.getchannel("A"))

                final = background.convert("RGB")
                st.image(final, caption="✅ Cleaned Image", use_column_width=True)

                # Download option
                buf = io.BytesIO()
                final.save(buf, format="JPEG")
                st.download_button("📥 Download Image", data=buf.getvalue(),
                                   file_name="jumia-product.jpg", mime="image/jpeg")
        else:
            st.error(f"❌ Could not fetch image. HTTP {response.status_code}")

    except Exception as e:
        st.error(f"⚠️ Error loading image: {e}")

