# Research Report: AI-Recruiter Pro

**Feature**: 001-ai-recruiter-pro | **Date**: 2026-04-23
**Purpose**: Resolve all NEEDS CLARIFICATION items from Technical Context

## Research Task 1: CV Parsing Libraries

**Decision**: Use combination of `pdfplumber` (PDF), `python-docx` (DOCX), and native `open()` (TXT)

**Rationale**:
- **pdfplumber**: Superior text extraction from PDFs, preserves layout better than PyPDF2, handles tables well
- **python-docx**: Official library for DOCX, reliable extraction of paragraphs, headers, lists
- **open()**: Simple text files need no special handling

**Alternatives Considered**:
- PyPDF2: Faster but loses formatting, struggles with complex PDFs
- pdfminer.six: More powerful but heavier dependency, overkill for this use case
- textract: Unified interface but adds unnecessary abstraction layer

**Implementation Pattern**:
```python
def extract_text(file_path: str, file_type: str) -> str:
    if file_type == ".pdf":
        with pdfplumber.open(file_path) as pdf:
            return "\n".join([page.extract_text() for page in pdf.pages])
    elif file_type == ".docx":
        doc = Document(file_path)
        return "\n".join([p.text for p in doc.paragraphs])
    elif file_type == ".txt":
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
```

---

## Research Task 2: AI Analysis Engine Approach

**Decision**: Hybrid approach using sentence embeddings (HuggingFace) + keyword matching for transparency

**Rationale**:
- **Embeddings** (semantic matching): Captures meaning beyond exact keywords, handles synonyms
- **Keyword matching** (explicit requirements): Ensures mandatory skills/terms are detected
- **Combined score**: 70% embedding similarity + 30% keyword coverage
- **Feedback generation**: LLM (via prompts) for natural language explanations

**Model Selection**:
- **embeddings**: `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` (supports Spanish, lightweight)
- **keyword extraction**: spaCy + custom NER for skills/education/experience
- **feedback generation**: Template-based with dynamic insertion (no LLM API dependency for v1)

**Scoring Algorithm**:
```python
def calculate_score(cv_embeddings, profile_embeddings, keywords):
    semantic_similarity = cosine_similarity(cv_embeddings, profile_embeddings)  # 0-1
    keyword_coverage = count_matches(cv_text, keywords) / len(keywords)  # 0-1
    final_score = (0.7 * semantic_similarity + 0.3 * keyword_coverage) * 100
    return int(final_score)
```

**Alternatives Considered**:
- Pure LLM scoring (OpenAI API): Expensive at scale, latency issues, data privacy concerns
- Pure keyword matching: Misses semantic meaning, too rigid
- Custom ML model: Requires training data, overkill for MVP

---

## Research Task 3: FastAPI Session Management

**Decision**: Server-side sessions with SQLAlchemy + secure cookies

**Rationale**:
- **Team collaboration requirement**: All users see shared data, but sessions are individual
- **Server-side sessions**: Easy invalidation, no JWT token complexity, works with HTMX
- **Secure cookies**: HttpOnly, Secure, SameSite=Lax for CSRF protection

**Implementation Pattern**:
```python
# Session model
class Session(Base):
    id = Column(String, primary_key=True)  # UUID
    user_id = Column(Integer, ForeignKey("usuario.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime)
    is_valid = Column(Boolean, default=True)

# Middleware
@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    session_id = request.cookies.get("session_id")
    if session_id and not is_valid_session(session_id):
        if request.url.path not in ["/login", "/api/auth/login"]:
            return RedirectResponse("/login")
    return await call_next(request)
```

**Password Recovery Flow**:
1. User requests recovery → generate secure token (UUID + expiry 1 hour)
2. Email token link: `https://app.com/reset-password?token={uuid}`
3. Validate token, allow password reset
4. Invalidate all existing sessions for security

**Alternatives Considered**:
- JWT tokens: Stateless but harder to invalidate, overkill for server-rendered app
- OAuth2: Unnecessary complexity, no SSO requirement mentioned
- Session cookies only: No persistence across restarts

---

## Research Task 4: XLSX Export Libraries

**Decision**: Use `openpyxl` for XLSX generation

**Rationale**:
- **Formatting support**: Colors, borders, fonts, column widths (matches spec requirements)
- **Active development**: Well-maintained, good documentation
- **Streaming writer**: Memory-efficient for large datasets (10,000+ CVs)

**Implementation Pattern**:
```python
from openpyxl import Workbook
from openpyxl.styles import Font, Color, PatternFill

def export_to_xlsx(analisis_list, output_path):
    wb = Workbook()
    ws = wb.active
    ws.title = "Análisis CVs"
    
    # Headers with corporate blue
    headers = ["Candidato", "Perfil", "Puntaje", "Etiqueta", "Fecha"]
    for col, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col, value=header)
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill(start_color="125488", fill_type="solid")
    
    # Data rows with color-coded scores
    for row_idx, analisis in enumerate(analisis_list, 2):
        score_cell = ws.cell(row=row_idx, column=3, value=analisis.puntaje)
        if analisis.puntaje >= 70:
            score_cell.fill = PatternFill(start_color="28a745", fill_type="solid")
        elif analisis.puntaje >= 40:
            score_cell.fill = PatternFill(start_color="ffc107", fill_type="solid")
        else:
            score_cell.fill = PatternFill(start_color="dc3545", fill_type="solid")
    
    wb.save(output_path)
```

