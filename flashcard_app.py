import streamlit as st
import logging
import openai  # OpenAI SDK
import fitz  # PyMuPDF
import json
import re
from typing import List, Optional, Dict, Any
from streamlit.runtime.uploaded_file_manager import UploadedFile
from streamlit_agraph import agraph, Node, Edge, Config
from io import BytesIO
from docx import Document

# --- App Configuration & Logging ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

st.set_page_config(
    page_title="AI Syllabus Mind Map Generator",
    page_icon="🧠",
    layout="wide"
)
logging.info("Application configured and started.")


# --- Functions ---
def generate_structure_with_openai(api_key: str, syllabus_text: str) -> Optional[str]:
    """Sends syllabus text to OpenAI GPT-4o-mini and asks for JSON structured output."""
    try:
        openai.api_key = api_key

        prompt = f"""
        You are an expert educator and learning assistant. Your task is to analyze the following syllabus text and structure it into a hierarchical mind map, designed for easy memorization.

        Focus on identifying the core concepts, main topics, and sub-topics, and organize them logically.

        Provide your output ONLY as a single, valid JSON object. The JSON structure should be recursive, with a 'name' for the topic and a 'children' array for its sub-topics. The root element should represent the overall subject of the syllabus.

        Do not include any text, explanations, or markdown formatting like ```json outside of the JSON object itself.
        """

        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt + syllabus_text}],
            temperature=0
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logging.error(f"OpenAI API error (structure generation): {e}", exc_info=True)
        st.error(f"An error occurred during structure generation: {e}")
        return None


def generate_topic_details_with_openai(api_key: str, topic_name: str) -> Optional[str]:
    """Sends a topic name to OpenAI GPT-4o-mini and asks for detailed explanation."""
    try:
        openai.api_key = api_key

        prompt = f"""
        You are a world-class educator, skilled at breaking down complex topics into simple, memorable concepts.
        Provide a clear and detailed explanation for the following topic, formatted in markdown.
        """

        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt + topic_name}],
            temperature=0.5
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logging.error(f"OpenAI API error (topic details for '{topic_name}'): {e}", exc_info=True)
        st.error(f"An error occurred while generating details for '{topic_name}': {e}")
        return None


# --- Graph Generation ---
def build_agraph_nodes_edges(
    node_data: Dict[str, Any],
    parent_id: str,
    nodes: List[Node],
    edges: List[Edge],
    id_to_name_map: Dict[str, str],
    level: int
):
    """Recursively builds nodes/edges for streamlit-agraph with styling per hierarchy level."""
    node_name = node_data['name']
    node_id = str(hash(parent_id + node_name))

    id_to_name_map[node_id] = node_name

    # 🎨 Style nodes based on hierarchy level
    if level == 1:   # First layer under root
        size, color = 45, "#42A5F5"   # Blue
    elif level == 2: # Second layer
        size, color = 35, "#66BB6A"   # Green
    elif level == 3: # Third layer
        size, color = 30, "#FF7043"   # Orange
    elif level == 4: # Fourth layer
        size, color = 25, "#ed1717"   # Red
    elif level == 5: #fifth layer 
        size, color = 20, "#97f867"   # light green
    elif level == 6: #sixth layer
        size, color = 15, "#ffd966"   # light orange
    else:            # Deeper levels
        size, color = 10, "#AB47BC"   # Purple

    nodes.append(Node(id=node_id, label=node_name, size=size, color=color))
    edges.append(Edge(source=parent_id, target=node_id, type="CURVE_SMOOTH"))

    if 'children' in node_data and node_data['children'] is not None:
        for child in node_data['children']:
            build_agraph_nodes_edges(child, node_id, nodes, edges, id_to_name_map, level + 1)


def create_interactive_mindmap_data(structure: Dict[str, Any]) -> tuple[List[Node], List[Edge], Dict[str, str]]:
    """Creates node and edge lists for streamlit-agraph from a structured dictionary."""
    nodes: List[Node] = []
    edges: List[Edge] = []
    id_to_name_map: Dict[str, str] = {}

    root_name = structure.get('name', 'Syllabus')
    root_id = str(hash(root_name))
    id_to_name_map[root_id] = root_name

    # 🎨 Root always larger & gold color
    nodes.append(Node(id=root_id, label=root_name, size=50, color="#FFD700"))

    if 'children' in structure and structure['children'] is not None:
        for child in structure['children']:
            build_agraph_nodes_edges(child, root_id, nodes, edges, id_to_name_map, level=1)

    return nodes, edges, id_to_name_map


# --- Helper Functions ---
def extract_text_from_pdf(uploaded_file: UploadedFile) -> Optional[str]:
    """Extracts text from an uploaded PDF file."""
    try:
        file_bytes = uploaded_file.getvalue()
        with fitz.open(stream=file_bytes, filetype="pdf") as doc:
            text = "".join(page.get_text() for page in doc)
        return text
    except Exception as e:
        logging.error(f"Error reading PDF file: {e}", exc_info=True)
        st.error(f"Error processing PDF file: {e}")
        return None


