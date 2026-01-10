"""
Rule Version Conflict Detection Service

Detects overlapping rule versions and conflicts before creation.
"""
import logging
from typing import List, Dict, Optional, Tuple
from datetime import datetime
from django.utils import timezone
from django.db.models import Q
from rules_knowledge.models.visa_rule_version import VisaRuleVersion
from rules_knowledge.models.visa_type import VisaType
from rules_knowledge.selectors.visa_rule_version_selector import VisaRuleVersionSelector

logger = logging.getLogger('django')


class RuleVersionConflictService:
    """Service for detecting rule version conflicts."""
    
    @staticmethod
    def detect_conflicts(
        visa_type_id: str,
        effective_from: datetime,
        effective_to: Optional[datetime] = None
    ) -> List[Dict[str, any]]:
        """
        Detect overlapping rule versions for a visa type.
        
        Args:
            visa_type_id: UUID of visa type
            effective_from: Proposed effective_from date
            effective_to: Proposed effective_to date (None means current/ongoing)
            
        Returns:
            List of conflicting rule versions with details:
            [
                {
                    'rule_version_id': str,
                    'effective_from': datetime,
                    'effective_to': datetime or None,
                    'is_published': bool,
                    'conflict_type': 'overlap' | 'contains' | 'contained_by'
                }
            ]
        """
        conflicts = []
        
        try:
            # Get all rule versions for this visa type (excluding soft deleted)
            all_versions = VisaRuleVersion.objects.filter(
                visa_type_id=visa_type_id,
                is_deleted=False
            )
            
            for version in all_versions:
                conflict_type = RuleVersionConflictService._check_overlap(
                    version.effective_from,
                    version.effective_to,
                    effective_from,
                    effective_to
                )
                
                if conflict_type:
                    conflicts.append({
                        'rule_version_id': str(version.id),
                        'effective_from': version.effective_from,
                        'effective_to': version.effective_to,
                        'is_published': version.is_published,
                        'conflict_type': conflict_type,
                        'visa_type_name': version.visa_type.name
                    })
            
            return conflicts
            
        except Exception as e:
            logger.error(f"Error detecting rule version conflicts: {e}", exc_info=True)
            return []
    
    @staticmethod
    def _check_overlap(
        existing_from: datetime,
        existing_to: Optional[datetime],
        new_from: datetime,
        new_to: Optional[datetime]
    ) -> Optional[str]:
        """
        Check if two date ranges overlap.
        
        Returns:
            Conflict type: 'overlap', 'contains', 'contained_by', or None
        """
        # Case 1: New range is completely before existing range
        if new_to and new_to < existing_from:
            return None
        
        # Case 2: New range is completely after existing range
        if existing_to and new_from > existing_to:
            return None
        
        # Case 3: New range contains existing range
        if (not new_to or new_to >= (existing_to or timezone.now())) and new_from <= existing_from:
            return 'contains'
        
        # Case 4: New range is contained by existing range
        if (not existing_to or existing_to >= (new_to or timezone.now())) and existing_from <= new_from:
            return 'contained_by'
        
        # Case 5: Overlap (partial)
        return 'overlap'
    
    @staticmethod
    def can_create_version(
        visa_type_id: str,
        effective_from: datetime,
        effective_to: Optional[datetime] = None,
        allow_overlap_with_unpublished: bool = False
    ) -> Tuple[bool, List[Dict[str, any]]]:
        """
        Check if a new rule version can be created without conflicts.
        
        Args:
            visa_type_id: UUID of visa type
            effective_from: Proposed effective_from date
            effective_to: Proposed effective_to date
            allow_overlap_with_unpublished: Allow overlaps with unpublished versions
            
        Returns:
            Tuple of (can_create, conflicts)
        """
        conflicts = RuleVersionConflictService.detect_conflicts(
            visa_type_id,
            effective_from,
            effective_to
        )
        
        # Filter out unpublished conflicts if allowed
        if allow_overlap_with_unpublished:
            conflicts = [c for c in conflicts if c['is_published']]
        
        can_create = len(conflicts) == 0
        return can_create, conflicts
    
    @staticmethod
    def get_gap_analysis(
        visa_type_id: str,
        start_date: datetime,
        end_date: Optional[datetime] = None
    ) -> Dict[str, any]:
        """
        Analyze gaps and overlaps in rule version coverage.
        
        Args:
            visa_type_id: UUID of visa type
            start_date: Start of analysis period
            end_date: End of analysis period (None means current time)
            
        Returns:
            Dict with gap analysis:
            {
                'gaps': [...],
                'overlaps': [...],
                'coverage_percentage': float
            }
        """
        if end_date is None:
            end_date = timezone.now()
        
        # Get all versions in the period
        versions = VisaRuleVersion.objects.filter(
            visa_type_id=visa_type_id,
            is_deleted=False,
            effective_from__lte=end_date
        ).filter(
            Q(effective_to__isnull=True) | Q(effective_to__gte=start_date)
        ).order_by('effective_from')
        
        gaps = []
        overlaps = []
        total_duration = (end_date - start_date).total_seconds()
        covered_duration = 0
        
        prev_end = start_date
        
        for version in versions:
            version_start = version.effective_from
            version_end = version.effective_to or end_date
            
            # Check for gap
            if version_start > prev_end:
                gaps.append({
                    'from': prev_end,
                    'to': version_start,
                    'duration_seconds': (version_start - prev_end).total_seconds()
                })
            
            # Check for overlap with previous
            if version_start < prev_end:
                overlaps.append({
                    'from': version_start,
                    'to': min(prev_end, version_end),
                    'duration_seconds': (min(prev_end, version_end) - version_start).total_seconds(),
                    'rule_version_id': str(version.id)
                })
            
            # Update covered duration
            covered_duration += (version_end - max(version_start, start_date)).total_seconds()
            prev_end = max(prev_end, version_end)
        
        # Check for gap at the end
        if prev_end < end_date:
            gaps.append({
                'from': prev_end,
                'to': end_date,
                'duration_seconds': (end_date - prev_end).total_seconds()
            })
        
        coverage_percentage = (covered_duration / total_duration * 100) if total_duration > 0 else 0.0
        
        return {
            'gaps': gaps,
            'overlaps': overlaps,
            'coverage_percentage': round(coverage_percentage, 2),
            'total_gaps': len(gaps),
            'total_overlaps': len(overlaps)
        }
