import streamlit as st
from PIL import Image
import requests
import io
import zipfile

st.set_page_config(page_title="Background Remover", layout="wide")
st.title("🧼 Remove Background (Powered by remove.bg API)")

# --------------------------
# Settings
# --------------------------
REMOVE_BG_API_KEY = st.secrets["REMOVE_BG_API_KEY"]  # Store your key in Streamlit secrets
replace_color = st.color_picker("🎨 Background color", "#F2F2F2")
bg_choice = st.radio("Background type", ["Transparent", "White", "Custom Color"])

# --------------------------
# Upload & URL input
# --------------------------
uploaded_files = st.file_uploader("📤 Upload image(s)", type=["jpg", "jpeg", "png"], accept_multiple_files=True)
url = st.text_input("🔗 Or paste image URL")

image_queue = []

# --------------------------
# Load image from URL
# --------------------------
if url:
    try:
        response = requests.get(url)
        if response.status_code == 200:
            img = Image.open(io.BytesIO(response.content))
            image_queue.append(("linked_image.png", img))
        else:
            st.error(f"❌ Could not load image. HTTP {response.status_code}")
    except Exception as e:
        st.error(f"⚠️ Error loading image: {e}")

# --------------------------
# Load uploaded images
# --------------------------
if uploaded_files:
    for file in uploaded_files:
        try:
            image = Image.open(file)
            image_queue.append((file.name, image))
        except:
            st.warning(f"{file.name} is not a valid image.")

# --------------------------
# Process images
# --------------------------
zip_buffer = io.BytesIO()
processed_files = []

if image_queue:
    st.subheader("✅ Processed Images")
    with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED) as zipf:
        for name, image in image_queue:
            # Convert image to bytes
            img_byte_arr = io.BytesIO()
            image.save(img_byte_arr, format="PNG")
            img_byte_arr.seek(0)

            # Send to remove.bg API
            bg_color = None
            if bg_choice == "White":
                bg_color = "ffffff"
            elif bg_choice == "Custom Color":
                bg_color = replace_color.lstrip("#")

            response = requests.post(
                "https://api.remove.bg/v1.0/removebg",
                files={"image_file": img_byte_arr},
                data={"size": "auto", "bg_color": bg_color} if bg_color else {"size": "auto"},
                headers={"X-Api-Key": REMOVE_BG_API_KEY},
            )

            if response.status_code == requests.codes.ok:
                cleaned_img = Image.open(io.BytesIO(response.content)).resize((1000, 1000))
                
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(f"**🖼️ {name} – Original**")
                    st.image(image, width=300)
                with col2:
                    st.markdown("**🧼 Cleaned**")
                    st.image(cleaned_img, width=300)

                # Save in ZIP
                img_io = io.BytesIO()
                cleaned_img.save(img_io, format="PNG")
                zipf.writestr(name, img_io.getvalue())

                # Add individual download button
                st.download_button(
                    label=f"⬇️ Download {name}",
                    data=img_io.getvalue(),
                    file_name=name,
                    mime="image/png"
                )

            else:
                st.error(f"❌ Failed to process {name}: {response.text}")

    # ZIP download
    zip_buffer.seek(0)
    st.download_button(
        label="📦 Download All as ZIP",
        data=zip_buffer,
        file_name="cleaned_images.zip",
        mime="application/zip"
    )
