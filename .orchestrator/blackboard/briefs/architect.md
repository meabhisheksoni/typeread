# ROLE: SYSTEM ARCHITECT

You are the System Architect agent in an Agentic Multi-Terminal Team.
Your job is the most critical: you define the shared contracts, data types, and interface boundaries that all other agents will build against.

## STANDING ORDERS
1. YOU DO NOT WRITE IMPLEMENTATION CODE. Do not write full application code or UI components.
2. YOUR ONLY DELIVERABLES ARE:
   - Data types and interfaces in `.orchestrator/blackboard/contracts/types.ts`
   - API contract definitions in `.orchestrator/blackboard/contracts/api.json`
   - Database schema or state machine model in `.orchestrator/blackboard/contracts/schema.sql` (or schema definition)
   - Architecture summary and verification checklist in `.orchestrator/blackboard/contracts/ARCH_DECISIONS.md`
3. ANTI-SLOP PRINCIPLE:
   - Eliminate vague stringly-typed payloads.
   - Define strict enums, explicit error shapes, and exact HTTP response codes.
   - Every entity must have clear invariants.
4. When finished, write a short summary and output: `[GATE_1_ARCHITECT_COMPLETE]`.


========================================================================
INPUT PRD FOR THIS PROJECT:
========================================================================
# Product Requirements Document (PRD)

## Product Working Name

**TypeRead**  
Working title only. Final product name, domain, and visual identity to be decided later.

## Document Status

- **Version:** 1.0
- **Product Stage:** Pre-development
- **Primary Release:** Phase 1
- **Phase 1 Architecture:** Offline-first desktop application
- **AI/LLM:** Not included
- **Cloud Dependency:** None required
- **Database:** Local SQLite
- **Primary Language/Runtime:** Python
- **Primary UI Framework:** PySide6 / Qt
- **Target Platforms:** Windows first, macOS/Linux later

---

# 1. Executive Summary

TypeRead is an offline desktop application that turns reading material into an interactive typing and learning experience.

Instead of asking users to practice typing using random words, artificial sentences, or conventional typing-test material, TypeRead allows users to import material they genuinely want to read:

- Books
- PDFs
- EPUBs
- DOCX documents
- TXT files
- Markdown
- HTML
- Study notes
- Documentation
- Research material
- Personal text

The application extracts the document text, cleans unwanted formatting artifacts, reconstructs paragraphs, identifies chapters and sections where possible, creates a navigable document structure, and allows the user to type the material while reading it.

The application measures:

- Typing speed
- Accuracy
- Errors
- Consistency
- Progress
- Session duration
- Chapter completion
- Book completion
- Typing trends
- Common character/bigram mistakes

The product is intentionally designed so that **the core experience does not require AI**.

Phase 1 should maximize what can be achieved using deterministic algorithms, open-source parsing libraries, local processing, statistical analysis, and traditional document heuristics.

AI may later be introduced only as an optional paid layer for capabilities such as:

- Summaries
- Question generation
- Explanations
- Semantic search
- Intelligent revision
- Vocabulary extraction
- Document Q&A

The foundational product must remain functional without AI.

---

# 2. Product Vision

## Vision

> **Make reading an active skill-building activity instead of a passive activity.**

The product should combine three activities that are normally separate:

```text
Reading
   +
Typing
   +
Revision
```

into one continuous workflow:

```text
Import
   ↓
Organize
   ↓
Read
   ↓
Type
   ↓
Measure
   ↓
Review
   ↓
Improve
```

The long-term vision is to become a **document-to-practice platform** rather than merely a typing-test website.

---

# 3. Product Thesis

Traditional typing applications ask:

> How quickly can you type this text?

TypeRead asks:

> What useful thing can you read while improving your typing?

The product therefore creates a dual-value activity.

### User gets:

**Value 1:** They consume useful information.

**Value 2:** They improve typing ability.

This creates a stronger reason to spend time inside the product than conventional typing-test applications.

---

# 4. Problem Statement

Users who want to improve typing usually practice with:

- Random word lists
- Artificial sentences
- Typing tests
- Repeated passages
- Generic exercises

The problem is that typing practice often feels disconnected from meaningful work.

At the same time, users consume books and study materials passively.

There is an opportunity to combine these activities.

### Current problems

#### Problem A: Typing practice becomes repetitive

After a few sessions, users often experience typing practice as a test rather than a useful activity.

#### Problem B: Reading is passive

Users may read for hours but retain little and have no structured interaction with the material.

#### Problem C: Long documents are difficult to navigate

PDFs often contain:

- Page numbers
- Headers
- Footers
- Broken lines
- Broken words
- Formatting artifacts
- Poor text extraction
- Inconsistent spacing

#### Problem D: Personal documents are poorly supported

Most typing applications focus on predefined text rather than turning a user's own material into a structured practice environment.

#### Problem E: Users lose their place

Long books require:

- Chapter navigation
- Section navigation
- Search
- Resume position
- Progress tracking

---

# 5. Product Goals

## Primary Goals

### G1. Turn arbitrary user documents into typing material

A user should be able to import supported documents and start practicing with minimal manual cleanup.

### G2. Make reading and typing one activity

The interface should allow the user to see the source material while actively typing it.

### G3. Provide excellent document processing without AI

The system should automatically handle as much as possible using deterministic processing.

### G4. Provide structured navigation

Users should never be trapped inside a giant endless document.

### G5. Provide meaningful typing analytics

The product should measure more than simple WPM.

### G6. Preserve user ownership and privacy

Imported documents should remain local during Phase 1.

### G7. Create a foundation for future AI features

The internal architecture should support future AI modules without requiring the entire application to be rewritten.

---

# 6. Non-Goals for Phase 1

The following are explicitly outside the Phase 1 scope.

## Not included

- LLM integration
- Generative AI
- Cloud AI APIs
- AI summarization
- AI chat
- AI semantic search
- AI-generated quizzes
- AI-generated explanations
- Cloud synchronization
- Web-based SaaS
- Mobile application
- Social network
- Multiplayer typing
- Public upload repository for copyrighted books
- Automatic distribution of commercially copyrighted books
- Institution dashboard
- Payments/subscriptions inside the initial release
- Ad network integration inside the offline application

The objective is to first prove:

> **People want to read and practice typing using their own material.**

---

# 7. Target Users

## Persona 1: Book Reader

Reads books regularly and wants a more active reading experience.

Typical material:

- Non-fiction
- Public-domain books
- Self-improvement
- Business books
- Philosophy
- Productivity

Primary need:

> "I want to read, but I also want to improve my typing."

---

## Persona 2: Student

Uses:

- Textbooks
- Class notes
- Study PDFs
- Exam preparation documents
- Lecture material

Primary need:

> "I need to revise material and want an active way to interact with it."

---

## Persona 3: Programmer

Uses:

- Documentation
- Tutorials
- Technical PDFs
- Markdown notes
- Programming books

Primary need:

> "I spend time reading technical material and could use that time as typing practice."

---

## Persona 4: Professional

Uses:

- Reports
- Documentation
- Training material
- Research documents
- Company notes

Primary need:

> "I want to improve typing while processing material that is already useful to me."

---

# 8. Core User Value Proposition

### One-line value proposition

> **Read what matters. Type what you read. Improve while learning.**

### Product promise

The application should make it possible to take a document from:

```text
messy file
```

to:

```text
clean, navigable, interactive typing experience
```

without requiring the user to manually prepare the text.

---

# 9. Product Principles

