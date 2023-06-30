import streamlit as st
import session_state  # this is from the streamlit-session-state package
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

# Get the current session state
state = session_state.get(conversation=[], user_message='')

# Start conversation with the AI assistant greeting the user
st.header("Chat with the Assistant")
st.write("Assistant: Hi there! How can I assist you with your fashion choices today?")

# User input and button
state.user_message = st.text_input("Your message:", state.user_message)
if st.button("Send"):
    # User preferences
    user_preferences = f"I am a {gender} from {location} interested in {', '.join(fashion_likes)} fashion. I typically wear size {', '.join(sizes)}. My favorite brands are {', '.join(favorite_brands)} and I'm influenced by {favorite_influencers}. Currently, I'm looking for {looking_for}."

    # Update the conversation
    state.conversation.append({"role": "user", "content": user_preferences})
    state.conversation.append({"role": "user", "content": state.user_message})

    # Get the AI response
    response = chat_with_gpt3(state.conversation)

    # Append the response to the conversation
    state.conversation.append({"role": "assistant", "content": response})

    # Empty the text input for the next message
    state.user_message = ""

# Display conversation history
for message in state.conversation:
    st.write(f"{message['role'].capitalize()}: {message['content']}")

# End of the chat
if st.button("End Chat"):
    # Clear the conversation
    state.conversation = []
    st.success("Chat ended.")

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
