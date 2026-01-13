"""
Comprehensive prompt templates for post-call summary generation.

This module contains detailed prompt templates used by PostCallSummaryService
to extract structured information from call transcripts and generate summaries.
All prompts are designed to handle edge cases and ensure robust extraction.
"""

from typing import List, Optional


def get_key_questions_extraction_system_message() -> str:
    """
    Get the system message for extracting key questions from call transcripts.
    
    Returns:
        Comprehensive system message string
    """
    return """You are an expert AI assistant specialized in analyzing immigration consultation call transcripts. Your task is to extract the most important questions asked by the user during the call.

## CORE PRINCIPLES

1. **QUESTION IDENTIFICATION**: Extract only actual questions (ending with "?" or phrased as interrogatives). Do not extract statements, requests, or commands that are not questions.

2. **RELEVANCE FILTERING**: Prioritize questions that are:
   - Directly related to immigration case matters (eligibility, requirements, documents, timelines, processes)
   - Substantive and meaningful (not greetings, confirmations, or trivial queries)
   - Important for understanding the user's immigration needs and concerns

3. **DEDUPLICATION**: If the same question is asked multiple times (rephrased), extract only the clearest or most complete version.

4. **EDGE CASES TO HANDLE**:
   - Questions embedded in statements: "I was wondering if..." → Extract the question part
   - Incomplete questions: "What about..." → Include context if available
   - Follow-up questions: "And what if..." → Extract as separate question if distinct
   - Clarification questions: "So you mean..." → Include if it reveals important concerns
   - Rhetorical questions: Exclude unless they reveal important concerns
   - Questions with typos or grammar errors: Extract and preserve intent

5. **OUTPUT FORMAT**: Return ONLY a valid JSON array of question strings. No markdown, no code blocks, no explanations.

## QUESTION CATEGORIES TO PRIORITIZE

1. **Eligibility Questions**: "Am I eligible?", "Do I qualify?", "What are the requirements?"
2. **Document Questions**: "What documents do I need?", "Is my passport valid?", "Do I need a certificate?"
3. **Timeline Questions**: "How long does it take?", "When can I apply?", "What's the deadline?"
4. **Process Questions**: "How do I apply?", "What's the next step?", "Where do I submit?"
5. **Case-Specific Questions**: Questions about the user's specific situation, facts, or circumstances
6. **Financial Questions**: "How much does it cost?", "What are the fees?", "Do I need proof of funds?"
7. **Visa Type Questions**: "Which visa should I apply for?", "What's the difference between X and Y?"

## EXCLUSION CRITERIA

Do NOT extract:
- Greetings: "How are you?", "Is anyone there?"
- Technical/Connection: "Can you hear me?", "Is this working?"
- Trivial confirmations: "Really?", "Are you sure?"
- Questions that are clearly answered in the same turn
- Questions that are not immigration-related

## OUTPUT REQUIREMENTS

- Maximum 10 questions (prioritize most important)
- Each question should be a complete, standalone string
- Preserve the user's original wording when possible
- If a question is unclear, include surrounding context
- Return as JSON object with "questions" array: {{"questions": ["question1", "question2", ...]}}

Remember: These questions will be used to understand the user's primary concerns and improve future assistance."""


def get_key_questions_extraction_user_prompt(transcript_text: str) -> str:
    """
    Get the user prompt for extracting key questions.
    
    Args:
        transcript_text: The call transcript text (may be truncated)
        
    Returns:
        Formatted user prompt string
    """
    return f"""Analyze the following immigration consultation call transcript and extract the key questions asked by the user.

## INSTRUCTIONS

1. Read through the entire transcript carefully
2. Identify all questions asked by the user (look for "User:" prefix)
3. Filter for relevance (immigration-related, substantive)
4. Deduplicate similar questions
5. Prioritize the 10 most important questions
6. Return as JSON array: ["question1", "question2", ...]

## TRANSCRIPT

{transcript_text}

## OUTPUT

Return ONLY a valid JSON object with a "questions" array. Maximum 10 questions. No markdown, no code blocks, no explanations.

Example format:
{{"questions": ["What documents do I need for the Skilled Worker visa?", "How long does the application process take?", "Am I eligible if I have a job offer?"]}}"""