## Principle 1: Document first

The user's document is the center of the experience.

The product should not feel like a typing test with a book pasted into it.

---

## Principle 2: Offline by default

The core Phase 1 workflow should work without:

- Internet
- API key
- AI model
- Cloud server
- User account on an external service

---

## Principle 3: Preserve original content

Never destroy the original import.

Maintain:

```text
Original Source
      +
Processed Representation
      +
Typing Representation
```

---

## Principle 4: Automation with user control

Automatic processing should be powerful but reversible.

The user must be able to correct:

- Chapters
- Section boundaries
- Excluded sections
- Document title
- Author
- Text processing mode

---

## Principle 5: Minimal interface

The application should feel elegant, focused, and calm.

Avoid:

- unnecessary dashboards
- noisy animations
- excessive badges
- intrusive notifications
- ads in the typing experience

---

## Principle 6: Keyboard-first interaction

The user is typing.

The product should therefore minimize mouse dependency.

---

# 10. High-Level Product Architecture

```text
                           TYPEread
                              │
              ┌───────────────┴────────────────┐
              │                                │
       Document Engine                    Typing Engine
              │                                │
     ┌────────┼─────────┐               ┌──────┼────────┐
     │        │         │               │      │        │
 Extraction  Cleanup  Structure        Input  Metrics  Practice
     │        │         │               │      │        │
     └────────┴─────────┘               └──────┴────────┘
              │                                │
              └──────────────┬─────────────────┘
                             │
                       Local Storage
                             │
                     ┌───────┴───────┐
                     │               │
                 SQLite          File System
                     │               │
                 Metadata         Source Files
                 Progress         Processed Data
                 Analytics        Backups
```

---

# 11. Recommended Phase 1 Technology Stack

## Desktop UI

**PySide6 / Qt**

Responsibilities:

- Application shell
- Navigation
- Panels
- Dialogs
- Menus
- Settings
- Custom typing interface
- Progress visualization

---

## Database

**SQLite**

Responsibilities:

- User profiles
- Documents
- Chapters
- Sections
- Paragraphs
- Progress
- Sessions
- Analytics
- Bookmarks
- Notes
- Settings

SQLite FTS5 can be used for full-text document search.

---

## PDF Processing

### Primary

**PyMuPDF**

Use for:

- Text extraction
- Page processing
- Blocks
- Lines
- Spans
- Font information
- Coordinates
- PDF outline/TOC
- Metadata
- Page-level processing

### Secondary

**pypdf**

Use for:

- PDF metadata
- Outlines
- PDF-related fallback processing

---

## EPUB

**EbookLib**

Responsibilities:

- EPUB extraction
- Chapters
- TOC
- Spine
- HTML content

---

## DOCX

**python-docx**

Responsibilities:

- Paragraph extraction
- Heading extraction
- Basic document structure

---

## HTML

**BeautifulSoup**

Responsibilities:

- HTML parsing
- Tag cleaning
- Content extraction

---

## Text Encoding Cleanup

**ftfy**

Responsibilities:

- Unicode cleanup
- Mojibake correction
- Encoding artifacts

---

## Regex

Python `re` and optionally the third-party `regex` package.

Responsibilities:

- Pattern detection
- Page number removal
- Header/footer identification
- Heading pattern detection
- Whitespace cleanup
- Character filtering

---

## OCR

Optional local module:

- Tesseract
- OCRmyPDF

This is explicitly a local processing feature and does not involve LLMs or cloud AI.

---

# 12. Document Import Pipeline

Every imported document should follow a standardized processing pipeline.

```text
User selects file
       ↓
File validation
       ↓
Format detection
       ↓
Extraction
       ↓
Unicode normalization
       ↓
Whitespace normalization
       ↓
Header/footer analysis
       ↓
Page-number cleanup
       ↓
Hyphenation repair
       ↓
Line reconstruction
       ↓
Paragraph reconstruction
       ↓
Heading detection
       ↓
TOC detection
       ↓
Structure generation
       ↓
User preview
       ↓
Manual corrections
       ↓
Final document model
       ↓
Library
```

---

# 13. Supported Formats

## Phase 1 mandatory

- PDF
- EPUB
- TXT
- DOCX
- Markdown
- HTML

## Phase 1 optional

- RTF
- ODT

## Later

- PPTX
- XLSX
- Other structured formats

The application should not claim "all file types supported" unless there is a real parser for the format.

---

# 14. PDF Processing Requirements

## FR-PDF-001: Extract text

The system must attempt to extract textual content from every supported text-based PDF.

### Acceptance criteria

Given a normal text PDF:

- Text is extracted page-by-page.
- Page boundaries are preserved internally.
- Reading order is reconstructed.
- Original page references remain available.

---

## FR-PDF-002: Detect PDF outline

When a PDF contains bookmarks or a document outline:

- Extract the hierarchy.
- Preserve nesting.
- Map entries to page numbers.
- Use the existing structure as the preferred navigation source.

---

## FR-PDF-003: Detect missing structure

When no usable outline exists:

The system should estimate structure using deterministic signals.

Signals may include:

- Font size
- Font weight
- Font family
- Line length
- Text position
- Center alignment
- Whitespace before/after
- Numbering
- Capitalization
- Repeated formatting
- Page position

---

# 15. Heading Detection Engine

The system should assign a heading score to candidate lines.

Example conceptual model:

```text
Heading Score =
    Font Size Score
  + Bold Score
  + Numbering Score
  + Position Score
  + Whitespace Score
  + Short Line Score
  - Paragraph Length Penalty
```

No generative model is required.

Possible output:

```text
H1
H2
H3
Paragraph
List
Caption
Footnote
Header
Footer
Page Number
Unknown
```

---

# 16. Confidence-Based Structure Detection

The system should not pretend certainty.

Each automatically detected structural element can contain:

```text
type
confidence
source_page
source_position
```

For example:

```text
Chapter 7
type = H1
confidence = 0.94
```

Low-confidence sections should be surfaced for manual review.

---

# 17. Header Removal

The system should detect repeated text appearing in similar positions across pages.

Example:

```text
PAGE 15
Atomic Habits
Text...

PAGE 16
Atomic Habits
Text...
```

If the repeated string and position satisfy detection criteria, classify it as a probable header.

User should be able to:

- Accept
- Reject
- Exclude manually

---

# 18. Footer Removal

Same logic should be applied to footers.

Examples:

- Book title
- Chapter title
- Author
- Copyright notice
- Repeated footer text

---

# 19. Page Number Removal

The system should recognize:

```text
1
2
3
...
125
```

and formatted variants:

```text
- 12 -
Page 12
12
```

Page number removal should be conservative.

A number within a paragraph should never be removed merely because it is numeric.

---

# 20. Hyphenation Repair

Example source:

```text
psychol-
ogy
```

Processed:

```text
psychology
```

The engine should use:

- line position
- next-line capitalization
- surrounding tokens
- punctuation
- word length
- dictionary-style checks where available

The system should preserve legitimate hyphenation where confidence is low.

---

# 21. Line Reconstruction

PDF extraction often returns visual lines rather than semantic sentences.

The document engine must reconstruct:

```text
line 1
line 2
line 3
```

into appropriate paragraphs.

Signals:

- vertical distance
- indentation
- font consistency
- line width
- page position
- paragraph spacing

---

# 22. Paragraph Reconstruction

The resulting document should use semantic paragraphs rather than arbitrary PDF lines.

Example:

### Raw

