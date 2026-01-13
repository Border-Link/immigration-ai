"""
Service for post-call summary generation using AI.

Uses LLM to generate comprehensive summaries, extract key information,
and identify action items from call transcripts.
"""
import logging
import json
from typing import Optional, List, Dict, Any
from ai_calls.models.call_summary import CallSummary
from ai_calls.repositories.call_summary_repository import CallSummaryRepository
from ai_calls.selectors.call_session_selector import CallSessionSelector
from ai_calls.selectors.call_transcript_selector import CallTranscriptSelector
from data_ingestion.helpers.llm_client import LLMClient, _call_llm_with_retry
from data_ingestion.exceptions.rule_parsing_exceptions import (
    LLMRateLimitError,
    LLMTimeoutError,
    LLMServiceUnavailableError,
    LLMAPIKeyError,
    LLMInvalidResponseError
)
from django.conf import settings
from ai_calls.helpers.summary_prompts import (
    get_key_questions_extraction_system_message,
    get_key_questions_extraction_user_prompt,
    get_topics_extraction_system_message,
    get_topics_extraction_user_prompt,
    get_action_items_extraction_system_message,
    get_action_items_extraction_user_prompt,
    get_next_steps_suggestion_system_message,
    get_next_steps_suggestion_user_prompt,
    get_summary_generation_system_message,
    get_summary_generation_user_prompt
)

logger = logging.getLogger('django')


