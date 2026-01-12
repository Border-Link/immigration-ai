## **2. Authentication Module**

* **User**: Register, login, reset password
* **Reviewer**: Login
* **Staff**: Login, create users
* **Super Admin**: Full user management (CRUD users, assign roles)

---

## **3. Case Management Module**

* **User**:

  * Create case
  * Submit facts
  * Retrieve own cases
* **Reviewer**:

  * Retrieve assigned cases
  * Add review notes
* **Staff**:

  * Retrieve all cases
  * Update case status (limited)
* **Super Admin**:

  * Full CRUD on all cases

---

## **4. Rule Engine Module**

* **User**: Run eligibility checks (read-only, cannot modify rules)
* **Reviewer**: Read-only (see rule outcomes)
* **Staff**: Create/edit rules (limited to staging, maybe)
* **Super Admin**: Full rule management (publish, archive, override)

---

## **5. Document Service Module**

* **User**:

  * Upload documents
  * View own documents
* **Reviewer**:

  * Access documents for assigned cases
  * Validate document classification
* **Staff**:

  * Access all documents
  * Delete/reclassify documents
* **Super Admin**:

  * Full access to all documents and storage settings

---

## **6. AI Reasoning Service Module**

* **User**: Trigger AI reasoning for own cases (read-only results)
* **Reviewer**: Access AI outputs for assigned cases
* **Staff**: View AI logs, cannot edit
* **Super Admin**: Full access to AI logs, LLM prompts, embeddings

---

## **7. Ingestion Service Module**

* **User**: No access
* **Reviewer**: No access
* **Staff**: Monitor ingestion status
* **Super Admin**: Full ingestion service management (scheduler, rule parsing, publishing)

---

## **8. Review Service Module**

* **User**: Request review (manual escalation)
* **Reviewer**:

  * Access assigned review tasks
  * Approve/reject/override
  * Add notes
* **Staff**: Monitor reviews
* **Super Admin**: Full review management, reassign reviewers, audit reviews

---

## **9. Admin Console Module**

* **User**: No access
* **Reviewer**: No access
* **Staff**: Limited admin tasks (e.g., audit logs, rule validation tasks)
* **Super Admin**: Full admin console access

---

## **10. Frontend Module**

* **User**: User portal
* **Reviewer**: Reviewer console
* **Staff**: Staff dashboard
* **Super Admin**: All dashboards

---

## **Django DRF Implementation Strategy**

1. **User model**:

   ```python
   class User(AbstractUser):
       ROLE_CHOICES = [
           ('user', 'User'),
           ('reviewer', 'Reviewer'),
           ('staff', 'Staff'),
           ('superadmin', 'Super Admin'),
       ]
       role = models.CharField(max_length=20, choices=ROLE_CHOICES)
   ```

2. **Custom DRF permissions per module**:

   ```python
   from rest_framework.permissions import BasePermission

   class IsSuperAdmin(BasePermission):
       def has_permission(self, request, view):
           return request.user.role == 'superadmin'

   class IsStaff(BasePermission):
       def has_permission(self, request, view):
           return request.user.role in ['staff', 'superadmin']

   class IsReviewer(BasePermission):
       def has_permission(self, request, view):
           return request.user.role in ['reviewer', 'staff', 'superadmin']

   class IsUser(BasePermission):
       def has_permission(self, request, view):
           return request.user.role in ['user', 'reviewer', 'staff', 'superadmin']
   ```

3. **Assign permissions to views** (example for Case Management):

   ```python
   from rest_framework import viewsets
   from .models import Case
   from .serializers import CaseSerializer
   from .permissions import IsUser, IsReviewer, IsStaff, IsSuperAdmin

   class CaseViewSet(viewsets.ModelViewSet):
       queryset = Case.objects.all()
       serializer_class = CaseSerializer

       def get_permissions(self):
           if self.action in ['create', 'retrieve']:
               permission_classes = [IsUser]
           elif self.action in ['update', 'partial_update']:
               permission_classes = [IsStaff|IsSuperAdmin]
           elif self.action == 'list':
               permission_classes = [IsStaff|IsSuperAdmin]
           else:
               permission_classes = [IsSuperAdmin]
           return [perm() for perm in permission_classes]
   ```
