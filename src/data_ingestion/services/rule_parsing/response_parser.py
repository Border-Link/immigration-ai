"""
Response parser for LLM rule extraction.

Handles parsing of LLM responses and extracting structured rules.
"""

import json
import re
import logging
from typing import Dict, List, Optional

logger = logging.getLogger('django')


class ResponseParser:
    """Parses LLM responses and extracts structured rules."""
    
    @staticmethod
    def parse_llm_response(llm_response: str) -> Optional[Dict]:
        """
        Parse LLM response and extract JSON.
        Handles cases where LLM wraps JSON in markdown or adds extra text.
        
        Args:
            llm_response: Raw LLM response text
            
        Returns:
            Parsed JSON dict or None if parsing fails
        """
        if not llm_response or not llm_response.strip():
            logger.error("Empty LLM response received")
            return None
        
        try:
            # Try direct JSON parsing first (most common case with response_format)
            return json.loads(llm_response.strip())
        except json.JSONDecodeError:
            pass
        
        # Try to extract JSON from markdown code blocks
        json_match = re.search(r'```(?:json)?\s*(\{.*?})\s*```', llm_response, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass
        
        # Try to find JSON object in the response using balanced braces
        start_pos = llm_response.find('{')
        if start_pos != -1:
            brace_count = 0
            for i in range(start_pos, len(llm_response)):
                if llm_response[i] == '{':
                    brace_count += 1
                elif llm_response[i] == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        json_candidate = llm_response[start_pos:i+1]
                        try:
                            return json.loads(json_candidate)
                        except json.JSONDecodeError:
                            break
        
        # Last resort: try regex
        json_match = re.search(r'\{[^{}]*(?:\{[^{}]*}[^{}]*)*}', llm_response, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(0))
            except json.JSONDecodeError:
                pass
        
        logger.error(f"Could not parse LLM response as JSON. Response preview: {llm_response[:500]}")
        return None
    
    @staticmethod
    def extract_rules_from_response(parsed_response: Dict) -> List[Dict]:
        """
        Extract rules from parsed LLM response.
        
        Args:
            parsed_response: Parsed JSON response from LLM
            
        Returns:
            List of rule dictionaries
        """
        rules = []
        
        if isinstance(parsed_response, dict):
            if 'requirements' in parsed_response:
                visa_code = parsed_response.get('visa_code', 'UNKNOWN')
                requirements = parsed_response.get('requirements', [])
                
                if not isinstance(requirements, list):
                    logger.warning("Requirements is not a list, converting")
                    requirements = [requirements] if requirements else []
                
                for req in requirements:
                    if isinstance(req, dict):
                        rule = {
                            'visa_code': visa_code,
                            'requirement_code': req.get('requirement_code', 'UNKNOWN'),
                            'description': req.get('description', ''),
                            'condition_expression': req.get('condition_expression', {}),
                            'source_excerpt': req.get('source_excerpt', '')
                        }
                        rules.append(rule)
                    else:
                        logger.warning(f"Invalid requirement format: {req}")
            
            elif 'requirement_code' in parsed_response:
                rules.append({
                    'visa_code': parsed_response.get('visa_code', 'UNKNOWN'),
                    'requirement_code': parsed_response.get('requirement_code', 'UNKNOWN'),
                    'description': parsed_response.get('description', ''),
                    'condition_expression': parsed_response.get('condition_expression', {}),
                    'source_excerpt': parsed_response.get('source_excerpt', '')
                })
        
        if not rules:
            logger.warning(f"No rules extracted from response: {parsed_response}")
        
        return rules
