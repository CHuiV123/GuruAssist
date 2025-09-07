import streamlit as st
import fitz  # PyMuPDF
import logging
from typing import List, Optional
import json
import google.generativeai as genai
from typing import List, Optional, Dict, Any
from streamlit.runtime.uploaded_file_manager import UploadedFile
from streamlit_agraph import agraph, Node, Edge, Config

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
# --- Gemini API Interaction ---

def generate_structure_with_gemini(api_key: str, syllabus_text: str) -> Optional[str]:
    """
    Sends syllabus text to the Gemini API and asks for a structured JSON output.
    """
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        prompt = f"""
        You are an expert educator and learning assistant. Your task is to analyze the following syllabus text and structure it into a hierarchical mind map, designed for easy memorization.

        Focus on identifying the core concepts, main topics, and sub-topics, and organize them logically.

        Provide your output ONLY as a single, valid JSON object. The JSON structure should be recursive, with a 'name' for the topic and a 'children' array for its sub-topics. The root element should represent the overall subject of the syllabus.

        Do not include any text, explanations, or markdown formatting like ```json outside of the JSON object itself.

        Example of the required JSON format:
        {{
          "name": "Overall Subject",
          "children": [
            {{
              "name": "Main Topic 1",
              "children": [
                {{"name": "Sub-topic 1.1"}},
                {{"name": "Sub-topic 1.2"}}
              ]
            }},
            {{
              "name": "Main Topic 2"
            }}
          ]
        }}

        Syllabus Text to Analyze:
        ---
        {syllabus_text}
        ---
        """
        
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        logging.error(f"Gemini API error (structure generation): {e}", exc_info=True)
        st.error(f"An error occurred during structure generation: {e}")
        return None

def generate_topic_details_with_gemini(api_key: str, topic_name: str) -> Optional[str]:
    """
    Sends a topic name to Gemini and asks for a detailed explanation.
    """
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        prompt = f"""
        You are a world-class educator, skilled at breaking down complex topics into simple, memorable concepts.
        Provide a clear and detailed explanation for the following topic, formatted in markdown.
        Your explanation should include:
        1.  **Summary**: A brief, one or two-sentence summary of the topic.
        2.  **Key Points**: A bulleted list of the 3-5 most important concepts or facts.
        3.  **Example/Analogy**: A simple, real-world example or an easy-to-understand analogy.

        Do not include the topic name as a header in your response (e.g., no "### Topic Name"). The application will provide the title.

        Topic to explain: "{topic_name}"
        """
        
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        logging.error(f"Gemini API error (topic details for '{topic_name}'): {e}", exc_info=True)
        st.error(f"An error occurred while generating details for '{topic_name}': {e}")
        return None

# --- Graph Generation ---

def build_agraph_nodes_edges(node_data: Dict[str, Any], parent_id: str, nodes: List[Node], edges: List[Edge], id_to_name_map: Dict[str, str]):
    """Recursively builds lists of nodes and edges for streamlit-agraph."""
    node_name = node_data['name']
    # Use a combination of parent and name for a more unique ID
    node_id = str(hash(parent_id + node_name))
    
    id_to_name_map[node_id] = node_name
    nodes.append(Node(id=node_id, label=node_name, size=15))
    edges.append(Edge(source=parent_id, target=node_id, type="CURVE_SMOOTH"))
    
    if 'children' in node_data and node_data['children'] is not None:
        for child in node_data['children']:
            build_agraph_nodes_edges(child, node_id, nodes, edges, id_to_name_map)

def create_interactive_mindmap_data(structure: Dict[str, Any]) -> tuple[List[Node], List[Edge], Dict[str, str]]:
    """Creates node and edge lists for streamlit-agraph from a structured dictionary."""
    nodes: List[Node] = []
    edges: List[Edge] = []
    id_to_name_map: Dict[str, str] = {}
    
    root_name = structure.get('name', 'Syllabus')
    root_id = str(hash(root_name))
    id_to_name_map[root_id] = root_name
    # Make the root node bigger and a different color
    nodes.append(Node(id=root_id, label=root_name, size=25, color="#F9A825")) 
    
    if 'children' in structure and structure['children'] is not None:
        for child in structure['children']:
            build_agraph_nodes_edges(child, root_id, nodes, edges, id_to_name_map)
            
    return nodes, edges, id_to_name_map

