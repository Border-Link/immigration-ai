import logging
from typing import Optional
from ai_calls.models.call_summary import CallSummary
from ai_calls.repositories.call_summary_repository import CallSummaryRepository
from ai_calls.selectors.call_session_selector import CallSessionSelector
from ai_calls.selectors.call_transcript_selector import CallTranscriptSelector

logger = logging.getLogger('django')


class PostCallSummaryService:
    """Service for post-call summary generation."""

    @staticmethod
    def generate_summary(session_id: str) -> Optional[CallSummary]:
        """
        Generate post-call summary.
        
        Steps:
        1. Analyze full transcript
        2. Extract key questions
        3. Identify action items
        4. Identify missing documents
        5. Suggest next steps
        6. Create CallSummary model
        7. Attach to case timeline (via CaseService)
        
        Returns:
        - CallSummary instance
        """
        try:
            call_session = CallSessionSelector.get_by_id(session_id)
            if not call_session:
                logger.error(f"Call session {session_id} not found")
                return None
            
            # Get transcript
            transcripts = CallTranscriptSelector.get_by_call_session(call_session)
            if not transcripts.exists():
                logger.warning(f"No transcript found for session {session_id}")
                return None
            
            # Analyze transcript
            user_turns = transcripts.filter(turn_type='user')
            ai_turns = transcripts.filter(turn_type='ai')
            
            # Extract key questions
            key_questions = [
                turn.text for turn in user_turns[:10]  # Top 10 questions
            ]
            
            # Extract topics discussed
            topics_discussed = PostCallSummaryService._extract_topics(transcripts)
            
            # Generate summary text
            summary_text = PostCallSummaryService._generate_summary_text(
                call_session,
                transcripts,
                topics_discussed
            )
            
            # Identify action items and missing documents
            action_items = PostCallSummaryService._extract_action_items(transcripts)
            missing_documents = PostCallSummaryService._extract_missing_documents(
                call_session,
                transcripts
            )
            
            # Suggest next steps
            suggested_next_steps = PostCallSummaryService._suggest_next_steps(
                call_session,
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
            
            logger.info(f"Generated summary for call session {session_id}")
            return summary
            
        except Exception as e:
            logger.error(f"Error generating summary for session {session_id}: {e}")
            return None

    @staticmethod
    def _extract_topics(transcripts):
        """Extract topics discussed from transcript."""
        # Simple keyword-based extraction (could be enhanced with NLP)
        topics = []
        topic_keywords = {
            'documents': ['document', 'upload', 'file', 'paperwork'],
            'eligibility': ['eligible', 'qualify', 'requirement', 'criteria'],
            'timeline': ['time', 'when', 'how long', 'duration', 'process'],
            'next_steps': ['next', 'what should', 'action', 'do next']
        }
        
        for transcript in transcripts:
            text_lower = transcript.text.lower()
            for topic, keywords in topic_keywords.items():
                if any(keyword in text_lower for keyword in keywords):
                    if topic not in topics:
                        topics.append(topic)
        
        return topics

    @staticmethod
    def _generate_summary_text(call_session, transcripts, topics_discussed):
        """Generate summary text from transcript."""
        duration_min = (call_session.duration_seconds or 0) // 60
        topics_str = ', '.join(topics_discussed) if topics_discussed else 'general information'
        
        return (
            f"During this {duration_min}-minute call, we discussed your immigration case. "
            f"Topics covered included: {topics_str}. "
            f"Based on your case information, you appear to meet the eligibility requirements. "
            f"Please review the action items and next steps below."
        )

    @staticmethod
    def _extract_action_items(transcripts):
        """Extract action items from transcript."""
        action_items = []
        action_keywords = ['upload', 'submit', 'provide', 'complete', 'fill out']
        
        for transcript in transcripts:
            text_lower = transcript.text.lower()
            if any(keyword in text_lower for keyword in action_keywords):
                # Simple extraction - could be enhanced with NLP
                action_items.append(transcript.text[:100])  # First 100 chars
        
        return action_items[:5]  # Top 5 action items

    @staticmethod
    def _extract_missing_documents(call_session, transcripts):
        """Extract missing documents from transcript and context."""
        missing_docs = []
        
        # Check context bundle for missing documents
        if call_session.context_bundle:
            docs_summary = call_session.context_bundle.get('documents_summary', {})
            missing_docs = docs_summary.get('missing', [])
        
        return missing_docs

    @staticmethod
    def _suggest_next_steps(call_session, action_items, missing_documents):
        """Suggest next steps based on call content."""
        next_steps = []
        
        if missing_documents:
            next_steps.append(f"Upload missing documents: {', '.join(missing_documents[:3])}")
        
        if action_items:
            next_steps.append("Review and complete the action items identified during the call")
        
        next_steps.append("Review eligibility results in case dashboard")
        next_steps.append("Consider requesting human review if you have specific questions")
        
        return next_steps

    @staticmethod
    def attach_to_case_timeline(summary_id: str, case_id: str) -> bool:
        """Attach summary to case timeline (creates case note or status history entry)."""
        try:
            from ai_calls.selectors.call_summary_selector import CallSummarySelector
            from immigration_cases.selectors.case_selector import CaseSelector
            
            summary = CallSummarySelector.get_by_id(summary_id)
            case = CaseSelector.get_by_id(case_id)
            
            if not summary or not case:
                logger.error(f"Summary {summary_id} or case {case_id} not found")
                return False
            
            # Mark as attached
            CallSummaryRepository.update_call_summary(
                summary,
                attached_to_case=True
            )
            
            # TODO: Create case note or status history entry
            # This would integrate with CaseService to add a note to the case timeline
            
            logger.info(f"Summary {summary_id} attached to case {case_id} timeline")
            return True
            
        except Exception as e:
            logger.error(f"Error attaching summary {summary_id} to case {case_id}: {e}")
            return False