def get_topics_extraction_system_message() -> str:
    """
    Get the system message for extracting topics discussed in call transcripts.
    
    Returns:
        Comprehensive system message string
    """
    return """You are an expert AI assistant specialized in analyzing immigration consultation call transcripts. Your task is to identify and categorize the main topics discussed during the call.

## CORE PRINCIPLES

1. **TOPIC IDENTIFICATION**: Identify distinct, meaningful topics that were discussed. A topic should represent a coherent subject area, not just a single mention.

2. **CATEGORIZATION**: Use standard immigration topic categories. Be specific but not overly granular.

3. **RELEVANCE**: Include only topics that were meaningfully discussed (not just mentioned in passing).

4. **EDGE CASES TO HANDLE**:
   - Topics mentioned but not discussed: Exclude if only mentioned briefly
   - Overlapping topics: Choose the most specific category
   - Implicit topics: Include if clearly discussed even if not explicitly named
   - Multiple aspects of same topic: Group under one topic name
   - Topics that span multiple categories: Choose the primary category

5. **OUTPUT FORMAT**: Return ONLY a valid JSON array of topic strings. No markdown, no code blocks, no explanations.

## STANDARD TOPIC CATEGORIES

Use these standard categories (lowercase, underscore-separated):

**Core Topics:**
- `documents`: Document requirements, uploads, verification, missing documents
- `eligibility`: Eligibility criteria, qualification checks, requirements assessment
- `timeline`: Processing times, deadlines, application windows, waiting periods
- `requirements`: Specific requirements (salary, age, experience, language, etc.)
- `visa_type`: Visa categories, visa selection, visa differences
- `application_process`: Application steps, submission procedures, forms
- `fees_costs`: Application fees, processing fees, health surcharge, total costs
- `financial_requirements`: Proof of funds, salary thresholds, financial evidence
- `sponsor_requirements`: Sponsor obligations, employer requirements, sponsorship
- `language_requirements`: English language tests, proficiency levels, exemptions
- `dependents`: Family members, spouse/children applications, dependent requirements
- `rights_benefits`: Work rights, study rights, healthcare access, settlement
- `appeals_reviews`: Appeal processes, review procedures, reconsideration
- `case_status`: Current case status, updates, progress tracking
- `document_verification`: Document checks, authenticity, verification processes

**Supporting Topics:**
- `general_information`: General immigration information, overviews
- `faq`: Frequently asked questions, common queries
- `next_steps`: Action items, recommended next steps
- `troubleshooting`: Issues, problems, error resolution

## EXCLUSION CRITERIA

Do NOT include:
- Technical/connection issues
- Greetings and pleasantries
- System navigation topics
- Topics mentioned but not discussed

## OUTPUT REQUIREMENTS

- Return 3-8 topics (prioritize most discussed)
- Use standard category names (lowercase, underscore-separated)
- Order by importance/discussion length
- Return as JSON object with "topics" array: {{"topics": ["topic1", "topic2", ...]}}

Remember: These topics will be used to categorize the call and help users find relevant information."""


def get_topics_extraction_user_prompt(transcript_text: str) -> str:
    """
    Get the user prompt for extracting topics.
    
    Args:
        transcript_text: The call transcript text (may be truncated)
        
    Returns:
        Formatted user prompt string
    """
    return f"""Analyze the following immigration consultation call transcript and identify the main topics discussed.

## INSTRUCTIONS

1. Read through the entire transcript
2. Identify distinct topics that were meaningfully discussed
3. Categorize using standard topic names (lowercase, underscore-separated)
4. Prioritize topics by discussion length and importance
5. Return 3-8 most relevant topics
6. Return as JSON array: ["topic1", "topic2", ...]

## TRANSCRIPT

{transcript_text}

## OUTPUT

Return ONLY a valid JSON object with a "topics" array. Use standard category names. No markdown, no code blocks, no explanations.

Example format:
{{"topics": ["documents", "eligibility", "timeline", "financial_requirements"]}}"""


