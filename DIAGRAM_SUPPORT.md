# Diagram Extraction & Rendering System

## 🎯 New Feature

The system now automatically extracts **diagrams, graphs, and figures** from PDF question papers and displays them **inline** with the corresponding questions.

### 🖼️ How It Works

#### 1. extraction Phase (`extract_text_from_file`)

- **PDF Analysis**: Used `pdfplumber` to analyze both text words and image objects on each page.
- **Position Mapping**: Sorted all elements (text lines and images) by their vertical position (`top` coordinate).
- **Merge Logic**: Reconstructed the page content stream by interleaving text and images in their visual order.
- **Image Saving**: Cropped diagrams are saved to `static/images/` with unique IDs.
- **Markdown Injection**: Inserted `![Diagram](url)` markers into the text stream exactly where the image appears.

#### 2. Analysis Phase (`parse_questions`)

- **Multi-Line Support**: Upgraded the parser to support multi-line questions.
- **Context Preservation**: The parser now "accumulates" lines following a question starter, ensuring that a diagram appearing after the question text is included in that question's block.
- **Cleaning**: Filters out noise but strictly preserves `![Diagram](...)` tags.

#### 3. Content Delivery (`FastAPI`)

- **Static Hosting**: Mounted `/static` endpoint to serve the extracted image files.
- **CORS Handling**: Images are accessible to the frontend via localhost.

#### 4. Frontend Rendering (`PYQAnalytics.jsx`)

- **Markdown Parsing**: Implemented a custom renderer to detect `![Diagram](url)` syntax.
- **Visual Display**: Renders a styled `<img>` tag within the question card.
- **Responsive Design**: Images are scaled to fit the container with a subtle bounding box.

### ✅ User Benefit

- **Complete Context**: Questions like "Analyze the given circuit" now show the actual circuit.
- **Visual Learning**: Graph-based questions are fully fully represented.
- **No Missing Info**: Students don't need to refer back to the original PDF.

---

**Status**: Implemented & Active ✅
**Version**: 1.0 (Visual Support)
