import streamlit as st
import os

st.set_page_config(page_title="AI Insights Agent", page_icon="🤖", layout="wide")
st.title("🤖 AI Insights Agent")

st.markdown("""
Ask natural language questions about the GitHub Peru Developer ecosystem. The AI Agent will use its specific tools to query the local datasets and answer.

**Examples:**
- *Who are the top developers based on stars?*
- *What is the total ecosystem overview?*
- *Find repositories related to the Manufacturing industry.*
""")

# Setup Langchain agent
try:
    import sys
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
    from src.agents.insights_agent import InsightsAgent
    
    # Needs to be cached explicitly or loaded once per session
    if 'agent' not in st.session_state:
        st.session_state.agent = InsightsAgent()
        
except Exception as e:
    st.error(f"Could not load AI Agent: {e}")
    st.stop()

if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# React to user input
if prompt := st.chat_input("Ask a question about the ecosystem..."):
    # Display user message in chat message container
    st.chat_message("user").markdown(prompt)
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("assistant"):
        with st.spinner("Thinking and analyzing datasets..."):
            try:
                # The agent automatically determines which Tool to use and formulates an answer
                response = st.session_state.agent.run_query(prompt)
            except Exception as e:
                response = f"An error occurred while reasoning: {e}"
        st.markdown(response)
        
    st.session_state.messages.append({"role": "assistant", "content": response})