# --- Helper Functions ---

def extract_text_from_pdf(uploaded_file: UploadedFile) -> Optional[str]:
    """Extracts text from an uploaded PDF file."""
    try:
        # To read the uploaded file, we need to get its content in bytes
        file_bytes = uploaded_file.getvalue()
        with fitz.open(stream=file_bytes, filetype="pdf") as doc:
            # Use a generator expression within join for better performance on large files
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
    """
    Takes text input, calls Gemini to get a structure, and updates session state with mindmap data.
    Returns True on success, False on failure.
    """
    with st.spinner("AI is analyzing your input and building the mind map... This may take a moment."):
        # 1. Clean the input text
        cleaned_syllabus = clean_text(text_input)
        logging.info(f"Cleaned input text. Length: {len(cleaned_syllabus)} characters.")

        # 2. Call Gemini API to get structured data
        logging.info("Calling Gemini API to generate mind map structure.")
        json_response_text = generate_structure_with_gemini(api_key, cleaned_syllabus)
        if not json_response_text:
            logging.error("Received no response from structure generation API.")
            st.error("Failed to get a response from the AI for structure generation.")
            return False

        # If the API call was successful, store the key for subsequent calls
        st.session_state.api_key = api_key
        logging.info("API key validated and stored in session state.")

        # 3. Parse the JSON response
        try:
            if json_response_text.strip().startswith("```json"):
                json_response_text = json_response_text.strip()[7:-3].strip()
            logging.info("Parsing JSON response from AI.")
            mindmap_structure = json.loads(json_response_text)
            logging.info("Successfully parsed mind map structure.")
        except json.JSONDecodeError:
            logging.error("Failed to decode JSON from AI response.", exc_info=True)
            st.error("The AI returned an invalid format. Please try again.")
            st.code(json_response_text)
            return False

        # 4. Create and store mind map data
        if not mindmap_structure:
            logging.warning("Mind map structure is empty after parsing.")
            st.warning("The AI could not generate a structure from the provided text.")
            return False
        else:
            logging.info("Creating interactive mind map data (nodes and edges).")
            nodes, edges, id_to_name_map = create_interactive_mindmap_data(mindmap_structure)
            
            st.session_state.nodes = nodes
            st.session_state.edges = edges
            st.session_state.id_to_name_map = id_to_name_map
            st.session_state.selected_topic = None
            st.session_state.topic_details = None
            
            st.success("Mind map generated successfully!")
            logging.info("Mind map displayed successfully.")
            return True

# --- Main App Interface ---
st.title("🧠 AI-Powered Syllabus Mind Map Generator")
st.write(
    "Upload your course syllabus as a PDF. Gemini will analyze the content and generate a conceptual mind map to supercharge your study sessions!"
)

# --- Sidebar for API Key and File Upload ---
st.sidebar.header("Configuration")
api_key = st.sidebar.text_input("Enter your Google AI API Key", type="password", help="Get your key from Google AI Studio.")
uploaded_file = st.sidebar.file_uploader("Choose a syllabus PDF", type="pdf")
st.sidebar.markdown("<p style='text-align: center;'>OR</p>", unsafe_allow_html=True)
manual_text = st.sidebar.text_area(
    "Paste your topic/syllabus text here",
    height=200,
    placeholder="e.g., Introduction to Python, Variables, Data Types, Loops..."
)

st.sidebar.markdown("---")
if st.sidebar.button("Reset and Start Over"):
    # Clear all relevant session state to start fresh
    st.session_state.nodes = []
    st.session_state.edges = []
    st.session_state.id_to_name_map = {}
    st.session_state.selected_topic = None
    st.session_state.topic_details = None
    st.session_state.path = []
    # We keep the api_key in case the user wants to reuse it
    logging.info("Session state has been reset by the user.")
    st.rerun()

# --- Session State Initialization ---
# This ensures that our data persists across reruns (e.g., after a node click)
if 'nodes' not in st.session_state:
    st.session_state.nodes = []
