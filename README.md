# IELTS Content Repository

This repository contains structured IELTS (International English Language Testing System) content formatted for use with LingoLugo/Switchboard.

## Structure

```
IELTS-Content/
├── README.md
├── source-material/          # Raw source files (PDFs, text extracts)
├── json-content/            # Structured JSON files matching Switchboard schema
├── scripts/                 # Conversion/processing scripts
└── docs/                    # Documentation
```

## Content Types

### Reading (Academic & General Training)
- Passage 1, 2, 3 for each test
- Question types: Multiple Choice, True/False/Not Given, Yes/No/Not Given, Matching Headings, Matching Information, Sentence Completion, Summary Completion, Short Answer

### Listening (Same for Academic & General)
- Section 1-4 for each test
- Question types: Multiple Choice, Matching, Plan/Map/Diagram Labeling, Form/Note/Table/Flow-chart/Summary Completion, Sentence Completion, Short Answer

### Writing
- Task 1 (Academic): Describe visual information
- Task 1 (General Training): Write a letter
- Task 2: Essay on a given topic

### Speaking
- Part 1: Introduction & Interview
- Part 2: Long Turn / Individual Talk
- Part 3: Discussion
*(Note: Speaking tasks already exist in Switchboard)*

## JSON Schema

Files follow the same structure as Switchboard's `sourceMaterialForMockExams/`:

```json
{
  "exam_id": "IELTS_Academic_Test_1",
  "title": "IELTS Academic - Test 1",
  "time_allowed": 60,
  "sections": [
    {
      "sectionType": "RUE",
      "title": "Reading",
      "time_allowed": 60,
      "parts": [
        {
          "partId": "passage1",
          "title": "Passage 1",
          "instructions": "...",
          "text": "...",
          "items": [
            {
              "itemId": "1",
              "itemType": "multipleChoice",
              "question": "...",
              "options": [...],
              "correct_answer": "A",
              "explanation": "..."
            }
          ]
        }
      ]
    }
  ]
}
```

## Source Material

Using official free IELTS practice tests from:
- British Council: https://takeielts.britishcouncil.org/take-ielts/prepare/free-ielts-practice-tests
- IELTS.org: https://ielts.org/for-test-takers/sample-test-questions

## License

Content derived from official IELTS practice materials is for educational use only. IELTS is jointly owned by British Council, IDP: IELTS Australia, and Cambridge Assessment English.