```text
The first principle of behavior
change is to make it obvious.
The system works because...
```

### Processed

```text
The first principle of behavior change is to make it obvious.
The system works because...
```

---

# 23. Text Transformation Engine

The application must maintain multiple representations.

```text
source_text
normalized_text
display_text
typing_text
```

Possible processing options:

### Mode 1: Original

Preserve:

- Case
- Punctuation
- Numbers
- Symbols

### Mode 2: Lowercase

Convert:

```text
The Habit Loop
```

to:

```text
the habit loop
```

### Mode 3: No Punctuation

Remove punctuation while preserving word boundaries.

### Mode 4: Letters Only

Keep alphabetic characters and spaces.

### Mode 5: Custom

Allow users to choose:

- punctuation
- numbers
- symbols
- capitalization

---

# 24. Text Cleanup Controls

Users should be able to configure:

```text
☑ Remove page numbers
☑ Remove repeated headers
☑ Remove repeated footers
☑ Repair broken words
☑ Merge wrapped lines
☑ Normalize whitespace
☑ Normalize Unicode
☐ Remove references
☐ Remove acknowledgments
☐ Remove preface
```

---

# 25. Document Structure

Each document should be represented as a tree.

Example:

```text
Atomic Habits
│
├── Introduction
│
├── Chapter 1
│   ├── Section 1
│   ├── Section 2
│   └── Section 3
│
├── Chapter 2
│   ├── Section 1
│   └── Section 2
│
└── Conclusion
```

Every node should have:

```text
id
parent_id
document_id
title
order
level
page_start
page_end
text_start
text_end
```

---

# 26. Structure Editor

After import, the user must see a preview.

Example:

```text
Document Structure

✓ Introduction
✓ Chapter 1
    ✓ 1.1
    ✓ 1.2
✓ Chapter 2
    ✓ 2.1
```

Actions:

- Rename
- Move
- Merge
- Split
- Delete from practice
- Change hierarchy
- Add section
- Reorder

---

# 27. Exclusion System

The document source must remain intact.

Exclusion means:

> "Do not include this section in typing practice."

Example:

```text
Practice Content

☐ Preface
☑ Chapter 1
☑ Chapter 2
☑ Chapter 3
☐ Bibliography
☐ Index
```

The excluded content remains searchable and recoverable unless the user explicitly deletes the local document.

---

# 28. Library

The main library should show:

```text
My Library

Continue Reading
Recently Added
Favorites
Completed
All Documents
```

Each book card should display:

- Title
- Author
- Progress
- Current chapter
- Last session
- WPM
- Accuracy

---

# 29. Import UX

The import process should be:

```text
+ Add Document
        ↓
File picker
        ↓
Processing
        ↓
Preview
        ↓
Adjust settings
        ↓
Structure review
        ↓
Save
```

Processing screen:

```text
Processing document...

✓ Reading file
✓ Extracting text
✓ Cleaning formatting
✓ Detecting chapters
✓ Building index

14 chapters
327 sections
82,341 words
```

---

# 30. Reader + Typing Interface

Primary desktop layout:

```text
┌───────────────────────────────────────────────────────────────┐
│ Logo            Book Title              Search      Settings  │
├───────────────┬───────────────────────────────────────────────┤
│               │                                               │
│ CHAPTERS      │               CHAPTER 4                       │
│               │                                               │
│ Introduction  │               The Habit Loop                  │
│ Chapter 1     │                                               │
│ Chapter 2     │ The most effective way to change behavior     │
│ Chapter 3     │ is to focus not on goals but on systems...    │
│ Chapter 4  ←  │                                               │
│ Chapter 5     │                                               │
│               │                                               │
│               │───────────────────────────────────────────────│
│               │                                               │
│               │ TYPE HERE                                     │
│               │                                               │
│               │ The most effective way to change behavior...  │
│               │                                               │
├───────────────┴───────────────────────────────────────────────┤
│ 58 WPM       97.3%       0 Errors       42:18       73%       │
└───────────────────────────────────────────────────────────────┘
```

---

# 31. Alternative Typing Layout

A second layout may be offered:

```text
┌──────────────────────────────┬───────────────────────────────┐
│ Source                       │ Typing                         │
│                              │                                │
│ The most effective way...    │ The most effective way...     │
│                              │                                │
│ paragraph continues...       │ paragraph continues...        │
└──────────────────────────────┴───────────────────────────────┘
```

User preference:

- Source above typing
- Source beside typing
- Typing-only mode

---

# 32. Typing Engine

The engine should process text character-by-character.

For each keystroke:

```text
expected_character
actual_character
timestamp
position
correct/incorrect
```

The engine should support:

- Correct input
- Incorrect input
- Backspace
- Cursor position
- Pausing
- Resuming
- Completion
- Restart
- Skip section

---

# 33. Typing Modes

## Standard

Normal typing.

## No Punctuation

Punctuation removed.

## Lowercase

Everything converted to lowercase.

## Numbers

Numbers included.

## Punctuation

Punctuation intentionally included.

## Quotes

Quotation-heavy material preserved.

## Custom

User chooses characters.

---

# 34. Typing Metrics

The system should calculate:

### WPM

Words per minute.

### Raw WPM

Speed before accuracy correction.

### Accuracy

```text
correct / total × 100
```

### Error Count

Total incorrect keystrokes.

### Error Rate

Errors relative to total keystrokes.

### Backspace Count

Number of backspaces used.

### Consistency

Measure variation in typing speed across the session.

### Session Duration

Total active typing time.

### Characters Typed

Total characters entered.

---

# 35. Advanced Error Analytics

Store character-level error information.

Example:

```text
Common mistakes

e → r     18
t → y     11
i → o      9
```

Also calculate bigram/trigram error frequency where useful.

Example:

```text
Weak combinations

th
he
er
in
```

---

# 36. Weak-Key Practice

The system should automatically generate practice material from existing errors.

Example:

User repeatedly mistypes:

```text
th
er
ou
```

System creates:

```text
the
there
their
other
thought
through
```

This must be algorithmically generated without AI.

Possible generation sources:

1. Imported document vocabulary
2. Local dictionary
3. Built-in word corpus
4. Frequency lists

---

# 37. Book Progress

Track progress at multiple levels.

```text
Document
    ↓
Chapter
    ↓
Section
    ↓
Paragraph
    ↓
Character
```

The system must store exact typing position.

---

# 38. Resume Functionality

When a user leaves the application:

```text
Document: Atomic Habits
Chapter: 4
Section: 4.2
Paragraph: 17
Character offset: 241
```

On next launch:

> Continue where you stopped.

The user should never have to manually search through a long document to find their place again.

---

# 39. Search

Search must operate over:

- Title
- Author
- Chapter titles
- Sections
- Paragraphs
- Notes

Document search should use SQLite FTS5 or equivalent local search.

Search result:

```text
"habit stacking"

Chapter 5
Section 2
Page 87
```

Selecting the result must jump directly to the corresponding passage.

---

# 40. Bookmarks

Keyboard shortcut example:

```text
Ctrl + B
```

Bookmark stores:

```text
document_id
section_id
paragraph_id
character_offset
label
created_at
```

---

# 41. Notes

Users should optionally attach a local note to:

- Chapter
- Section
- Paragraph
- Bookmark

Example:

```text
Chapter 3
Note:
Important concept for my exam.
```

---

# 42. Focus Mode

Focus mode should hide unnecessary UI.

```text
                 Chapter 4

       The most effective way...

              [typing area]

             58 WPM
             97.3%
```