if 'edges' not in st.session_state:
    st.session_state.edges = []
if 'id_to_name_map' not in st.session_state:
    st.session_state.id_to_name_map = {}
if 'selected_topic' not in st.session_state:
    st.session_state.selected_topic = None
if 'topic_details' not in st.session_state:
    st.session_state.topic_details = None
if 'api_key' not in st.session_state:
    st.session_state.api_key = None
if 'path' not in st.session_state:
    st.session_state.path = []

if st.sidebar.button("Generate Mind Map", type="primary"):
    logging.info("'Generate Mind Map' button clicked.")
    if not api_key:
        st.warning("Please enter your Google AI API Key in the sidebar.")
        logging.warning("API key is missing.")
    elif not uploaded_file and not manual_text:
        st.warning("Please upload a PDF or paste text into the text box to generate a mind map.")
        logging.warning("No input provided (neither PDF nor text).")
    else:
        # 1. Get text from either the uploaded file or the text area
        raw_text = ""
        if uploaded_file:
            logging.info(f"Processing uploaded file: {uploaded_file.name}")
            raw_text = extract_text_from_pdf(uploaded_file)
        elif manual_text:
            logging.info("Processing text from manual input.")
            raw_text = manual_text

        if raw_text:
            # Reset path for a new top-level generation
            st.session_state.path = []
            success = process_and_generate_mindmap(api_key, raw_text)
            if success:
                # Find the root node to initialize the breadcrumb path
                root_node_id = next((node.id for node in st.session_state.nodes if node.size == 25), None)
                if root_node_id:
                    root_name = st.session_state.id_to_name_map.get(root_node_id, "Syllabus")
                    st.session_state.path.append(root_name)
                st.rerun()

# --- Display Mind Map and Details (if data exists in session state) ---
if st.session_state.nodes:
    if st.session_state.path:
        st.markdown(f"**Path:** `{' > '.join(st.session_state.path)}`")

    st.subheader("Generated Interactive Mind Map")
    st.info("Click on a node to get a detailed explanation of the topic.")
    
    config = Config(width=900, 
                    height=600, 
                    directed=True, 
                    physics=True, 
                    hierarchical=False,
                    # Highlight clicked node
                    nodeHighlightBehavior=True,
                    highlightColor="#F7A7A6",
                   )

    # agraph returns the ID of the last clicked node
    clicked_node_id = agraph(nodes=st.session_state.nodes, edges=st.session_state.edges, config=config)

    if clicked_node_id:
        topic_name = st.session_state.id_to_name_map.get(clicked_node_id)
        logging.info(f"Node clicked. ID: {clicked_node_id}, Topic: {topic_name}")
        # If a new topic is clicked, fetch its details
        if topic_name and topic_name != st.session_state.selected_topic:
            # Use the API key stored in the session state for robustness
            if not st.session_state.api_key:
                st.warning("Could not find a valid API key. Please generate the mind map again with a valid key.")
            else:
                st.session_state.selected_topic = topic_name
                with st.spinner(f"🧠 Generating details for '{topic_name}'..."):
                    logging.info(f"Fetching details for new topic: '{topic_name}'")
                    details = generate_topic_details_with_gemini(st.session_state.api_key, topic_name)
                    st.session_state.topic_details = details
                st.rerun() # Rerun to display the new details immediately

    # Display the details if they exist in the session state
    if st.session_state.selected_topic and st.session_state.topic_details:
        st.markdown("---")
        st.subheader(f"Learn about: {st.session_state.selected_topic}")
        st.markdown(st.session_state.topic_details)

        # Add the "Drill Down" button
        if st.button(f"Drill Down: Create New Mind Map for '{st.session_state.selected_topic}'"):
            logging.info(f"Drill down requested for topic: {st.session_state.selected_topic}")
            topic_to_drill = st.session_state.selected_topic
            if process_and_generate_mindmap(st.session_state.api_key, topic_to_drill):
                st.session_state.path.append(topic_to_drill)
                st.rerun()
else:
    st.info("Enter your API key, then upload a PDF or paste text in the sidebar to get started.")