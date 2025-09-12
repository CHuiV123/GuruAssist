## Originally from: https://github.com/ranjithmadheswaran/GuruAssist

## Forked and modified by: Hui Voon 
## Additional features: 
1. added in **Language Selection** for user to select the mindmap generation language
2. added in **Download Function** for user to download the generated text 
3. added in **Model Provider** option for user to select between OpenAI or Google Gemini
4. changing fundamental function to be study assist app
5. added in color hieracy for the mind map node
   
   <img width="230" height="300" alt="image" src="https://github.com/user-attachments/assets/0eeb4acb-bb31-40ae-b5fd-3ca4e005c774" />




# 🧠 StudyAssist: AI-Powered Mind Map Generator

StudyAssist is a smart learning tool that transforms your syllabus or study notes into interactive, explorable mind maps. Built with Streamlit and powered by OpenAI GPT4o-mini, Google Gemini 2.0-flash model, it helps you visualize complex topics, understand relationships between concepts, and dive deep into subjects on demand.

*Replace this with a GIF or screenshot of your application in action!*

## ✨ Features

- **Dual Input Methods**: Generate mind maps from either a **PDF file** or by **pasting raw text**.
- **AI-Powered Generation**: Leverages the OpenAI API to intelligently analyze your content and build a hierarchical mind map.
- **Interactive Visualization**: Explore your mind map with a dynamic, zoomable, and draggable interface.
- **Click-to-Learn**: Click on any topic (node) in the mind map to get an instant, AI-generated summary, key points, and examples.
- **Recursive Drill-Down**: Not enough detail? Select any topic and generate a brand new, more focused mind map for it.
- **Breadcrumb Navigation**: Keep track of your learning path as you drill down into sub-topics.

## 🛠️ Tech Stack

- **Framework**: [Streamlit](https://streamlit.io/)
- **AI Engine**: [OpenAI API](https://platform.openai.com/)
- **PDF Extraction**: [PyMuPDF](https://pymupdf.readthedocs.io/en/latest/)
- **Graph Visualization**: [streamlit-agraph](https://github.com/ChrisChs/streamlit-agraph)
- **Language**: Python

## 🚀 Getting Started

Follow these steps to set up and run GuruAssist on your local machine.

### Prerequisites

- Python 3.8+
- A Google AI API Key. You can get a paid api key from [OpenAI API Platform](https://platform.openai.com/).

### Installation

1.  **Clone the repository:**
    *(Replace the URL with your actual repository link after you push it to GitHub/GitLab etc.)*
    ```bash
    git clone https://github.com/your-username/GuruAssist.git
    cd GuruAssist
    ```

2.  **Create and activate a virtual environment (recommended):**
    ```bash
    # For macOS/Linux
    python3 -m venv venv
    source venv/bin/activate

    # For Windows
    python -m venv venv
    .\venv\Scripts\activate
    ```

3.  **Install the required dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

### Running the Application

1.  **Run the Streamlit app from your terminal:**
    ```bash
    streamlit run flashcard_app.py
    ```

2.  **Open your browser** to `http://localhost:8501`.

3.  **Enter your OpenAI API Key** in the sidebar, upload a PDF or paste text, and click "Generate Mind Map"!

## Usage

1.  Provide your OpenAI API Key in the sidebar.
2.  Upload a syllabus PDF or paste your study notes into the text area.
3.  Click **"Generate Mind Map"**.
4.  Interact with the generated mind map:
    - Drag nodes to rearrange them.
    - Use your mouse wheel to zoom in and out.
    - Click on a node to view a detailed explanation.
5.  To explore a topic further, click the **"Drill Down"** button that appears below the details.
6.  Use the **"Reset and Start Over"** button to clear the canvas and begin again.

---
This project was a fun exploration of how quickly ideas can be prototyped with modern AI and Python tools. Enjoy!
