import streamlit as st

# Page setup
st.set_page_config(page_title="Agent Playground Home", page_icon="🤖", layout="centered")

# Title and intro
st.title("🧠 Agent Playground")
st.markdown("""
Welcome to the **Agent Playground**. This tool helps you create intelligent agents that can:
- 🔌 Connect to enterprise data tools like Fabric
- 🤖 Use custom logic (like Genie functions)
- 💬 Interact in a natural, chat-like interface

Use this playground to **prototype**, **test**, and **refine** your agents step-by-step.
""")

st.divider()

# Step-by-step section
st.header("🛠️ Step-by-Step Guide")

col1, col2 = st.columns(2)

with col1:
    st.subheader("1️⃣ Create Your Agent")
    st.markdown("""
    - Configure your agent’s **name**, **prompt**, and **deployment**
    - Attach tools like Fabric or Genie
    - Agents are saved in your session and reusable
    """)
    if st.button("Go to Agent Configuration"):
        st.switch_page("pages/01-Configure_Agent.py")

with col2:
    st.subheader("2️⃣ Chat with Your Agent")
    st.markdown("""
    - Use the **Agent Playground** to send natural language prompts
    - Get responses backed by your tools
    - Thumbs-up/down feedback for fine-tuning
    """)
    if st.button("Go to Agent Playground"):
        st.switch_page("pages/02-Agent_Playground.py")

st.divider()

# Optional section for advanced users
with st.expander("✨ Advanced Functionality"):
    st.markdown("""
    - View and switch between multiple agents in the sidebar
    - Inspect agent configuration and prompt snippets
    - Responses are powered by Azure OpenAI and toolsets in real time
    - Easily restart threads or reconfigure prompts
    """)

# Footer
st.caption("Built with ❤️ using Azure AI Foundry + Streamlit")
