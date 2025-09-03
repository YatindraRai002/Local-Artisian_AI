# 🏗️ Kala-Kaart System Architecture

## Current Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                               USER INTERFACE                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                     React Web App                                    │   │
│  │                   (TypeScript + Tailwind)                            │   │
│  │                                                                      │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │   │
│  │  │    Login    │  │   User      │  │   Artist    │  │     AI      │  │   │
│  │  │ Component   │  │ Dashboard   │  │ Dashboard   │  │ Assistant   │  │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘  │   │
│  └──────────────────────────────┬───────────────────────────────────────┘   │
└─────────────────────────────────┼───────────────────────────────────────────┘
                                  │
                                  │ HTTP Requests
                                  │
┌─────────────────────────────────▼───────────────────────────────────────────┐
│                              API LAYER                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────┐    ┌─────────────────────────────────────┐  │
│  │      Chat API (Node.js)     │    │    Backend Services (Python)       │  │
│  │        api/chat.js          │    │                                     │  │
│  │                             │    │  ┌─────────────────────────────────┐│  │
│  │ ┌─────────────────────────┐ │    │  │     enhanced_chatbot.py         ││  │
│  │ │ CSV Data Processing     │ │    │  │  - Intent Classification        ││  │
│  │ │ & Artist Search         │ │    │  │  - Entity Extraction            ││  │
│  │ └─────────────────────────┘ │    │  │  - Language Detection           ││  │
│  │ ┌─────────────────────────┐ │    │  └─────────────────────────────────┘│  │
│  │ │ Hindi/English Support   │ │    │  ┌─────────────────────────────────┐│  │
│  │ │ & Response Generation   │ │    │  │     data_processor.py           ││  │
│  │ └─────────────────────────┘ │    │  │  - Data Analysis & Stats        ││  │
│  │ ┌─────────────────────────┐ │    │  │  - Search & Filtering           ││  │
│  │ │ CORS & Error Handling   │ │    │  └─────────────────────────────────┘│  │
│  │ └─────────────────────────┘ │    │                                     │  │
│  └─────────────────────────────┘    └─────────────────────────────────────┘  │
└─────────────────────┬───────────────────────────┬───────────────────────────┘
                      │                           │
                      │                           │
┌─────────────────────▼───────────────────────────▼───────────────────────────┐
│                              DATA LAYER                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────┐    ┌─────────────────────────────────────┐  │
│  │        CSV Database         │    │      In-Memory Processing          │  │
│  │      (Artisans.csv)         │    │                                     │  │
│  │                             │    │  ┌─────────────────────────────────┐│  │
│  │ ┌─────────────────────────┐ │    │  │ Parsed Artist Data              ││  │
│  │ │ Artist Personal Info    │ │    │  │ - Name, Age, Gender             ││  │
│  │ │ - ID, Name, Age         │ │    │  │ - Craft Types & Skills          ││  │
│  │ └─────────────────────────┘ │    │  │ - Location (State/District)     ││  │
│  │ ┌─────────────────────────┐ │    │  └─────────────────────────────────┘│  │
│  │ │ Contact Information     │ │    │  ┌─────────────────────────────────┐│  │
│  │ │ - Phone, Email          │ │    │  │ Search Indexes                  ││  │
│  │ └─────────────────────────┘ │    │  │ - State-based filtering         ││  │
│  │ ┌─────────────────────────┐ │    │  │ - Craft-based filtering         ││  │
│  │ │ Location Data           │ │    │  │ - Text-based search             ││  │
│  │ │ - State, District       │ │    │  └─────────────────────────────────┘│  │
│  │ └─────────────────────────┘ │    │                                     │  │
│  │ ┌─────────────────────────┐ │    │                                     │  │
│  │ │ Craft Information       │ │    │                                     │  │
│  │ │ - Types, Specialties    │ │    │                                     │  │
│  │ └─────────────────────────┘ │    │                                     │  │
│  └─────────────────────────────┘    └─────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Model Workflow & Data Flow

```
USER QUERY PROCESSING PIPELINE
═══════════════════════════════

┌─────────────────────┐
│   User Input        │
│  "Show pottery      │
│   artists in        │
│   Gujarat"          │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Language Detection │
│                     │
│ • Unicode Analysis  │
│ • Script Detection  │
│ • Language Flag     │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Intent              │
│ Classification      │
│                     │
│ • Pattern Matching  │
│ • Regex Analysis    │
│ • Context Mapping   │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Entity Extraction   │
│                     │
│ • State: "Gujarat"  │
│ • Craft: "Pottery"  │
│ • Context Variables │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Semantic Search     │
│                     │
│ • Filter Building   │
│ • Data Querying     │
│ • Relevance Scoring │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Response Generation │
│                     │
│ • Template Selection│
│ • Data Formatting   │
│ • Suggestion Engine │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│   Formatted         │
│   Response          │
│                     │
│ • Artists List      │
│ • Smart Suggestions │
│ • Context Data      │
└─────────────────────┘
```

## AI/ML Components Deep Dive

### 1. Enhanced Chatbot Engine
```
┌──────────────────────────────────────────────────────────────┐
│                    NLP PROCESSING PIPELINE                   │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  Input Text → Preprocessing → Feature Extraction           │
│       │             │                │                      │
│       │             │                └── Tokenization       │
│       │             │                └── Normalization      │
│       │             │                └── Stop Word Removal  │
│       │             │                                       │
│       │             └── Language Detection                  │
│       │                     │                               │
│       │                     ├── Hindi Pattern              │
│       │                     ├── English Pattern            │
│       │                     └── Tamil/Telugu Pattern       │
│       │                                                     │
│       └── Intent Classification                             │
│               │                                             │
│               ├── Greeting Patterns                        │
│               ├── Search Patterns                          │
│               ├── Statistics Patterns                      │
│               └── Contact Patterns                         │
│                                                             │
│  Entity Extraction ← Pattern Matching ← Regex Library     │
│       │                                                     │
│       ├── State Extraction                                 │
│       ├── Craft Type Extraction                            │
│       ├── Demographic Filters                              │
│       └── Context Variables                                │
│                                                             │
└──────────────────────────────────────────────────────────────┘
```

### 2. Data Processing & Search Engine
```
┌──────────────────────────────────────────────────────────────┐
│               ARTISAN DATA PROCESSING                        │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  CSV Data → Data Validation → Normalization                │
│      │            │                │                        │
│      │            │                ├── Phone Formatting     │
│      │            │                ├── Address Parsing      │
│      │            │                └── Skill Categorization │
│      │            │                                         │
│      │            └── Quality Checks                        │
│      │                    │                                 │
│      │                    ├── Missing Data Detection        │
│      │                    ├── Duplicate Removal             │
│      │                    └── Consistency Validation        │
│      │                                                      │
│      └── Clustering & Analysis                              │
│              │                                              │
│              ├── Geographic Clustering                      │
│              ├── Skill-based Grouping                       │
│              ├── Demographic Analysis                       │
│              └── Statistical Profiling                      │
│                                                             │
│  Search Index ← Vector Embeddings ← Feature Engineering    │
│       │                                                     │
│       ├── Text-based Search                                │
│       ├── Fuzzy Matching                                   │
│       ├── Multi-filter Queries                             │
│       └── Relevance Ranking                                │
│                                                             │
└──────────────────────────────────────────────────────────────┘
```

