"""
AI Reasoning Service

Service for AI-assisted reasoning using RAG (Retrieval-Augmented Generation).
This service:
1. Retrieves relevant context using pgvector similarity search
2. Constructs prompts with context
3. Calls LLM API
4. Extracts citations and stores reasoning logs
"""
import logging
from typing import Dict, List, Optional, Any
from django.conf import settings
from ai_decisions.services.vector_db_service import PgVectorService
from ai_decisions.services.embedding_service import EmbeddingService
from ai_decisions.services.ai_reasoning_log_service import AIReasoningLogService
from ai_decisions.services.ai_citation_service import AICitationService

logger = logging.getLogger('django')


class AIReasoningService:
    """
    Service for AI reasoning with RAG (Retrieval-Augmented Generation).
    
    This service implements the AI reasoning workflow from implementation.md Section 6.3:
    1. Retrieve relevant context using pgvector similarity search
    2. Construct AI prompt
    3. Call LLM (OpenAI/Anthropic)
    4. Store reasoning & citations
    
    Note: Uses pgvector (PostgreSQL extension) for vector similarity search.
    No separate vector database is required.
    """

    @staticmethod
    def retrieve_context(
        case_facts: Dict[str, Any],
        visa_type_id: Optional[str] = None,
        visa_code: Optional[str] = None,
        jurisdiction: Optional[str] = None,
        limit: int = 5,
        similarity_threshold: float = 0.7
    ) -> List[Dict[str, Any]]:
        """
        Step 1: Retrieve relevant context using pgvector similarity search.
        
        Uses pgvector (PostgreSQL extension) to perform cosine similarity search
        on document chunk embeddings stored in PostgreSQL.
        
        Args:
            case_facts: Dictionary of case facts
            visa_type_id: Optional visa type ID for filtering
            visa_code: Optional visa code for metadata filtering
            jurisdiction: Optional jurisdiction for filtering
            limit: Maximum number of context chunks to retrieve
            similarity_threshold: Minimum similarity score (0-1)
            
        Returns:
            List of context dicts with 'text', 'source', 'metadata', 'similarity'
        """
        try:
            # Construct query text from case facts
            query_text = AIReasoningService._construct_query(case_facts)
            
            # Generate query embedding
            query_embedding = EmbeddingService.generate_embedding(query_text)
            if not query_embedding:
                logger.error("Failed to generate query embedding")
                return []
            
            # Build filters
            filters = {}
            if visa_code:
                filters['visa_code'] = visa_code
            if jurisdiction:
                filters['jurisdiction'] = jurisdiction
            
            # Search similar chunks using pgvector
            chunks = PgVectorService.search_similar(
                query_embedding=query_embedding,
                limit=limit,
                filters=filters,
                similarity_threshold=similarity_threshold
            )
            
            # Format context
            context = []
            for chunk in chunks:
                # Calculate similarity from distance
                # distance = 0 means similarity = 1.0
                # distance = 2 means similarity = 0.0
                distance = getattr(chunk, 'distance', None)
                if distance is not None:
                    similarity = 1.0 - (distance / 2.0)
                else:
                    similarity = 0.8  # Default if distance not available
                
                context.append({
                    'text': chunk.chunk_text,
                    'source': chunk.document_version.source_document.source_url,
                    'metadata': chunk.metadata,
                    'similarity': similarity,
                    'chunk_id': str(chunk.id)
                })
            
            logger.info(f"Retrieved {len(context)} context chunks for reasoning")
            return context
            
        except Exception as e:
            logger.error(f"Error retrieving context: {e}", exc_info=True)
            return []

    @staticmethod
    def _construct_query(case_facts: Dict[str, Any]) -> str:
        """
        Construct query text from case facts for embedding generation.
        
        Args:
            case_facts: Dictionary of case facts
            
        Returns:
            Query text string
        """
        # Build query from key facts
        query_parts = []
        
        # Add visa type if available
        if 'visa_type' in case_facts:
            query_parts.append(f"visa type: {case_facts['visa_type']}")
        
        # Add key eligibility factors
        key_fields = ['salary', 'age', 'education', 'work_experience', 'language_proficiency', 
                     'sponsor', 'job_offer', 'country', 'nationality']
        
        for field in key_fields:
            if field in case_facts and case_facts[field]:
                query_parts.append(f"{field}: {case_facts[field]}")
        
        # Add any other relevant facts
        for key, value in case_facts.items():
            if key not in key_fields and key != 'visa_type' and value:
                if isinstance(value, (str, int, float)):
                    query_parts.append(f"{key}: {value}")
        
        query_text = " ".join(query_parts)
        
        # If no facts, use generic query
        if not query_text.strip():
            query_text = "immigration eligibility requirements"
        
        return query_text

    @staticmethod
    def construct_prompt(
        case_facts: Dict[str, Any],
        rule_results: Optional[Dict[str, Any]] = None,
        context_chunks: List[Dict[str, Any]] = None
    ) -> str:
        """
        Step 2: Construct AI prompt with context.
        
        Args:
            case_facts: Dictionary of case facts
            rule_results: Optional rule engine evaluation results
            context_chunks: Optional retrieved context chunks
            
        Returns:
            Formatted prompt string
        """
        prompt_parts = []
        
        # System instruction
        prompt_parts.append(
            "You are an immigration eligibility advisor. Analyze the case facts and provide "
            "a reasoned assessment of eligibility based on the provided context."
        )
        
        # Context section
        if context_chunks:
            prompt_parts.append("\n## Relevant Context:")
            for i, chunk in enumerate(context_chunks, 1):
                prompt_parts.append(f"\n### Context {i} (Similarity: {chunk.get('similarity', 0):.2f}):")
                prompt_parts.append(chunk['text'])
                if chunk.get('source'):
                    prompt_parts.append(f"\nSource: {chunk['source']}")
        
        # Rule engine results
        if rule_results:
            prompt_parts.append("\n## Rule Engine Evaluation:")
            prompt_parts.append(f"Overall Outcome: {rule_results.get('outcome', 'unknown')}")
            prompt_parts.append(f"Confidence: {rule_results.get('confidence', 0):.2f}")
            
            requirements = rule_results.get('requirements', [])
            if requirements:
                prompt_parts.append("\nRequirement Results:")
                for req in requirements:
                    status = req.get('status', 'unknown')
                    desc = req.get('description', 'N/A')
                    prompt_parts.append(f"- {desc}: {status}")
        
        # Case facts
        prompt_parts.append("\n## Case Facts:")
        for key, value in case_facts.items():
            prompt_parts.append(f"- {key}: {value}")
        
        # Instruction
        prompt_parts.append(
            "\n## Instruction:\n"
            "Based on the context, rule engine results, and case facts, provide:\n"
            "1. A clear eligibility assessment (likely/possible/unlikely)\n"
            "2. Key factors supporting your assessment\n"
            "3. Any concerns or missing information\n"
            "4. Recommendations for the applicant\n\n"
            "Cite specific context sources when referencing information."
        )
        
        return "\n".join(prompt_parts)

    @staticmethod
    def call_llm(prompt: str, model: str = "gpt-4", temperature: float = 0.3) -> Dict[str, Any]:
        """
        Step 3: Call LLM API (OpenAI/Anthropic).
        
        Args:
            prompt: Formatted prompt string
            model: Model name (default: gpt-4)
            temperature: Sampling temperature (default: 0.3 for deterministic)
            
        Returns:
            Dict with 'response', 'model', 'tokens_used', 'citations'
        """
        try:
            # Import OpenAI client
            try:
                from openai import OpenAI
            except ImportError:
                logger.error("OpenAI package not installed. Install with: pip install openai")
                raise ImportError("OpenAI package required for LLM calls")
            
            # Get API key from settings
            api_key = getattr(settings, 'OPENAI_API_KEY', None)
            if not api_key:
                logger.error("OPENAI_API_KEY not set in settings")
                raise ValueError("OPENAI_API_KEY must be set in settings")
            
            client = OpenAI(api_key=api_key)
            
            # Call LLM
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are a helpful immigration eligibility advisor."},
                    {"role": "user", "content": prompt}
                ],
                temperature=temperature,
                max_tokens=2000
            )
            
            # Extract response
            llm_response = response.choices[0].message.content
            tokens_used = response.usage.total_tokens if response.usage else None
            
            # Extract citations from response
            citations = AIReasoningService._extract_citations(llm_response)
            
            logger.info(f"LLM call completed: {tokens_used} tokens used, {len(citations)} citations")
            
            return {
                'response': llm_response,
                'model': model,
                'tokens_used': tokens_used,
                'citations': citations
            }
            
        except Exception as e:
            logger.error(f"Error calling LLM: {e}", exc_info=True)
            raise

    @staticmethod
    def _extract_citations(response_text: str) -> List[Dict[str, Any]]:
        """
        Extract citations from LLM response.
        
        Looks for patterns like:
        - "Source: [URL]"
        - "According to [source]"
        - References to context chunks
        
        Args:
            response_text: LLM response text
            
        Returns:
            List of citation dicts
        """
        citations = []
        
        # Simple pattern matching for now
        # Can be enhanced with more sophisticated parsing
        import re
        
        # Look for URLs
        url_pattern = r'https?://[^\s\)]+'
        urls = re.findall(url_pattern, response_text)
        for url in urls:
            citations.append({
                'type': 'url',
                'reference': url,
                'excerpt': None
            })
        
        # Look for context references
        context_pattern = r'Context\s+(\d+)'
        context_refs = re.findall(context_pattern, response_text, re.IGNORECASE)
        for ref in context_refs:
            citations.append({
                'type': 'context',
                'reference': f"Context {ref}",
                'excerpt': None
            })
        
        return citations

    @staticmethod
    def run_ai_reasoning(
        case_id: str,
        case_facts: Dict[str, Any],
        rule_results: Optional[Dict[str, Any]] = None,
        visa_type_id: Optional[str] = None,
        visa_code: Optional[str] = None,
        jurisdiction: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Main method: Run complete AI reasoning workflow.
        
        This orchestrates:
        1. Retrieve context (vector search)
        2. Construct prompt
        3. Call LLM
        4. Store reasoning log and citations
        
        Args:
            case_id: UUID of the case
            case_facts: Dictionary of case facts
            rule_results: Optional rule engine evaluation results
            visa_type_id: Optional visa type ID
            visa_code: Optional visa code for filtering
            jurisdiction: Optional jurisdiction for filtering
            
        Returns:
            Dict with reasoning results:
            {
                'success': bool,
                'response': str,
                'context_chunks': List[Dict],
                'citations': List[Dict],
                'reasoning_log_id': str
            }
        """
        try:
            # Step 1: Retrieve context
            context_chunks = AIReasoningService.retrieve_context(
                case_facts=case_facts,
                visa_code=visa_code,
                jurisdiction=jurisdiction,
                limit=5,
                similarity_threshold=0.7
            )
            
            # Step 2: Construct prompt
            prompt = AIReasoningService.construct_prompt(
                case_facts=case_facts,
                rule_results=rule_results,
                context_chunks=context_chunks
            )
            
            # Step 3: Call LLM
            llm_result = AIReasoningService.call_llm(prompt)
            
            # Step 4: Store reasoning log
            reasoning_log = AIReasoningLogService.create_reasoning_log(
                case_id=case_id,
                prompt=prompt,
                response=llm_result['response'],
                model_name=llm_result['model'],
                tokens_used=llm_result.get('tokens_used')
            )
            
            # Step 5: Store citations
            citations_created = 0
            if reasoning_log and context_chunks:
                # Map citations to document versions from context chunks
                # Context chunks contain document_version relationship
                from data_ingestion.models.document_chunk import DocumentChunk
                
                for chunk_data in context_chunks:
                    chunk_id = chunk_data.get('chunk_id')
                    if not chunk_id:
                        continue
                    
                    try:
                        # Get the DocumentChunk to access document_version
                        # Use select_related to avoid N+1 queries
                        document_chunk = DocumentChunk.objects.select_related(
                            'document_version'
                        ).get(id=chunk_id)
                        
                        if document_chunk and document_chunk.document_version:
                            # Create citation for this chunk
                            citation = AICitationService.create_citation(
                                reasoning_log_id=str(reasoning_log.id),
                                document_version_id=str(document_chunk.document_version.id),
                                excerpt=chunk_data.get('text', '')[:1000],  # Truncate excerpt to 1000 chars
                                relevance_score=chunk_data.get('similarity', 0.0)
                            )
                            if citation:
                                citations_created += 1
                    except DocumentChunk.DoesNotExist:
                        logger.warning(f"DocumentChunk {chunk_id} not found for citation")
                    except Exception as e:
                        logger.warning(f"Failed to create citation for chunk {chunk_id}: {e}", exc_info=True)
                
                # Also store citations extracted from LLM response (if any)
                if llm_result.get('citations'):
                    logger.info(
                        f"Found {len(llm_result['citations'])} citations in LLM response, "
                        f"stored {citations_created} citations from context chunks"
                    )
            
            logger.info(
                f"AI reasoning completed for case {case_id}: "
                f"{len(context_chunks)} context chunks, {citations_created} citations stored"
            )
            
            return {
                'success': True,
                'response': llm_result['response'],
                'context_chunks': context_chunks,
                'citations': llm_result.get('citations', []),
                'reasoning_log_id': str(reasoning_log.id) if reasoning_log else None,
                'model': llm_result['model'],
                'tokens_used': llm_result.get('tokens_used')
            }
            
        except Exception as e:
            logger.error(f"Error running AI reasoning for case {case_id}: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }

