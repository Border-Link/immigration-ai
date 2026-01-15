"""
Cost tracking utilities for LLM API calls.

Tracks token usage and calculates costs based on model pricing.
"""

import logging
from typing import Dict, Optional
from decimal import Decimal
from django.conf import settings

logger = logging.getLogger('django')

# Model pricing per 1K tokens (as of 2024)
# Pricing: input tokens / output tokens
MODEL_PRICING = {
    'gpt-4-turbo-preview': {
        'input': Decimal('0.010'),  # $0.01 per 1K input tokens
        'output': Decimal('0.030'),  # $0.03 per 1K output tokens
    },
    'gpt-4': {
        'input': Decimal('0.030'),  # $0.03 per 1K input tokens
        'output': Decimal('0.060'),  # $0.06 per 1K output tokens
    },
    'gpt-4-turbo': {
        'input': Decimal('0.010'),
        'output': Decimal('0.030'),
    },
    'gpt-3.5-turbo': {
        'input': Decimal('0.0015'),
        'output': Decimal('0.002'),
    },
}

# Default pricing if model not found
DEFAULT_PRICING = {
    'input': Decimal('0.010'),
    'output': Decimal('0.030'),
}


def calculate_cost(
    model: str,
    prompt_tokens: int,
    completion_tokens: int
) -> Decimal:
    """
    Calculate cost for LLM API call.
    
    Args:
        model: Model name
        prompt_tokens: Number of input tokens
        completion_tokens: Number of output tokens
        
    Returns:
        Total cost in USD as Decimal
    """
    pricing = MODEL_PRICING.get(model, DEFAULT_PRICING)
    
    input_cost = (Decimal(prompt_tokens) / 1000) * pricing['input']
    output_cost = (Decimal(completion_tokens) / 1000) * pricing['output']
    
    total_cost = input_cost + output_cost
    
    return total_cost


def track_usage(
    model: str,
    usage: Dict[str, int],
    document_version_id: Optional[str] = None
) -> Dict[str, any]:
    """
    Track LLM usage and calculate cost.
    
    Args:
        model: Model name used
        usage: Dict with 'prompt_tokens', 'completion_tokens', 'total_tokens'
        document_version_id: Optional document version ID for tracking
        
    Returns:
        Dict with 'tokens_used', 'estimated_cost', 'model'
    """
    prompt_tokens = usage.get('prompt_tokens', 0)
    completion_tokens = usage.get('completion_tokens', 0)
    total_tokens = usage.get('total_tokens', 0)
    
    estimated_cost = calculate_cost(model, prompt_tokens, completion_tokens)
    # Keep the value compatible with ParsedRule.estimated_cost (decimal_places=6).
    estimated_cost_float = round(float(estimated_cost), 6)
    
    result = {
        'tokens_used': total_tokens,
        'estimated_cost': estimated_cost_float,
        'model': model,
        'prompt_tokens': prompt_tokens,
        'completion_tokens': completion_tokens,
    }
    
    # Log cost tracking
    if getattr(settings, "APP_ENV", None) != "test":
        logger.info(
            f"LLM usage tracked: model={model}, tokens={total_tokens}, "
            f"cost=${estimated_cost:.6f}, document_version={document_version_id}"
        )
    
    # Check for cost alerts (if configured)
    cost_threshold = getattr(settings, 'LLM_COST_ALERT_THRESHOLD', None)
    if cost_threshold and estimated_cost > Decimal(str(cost_threshold)):
        if getattr(settings, "APP_ENV", None) != "test":
            logger.warning(
                f"High LLM cost alert: ${estimated_cost:.6f} exceeds threshold "
                f"${cost_threshold} for model {model}"
            )
    
    return result