No sidebar.

No secondary controls.

No visual noise.

Keyboard shortcut:

```text
Ctrl + Shift + F
```

---

# 43. Zen Mode

Optional mode:

- Fullscreen
- Minimal typography
- Hidden metrics
- Hidden chapter list
- Typing only

Useful for users who want immersion.

---

# 44. Visual Customization

Users should be able to configure:

- Font family
- Font size
- Line height
- Letter spacing
- Content width
- Cursor style
- Cursor animation
- Theme
- Background brightness
- Typing text opacity

---

# 45. Theme System

Minimum:

- Light
- Dark
- High contrast

Potential later themes:

- Paper
- Sepia
- Midnight
- Minimal monochrome

The visual style should remain elegant and minimal rather than resembling a gaming dashboard.

---

# 46. Keyboard Shortcuts

Suggested shortcuts:

```text
Ctrl + O          Open document
Ctrl + B          Bookmark
Ctrl + F          Search
Ctrl + K          Focus search
Ctrl + Shift + F  Focus mode
Ctrl + Shift + Z  Zen mode
Ctrl + S          Save
Esc               Pause
F1                Help
```

Typing itself should never be interrupted by unnecessary shortcuts.

---

# 47. Session System

Every typing session should be recorded separately.

Session object:

```text
session_id
document_id
section_id
start_time
end_time
active_seconds
characters
correct_characters
incorrect_characters
backspaces
wpm
accuracy
```

---

# 48. Analytics Dashboard

## Overview

```text
Typing Overview

Average WPM       57
Best WPM          74
Average Accuracy  96.8%
Total Time        19h 42m
Words Typed       142,920
```

---

# 49. Trend Charts

Examples:

### WPM trend

```text
Day 1     42
Day 7     49
Day 14    53
Day 30    58
```

### Accuracy trend

```text
93%
94%
95%
96%
97%
```

### Daily practice

```text
Mon     24 min
Tue     31 min
Wed     18 min
Thu     46 min
Fri     34 min
```

---

# 50. Book-Level Analytics

For each book:

```text
Atomic Habits

Progress        63%
Time typed      6h 14m
Words typed     42,890
Average WPM     56
Accuracy        97.1%
Sessions        24
```

---

# 51. Chapter-Level Analytics

```text
Chapter 4

Progress        100%
Average WPM     61
Accuracy        98.2%
Best WPM        72
Time            34m
```

---

# 52. Achievements

Achievements should reinforce useful behavior.

Examples:

```text
First Session
First Chapter
10,000 Characters
100,000 Characters
First Complete Book
7-Day Practice Streak
50 WPM
60 WPM
80 WPM
95% Accuracy
100% Chapter
```

Avoid excessive gamification.

---

# 53. Streak System

Track consecutive days with qualifying practice.

Example:

```text
Current streak: 7 days
Longest streak: 18 days
```

A qualifying session could require:

- minimum active typing time
or
- minimum typed characters

This prevents a user from pressing one key and technically "maintaining" a streak.

---

# 54. Revision System Without AI

AI is not necessary to create a revision loop.

The application can use deterministic spaced repetition.

Example:

```text
Session 1
    ↓
1 day
    ↓
Review
    ↓
3 days
    ↓
Review
    ↓
7 days
    ↓
Review
```

A chapter that has been completed can enter a revision queue.

---

# 55. Adaptive Difficulty Without AI

Use performance statistics.

Example:

```text
Accuracy >= 98%
        ↓
Increase difficulty

Accuracy 94-97%
        ↓
Normal

Accuracy < 94%
        ↓
Repeat section
```

Difficulty can change:

- punctuation
- capitalization
- numbers
- passage length
- session duration
- unfamiliar words

No LLM required.

---

# 56. Study Mode

A future Phase 1.5 feature can use deterministic study mechanics.

After finishing a section:

```text
Section Complete

Words Typed: 1,142
Average WPM: 55
Accuracy: 97.1%

Review Options:

[Retype]
[Review Passage]
[Bookmark]
[Write Your Own Note]
```

The product should not pretend that it can understand the material semantically without AI.

---

# 57. Public Library

The application may eventually include a built-in public-domain library.

The library should contain only material whose distribution rights are appropriately verified for the intended market.

Possible categories:

- Classic literature
- Philosophy
- History
- Public-domain essays
- Public-domain educational material

The system should maintain metadata:

```text
title
author
publication_year
source
license/status
jurisdiction_notes
```

---

# 58. User-Imported Copyrighted Material

Phase 1 should support importing a user's own files for their own use.

The application should **not** create a public repository of arbitrary copyrighted books.

The architecture should distinguish:

```text
Public Library Content
```

from:

```text
Private User Content
```

Private user content must not automatically become publicly accessible.

The exact terms, distribution behavior, and legal compliance should be reviewed before public launch.

---

# 59. Privacy

Phase 1 should be privacy-first.

### Default behavior

- Documents remain on device.
- Database remains on device.
- Progress remains on device.
- Notes remain on device.
- No document uploads to a server.
- No AI API calls.
- No cloud processing.

---

# 60. Telemetry

Default:

**No analytics telemetry.**

Optional anonymous telemetry may be introduced later only after clear user consent.

Possible future telemetry:

- crash logs
- feature usage
- document import success rate
- performance metrics

No document content should be collected by default.

---

# 61. Local User Profile

The phrase "account" in Phase 1 should mean a **local profile**, not an online account.

Example:

```text
Profile: Abhishek
```

Stored locally.

No email requirement.

No password requirement initially.

Future cloud sync can introduce:

```text
Local Profile
       ↓
Optional Cloud Account
```

---

# 62. Data Model

## users

```text
id
display_name
created_at
last_active_at
settings_id
```

## documents

```text
id
title
author
file_name
file_path
file_hash
source_format
word_count
character_count
created_at
updated_at
```

## document_versions

```text
id
document_id
version
processing_profile
created_at
```

## chapters

```text
id
document_id
parent_id
title
level
order_index
page_start
page_end
text_start
text_end
confidence
included_in_practice
```

## paragraphs

```text
id
document_id
chapter_id
section_id
order_index
text
source_page
source_position
```

## bookmarks

```text
id
document_id
chapter_id
paragraph_id
character_offset
title
created_at
```

## notes

```text
id
document_id
chapter_id
paragraph_id
content
created_at
updated_at
```

## typing_sessions

```text
id
document_id
chapter_id
section_id
start_time
end_time
active_seconds
characters
correct_characters
incorrect_characters
backspaces
wpm
raw_wpm
accuracy
```

## typing_errors

```text
id
session_id
expected_character
actual_character
position
timestamp
```

## user_settings

```text
theme
font
font_size
line_height
typing_mode
difficulty
cursor_style
sound_enabled
autosave_enabled
```

---

# 63. File System Layout

Suggested layout:

```text
TypeRead/
│
├── database/
│   └── library.db
│
├── documents/
│   ├── <document-id>/
│   │   ├── source/
│   │   │   └── original.pdf
│   │   │
│   │   ├── processed/
│   │   │   ├── document.json
│   │   │   └── structure.json
│   │   │
│   │   └── assets/
│   │       └── cover.jpg
│
├── backups/
│
└── logs/
```

---

# 64. Backup and Export

Users must be able to export their library.

### Export format

Recommended:

```text
.typeread-backup
```

internally a ZIP-like archive containing:

```text
manifest.json
database.sqlite
documents/
settings.json
```