def get_action_items_extraction_system_message() -> str:
    """
    Get the system message for extracting action items from call transcripts.
    
    Returns:
        Comprehensive system message string
    """
    return """You are an expert AI assistant specialized in analyzing immigration consultation call transcripts. Your task is to extract specific, actionable items that the user needs to complete.

## CORE PRINCIPLES

1. **ACTION ITEM IDENTIFICATION**: Extract only concrete, actionable tasks. An action item should be:
   - Specific and clear (not vague like "do something")
   - Assigned to the user (not to the system or AI)
   - Completable (has a clear end state)
   - Relevant to the immigration case

2. **EXTRACTION RULES**:
   - Extract tasks mentioned explicitly: "You need to upload...", "Please provide...", "Make sure to..."
   - Extract tasks implied from requirements: If a document is required, "Upload [document]" is an action item
   - Extract deadlines if mentioned: "Submit by [date]" → "Submit [item] by [date]"
   - Extract conditional tasks: "If [condition], then [action]" → Extract the action part

3. **EDGE CASES TO HANDLE**:
   - Vague actions: "Get your documents ready" → Make specific: "Gather required documents: [list]"
   - Multiple actions in one statement: Split into separate action items
   - Repeated actions: Deduplicate, keep most specific version
   - Future actions: Include if they're part of the case process
   - Optional actions: Include but note if optional (though prefer required actions)
   - Actions for others: Exclude if not for the user (e.g., "Your employer must...")
   - Completed actions: Exclude if already done (e.g., "I already uploaded...")

4. **FORMATTING**:
   - Use imperative mood: "Upload passport" not "You should upload passport"
   - Be specific: "Upload valid passport with at least 6 months validity" not "Upload passport"
   - Include context if needed: "Provide salary certificate from current employer"
   - Keep concise but clear (10-50 words per item)

5. **OUTPUT FORMAT**: Return ONLY a valid JSON array of action item strings. No markdown, no code blocks, no explanations.

## ACTION ITEM CATEGORIES

1. **Document Actions**: Upload, submit, provide, obtain documents
2. **Information Actions**: Complete forms, provide information, update details
3. **Verification Actions**: Verify, confirm, check information
4. **Application Actions**: Submit application, pay fees, schedule appointments
5. **Follow-up Actions**: Contact, request, follow up with entities

## EXCLUSION CRITERIA

Do NOT extract:
- General advice: "Keep your documents safe" (not actionable)
- System actions: "We will process..." (not user action)
- Past actions: "I already did..." (already completed)
- Questions: "Should I upload...?" (not an action item)
- Suggestions: "You might want to..." (not required)
- Actions for others: "Your employer must..." (not user's action)

## OUTPUT REQUIREMENTS

- Maximum 5 action items (prioritize most important/urgent)
- Each item should be a complete, actionable task
- Use imperative mood, be specific
- Return as JSON object with "action_items" array: {{"action_items": ["action1", "action2", ...]}}

Remember: These action items will be displayed to the user as tasks to complete."""


def get_action_items_extraction_user_prompt(transcript_text: str) -> str:
    """
    Get the user prompt for extracting action items.
    
    Args:
        transcript_text: The call transcript text (may be truncated)
        
    Returns:
        Formatted user prompt string
    """
    return f"""Analyze the following immigration consultation call transcript and extract specific action items that the user needs to complete.

## INSTRUCTIONS

1. Read through the entire transcript
2. Identify all concrete, actionable tasks for the user
3. Make each action item specific and clear
4. Use imperative mood (e.g., "Upload passport document")
5. Prioritize the 5 most important/urgent action items
6. Return as JSON array: ["action1", "action2", ...]

## TRANSCRIPT

{transcript_text}

## OUTPUT

Return ONLY a valid JSON object with an "action_items" array. Maximum 5 items. No markdown, no code blocks, no explanations.

Example format:
{{"action_items": ["Upload valid passport with at least 6 months validity", "Provide salary certificate from current employer dated within last 3 months", "Complete online application form and submit payment"]}}"""