def clean_text(text: str) -> str:
    """Cleans the extracted text to make it more parsable."""
    lines = [
        line.strip() for line in text.split('\n')
        if line.strip() and not line.strip().isdigit() and len(line.strip()) > 2
    ]
    return "\n".join(lines)


def process_and_generate_mindmap(api_key: str, text_input: str) -> bool:
    """Takes text input, calls OpenAI to get a structure, and updates session state with mindmap data."""
    with st.spinner("AI is analyzing your input and building the mind map... This may take a moment."):
        cleaned_syllabus = clean_text(text_input)
        json_response_text = generate_structure_with_openai(api_key, cleaned_syllabus)
        if not json_response_text:
            st.error("Failed to get a response from the AI for structure generation.")
            return False

        st.session_state.api_key = api_key
        try:
            if json_response_text.strip().startswith("```json"):
                json_response_text = json_response_text.strip()[7:-3].strip()
            mindmap_structure = json.loads(json_response_text)
        except json.JSONDecodeError:
            st.error("The AI returned an invalid format. Please try again.")
            st.code(json_response_text)
            return False

        if not mindmap_structure:
            st.warning("The AI could not generate a structure from the provided text.")
            return False
        else:
            nodes, edges, id_to_name_map = create_interactive_mindmap_data(mindmap_structure)
            st.session_state.nodes = nodes
            st.session_state.edges = edges
            st.session_state.id_to_name_map = id_to_name_map
            st.session_state.selected_topic = None
            st.session_state.topic_details = None
            st.success("Mind map generated successfully!")
            return True

def markdown_to_plain(text: str) -> str:
    """Convert Markdown text to plain text safely."""
    if not text:
        return ""
    # Remove headers (###, ##, #)
    text = re.sub(r"^#+\s*", "", text, flags=re.MULTILINE)
    # Remove bold/italic (**text**, *text*)
    text = re.sub(r"\*\*(.*?)\*\*", r"\1", text)
    text = re.sub(r"\*(.*?)\*", r"\1", text)
    # Remove bullet symbols (-, *, +) but keep text
    text = re.sub(r"^\s*[-*+]\s+", "", text, flags=re.MULTILINE)
    return text.strip()


def create_word_doc(text: str) -> BytesIO:
    """Generate a Word document from plain text and return as BytesIO."""
    plain_text = markdown_to_plain(text or "")
    doc = Document()
    doc.add_paragraph(plain_text)

    buffer = BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer


# --- Main App Interface ---
st.title("🧠 AI-Powered Syllabus Mind Map Generator")

# --- Sidebar ---
st.sidebar.header("Configuration")
api_key = st.sidebar.text_input("Enter your OpenAI API Key", type="password")
uploaded_file = st.sidebar.file_uploader("Choose a syllabus PDF", type="pdf")
manual_text = st.sidebar.text_area("Paste syllabus text", height=200)

if st.sidebar.button("Generate Mind Map", type="primary"):
    if uploaded_file:
        raw_text = extract_text_from_pdf(uploaded_file)
    else:
        raw_text = manual_text
    if raw_text:
        process_and_generate_mindmap(api_key, raw_text)

# --- Display Mind Map ---
if 'nodes' in st.session_state and st.session_state.nodes:
    st.subheader("Generated Interactive Mind Map")
    config = Config(width=720, height=720, directed=True, physics=True, hierarchical=False, nodeHighlightBehavior=True)
    clicked_node_id = agraph(nodes=st.session_state.nodes, edges=st.session_state.edges, config=config)

    if clicked_node_id:
        topic_name = st.session_state.id_to_name_map.get(clicked_node_id)
        if topic_name and topic_name != st.session_state.get("selected_topic"):
            st.session_state.selected_topic = topic_name
            details = generate_topic_details_with_openai(api_key, topic_name)
            st.session_state.topic_details = details
            st.rerun()

    if st.session_state.get("topic_details"):
        st.markdown("---")
        st.subheader(f"Learn about: {st.session_state.selected_topic}")
        st.markdown(st.session_state.topic_details)
        
        if st.button(f"Drill Down: Create New Mind Map for '{st.session_state.selected_topic}'"):
            logging.info(f"Drill down requested for topic: {st.session_state.selected_topic}")
            topic_to_drill = st.session_state.selected_topic
            if process_and_generate_mindmap(st.session_state.api_key, topic_to_drill):
                st.session_state.path.append(topic_to_drill)
                st.rerun()
                
        # Download as Word
        word_file = create_word_doc(st.session_state.topic_details)
        st.download_button(
            label="📥 Download Explanation as Word (Plain Text)",
            data=word_file,
            file_name=f"{st.session_state.selected_topic}.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
else:
    st.info("Enter your API key, then upload a PDF or paste text in the sidebar to get started.")
