"""
User Management Tasks

Celery tasks for user management operations.
"""
from celery import shared_task
import logging
from main_system.utils.tasks_base import BaseTaskWithMeta
from users_access.services.user_service import UserService

logger = logging.getLogger('django')


@shared_task(bind=True, base=BaseTaskWithMeta)
def schedule_user_unsuspension_task(self, user_id: str):
    """
    Celery task to automatically unsuspend a user after suspension expiration.
    
    This task is scheduled when a user is suspended with a suspended_until date.
    
    Args:
        user_id: UUID of the user to unsuspend
    """
    try:
        logger.info(f"Executing automatic unsuspension for user {user_id}")
        
        user = UserService.get_by_id(user_id)
        if not user:
            logger.error(f"User {user_id} not found for unsuspension")
            return {'success': False, 'error': 'User not found'}
        
        # Check if user is still suspended
        if user.is_active:
            logger.info(f"User {user_id} is already active, no unsuspension needed")
            return {'success': True, 'message': 'User already active'}
        
        # Activate user
        updated_user = UserService.activate_user_by_id(user_id)
        if not updated_user:
            logger.error(f"Failed to unsuspend user {user_id}")
            return {'success': False, 'error': 'Failed to activate user'}
        
        logger.info(f"User {user_id} automatically unsuspended successfully")
        return {
            'success': True,
            'user_id': user_id,
            'message': 'User automatically unsuspended'
        }
        
    except Exception as e:
        logger.error(f"Error in automatic unsuspension task for user {user_id}: {e}", exc_info=True)
        raise self.retry(exc=e, countdown=300, max_retries=3)