Users should be able to restore the library on another machine.

---

# 65. Import Hashing

Generate a file hash for imported documents.

Purpose:

- Detect duplicate imports
- Detect source changes
- Maintain document identity

Example:

```text
SHA-256
```

---

# 66. Duplicate Detection

If the user imports the same document twice:

```text
This document already exists.

[Open Existing]
[Import as Separate Copy]
[Cancel]
```

---

# 67. Document Processing Profiles

Users can create reusable settings.

Example:

### Book Profile

```text
Remove headers: Yes
Remove footers: Yes
Remove page numbers: Yes
Preserve punctuation: Yes
Lowercase: No
```

### Typing Practice Profile

```text
Remove punctuation: Yes
Lowercase: Yes
Numbers: No
```

---

# 68. Reader Position Model

Exact position must be stored.

```text
document_id
chapter_id
section_id
paragraph_id
character_offset
```

This enables perfect resume behavior.

---

# 69. Autosave

Progress must save automatically.

Target behavior:

- Save after meaningful progression
- Save on pause
- Save on section completion
- Save on application close

There should be no "Oops, the app crashed and three chapters vanished" experience.

---

# 70. Crash Recovery

On application restart:

```text
We found an unfinished session.

Atomic Habits
Chapter 4
Progress: 72%

[Continue]
[Discard Session]
```

---

# 71. Error Handling

User-facing messages should be understandable.

Bad:

```text
PyMuPDF extraction exception.
```

Better:

```text
This PDF could not be read as normal text.

It may be a scanned document.

Try OCR processing.
```

---

# 72. OCR Flow

If a PDF contains little or no extractable text:

```text
Text extraction appears incomplete.

Possible scanned document detected.

[Run Local OCR]
[Continue Without OCR]
[Cancel]
```

OCR must run locally.

---

# 73. Processing Preview

Before saving a document, show:

```text
Original pages:      327
Extracted words:     82,341
Detected chapters:   14
Detected sections:   87
Removed headers:     1
Removed footers:     1
Removed page nums:   327
Repaired words:      214
```

User can inspect examples.

---

# 74. Before/After Cleanup Preview

Example:

```text
Original

The habit-form-
ing process...

Cleaned

The habit-forming process...
```

This gives the user confidence in the processing engine.

---

# 75. Manual Text Editor

Users should have access to an optional document cleanup editor.

They can:

- Edit extracted text
- Correct paragraphs
- Rename headings
- Remove unwanted content
- Add section breaks

The original file remains untouched.

---

# 76. Search and Navigation UX

Left sidebar:

```text
CONTENTS
────────────
Introduction
Chapter 1
  1.1
  1.2
Chapter 2
Chapter 3
Conclusion
```

Search results should deep-link into exact locations.

The navigation system must support:

- keyboard
- scroll
- chapter selection
- section selection
- search

---

# 77. Reading Position Indicator

Show:

```text
Chapter 4
Section 2
Paragraph 13 / 28
```

Optional:

```text
Page 83 of 327
```

---

# 78. Completion States

A section is complete when:

```text
100% of required characters
```

have been typed according to the selected practice mode.

A chapter becomes complete when all included sections are complete.

A document becomes complete when all included chapters are complete.

---

# 79. Partial Completion

Users should be able to stop anywhere.

Progress should be represented accurately.

Example:

```text
Chapter 4
███████████░░░ 82%
```

Never round 82% to 100%.

Human beings notice lies, particularly when they're trying to avoid doing work.

---

# 80. Typing Accuracy Behavior

The application must define clearly how errors are treated.

Recommended default:

- incorrect keystrokes are recorded
- cursor remains at current expected position
- user may correct using backspace
- accuracy is calculated using all entered keystrokes
- corrected and uncorrected errors are distinguishable

A settings option can later allow alternative behavior.

---

# 81. Input Method Support

Phase 1:

- standard keyboard
- English QWERTY
- Unicode text

Future:

- Hindi
- regional Indian languages
- alternate keyboard layouts

---

# 82. Accessibility

The application should support:

- keyboard navigation
- screen-reader-friendly controls
- scalable fonts
- high contrast
- reduced animation
- clear focus indicators
- configurable text size

---

# 83. Internationalization

Architecture should not hard-code English.

Future-ready fields:

```text
language
locale
text_direction
keyboard_layout
```

Initially optimize for English.

---

# 84. Performance Requirements

These are targets for engineering validation, not claims about current performance.

## Startup

Target:

```text
< 3 seconds
```

for a normal local library.

## Library opening

Target:

```text
< 1 second
```

for normal libraries.

## Typing latency

Keypress-to-render latency should feel effectively immediate.

Target:

```text
< 50 ms
```

under normal conditions.

## Search

Target:

```text
< 300 ms
```

for typical local libraries.

## Document processing

Target:

```text
< 15 seconds
```

for a typical text-based book-sized PDF on a modern desktop.

Large/scanned documents may take substantially longer.

---

# 85. Memory Requirements

The application should avoid loading extremely large documents into memory unnecessarily.

Use:

- incremental parsing
- page-level processing
- chunked processing
- database-backed storage

Target should be acceptable on mainstream machines with approximately 8 GB RAM.

---

# 86. Security

Phase 1 should minimize the attack surface.

Requirements:

- No document upload server
- No API keys
- No remote code execution
- Validate imported files
- Restrict processing to supported file types
- Safe file path handling
- Sanitize HTML
- Avoid executing embedded document content
- Secure backups
- Do not expose local files through an HTTP server unless explicitly required

---

# 87. Application Navigation

Top-level navigation:

```text
Home
Library
Statistics
Bookmarks
Settings
```

Optional:

```text
Practice
```

could serve as a global weak-key training area.

---

# 88. Home Screen

The home screen should focus on continuation.

Example:

```text
Good evening

Continue
───────────────

Atomic Habits
Chapter 4
73% complete

58 WPM
97.3%

[Continue]
```

Then:

```text
Recent Documents
```

and:

```text
Typing Progress
```

---

# 89. Statistics Screen

Sections:

```text
Overview
WPM
Accuracy
Errors
Practice Time
Books
Weak Keys
Streaks
```

Charts should remain simple and readable.

---

# 90. Settings

## General

- Startup behavior
- Autosave
- Confirm delete
- Backup location

## Typing

- Typing mode
- Error behavior
- Caret
- Sound
- Difficulty

## Appearance

- Theme
- Font
- Font size
- Width
- Line height

## Documents

- Cleanup defaults
- OCR defaults
- Header/footer detection

## Privacy

- Telemetry
- Logs
- Local data location

---

# 91. Monetization Strategy

## Phase 1

Product launches **free**.

There should be no requirement to monetize immediately.

However, because the application is offline:

> Traditional advertisements are not a natural Phase 1 monetization mechanism.

Banner ads require some mechanism for ad delivery, which conflicts with the offline-first architecture and would damage the focused typing experience.

Therefore:

### Phase 1 objective

**User validation, retention, and product quality.**

---

# 92. Future Monetization

After user demand is demonstrated:

## Free

- Basic typing
- Local imports
- Basic statistics
- Basic library
- Basic navigation

## Pro

Potential features:

- Cloud sync
- Cross-device progress
- Advanced analytics
- Advanced document processing
- More customization
- Backup automation
- Advanced revision

## AI Add-on / AI Pro

Potential features:

- Summaries
- AI explanations
- Question generation
- Semantic search
- Vocabulary extraction
- AI-powered revision
- Document Q&A
- Personalized learning assistance