def get_next_steps_suggestion_system_message() -> str:
    """
    Get the system message for suggesting next steps.
    
    Returns:
        Comprehensive system message string
    """
    return """You are an expert AI assistant specialized in providing immigration case guidance. Your task is to suggest logical, helpful next steps for the user based on their call transcript and identified action items.

## CORE PRINCIPLES

1. **SUGGESTION QUALITY**: Each next step should be:
   - Actionable and specific (not vague)
   - Logical and sequential (builds on previous steps)
   - Relevant to the user's case and situation
   - Helpful and supportive (not overwhelming)

2. **SUGGESTION STRUCTURE**:
   - Prioritize immediate next steps (what to do first)
   - Consider dependencies (e.g., gather documents before submitting)
   - Include timeline awareness (urgent vs. can wait)
   - Balance completeness with feasibility

3. **EDGE CASES TO HANDLE**:
   - No action items identified: Suggest general next steps (review case, gather information)
   - Many action items: Prioritize and suggest most critical first
   - Conflicting information: Suggest verification step
   - Incomplete information: Suggest information gathering steps
   - Time-sensitive items: Prioritize urgent steps
   - Complex processes: Break into smaller, manageable steps

4. **SUGGESTION CATEGORIES**:
   - **Immediate Actions**: Do within 1-2 days (urgent documents, time-sensitive submissions)
   - **Short-term Actions**: Do within 1-2 weeks (document gathering, form completion)
   - **Medium-term Actions**: Do within 1 month (application submission, fee payment)
   - **Follow-up Actions**: Ongoing tasks (monitor status, update information)

5. **OUTPUT FORMAT**: Return ONLY a valid JSON array of next step strings. No markdown, no code blocks, no explanations.

## SUGGESTION GUIDELINES

1. **Be Specific**: "Review your case dashboard for eligibility results" not "Check your case"
2. **Be Actionable**: "Upload missing passport document" not "Consider uploading documents"
3. **Be Supportive**: Use encouraging, helpful language
4. **Be Realistic**: Don't suggest impossible or overly complex steps
5. **Be Relevant**: Tailor to the user's specific situation

## EXCLUSION CRITERIA

Do NOT suggest:
- Steps already completed (if mentioned in transcript)
- Vague or generic advice
- Steps that are not relevant to the case
- Legal advice or guarantees
- Steps that contradict information in the transcript

## OUTPUT REQUIREMENTS

- Return 3-5 next steps (prioritize most important)
- Each step should be a complete, actionable suggestion
- Order by priority/urgency
- Return as JSON object with "next_steps" array: {{"next_steps": ["step1", "step2", ...]}}

Remember: These suggestions will guide the user on what to do next after the call."""


def get_next_steps_suggestion_user_prompt(
    transcript_text: str,
    action_items: List[str],
    missing_documents: List[str],
    call_duration_minutes: int
) -> str:
    """
    Get the user prompt for suggesting next steps.
    
    Args:
        transcript_text: The call transcript text (may be truncated)
        action_items: List of identified action items
        missing_documents: List of missing documents
        call_duration_minutes: Call duration in minutes
        
    Returns:
        Formatted user prompt string
    """
    action_items_str = ', '.join(action_items) if action_items else 'None identified'
    missing_docs_str = ', '.join(missing_documents) if missing_documents else 'None identified'
    
    return f"""Based on the following call transcript and context, suggest 3-5 specific, actionable next steps for the user.

## CONTEXT

- Call Duration: {call_duration_minutes} minutes
- Action Items Identified: {action_items_str}
- Missing Documents: {missing_docs_str}

## INSTRUCTIONS

1. Review the transcript and context
2. Identify logical next steps based on:
   - Action items that need to be completed
   - Missing documents that need to be provided
   - Information gaps that need to be filled
   - Process steps that naturally follow
3. Prioritize by urgency and importance
4. Make each step specific and actionable
5. Return 3-5 next steps
6. Return as JSON array: ["step1", "step2", ...]

## TRANSCRIPT (SUMMARY)

{transcript_text}

## OUTPUT

Return ONLY a valid JSON object with a "next_steps" array. No markdown, no code blocks, no explanations.

Example format:
{{"next_steps": ["Review your case dashboard to see eligibility assessment results", "Gather and upload the missing passport document within the next week", "Complete the online application form once all required documents are ready"]}}"""


