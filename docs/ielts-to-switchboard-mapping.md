# IELTS to Switchboard Question Type Mapping

## Reading Question Types

| IELTS Question Type | Switchboard `itemType` | Notes |
|-------------------|-----------------------|-------|
| **Multiple Choice** (1 answer) | `multipleChoice` | Standard 4 options (A, B, C, D) |
| **Multiple Choice** (multiple answers) | `multipleChoice` | Multiple `isCorrect: true` options |
| **True/False/Not Given** | `multipleChoice` | Options: "True", "False", "Not Given" |
| **Yes/No/Not Given** | `multipleChoice` | Options: "Yes", "No", "Not Given" |
| **Matching Headings** | `draggable` / `dropTarget` | Headings = draggable, Paragraphs = dropTarget |
| **Matching Information** | `draggable` / `dropTarget` | Statements = draggable, Paragraphs = dropTarget |
| **Matching Features** | `draggable` / `dropTarget` | Features = draggable, Options = dropTarget |
| **Matching Sentence Endings** | `draggable` / `dropTarget` | Sentence starts = draggable, Endings = dropTarget |
| **Sentence Completion** | `inputText` | Short text input with correct answers |
| **Summary Completion** (word list) | `inputText` | With word bank options |
| **Summary Completion** (no word list) | `inputText` | Free text input |
| **Note/Table/Flow-chart Completion** | `inputText` | Form-like completion |
| **Short Answer Questions** | `inputText` | Short text answers |

## Listening Question Types

| IELTS Question Type | Switchboard `itemType` | Notes |
|-------------------|-----------------------|-------|
| **Multiple Choice** (1 answer) | `multipleChoice` | Standard 3 options |
| **Multiple Choice** (multiple answers) | `multipleChoice` | Multiple correct options |
| **Matching** | `draggable` / `dropTarget` | For matching tasks |
| **Plan/Map/Diagram Labeling** | `inputText` or `multipleChoice` | Depends on format |
| **Form/Note/Table/Flow-chart Completion** | `inputText` | Form completion |
| **Sentence Completion** | `inputText` | Sentence gaps |
| **Short Answer Questions** | `inputText` | Brief answers |

## Writing Tasks

| IELTS Task | Switchboard Handling | Notes |
|-----------|---------------------|-------|
| **Task 1 (Academic)** | `essay` itemType | Describe visual data |
| **Task 1 (General Training)** | `essay` itemType | Write a letter |
| **Task 2** | `essay` itemType | Argumentative essay |

## Speaking Tasks

Already implemented in Switchboard as `SpeakingTask` model with:
- **Part 1**: Introduction & Interview
- **Part 2**: Long Turn / Individual Talk  
- **Part 3**: Discussion

## Special Considerations

### True/False/Not Given vs Yes/No/Not Given
- Both map to `multipleChoice` with 3 options
- Difference is semantic only (fact vs opinion)
- In JSON: `options: [{text: "True"}, {text: "False"}, {text: "Not Given"}]`

### Word Limits
- IELTS often has "NO MORE THAN TWO WORDS AND/OR A NUMBER"
- This is validation logic in the frontend, not in JSON structure

### Audio for Listening
- `audioUrl` at section level (LST section)
- Each part (LSTp1, LSTp2, etc.) shares the same audio with different segments

### Writing Word Counts
- Task 1: 150 words minimum
- Task 2: 250 words minimum  
- Stored in `wordCount` field in items

## Example JSON Structure

```json
{
  "itemId": "1",
  "itemType": "multipleChoice",
  "question": "Do the following statements agree with the information in the text?",
  "options": [
    {"text": "True", "isCorrect": true},
    {"text": "False", "isCorrect": false},
    {"text": "Not Given", "isCorrect": false}
  ],
  "explanation": "<b>True</b> 📚 <br> The text clearly states that..."
}
```