AI should be isolated behind a service interface.

---

# 93. AI Future Architecture

Phase 1:

```text
Core
 ├── documents
 ├── parser
 ├── structure
 ├── typing
 ├── search
 └── analytics
```

Future:

```text
Core
      │
      └── AI Service Interface
                │
        ┌───────┴────────┐
        │                │
     Cloud LLM       Local Model
```

This allows future experimentation without rewriting the core product.

---

# 94. AI Waitlist

Once sufficient user activity exists, the product may expose:

```text
AI Features

Coming later:

✓ Chapter summaries
✓ Ask your document
✓ AI quiz
✓ Smart revision
✓ Vocabulary assistant

[Join AI Waitlist]
```

The waitlist should measure actual user demand before infrastructure spending.

---

# 95. Analytics for Product Validation

The application should internally support measuring product success, subject to privacy design.

Key events:

```text
document_imported
document_processing_completed
typing_session_started
typing_session_completed
chapter_completed
book_completed
bookmark_created
search_used
cleanup_editor_used
structure_corrected
weak_practice_started
```

For the offline version, these can initially remain local.

---

# 96. Product Success Metrics

## North Star Metric

**Completed focused read-and-type sessions per active user per week.**

This measures whether the core behavior is happening.

---

## Secondary Metrics

### Activation

Percentage of new users who:

1. Import a document
2. Complete processing
3. Start typing

### Engagement

- Sessions per week
- Minutes typed per week
- Chapters completed
- Words typed

### Retention

- Day 1
- Day 7
- Day 30

### Typing improvement

- WPM change
- Accuracy change
- Error-rate change

### Learning behavior

- Chapters revisited
- Revision sessions
- Bookmark usage
- Notes created

---

# 97. Product Health Metrics

Monitor:

```text
Import success rate
Processing failure rate
OCR failure rate
Document parsing correction rate
Crash rate
Typing latency
Search latency
Database corruption rate
Backup restore success rate
```

---

# 98. Primary Success Hypothesis

### Hypothesis

Users will practice typing for longer and return more frequently when the typing material is personally meaningful.

### Validation signal

Users repeatedly choose imported books/documents instead of generic typing tests.

---

# 99. Secondary Hypothesis

Users will tolerate automatic document cleanup when the result is good enough and the process remains editable.

### Validation signal

Low manual correction rate.

---

# 100. Third Hypothesis

Users may eventually pay for enhanced capabilities, particularly:

- cloud synchronization
- advanced analytics
- document intelligence
- AI features

This should be validated rather than assumed.

---

# 101. User Journey

## First launch

```text
Welcome
  ↓
Create local profile
  ↓
Add your first document
  ↓
Select file
  ↓
Process
  ↓
Preview
  ↓
Confirm structure
  ↓
Start typing
```

---

# 102. Returning User Journey

```text
Open app
  ↓
Continue Reading
  ↓
Exact previous location
  ↓
Start typing
  ↓
Session complete
  ↓
Progress updated
```

---

# 103. Importing a Book Journey

```text
Drag PDF
   ↓
Processing
   ↓
Detected:
  12 chapters
  73 sections
   ↓
Preview
   ↓
Remove:
  Preface
  Copyright page
  Bibliography
   ↓
Save
   ↓
Chapter 1
   ↓
Start typing
```

---

# 104. Error Recovery Journey

If parsing is imperfect:

```text
Structure Review

Chapter 2 detected incorrectly.

[Rename]
[Move]
[Merge]
[Delete]
[Ignore]
```

User fixes the structure instead of abandoning the application.

---

# 105. MVP Definition

The MVP is considered complete when all of the following work reliably:

### Document

- PDF import
- TXT import
- EPUB import
- DOCX import

### Processing

- Text extraction
- Cleanup
- Header/footer handling
- Page-number handling
- Paragraph reconstruction
- TOC extraction
- Basic heuristic structure detection

### Navigation

- Chapter list
- Section list
- Search
- Bookmark
- Resume

### Typing

- Typing engine
- WPM
- Accuracy
- Error count
- Progress
- Sessions

### Storage

- SQLite
- Local profile
- Local documents
- Progress persistence
- Backup/export

### UX

- Light mode
- Dark mode
- Focus mode
- Keyboard shortcuts
- Import preview

### Architecture

- No LLM
- No cloud processing
- No required Internet
- Modular document engine
- Modular typing engine

---

# 106. Phase 1 Feature Prioritization

## P0: Must Have

```text
PDF
TXT
EPUB
DOCX

Text extraction
Text cleanup
TOC
Structure detection
Manual correction

Typing engine
WPM
Accuracy
Errors
Progress

Library
Chapter navigation
Search
Resume
Bookmarks

SQLite
Local files
Autosave
Backup

Light/Dark
Focus mode
Keyboard shortcuts
```

---

## P1: Should Have

```text
OCR
Advanced heading detection
Weak-key practice
Detailed analytics
Streaks
Achievements
Notes
Document editor
Custom typing modes
Custom themes
```

---

## P2: Later

```text
Additional document formats
Advanced revision
Public-domain library
Cloud sync
Cross-platform sync
Teams
Institution features
AI
Mobile
Web
```

---

# 107. Technical Modules

Recommended project architecture:

```text
src/
│
├── app/
│   ├── main.py
│   ├── config.py
│   └── lifecycle.py
│
├── ui/
│   ├── windows/
│   ├── widgets/
│   ├── dialogs/
│   ├── themes/
│   └── shortcuts/
│
├── core/
│   ├── typing/
│   ├── documents/
│   ├── structure/
│   ├── cleaning/
│   ├── search/
│   ├── progress/
│   ├── analytics/
│   └── revision/
│
├── importers/
│   ├── pdf/
│   ├── epub/
│   ├── docx/
│   ├── txt/
│   ├── markdown/
│   └── html/
│
├── processing/
│   ├── extraction/
│   ├── normalization/
│   ├── header_footer/
│   ├── paragraph/
│   ├── headings/
│   └── ocr/
│
├── storage/
│   ├── database/
│   ├── repositories/
│   └── filesystem/
│
├── models/
│
├── services/
│
└── tests/
```

---

# 108. Separation of Concerns

The following components must remain independent:

### Document Engine

Knows how to process documents.

### Typing Engine

Knows how to score typing.

### Storage Layer

Knows how to persist information.

### UI Layer

Knows how to display the application.

### Analytics Layer

Knows how to calculate user statistics.

This allows future interfaces without rewriting the core.

---

# 109. Testing Strategy

## Unit Tests

Test:

- text cleanup
- punctuation removal
- Unicode repair
- heading detection
- paragraph reconstruction
- WPM calculation
- accuracy
- progress
- search indexing

## Integration Tests

Test:

```text
PDF
 ↓
Extraction
 ↓
Processing
 ↓
Structure
 ↓
Database
 ↓
Typing
 ↓
Progress
```

## UI Tests

Test:

- import
- navigation
- keyboard shortcuts
- resume
- backup/restore

---

# 110. Test Corpus

Build a permanent test library containing:

- clean PDF
- badly formatted PDF
- scanned PDF
- PDF with TOC
- PDF without TOC
- multi-column PDF
- PDF with headers
- PDF with footers
- PDF with page numbers
- EPUB
- DOCX
- TXT
- Markdown
- malformed document

Every processing change must run against this corpus.

---

# 111. Document Processing Golden Tests

For known documents:

```text
Input
 ↓
Expected:
chapters = 14
paragraphs = 327
headers_removed = 1
footers_removed = 1
```

The parser should be regression-tested.

This prevents one "smart" cleanup improvement from quietly destroying half the library.

---

# 112. Offline Requirement

The application should be able to run after installation with:

```text
Internet = OFF
```

and still allow:

- Opening library
- Reading
- Typing
- Searching
- Analytics
- Importing local files
- Saving progress
- Backups

---

# 113. Network Isolation Testing

Development test:

```text
Disable Wi-Fi
Disable Ethernet
Launch application
```

Everything in Phase 1 should continue functioning.

---

# 114. No Required API Keys

Application startup must not require:

- OpenAI key
- Gemini key
- Anthropic key
- Any other model key

---

# 115. No Background AI

Phase 1 must not silently make:

- API calls
- model requests
- embeddings
- external semantic searches

Everything should be deterministic/local.

---

# 116. Packaging

Target:

**Standalone desktop installer**

User should not need to manually install Python.

For Windows:

```text
TypeReadSetup.exe
```

The application should bundle necessary Python/runtime dependencies.

---

# 117. Update Strategy

Phase 1 can use manual updates initially.

Later:

- automatic updater
- signed releases
- migration system for SQLite

Database migrations must be versioned.

---

# 118. Data Migration

Database should include schema version.

Example:

```text
schema_version = 1
```

Future upgrade:

```text
1 → 2
2 → 3
```

Migration scripts must preserve existing progress and documents.

---

# 119. Product Design Language

## Visual Direction

**Minimalistic, rich, elegant, editorial.**

References in spirit:

- modern reading applications
- premium writing tools
- focused productivity software

Avoid:

- gaming-style overload
- neon everywhere
- excessive gradients
- giant dashboards
- cluttered sidebars

---

# 120. Typography

The UI should prioritize:

- high readability
- generous spacing
- restrained typography
- clear hierarchy

The document itself should feel like a premium reading experience.

---

# 121. Motion

Use subtle motion only for:

- page transitions
- progress changes
- focus states
- typing feedback

Typing itself must never become visually noisy.

---

# 122. Sound

Optional:

- keypress sound
- error sound
- completion sound

All disabled by default or configurable.

---

# 123. Accessibility and Comfort

Provide:

- adjustable font size
- adjustable line width
- adjustable line height
- dark mode
- high contrast
- reduced motion
- keyboard navigation

---

# 124. Product Copy

Potential homepage positioning:

> **Read what matters. Type what you read.**

Supporting line:

> Turn books, notes, PDFs, and study material into typing practice.

Alternative:

> **Practice typing with something worth reading.**

The product should communicate utility immediately rather than presenting itself as another generic typing test.

---

# 125. Empty State

New user:

```text
Your library is empty.

Import a book, study PDF, or document
to begin your first read-and-type session.

[Add Document]
```

---

# 126. Processing State

```text
Preparing your document...

Extracting text
██████████████░░

Building structure
████████████░░░░

Preparing typing material
████████████████
```

---

# 127. Completion State

After book completion:

```text
Book Complete

Atomic Habits

100% complete

Average WPM      58
Accuracy         97.4%
Practice Time    8h 32m
Words Typed      52,481

[View Statistics]
[Start Revision]
[Return to Library]
```

---

# 128. Retention Loop

Core loop:

```text
Import
  ↓
First session
  ↓
Progress
  ↓
Return later
  ↓
Resume
  ↓
Chapter completion
  ↓
Book completion
  ↓
Revision
  ↓
Typing improvement
  ↓
More documents
```

The strongest retention mechanism should be **unfinished meaningful material**, not notifications.

---

# 129. Notification Philosophy

Desktop notifications should be optional.

Possible future:

```text
Your revision is due.
```

But avoid aggressive streak manipulation.

The product should encourage useful practice rather than behave like a casino wearing a productivity hat.

---

# 130. Competitive Differentiation

TypeRead should not position itself solely as:

> "Another typing test."

Primary differentiation:

### Existing concept

Typing + books.

### TypeRead differentiation

```text
Any document
      ↓
Document intelligence
      ↓
Clean structure
      ↓
Typing
      ↓
Navigation
      ↓
Analytics
      ↓
Revision
```

The product should own the **document-to-practice workflow**.

---

# 131. Long-Term Product Expansion

Once the core is validated, expansion can move in several directions.

## Direction A

Reading + typing

## Direction B

Study + typing

## Direction C

Professional documentation + typing

## Direction D

Language learning + typing

## Direction E

AI-assisted learning

The same underlying document engine supports all five.

---

# 132. Future Language Learning

Without AI, the app can later support:

- bilingual documents
- vocabulary lists
- typing in a foreign language
- keyboard layout training

Future AI can add:

- explanations
- translation
- vocabulary generation
- sentence analysis

---

# 133. Future Education Version

Potential later product:

```text
Teacher
  ↓
Uploads lesson
  ↓
Students type
  ↓
Teacher receives analytics
```

Possible features:

- assignments
- deadlines
- completion reports
- classroom progress

This is outside Phase 1.

---

# 134. Future Web Version

If the product is later moved to web:

```text
Desktop Core
     ↓
Core business logic
     ↓
Web API
     ↓
Web UI
```

The document engine and typing logic should remain reusable wherever practical.

---

# 135. Future Cloud Architecture

Later:

```text
Desktop/Web
      ↓
API
      ↓
PostgreSQL / Neon
      ↓
Object Storage
```

But Phase 1 must not require this architecture.

---

# 136. Cloud Sync Requirements for Future

When eventually implemented:

- encrypted transport
- document ownership
- per-user access control
- versioning
- conflict resolution
- device management
- delete propagation
- backup

---

# 137. Future AI Boundary

AI should have explicit interfaces such as:

```text
SummaryService
QuestionService
ExplanationService
VocabularyService
SemanticSearchService
RevisionService
```

The core application should call interfaces rather than directly embedding model-specific code everywhere.

---

# 138. AI Pricing Hypothesis

Potential future:

```text
Free
₹0

Core typing + local documents
```

```text
Pro
₹299-499/month

Sync + analytics + advanced features
```

```text
AI Pro
₹699-999/month

AI processing allowance + learning features
```

These are hypotheses, not final pricing.

Pricing should be based on observed demand and infrastructure costs.

---

# 139. Launch Strategy

## Stage 1: Private Build

Target:

- Stable document engine
- Stable typing engine
- 20-50 test users

Focus:

- import failures
- structure failures
- UX friction

---

## Stage 2: Small Public Beta

Target:

- 100-500 users

Measure:

- import rate
- first-session completion
- weekly active sessions
- average practice duration
- retention

---

## Stage 3: Public Free Launch

Focus:

- stability
- product polish
- public-domain library
- community feedback

---

# 140. Launch Content

Potential demonstrations:

### Demo 1

Messy PDF → clean chapter tree

### Demo 2

Book → typing session

### Demo 3

Study PDF → chapter-based practice

### Demo 4

Typing analytics after reading

### Demo 5

Weak-key analysis generated from actual book typing

These show the product's value more clearly than generic marketing.

---

# 141. MVP Acceptance Criteria

## AC-001 Document Import

**Given** a supported PDF  
**When** the user imports it  
**Then** the application extracts the text and creates a document entry.

---

## AC-002 Existing TOC

**Given** a PDF with a valid outline  
**When** it is processed  
**Then** the outline becomes the document navigation tree.

---