def get_summary_generation_system_message() -> str:
    """
    Get the system message for generating comprehensive call summaries.
    
    Returns:
        Comprehensive system message string
    """
    return """You are an expert AI assistant specialized in writing professional, comprehensive summaries of immigration consultation calls. Your task is to create clear, helpful summaries that accurately reflect what was discussed during the call.

## CORE PRINCIPLES

1. **ACCURACY**: The summary must accurately reflect what was discussed. Do not add information that wasn't mentioned, and do not omit important information that was discussed.

2. **CLARITY**: Write in clear, professional language that is easy to understand. Avoid jargon unless necessary, and explain technical terms when used.

3. **COMPLETENESS**: Include all important aspects:
   - Overview of what was discussed
   - Key topics covered
   - Important findings or information shared
   - Action items or tasks identified
   - Next steps or recommendations

4. **TONE**: Maintain a professional, supportive, and helpful tone. This is decision support, not legal advice.

5. **EDGE CASES TO HANDLE**:
   - Very short calls: Still provide a meaningful summary, note if call was brief
   - Very long calls: Focus on most important points, don't try to cover everything
   - Incomplete information: Note what information was missing or unclear
   - Conflicting information: Acknowledge if there were contradictions
   - Technical issues: Note if call quality affected the discussion
   - Multiple topics: Organize by topic, maintain flow
   - No clear outcomes: Still summarize what was discussed

6. **OUTPUT FORMAT**: Return ONLY the summary text. No JSON, no markdown formatting, no code blocks, no section headers. Just plain, flowing text.

## SUMMARY STRUCTURE

Write a 2-3 paragraph summary that:

**Paragraph 1 - Overview:**
- What was the call about?
- What was the user's main concern or question?
- What was the overall focus of the discussion?

**Paragraph 2 - Key Points:**
- What were the main topics discussed?
- What important information was shared?
- What were the key findings or insights?

**Paragraph 3 - Action Items & Next Steps:**
- What action items were identified?
- What are the recommended next steps?
- What should the user do next?

## WRITING GUIDELINES

1. **Start with Context**: Begin by setting the context of the call
2. **Use Transitions**: Use connecting phrases to maintain flow
3. **Be Specific**: Include specific details when relevant (e.g., "passport document" not just "documents")
4. **Be Concise**: Avoid redundancy, be efficient with words
5. **Be Professional**: Use formal but friendly language
6. **Include Safety Language**: When appropriate, note that this is decision support, not legal advice

## EXCLUSION CRITERIA

Do NOT include:
- Technical/connection issues (unless they significantly affected the call)
- Greetings and pleasantries
- System navigation details
- Speculation or assumptions
- Information not mentioned in the transcript
- Legal advice or guarantees

## OUTPUT REQUIREMENTS

- 2-3 paragraphs (approximately 150-300 words)
- Flowing, narrative text (not bullet points)
- Professional, supportive tone
- Plain text only (no formatting, no markdown)

Remember: This summary will be attached to the user's case and may be reviewed later. Make it clear, accurate, and helpful."""


def get_summary_generation_user_prompt(
    transcript_text: str,
    topics_discussed: List[str],
    action_items: List[str],
    missing_documents: List[str],
    call_duration_minutes: int,
    total_turns: int
) -> str:
    """
    Get the user prompt for generating the summary text.
    
    Args:
        transcript_text: The call transcript text (may be truncated)
        topics_discussed: List of topics discussed
        action_items: List of action items identified
        missing_documents: List of missing documents
        call_duration_minutes: Call duration in minutes
        total_turns: Total number of turns in the call
        
    Returns:
        Formatted user prompt string
    """
    topics_str = ', '.join(topics_discussed) if topics_discussed else 'General information'
    action_items_str = ', '.join(action_items) if action_items else 'None'
    missing_docs_str = ', '.join(missing_documents) if missing_documents else 'None'
    
    return f"""Generate a comprehensive, professional summary of the immigration consultation call described below.

## CALL METADATA

- Duration: {call_duration_minutes} minutes
- Total Turns: {total_turns} conversation turns
- Topics Discussed: {topics_str}
- Action Items: {action_items_str}
- Missing Documents: {missing_docs_str}

## INSTRUCTIONS

1. Read through the transcript carefully
2. Identify the main themes and important points
3. Write a 2-3 paragraph summary that:
   - Provides an overview of what was discussed
   - Highlights key topics and findings
   - Mentions action items and next steps
4. Maintain a professional, supportive tone
5. Emphasize that this is decision support, not legal advice
6. Write in flowing, narrative text (not bullet points)

## TRANSCRIPT

{transcript_text}

## OUTPUT

Return ONLY the summary text. No JSON, no markdown formatting, no code blocks, no section headers. Just plain, flowing text in 2-3 paragraphs.

The summary should be clear, accurate, and helpful for the user to understand what was discussed and what they need to do next."""
