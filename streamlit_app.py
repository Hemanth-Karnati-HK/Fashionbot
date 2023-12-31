import streamlit as st
import json
import requests
from PIL import Image
import os
from recombee_api_client.api_client import RecombeeClient, Region
from recombee_api_client.api_requests import AddItem, AddDetailView, RecommendItemsToUser
import openai


openai.api_key = 'place holder'
client = RecombeeClient('place holder', 'place holder',region=Region.US_WEST)

# Load JSON data from files in a directory
clothes_data = []
for file_name in os.listdir('data'):  
    if file_name.endswith('.json'):
        with open(os.path.join('data', file_name)) as f:
            clothes_data.extend(json.load(f))

# Handles conversation with OpenAI Model
def chat_with_gpt3(messages):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo", 
            messages=messages
        )
        return response.choices[0].message['content']
    except Exception as e:
        print(f"Error in chat_with_gpt3: {e}")
        return "Error in generating AI response"

# Get DALL-E image from description
def get_dalle_image(description):
    try:
        response = openai.Image.create(
            prompt=description,
            n=1,
            size="1024x1024"
        )
        image_url = response['data'][0]['url']
        return image_url
    except Exception as e:
        print(f"Error in get_dalle_image: {e}")
        return None

# Record an interaction when a user views an item
def record_user_interaction(user_id, item_id):
    try:
        client.send(AddDetailView(user_id, item_id, cascade_create=True))
    except Exception as e:
        print(f"Error in record_user_interaction: {e}")

# Get recommendations for a user
def get_recommendations(user_id, count):
    try:
        recommended = client.send(RecommendItemsToUser(user_id, count))
        return recommended['recomms']
    except Exception as e:
        print(f"Error in get_recommendations: {e}")
        return []

# Create title for the app
st.title("Fashion Recommendation Assistant")

# Ask the user to enter a username at the start of the app
if "username" not in st.session_state:
    st.session_state.username = st.text_input("Enter a username to start:")
    if st.session_state.username:
        st.success(f"Welcome, {st.session_state.username}!")
    else:
        st.stop()  # Stop execution until a username is entered
else:
    st.write(f"Welcome back, {st.session_state.username}!")

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

# Generate DALL-E Image
st.header("See Some Surprise!")
if st.button("Generate"):
    # Generate a detailed description
    description = f"A {gender}-appropriate shirt suited for someone in {location} who likes {', '.join(fashion_likes)} fashion. The shirt should be in size {', '.join(sizes)} and resonate with the styles of {favorite_influencers}."

    # Get the generated image URL
    image_url = get_dalle_image(description)

    # Display the image
    st.image(image_url)

# Filter clothes based on user preferences and sizes
filtered_clothes = [item for item in clothes_data 
                    if (not favorite_brands or favorite_brands in item.get("brandName", "").lower())
                    and (not sizes or any(size.lower() in item.get("sizes", "").lower() for size in sizes))
                    and (not looking_for or looking_for.lower() in item.get("description", "").lower() or looking_for.lower() in item.get("brandName", "").lower())]

# Get recommendations from the filtered clothes
# for index, item in enumerate(filtered_clothes):
#     item_id = f"item_{index}"  # Generate an ID using index
#     try:
#         # Ensure item properties are properly formatted
#         item_properties = {
#             'brandName': item.get('brandName', ''),
#             'description': item.get('description', ''),
#             'imageLink': item.get('imageLink', ''),
#             'price': item.get('price', ''),
#             'sizes': item.get('sizes', '')
#         }
#         client.send(AddItem(item_id, item_properties))
#     except Exception as e:
#         print(f"Error adding item {item_id} to Recombee: {e}")
# Get recommendations from the filtered clothes
for index, item in enumerate(filtered_clothes):
    item_id = f"item_{index}"  # Generate an ID using index
    try:
        client.send(AddItem(item_id))
    except Exception as e:
        print(f"Error adding item {item_id} to Recombee: {e}")


# Display some recommendations
st.header("Recommended for you")
recommended_item_ids = get_recommendations(st.session_state.username, 10)
recommended_items = [item for index, item in enumerate(filtered_clothes) if f"item_{index}" in recommended_item_ids]

for item in recommended_items:
    col1, col2 = st.columns(2)
    with col1:
        st.write(f"Brand: {item['brandName']}")
        st.write(f"Description: {item['description']}")
        st.write(f"Price: {item['price']}")
        st.write(f"Sizes: {item['sizes']}")
    with col2:
        st.image(item['imageLink'])
    st.write("------")

# Display filtered clothes
st.header("Filtered Clothes for You")
for item in filtered_clothes:
    col1, col2 = st.columns(2)
    with col1:
        st.write(f"Brand: {item['brandName']}")
        st.write(f"Description: {item['description']}")
        st.write(f"Price: {item['price']}")
        st.write(f"Sizes: {item['sizes']}")
    with col2:
        st.image(item['imageLink'])
    st.write("------")

# End of the chat
if st.button("End Chat"):
    # Clear the conversation
    st.session_state.conversation = []
    st.success("Chat ended.")