## AC-003 Missing TOC

**Given** a PDF without a usable outline  
**When** it is processed  
**Then** the application attempts deterministic heading detection.

---

## AC-004 Manual Correction

**Given** incorrect structure detection  
**When** the user edits the structure  
**Then** the final navigation reflects those changes.

---

## AC-005 Typing

**Given** an imported document  
**When** the user starts a typing session  
**Then** every input character is evaluated and session metrics are updated.

---

## AC-006 Progress

**Given** a partially completed section  
**When** the application closes  
**Then** reopening the document resumes from the exact saved position.

---

## AC-007 Offline

**Given** no Internet connection  
**When** the user opens the application  
**Then** all Phase 1 core functionality remains available.

---

## AC-008 Search

**Given** a document with known text  
**When** the user searches a phrase  
**Then** matching passages are displayed and selectable.

---

## AC-009 Backup

**Given** a populated library  
**When** the user exports a backup  
**Then** documents, metadata, progress, notes, and settings can be restored.

---

## AC-010 No AI Dependency

**Given** a clean installation  
**When** no AI/API configuration exists  
**Then** the application starts and functions normally.

---

# 142. Major Risks

## Risk 1: PDF parsing quality

Different PDFs behave differently.

Mitigation:

- layered parser
- fallback extraction
- deterministic cleanup
- manual structure editor
- regression test corpus

---

## Risk 2: Structure detection errors

Mitigation:

- confidence scores
- manual review
- reversible changes
- preserve source document

---

## Risk 3: Scanned PDFs

Mitigation:

- local OCR
- clearly indicate OCR uncertainty
- allow manual correction

---

## Risk 4: Product becomes a Monkeytype clone

Mitigation:

Make the document engine and reading workflow the center of the product.

---

## Risk 5: Feature bloat

Mitigation:

Keep Phase 1 focused on:

```text
Import
Process
Navigate
Type
Track
Resume
```

---

## Risk 6: Copyright exposure

Mitigation:

- no public upload repository for arbitrary books
- separate private imports from public content
- verify public-domain/licensed materials
- conduct legal review before public content distribution

---

## Risk 7: Too much engineering before validation

Mitigation:

Build the smallest end-to-end version first.

---

# 143. Development Order

Recommended implementation order:

## Sprint 1

Project setup

- PySide6
- SQLite
- architecture
- settings
- local profile

## Sprint 2

Typing engine

- input handling
- WPM
- accuracy
- errors
- sessions

## Sprint 3

TXT importer

- normalization
- paragraphs
- typing integration

## Sprint 4

PDF extraction

- PyMuPDF
- pages
- metadata
- text

## Sprint 5

PDF cleanup

- headers
- footers
- page numbers
- hyphenation
- whitespace

## Sprint 6

Structure engine

- TOC
- headings
- sections
- hierarchy

## Sprint 7

Library

- documents
- progress
- resume
- bookmarks

## Sprint 8

Search

- SQLite FTS5
- navigation
- jump-to-result

## Sprint 9

Analytics

- history
- graphs
- trends
- errors

## Sprint 10

UI polish

- themes
- focus mode
- shortcuts
- animations
- onboarding

## Sprint 11

OCR

- Tesseract
- OCRmyPDF integration

## Sprint 12

Backup

- export
- restore
- migration

---

# 144. Development Philosophy

The project should follow this order:

```text
Correctness
   ↓
Reliability
   ↓
Speed
   ↓
UX
   ↓
Visual polish
   ↓
Advanced features
```

Do not start with animations while PDF processing is producing alphabet soup.

---

# 145. Definition of Done

Phase 1 is considered ready for public beta when:

```text
✓ PDF import works reliably
✓ EPUB import works reliably
✓ TXT import works reliably
✓ DOCX import works reliably
✓ Document cleanup works
✓ Structure is navigable
✓ Structure is editable
✓ Typing engine feels responsive
✓ WPM and accuracy are trustworthy
✓ Progress persists
✓ Resume works
✓ Search works
✓ Bookmarks work
✓ Backups work
✓ Offline mode works
✓ No AI/API dependency exists
✓ Crash recovery works
✓ Core workflows pass automated tests
✓ Test document corpus passes regression tests
```

---

# 146. Phase 1 Final Product Definition

The completed Phase 1 product can be described as:

> **An offline desktop application that transforms books, PDFs, study material, and personal documents into structured typing practice while preserving the original content, tracking progress, and helping users improve typing through meaningful reading.**

Core architecture:

```text
                 USER DOCUMENT
                       │
                       ↓
               DOCUMENT IMPORT
                       │
                       ↓
                TEXT EXTRACTION
                       │
                       ↓
                TEXT CLEANING
                       │
                       ↓
             STRUCTURE DETECTION
                       │
                       ↓
               MANUAL REVIEW
                       │
                       ↓
               DOCUMENT LIBRARY
                       │
             ┌─────────┴─────────┐
             ↓                   ↓
        READING MODE         TYPING MODE
             │                   │
             └─────────┬─────────┘
                       ↓
                   ANALYTICS
                       ↓
                    PROGRESS
                       ↓
                   REVISION
```

---

# 147. Product North Star

The ultimate experience should feel like this:

```text
"I was going to read this book anyway.

Now I can read it,
type it,
improve my typing,
track my progress,
and come back exactly where I stopped."
```

That is the product.

Not:

```text
"Here is another typing test."
```

---

# 148. One-Sentence PRD Summary

> **TypeRead is an offline-first read-and-type platform that converts user-owned documents into clean, structured, navigable typing experiences, combining meaningful reading with measurable typing improvement without requiring AI, cloud processing, or an Internet connection.**

---

# 149. Phase Roadmap Summary

```text
PHASE 1
────────────────────────────────
Offline desktop
No AI
No cloud
Local SQLite
PDF / EPUB / DOCX / TXT
Document processing
Structure
Typing
Analytics
Search
Bookmarks
Resume
Revision basics


PHASE 2
────────────────────────────────
User demand validation
Cloud account
Sync
Web
Mobile
Public-domain library
Teams
Payments


PHASE 3
────────────────────────────────
AI waitlist
AI summaries
AI Q&A
AI quizzes
AI explanations
AI vocabulary
AI revision
Semantic search
Personalized learning
```

---

# 150. Final Product Strategy

The strategic sequence should remain:

```text
BUILD THE CORE
      ↓
GET PEOPLE USING IT
      ↓
MEASURE REAL BEHAVIOR
      ↓
FIND WHAT THEY WANT
      ↓
MONETIZE USEFUL PREMIUM FEATURES
      ↓
ADD AI WHERE IT ACTUALLY ADDS VALUE
```

The core application should be valuable enough that, even if every AI API disappears tomorrow, **TypeRead still works**.

That independence is a product feature, not merely a technical constraint.


========================================================================
TASK INSTRUCTIONS FOR ARCHITECT:
========================================================================
1. Analyze the PRD above.
2. In the current workspace, create the following contract files under `.orchestrator/blackboard/contracts/`:
   - `types.ts` and `types.py` (Domain models, interfaces, entities, dataclasses, strictly typed)
   - `api.json` (List of HTTP routes / CLI commands / module APIs, payload schemas, response codes)
   - `schema.sql` (Relational schema or state store definition if applicable)
   - `ARCH_DECISIONS.md` (Architectural summary and guidelines for implementation)
3. Ensure types and routes are unambiguous. Avoid 'any' or vague payloads.
4. Output a summary of your decisions when complete.
