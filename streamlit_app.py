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

# Start conversation with the AI assistant greeting the user
st.header("Chat with the Assistant")
with st.empty():
    st.write("Assistant: Hi there! How can I assist you with your fashion choices today?")
conversation = [{"role": "system", "content": "You are a helpful assistant."}]
while True:
    user_message = st.text_input("Your message:")
    if user_message:
        # User preferences
        user_preferences = f"I am a {gender} from {location} interested in {', '.join(fashion_likes)} fashion. I typically wear size {', '.join(sizes)}. My favorite brands are {', '.join(favorite_brands)} and I'm influenced by {favorite_influencers}. Currently, I'm looking for {looking_for}."

        # Update the conversation
        conversation.append({"role": "user", "content": user_preferences})
        conversation.append({"role": "user", "content": user_message})

        # Get the AI response
        response = chat_with_gpt3(conversation)
        
        # Print the response
        with st.empty():
            st.write(f"Assistant: {response}")

        # Empty the text input for the next message
        user_message = ""

    if st.button("End Chat"):
        break

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
