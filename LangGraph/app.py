import streamlit as st
from bot import Bot

# Initialize session state
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'thread_id' not in st.session_state:
    st.session_state.thread_id = "1"

# Initialize bot
@st.cache_resource
def get_bot():
    return Bot()

def main():
    st.title("🤖 LangGraph Chat Interface")
    st.sidebar.title("Settings")
    
    # Get bot instance
    bot = get_bot()
    
    # Thread ID input in sidebar
    new_thread_id = st.sidebar.text_input("Thread ID", st.session_state.thread_id)
    if new_thread_id != st.session_state.thread_id:
        st.session_state.thread_id = new_thread_id
        st.session_state.messages = []
        st.experimental_rerun()

    # Clear chat button
    if st.sidebar.button("Clear Chat"):
        st.session_state.messages = []
        st.experimental_rerun()
    
    # Display chat messages
    for message in st.session_state.messages:
        if isinstance(message, dict):
            role = "assistant" if "assistant" in message else "user"
            content = message.get("assistant", message.get("user", ""))
        else:
            role = "user"
            content = message
            
        with st.chat_message(role):
            st.write(content)

    # Chat input
    if prompt := st.chat_input("What's on your mind?"):
        # Display user message
        with st.chat_message("user"):
            st.write(prompt)
        
        # Add message to session state
        st.session_state.messages.append({"user": prompt})
        
        # Get response
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            full_response = ""
            
            events = bot.chat(prompt, st.session_state.thread_id)
            
            for event in events:
                response = event["messages"][-1]
                message_placeholder.write(response)
                full_response = response
            
            # Add assistant's response to session state
            st.session_state.messages.append({"assistant": full_response})

    # Display memory status
    with st.sidebar.expander("Memory Status"):
        memory_data = bot.get_memory(st.session_state.thread_id)
        st.json(memory_data)

if __name__ == "__main__":
    main()