import streamlit as st
import json
import requests
import openai
from PIL import Image
import os

openai.api_key = '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'

# Load JSON data from files in a directory
clothes_data = []
for file_name in os.listdir('data'):  # replace with your directory
    if file_name.endswith('.json'):
        with open(os.path.join('data', file_name)) as f:
            clothes_data.extend(json.load(f))

# Handles conversation with OpenAI Model
def chat_with_gpt3(messages):
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo", 
        messages=messages
    )
    return response.choices[0].message['content']

# Get DALL-E image from description
def get_dalle_image(description):
    response = openai.Image.create(
        prompt=description,
        n=1,
        size="1024x1024"
    )
    image_url = response['data'][0]['url']
    return image_url

# Create title for the app
st.title("Fashion Recommendation Assistant")

# Create sidebar for user preferences
st.sidebar.header("Tell us about your preferences")

gender = st.sidebar.selectbox("What's your gender?", ["", "Female", "Male", "Other", "Prefer not to say"])
location = st.sidebar.text_input("What's your location?")
sizes = st.sidebar.multiselect("What's your size?", options=["XS", "S", "M", "L", "XL"])
fashion_likes = st.sidebar.multiselect("What kind of fashion do you like?", options=["Casual", "Formal", "Sporty", "Ethnic", "Hipster"])
favorite_brands = st.sidebar.multiselect("What are your favorite brands?", options=[brand['brandName'] for brand in clothes_data])
favorite_influencers = st.sidebar.text_input("Who are your favorite fashion influencers?")
looking_for = st.sidebar.text_input("What are you looking for specifically?")

# Initialize session state
if "conversation" not in st.session_state:
    st.session_state.conversation = []

if "user_message" not in st.session_state:
    st.session_state.user_message = ""

# Start conversation with the AI assistant greeting the user
st.header("Chat with the Assistant")
st.write("Assistant: Hi there! How can I assist you with your fashion choices today?")

# User input and button
st.session_state.user_message = st.text_input("Your message:", st.session_state.user_message)

if st.button("Send"):
    # User preferences
    user_preferences = f"I am a {gender} from {location} interested in {', '.join(fashion_likes)} fashion. I typically wear size {', '.join(sizes)}. My favorite brands are {', '.join(favorite_brands)} and I'm influenced by {favorite_influencers}. Currently, I'm looking for {looking_for}."

    # Update the conversation
    st.session_state.conversation.append({"role": "user", "content": user_preferences})
    st.session_state.conversation.append({"role": "user", "content": st.session_state.user_message})

    # Get the AI response
    response = chat_with_gpt3(st.session_state.conversation)

    # Append the response to the conversation
    st.session_state.conversation.append({"role": "assistant", "content": response})

    # Empty the text input for the next message
    st.session_state.user_message = ""

# Display conversation history
for message in st.session_state.conversation:
    st.write(f"{message['role'].capitalize()}: {message['content']}")

# End of the chat
if st.button("End Chat"):
    # Clear the conversation
    st.session_state.conversation = []
    st.success("Chat ended.")

# Generate DALL-E Image
st.header("See Some Surprise!")
if st.button("Generate"):
    # Generate a detailed description
    description = f"A {gender}-appropriate shirt suited for someone in {location} who likes {', '.join(fashion_likes)} fashion. The shirt should be in size {', '.join(sizes)} and resonate with the styles of {favorite_influencers}."

    # Get the generated image URL
    image_url = get_dalle_image(description)

    # Display the image
    st.image(image_url)

# Display clothes
st.header("Search the store")
search_term = st.text_input("Search for clothes")
search_price = st.text_input("Search by price range (e.g. 100-200)")

# Filter clothes based on search term and price range
filtered_clothes = [item for item in clothes_data 
                    if search_term.lower() in item.get("brandName", "").lower() 
                    or search_term.lower() in item.get("description", "").lower()
                    or (search_price and item.get("price") and int(search_price.split('-')[0]) <= int(item.get("price")) <= int(search_price.split('-')[1]))]

for item in filtered_clothes:
    # Get item details
    image_link = item.get("imageLink")
    brand_name = item.get("brandName")
    description = item.get("description")
    price = item.get("price")
    sizes = item.get("sizes")

    # Display item details
    st.subheader(f"{brand_name} - {description}")
    if price:
        st.text(f"Price: {price}")
    else:
        st.text("Price: Not Available")
    st.text(f"Available Sizes: {sizes}")

    # Display item image
    try:
        image = Image.open(requests.get(image_link, stream=True).raw)
        st.image(image, caption=f"{brand_name} - {description}")
    except Exception as e:
        st.write("Image not available")

    st.markdown("---")  # add a separator