class PostCallSummaryService:
    """Service for post-call summary generation with AI enhancement."""

    @staticmethod
    def generate_summary(session_id: str) -> Optional[CallSummary]:
        """
        Generate post-call summary using AI.
        
        Steps:
        1. Analyze full transcript
        2. Extract key questions using AI
        3. Identify action items using AI
        4. Identify missing documents from context and transcript
        5. Suggest next steps using AI
        6. Generate comprehensive summary text using AI
        7. Create CallSummary model
        8. Link summary to call session
        9. Attach to case timeline
        
        Returns:
        - CallSummary instance or None if generation fails
        """
        try:
            call_session = CallSessionSelector.get_by_id(session_id)
            if not call_session:
                logger.error(f"Call session {session_id} not found")
                return None
            
            if not call_session.case:
                logger.error(f"Call session {session_id} has no associated case")
                return None
            
            # Get transcript
            transcripts = CallTranscriptSelector.get_by_call_session(call_session)
            if not transcripts.exists():
                logger.warning(f"No transcript found for session {session_id}")
                return None
            
            # Order transcripts by turn number
            transcripts = transcripts.order_by('turn_number')
            
            # Build transcript text for AI analysis
            transcript_text = PostCallSummaryService._build_transcript_text(transcripts)
            
            # Extract key questions using AI
            key_questions = PostCallSummaryService._extract_key_questions_ai(
                transcript_text,
                call_session
            )
            
            # Extract topics discussed using AI
            topics_discussed = PostCallSummaryService._extract_topics_ai(
                transcript_text,
                call_session
            )
            
            # Extract action items using AI
            action_items = PostCallSummaryService._extract_action_items_ai(
                transcript_text,
                call_session
            )
            
            # Identify missing documents
            missing_documents = PostCallSummaryService._extract_missing_documents(
                call_session,
                transcripts
            )
            
            # Suggest next steps using AI
            suggested_next_steps = PostCallSummaryService._suggest_next_steps_ai(
                call_session,
                transcript_text,
                action_items,
                missing_documents
            )
            
            # Generate comprehensive summary text using AI
            summary_text = PostCallSummaryService._generate_summary_text_ai(
                call_session,
                transcript_text,
                topics_discussed,
                action_items,
                missing_documents
            )
            
            # Create summary
            summary = CallSummaryRepository.create_call_summary(
                call_session=call_session,
                summary_text=summary_text,
                total_turns=transcripts.count(),
                total_duration_seconds=call_session.duration_seconds or 0,
                key_questions=key_questions,
                action_items=action_items,
                missing_documents=missing_documents,
                suggested_next_steps=suggested_next_steps,
                topics_discussed=topics_discussed
            )
            
            # Link summary to call session (caller will handle this)
            # Note: attach_to_case_timeline is called separately by CallSessionService
            
            logger.info(f"Generated summary for call session {session_id}")
            return summary
            
        except (LLMRateLimitError, LLMTimeoutError, LLMServiceUnavailableError,
                LLMAPIKeyError, LLMInvalidResponseError) as e:
            logger.error(f"LLM error generating summary for session {session_id}: {e}")
            # Fallback to simple summary generation
            return PostCallSummaryService._generate_fallback_summary(session_id)
        except Exception as e:
            logger.error(f"Error generating summary for session {session_id}: {e}", exc_info=True)
            # Fallback to simple summary generation
            return PostCallSummaryService._generate_fallback_summary(session_id)

    @staticmethod
    def _build_transcript_text(transcripts) -> str:
        """Build formatted transcript text for AI analysis."""
        transcript_lines = []
        for transcript in transcripts:
            speaker = "User" if transcript.turn_type == 'user' else "AI"
            transcript_lines.append(f"{speaker}: {transcript.text}")
        
        return "\n".join(transcript_lines)

    @staticmethod
    def _call_llm_for_summary(system_message: str, user_prompt: str, model: str = None, 
                              temperature: float = 0.3, max_tokens: int = 2000,
                              response_format: Optional[Dict] = None) -> Optional[Dict[str, Any]]:
        """
        Call LLM API for summary generation using internal LLMClient.
        
        Uses the same retry logic and error handling as rule extraction,
        but with custom prompts for summary generation.
        
        Returns:
            Dict with 'content', 'usage', 'model', 'processing_time_ms' or None
        """
        try:
            llm_client = LLMClient()
            
            messages = [
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_prompt}
            ]
            
            model = model or getattr(settings, 'AI_CALLS_LLM_MODEL', 'gpt-4o-mini')
            
            response = _call_llm_with_retry(
                client=llm_client.client,
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                response_format=response_format,
                timeout=30.0
            )
            
            response['success'] = True
            return response
            
        except (LLMRateLimitError, LLMTimeoutError, LLMServiceUnavailableError,
                LLMAPIKeyError, LLMInvalidResponseError) as e:
            logger.warning(f"LLM call failed: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error in LLM call: {e}", exc_info=True)
            return None

    @staticmethod
    def _extract_key_questions_ai(transcript_text: str, call_session) -> List[str]:
        """Extract key questions asked by user using AI."""
        try:
            system_message = get_key_questions_extraction_system_message()
            user_prompt = get_key_questions_extraction_user_prompt(transcript_text[:4000])

            response = PostCallSummaryService._call_llm_for_summary(
                system_message=system_message,
                user_prompt=user_prompt,
                temperature=0.2,
                max_tokens=500,
                response_format={"type": "json_object"}
            )
            
            if response.get('success') and response.get('content'):
                try:
                    # Try to parse JSON from response
                    content = response['content'].strip()
                    # Remove markdown code blocks if present
                    if content.startswith('```'):
                        lines = content.split('\n')
                        content = '\n'.join(lines[1:-1]) if len(lines) > 2 else content
                    if content.startswith('```json'):
                        lines = content.split('\n')
                        content = '\n'.join(lines[1:-1]) if len(lines) > 2 else content
                    
                    parsed = json.loads(content)
                    # Handle both object format {"questions": [...]} and direct array format
                    if isinstance(parsed, dict) and 'questions' in parsed:
                        questions = parsed['questions']
                    elif isinstance(parsed, list):
                        questions = parsed
                    else:
                        questions = []
                    
                    if isinstance(questions, list):
                        return questions[:10]  # Limit to 10
                except (json.JSONDecodeError, ValueError) as e:
                    logger.warning(f"Failed to parse key questions JSON: {e}, using fallback")
            
            # Fallback to simple extraction
            return PostCallSummaryService._extract_key_questions_simple(transcript_text)
            
        except Exception as e:
            logger.warning(f"Error extracting key questions with AI: {e}, using fallback")
            return PostCallSummaryService._extract_key_questions_simple(transcript_text)

    @staticmethod
    def _extract_key_questions_simple(transcript_text: str) -> List[str]:
        """Simple keyword-based extraction of questions (fallback)."""
        questions = []
        lines = transcript_text.split('\n')
        
        for line in lines:
            if line.startswith('User:') and '?' in line:
                question = line.replace('User:', '').strip()
                if len(question) > 10:  # Filter out very short questions
                    questions.append(question)
                    if len(questions) >= 10:
                        break
        
        return questions

    @staticmethod
    def _extract_topics_ai(transcript_text: str, call_session) -> List[str]:
        """Extract topics discussed using AI."""
        try:
            system_message = get_topics_extraction_system_message()
            user_prompt = get_topics_extraction_user_prompt(transcript_text[:4000])

            response = PostCallSummaryService._call_llm_for_summary(
                system_message=system_message,
                user_prompt=user_prompt,
                temperature=0.2,
                max_tokens=300,
                response_format={"type": "json_object"}
            )
            
            if response.get('success') and response.get('content'):
                try:
                    content = response['content'].strip()
                    # Remove markdown code blocks if present
                    if content.startswith('```'):
                        lines = content.split('\n')
                        content = '\n'.join(lines[1:-1]) if len(lines) > 2 else content
                    if content.startswith('```json'):
                        lines = content.split('\n')
                        content = '\n'.join(lines[1:-1]) if len(lines) > 2 else content
                    
                    parsed = json.loads(content)
                    # Handle both object format {"topics": [...]} and direct array format
                    if isinstance(parsed, dict) and 'topics' in parsed:
                        topics = parsed['topics']
                    elif isinstance(parsed, list):
                        topics = parsed
                    else:
                        topics = []
                    
                    if isinstance(topics, list):
                        return topics
                except (json.JSONDecodeError, ValueError) as e:
                    logger.warning(f"Failed to parse topics JSON: {e}, using fallback")
            
            # Fallback to simple extraction
            return PostCallSummaryService._extract_topics_simple(transcript_text)
            
        except Exception as e:
            logger.warning(f"Error extracting topics with AI: {e}, using fallback")
            return PostCallSummaryService._extract_topics_simple(transcript_text)

    @staticmethod
    def _extract_topics_simple(transcript_text: str) -> List[str]:
        """Simple keyword-based topic extraction (fallback)."""
        topics = []
        topic_keywords = {
            'documents': ['document', 'upload', 'file', 'paperwork', 'certificate', 'passport'],
            'eligibility': ['eligible', 'qualify', 'requirement', 'criteria', 'meet', 'satisfy'],
            'timeline': ['time', 'when', 'how long', 'duration', 'process', 'deadline'],
            'requirements': ['require', 'need', 'must', 'should', 'requirement'],
            'visa_type': ['visa', 'permit', 'status', 'category'],
            'financial': ['salary', 'income', 'savings', 'funds', 'money', 'financial'],
            'sponsor': ['sponsor', 'employer', 'company', 'job offer']
        }
        
        text_lower = transcript_text.lower()
        for topic, keywords in topic_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                if topic not in topics:
                    topics.append(topic)
        
        return topics if topics else ['general_information']

    @staticmethod
    def _extract_action_items_ai(transcript_text: str, call_session) -> List[str]:
        """Extract action items using AI."""
        try:
            system_message = get_action_items_extraction_system_message()
            user_prompt = get_action_items_extraction_user_prompt(transcript_text[:4000])

            response = PostCallSummaryService._call_llm_for_summary(
                system_message=system_message,
                user_prompt=user_prompt,
                temperature=0.2,
                max_tokens=400,
                response_format={"type": "json_object"}
            )
            
            if response.get('success') and response.get('content'):
                try:
                    content = response['content'].strip()
                    # Remove markdown code blocks if present
                    if content.startswith('```'):
                        lines = content.split('\n')
                        content = '\n'.join(lines[1:-1]) if len(lines) > 2 else content
                    if content.startswith('```json'):
                        lines = content.split('\n')
                        content = '\n'.join(lines[1:-1]) if len(lines) > 2 else content
                    
                    parsed = json.loads(content)
                    # Handle both object format {"action_items": [...]} and direct array format
                    if isinstance(parsed, dict) and 'action_items' in parsed:
                        actions = parsed['action_items']
                    elif isinstance(parsed, list):
                        actions = parsed
                    else:
                        actions = []
                    
                    if isinstance(actions, list):
                        return actions[:5]  # Limit to 5
                except (json.JSONDecodeError, ValueError) as e:
                    logger.warning(f"Failed to parse action items JSON: {e}, using fallback")
            
            # Fallback to simple extraction
            return PostCallSummaryService._extract_action_items_simple(transcript_text)
            
        except Exception as e:
            logger.warning(f"Error extracting action items with AI: {e}, using fallback")
            return PostCallSummaryService._extract_action_items_simple(transcript_text)

    @staticmethod
    def _extract_action_items_simple(transcript_text: str) -> List[str]:
        """Simple keyword-based action item extraction (fallback)."""
        action_items = []
        action_keywords = ['upload', 'submit', 'provide', 'complete', 'fill out', 'send', 'deliver']
        
        lines = transcript_text.split('\n')
        for line in lines:
            text_lower = line.lower()
            if any(keyword in text_lower for keyword in action_keywords):
                # Extract the action item (clean up the line)
                action = line.replace('AI:', '').replace('User:', '').strip()
                if len(action) > 20 and len(action) < 200:  # Reasonable length
                    action_items.append(action)
                    if len(action_items) >= 5:
                        break
        
        return action_items

    @staticmethod
    def _extract_missing_documents(call_session, transcripts) -> List[str]:
        """Extract missing documents from context bundle and transcript."""
        missing_docs = []
        
        # Check context bundle for missing documents
        if call_session.context_bundle:
            docs_summary = call_session.context_bundle.get('documents_summary', {})
            missing_docs = docs_summary.get('missing', [])
        
        # Also check transcript for document mentions
        transcript_text = PostCallSummaryService._build_transcript_text(transcripts)
        document_keywords = ['passport', 'visa', 'certificate', 'diploma', 'transcript', 
                            'bank statement', 'employment letter', 'sponsor letter']
        
        text_lower = transcript_text.lower()
        for doc_keyword in document_keywords:
            if doc_keyword in text_lower and doc_keyword not in missing_docs:
                # Check if it's mentioned as missing
                if any(word in text_lower for word in ['missing', 'need', 'require', 'provide', 'upload']):
                    if doc_keyword not in missing_docs:
                        missing_docs.append(doc_keyword)
        
        return missing_docs[:10]  # Limit to 10

    @staticmethod
    def _suggest_next_steps_ai(call_session, transcript_text: str, action_items: List[str], 
                               missing_documents: List[str]) -> List[str]:
        """Suggest next steps using AI."""
        try:
            system_message = get_next_steps_suggestion_system_message()
            call_duration_minutes = call_session.duration_seconds // 60 if call_session.duration_seconds else 0
            user_prompt = get_next_steps_suggestion_user_prompt(
                transcript_text[:2000],
                action_items,
                missing_documents,
                call_duration_minutes
            )

            response = PostCallSummaryService._call_llm_for_summary(
                system_message=system_message,
                user_prompt=user_prompt,
                temperature=0.3,
                max_tokens=400,
                response_format={"type": "json_object"}
            )
            
            if response.get('success') and response.get('content'):
                try:
                    content = response['content'].strip()
                    # Remove markdown code blocks if present
                    if content.startswith('```'):
                        lines = content.split('\n')
                        content = '\n'.join(lines[1:-1]) if len(lines) > 2 else content
                    if content.startswith('```json'):
                        lines = content.split('\n')
                        content = '\n'.join(lines[1:-1]) if len(lines) > 2 else content
                    
                    parsed = json.loads(content)
                    # Handle both object format {"next_steps": [...]} and direct array format
                    if isinstance(parsed, dict) and 'next_steps' in parsed:
                        steps = parsed['next_steps']
                    elif isinstance(parsed, list):
                        steps = parsed
                    else:
                        steps = []
                    
                    if isinstance(steps, list):
                        return steps[:5]  # Limit to 5
                except (json.JSONDecodeError, ValueError) as e:
                    logger.warning(f"Failed to parse next steps JSON: {e}, using fallback")
            
            # Fallback to simple suggestions
            return PostCallSummaryService._suggest_next_steps_simple(action_items, missing_documents)
            
        except Exception as e:
            logger.warning(f"Error suggesting next steps with AI: {e}, using fallback")
            return PostCallSummaryService._suggest_next_steps_simple(action_items, missing_documents)

    @staticmethod
    def _suggest_next_steps_simple(action_items: List[str], missing_documents: List[str]) -> List[str]:
        """Simple next steps suggestions (fallback)."""
        next_steps = []
        
        if missing_documents:
            next_steps.append(f"Upload missing documents: {', '.join(missing_documents[:3])}")
        
        if action_items:
            next_steps.append("Review and complete the action items identified during the call")
        
        next_steps.append("Review eligibility results in your case dashboard")
        next_steps.append("Consider requesting human review if you have specific questions")
        
        return next_steps[:5]

    @staticmethod
    def _generate_summary_text_ai(call_session, transcript_text: str, topics_discussed: List[str],
                                  action_items: List[str], missing_documents: List[str]) -> str:
        """Generate comprehensive summary text using AI."""
        try:
            system_message = get_summary_generation_system_message()
            call_duration_minutes = call_session.duration_seconds // 60 if call_session.duration_seconds else 0
            total_turns = len(transcript_text.split('User:')) + len(transcript_text.split('AI:'))
            
            user_prompt = get_summary_generation_user_prompt(
                transcript_text[:3000],
                topics_discussed,
                action_items,
                missing_documents,
                call_duration_minutes,
                total_turns
            )

            response = PostCallSummaryService._call_llm_for_summary(
                system_message=system_message,
                user_prompt=user_prompt,
                temperature=0.4,
                max_tokens=500,
                response_format=None  # No JSON format for free-form text
            )
            
            if response.get('success') and response.get('content'):
                summary = response['content'].strip()
                # Clean up any markdown formatting
                if summary.startswith('```'):
                    lines = summary.split('\n')
                    summary = '\n'.join(lines[1:-1]) if len(lines) > 2 else summary
                return summary
            
            # Fallback to simple summary
            return PostCallSummaryService._generate_summary_text_simple(
                call_session, topics_discussed, action_items, missing_documents
            )
            
        except Exception as e:
            logger.warning(f"Error generating summary text with AI: {e}, using fallback")
            return PostCallSummaryService._generate_summary_text_simple(
                call_session, topics_discussed, action_items, missing_documents
            )

    @staticmethod
    def _generate_summary_text_simple(call_session, topics_discussed: List[str],
                                     action_items: List[str], missing_documents: List[str]) -> str:
        """Simple summary text generation (fallback)."""
        duration_min = (call_session.duration_seconds or 0) // 60
        topics_str = ', '.join(topics_discussed) if topics_discussed else 'general information'
        
        summary_parts = [
            f"During this {duration_min}-minute call, we discussed your immigration case.",
            f"Topics covered included: {topics_str}."
        ]
        
        if action_items:
            summary_parts.append(f"{len(action_items)} action item(s) were identified for you to complete.")
        
        if missing_documents:
            summary_parts.append(f"{len(missing_documents)} document(s) are still needed for your case.")
        
        summary_parts.append("Please review the detailed action items and next steps below.")
        
        return " ".join(summary_parts)

    @staticmethod
    def _generate_fallback_summary(session_id: str) -> Optional[CallSummary]:
        """Generate a simple fallback summary when AI fails."""
        try:
            call_session = CallSessionSelector.get_by_id(session_id)
            if not call_session:
                return None
            
            transcripts = CallTranscriptSelector.get_by_call_session(call_session)
            if not transcripts.exists():
                return None
            
            transcripts = transcripts.order_by('turn_number')
            transcript_text = PostCallSummaryService._build_transcript_text(transcripts)
            
            # Use simple extraction methods
            key_questions = PostCallSummaryService._extract_key_questions_simple(transcript_text)
            topics_discussed = PostCallSummaryService._extract_topics_simple(transcript_text)
            action_items = PostCallSummaryService._extract_action_items_simple(transcript_text)
            missing_documents = PostCallSummaryService._extract_missing_documents(call_session, transcripts)
            suggested_next_steps = PostCallSummaryService._suggest_next_steps_simple(action_items, missing_documents)
            summary_text = PostCallSummaryService._generate_summary_text_simple(
                call_session, topics_discussed, action_items, missing_documents
            )
            
            summary = CallSummaryRepository.create_call_summary(
                call_session=call_session,
                summary_text=summary_text,
                total_turns=transcripts.count(),
                total_duration_seconds=call_session.duration_seconds or 0,
                key_questions=key_questions,
                action_items=action_items,
                missing_documents=missing_documents,
                suggested_next_steps=suggested_next_steps,
                topics_discussed=topics_discussed
            )
            
            # Link summary to call session (caller will handle this)
            # Note: attach_to_case_timeline is called separately by CallSessionService
            
            logger.info(f"Generated fallback summary for call session {session_id}")
            return summary
            
        except Exception as e:
            logger.error(f"Error generating fallback summary for session {session_id}: {e}", exc_info=True)
            return None

    @staticmethod
    def attach_to_case_timeline(summary_id: str, case_id: str) -> bool:
        """
        Attach summary to case timeline by creating a case status history entry.
        
        This creates an audit trail entry showing that a call summary was generated
        and attached to the case.
        """
        try:
            from ai_calls.selectors.call_summary_selector import CallSummarySelector
            from immigration_cases.selectors.case_selector import CaseSelector
            from immigration_cases.repositories.case_status_history_repository import CaseStatusHistoryRepository
            
            summary = CallSummarySelector.get_by_id(summary_id)
            case = CaseSelector.get_by_id(case_id)
            
            if not summary or not case:
                logger.error(f"Summary {summary_id} or case {case_id} not found")
                return False
            
            # Mark summary as attached
            CallSummaryRepository.update_call_summary(
                summary,
                attached_to_case=True
            )
            
            # Create case status history entry for the call summary
            # This adds the summary to the case timeline
            reason = (
                f"AI call summary generated. "
                f"Call duration: {summary.total_duration_seconds // 60} minutes, "
                f"Total turns: {summary.total_turns}. "
                f"Topics discussed: {', '.join(summary.topics_discussed[:3]) if summary.topics_discussed else 'N/A'}"
            )
            
            metadata = {
                'type': 'call_summary',
                'summary_id': str(summary.id),
                'call_session_id': str(summary.call_session.id),
                'topics_discussed': summary.topics_discussed,
                'action_items_count': len(summary.action_items),
                'missing_documents_count': len(summary.missing_documents),
                'created_at': summary.created_at.isoformat() if summary.created_at else None
            }
            
            # Create status history entry (status remains the same, but we log the event)
            CaseStatusHistoryRepository.create_status_history(
                case=case,
                previous_status=case.status,
                new_status=case.status,  # Status doesn't change, but we're logging the event
                changed_by=None,  # System-generated
                reason=reason,
                metadata=metadata
            )
            
            logger.info(f"Summary {summary_id} attached to case {case_id} timeline")
            return True
            
        except Exception as e:
            logger.error(f"Error attaching summary {summary_id} to case {case_id}: {e}", exc_info=True)
            return False