**Alternatives Considered**:
- xlsxwriter: More features but write-once only (can't modify)
- pandas: Simpler but less formatting control, heavier dependency
- pyxlsb: Binary format, not requested

---

## Research Task 5: HTMX File Upload with Progress

**Decision**: HTMX + custom JavaScript progress tracking via polling

**Rationale**:
- **HTMX limitations**: No built-in progress bar support for file uploads
- **Solution**: Use `htmx:beforeRequest` to capture FormData, send via XMLHttpRequest for progress events
- **Server-side**: Store upload progress in Redis/cache, poll endpoint returns percentage

**Implementation Pattern**:
```javascript
// Frontend
document.body.addEventListener('htmx:beforeRequest', function(evt) {
    if (evt.detail.elt.querySelector('input[type="file"]')) {
        const xhr = evt.detail.xhr;
        xhr.upload.addEventListener('progress', function(e) {
            const percent = (e.loaded / e.total) * 100;
            updateProgressBar(evt.detail.elt.id, percent);
        });
    }
});

// Backend endpoint
@app.get("/api/cvs/upload-status/{upload_id}")
async def get_upload_status(upload_id: str):
    progress = redis.get(f"upload:{upload_id}:progress") or 0
    return {"progress": progress, "status": "uploading" if progress < 100 else "complete"}
```

**HTMX OOB Swaps for Results**:
```html
<!-- Server returns after upload -->
<div id="progress-123" hx-swap-oob="true">
  <div class="progress-bar" style="width: 100%"></div>
  <span>Upload complete - Processing...</span>
</div>

<div id="upload-results" hx-swap-oob="true">
  <!-- Analysis results table appended here -->
</div>
```

**Alternatives Considered**:
- Dropzone.js: More features but adds heavy dependency
- Native FormData + fetch: More boilerplate, loses HTMX benefits
- WebSocket for progress: Overkill for this use case

---

## Research Task 6: Tailwind CSS Without Build Step

**Decision**: Tailwind CLI standalone + CDN for development, pre-compiled for production

**Rationale**:
- **Spec requirement**: `tailwind.config.js` must exist
- **Development**: Use Tailwind CLI in watch mode (via Air for hot-reload)
- **Production**: Pre-compile CSS, serve as static file

**Setup**:
```bash
# Install Tailwind CLI standalone
curl -sLO https://github.com/tailwindlabs/tailwindcss/releases/latest/download/tailwindcss-linux-x64
chmod +x tailwindcss-linux-x64
mv tailwindcss-linux-x64 tailwindcss

# tailwind.config.js
module.exports = {
  content: ["./backend/templates/**/*.html"],
  theme: {
    extend: {
      colors: {
        corporate: {
          blue: '#125488',
          green: '#28a745',
        }
      }
    }
  },
  plugins: []
}

# Build command (run in background during dev)
./tailwindcss -i ./backend/static/css/input.css -o ./backend/static/css/styles.css --watch
```

**input.css**:
```css
@tailwind base;
@tailwind components;
@tailwind utilities;

/* Custom styles */
.score-bar {
  transition: width 0.3s ease;
}
```

**Alternatives Considered**:
- Tailwind Play CDN: Not suitable for production (CORS, performance)
- PostCSS + Node.js: Overkill, adds build complexity
- PurgeCSS: Manual setup, Tailwind CLI includes this

---

## Research Task 7: SQLite to PostgreSQL Migration

**Decision**: Alembic (SQLAlchemy's migration tool) with dialect-agnostic migrations

**Rationale**:
- **SQLAlchemy compatibility**: Already using SQLAlchemy, Alembic is natural choice
- **Dialect-agnostic**: Write migrations once, run on SQLite or PostgreSQL
- **Version control**: Track migration history, rollback capability

**Setup**:
```python
# alembic.ini
[alembic]
script_location = backend/src/alembic
sqlalchemy.url = sqlite:///./dev.db  # Changed per environment

# env.py (read from environment)
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./dev.db")
```

**Migration Example**:
```python
# Create initial tables
def upgrade():
    op.create_table(
        "usuario",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("email", sa.String, unique=True, nullable=False),
        sa.Column("password_hash", sa.String, nullable=False),
        sa.Column("nombre", sa.String),
        sa.Column("rol", sa.String),
        sa.Column("created_at", sa.DateTime, default=datetime.utcnow),
        sa.Column("last_login", sa.DateTime)
    )
    # ... other tables

def downgrade():
    op.drop_table("usuario")
```

**Environment Variables**:
```bash
# Development
DATABASE_URL=sqlite:///./dev.db

# Production
DATABASE_URL=postgresql://user:password@localhost:5432/ai_recruiter
```

**Migration Commands**:
```bash
# Generate new migration
alembic revision --autogenerate -m "Create usuario table"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

**Alternatives Considered**:
- Raw SQL scripts: No version tracking, error-prone
- Django migrations: Requires Django framework
- Flyway: Java-based, overkill for Python project

---

## Summary of Decisions

| Area | Decision | Key Library/Tool |
|------|----------|------------------|
| CV Parsing | Multi-library approach | pdfplumber + python-docx |
| AI Analysis | Hybrid embeddings + keywords | sentence-transformers |
| Sessions | Server-side with DB | SQLAlchemy + secure cookies |
| XLSX Export | Full formatting support | openpyxl |
| HTMX Upload | Custom XHR + polling | Native XMLHttpRequest |
| Tailwind CSS | CLI standalone | tailwindcss binary |
| Migrations | Alembic | sqlalchemy + alembic |

**All NEEDS CLARIFICATION items resolved**. Ready for Phase 1 design.
