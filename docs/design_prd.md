# Immigration Intelligence Platform
## Product Requirements Document (PRD) for Design

**Version:** 1.0  
**Date:** 2025  
**Audience:** Product Designers, UX Designers, UI Designers  
**Status:** Design-Ready Requirements

---

# Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [User Personas](#2-user-personas)
3. [System Overview](#3-system-overview)
4. [Part 1: Applicant Portal System](#part-1-applicant-portal-system)
5. [Part 2: Reviewer Console System](#part-2-reviewer-console-system)
6. [Part 3: Admin Console System](#part-3-admin-console-system)
7. [Shared Requirements](#7-shared-requirements)
8. [Success Metrics](#8-success-metrics)

---

# 1. Executive Summary

## 1.1 Product Overview

The Immigration Intelligence Platform is a compliance-aware AI system that helps immigration applicants understand 
their visa eligibility, prepare required documents, and make informed decisions. The platform provides 
**decision support** and **information interpretation**—not legal advice—through explainable 
AI and human-in-the-loop workflows.

## 1.2 Design Goals

- **Build Trust**: Transparent, explainable AI with source citations
- **Reduce Anxiety**: Clear guidance, confidence scores, risk indicators
- **Save Time**: Automated eligibility checks, document validation
- **Ensure Compliance**: Clear disclaimers, GDPR-compliant flows
- **Support Decision-Making**: Actionable recommendations, missing document detection

## 1.3 System Architecture

The platform consists of three distinct systems:
1. **Applicant Portal**: For immigration applicants to check eligibility and manage cases
2. **Reviewer Console**: For human immigration advisers to review cases
3. **Admin Console**: For platform administrators to manage rules and system

---

# 2. User Personas

## 2.1 Primary Persona: The Applicant

### Sarah - Skilled Worker Visa Applicant
- **Age**: 29
- **Location**: Nigeria
- **Occupation**: Software Engineer
- **Tech Comfort**: High
- **Goals**: 
  - Understand if she qualifies for UK Skilled Worker visa
  - Know what documents she needs
  - Get confidence in her application before submitting
- **Pain Points**:
  - Confused by complex immigration rules
  - Worried about missing documents
  - Uncertain about salary thresholds
  - Fear of application rejection
- **Needs**:
  - Clear, plain-English explanations
  - Step-by-step guidance
  - Source citations for trust
  - Confidence indicators

### Key Characteristics:
- **Anxious but motivated**: Wants to do things right
- **Detail-oriented**: Needs to understand every requirement
- **Time-conscious**: Wants quick answers but thorough information
- **Trust-sensitive**: Needs to see official sources

## 2.2 Secondary Persona: The Reviewer

### James - Immigration Adviser
- **Age**: 42
- **Role**: Licensed immigration adviser
- **Experience**: 8 years
- **Goals**:
  - Review cases efficiently
  - Provide accurate guidance
  - Maintain compliance
  - Handle edge cases
- **Pain Points**:
  - Too many cases to review
  - Need to verify AI recommendations
  - Must document decisions
  - Time pressure
- **Needs**:
  - Clear case summaries
  - Quick access to AI reasoning
  - Easy override mechanism
  - Audit trail visibility

### Key Characteristics:
- **Expert but busy**: Knows immigration law, needs efficiency
- **Accountability-focused**: Must document decisions
- **Quality-conscious**: Wants to catch AI errors
- **Compliance-aware**: Must follow OISC guidelines

## 2.3 Tertiary Persona: The Admin

### Maria - Platform Administrator
- **Age**: 35
- **Role**: System administrator
- **Goals**:
  - Manage rule updates
  - Monitor system health
  - Validate AI-extracted rules
  - Ensure data quality
- **Pain Points**:
  - Rule changes from government
  - Need to validate AI extractions
  - Monitor ingestion pipeline
  - Handle edge cases in rules
- **Needs**:
  - Rule validation interface
  - Change detection alerts
  - System monitoring dashboard
  - Audit log access

---

# 3. System Overview

## 3.1 Three-System Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   APPLICANT PORTAL                       │
│  - Case Management                                       │
│  - Eligibility Checks                                    │
│  - Document Upload                                       │
│  - Review Requests                                       │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│                  REVIEWER CONSOLE                        │
│  - Review Queue                                          │
│  - Case Review                                           │
│  - Decision Overrides                                    │
│  - Review History                                        │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│                   ADMIN CONSOLE                          │
│  - Rule Validation                                       │
│  - System Monitoring                                     │
│  - User Management                                       │
│  - Audit Logs                                            │
└─────────────────────────────────────────────────────────┘
```

## 3.2 User Access & Authentication

- **Separate Login Portals**: Each system has its own login
- **Role-Based Access**: Users can only access their assigned system
- **Single Sign-On (Future)**: Optional SSO for organizations

---

# Part 1: Applicant Portal System

## 1.1 System Purpose

The Applicant Portal enables immigration applicants to:
- Create and manage immigration cases
- Check eligibility for different visa types
- Upload and validate required documents
- Request human review when needed
- Track case progress

## 1.2 User Journey: Complete Eligibility Check

### Flow Diagram

```
1. Landing Page
   ↓
2. Sign Up / Login
   ↓
3. Create New Case
   - Select jurisdiction (UK)
   ↓
4. Onboarding
   - Consent & disclaimer
   - Profile setup (optional)
   ↓
5. Case Information Collection (Multi-Step)
   - Step 1: Basic Info (nationality, age, DOB, country of residence)
   - Step 2: Visa Interest (which visa types)
   - Step 3: Employment (salary, job title, sponsor name, has_sponsor)
   - Step 4: Financials (savings, dependants count)
   - Progress indicator visible
   ↓
6. Eligibility Check
   - Loading state with explanation
   - Processing time indicator
   ↓
7. Results Page
   - Outcome cards per visa type
   - Confidence scores
   - Key requirements met/missing
   - "Why" explanations
   - Source citations
   ↓
8. Document Checklist
   - Required documents list
   - Upload interface
   - Progress tracking
   ↓
9. Document Upload & Validation
   - Drag & drop upload
   - Auto-classification feedback
   - Validation results
   ↓
10. Optional: Request Human Review
    - Submit for review
    - Status tracking
    - Reviewer feedback
```

## 1.3 Information Architecture

```
Applicant Portal
├── Landing Page
├── Authentication
│   ├── Sign Up
│   ├── Login
│   └── Forgot Password
├── Dashboard
│   ├── Active Cases Overview
│   ├── Recent Activity
│   └── Quick Actions
├── Cases
│   ├── Create New Case
│   ├── Case List
│   └── Case Detail
│       ├── Overview Tab
│       ├── Eligibility Results Tab
│       ├── Documents Tab
│       └── Review Status Tab
├── Documents
│   ├── Document Checklist
│   ├── Upload Documents
│   └── Document Status
├── Help & Support
│   ├── FAQs
│   ├── Contact Support
│   └── Request Review
└── Account Settings
    ├── Profile
    ├── Privacy Settings
    └── Data Export (GDPR)
```

## 1.4 Feature Requirements

### 1.4.1 Case Management
**Priority**: P0 (Must Have)

**Functional Requirements**:
- Create new immigration case
- View all cases (active and archived)
- Edit case information (when status = draft)
- Delete case (with confirmation)
- Duplicate case (for trying different scenarios)
- Filter cases by status, visa type, date
- Sort cases by date, status, confidence score

**Screen Requirements**:
- **Case List Screen**:
  - Case cards showing: case ID/name, visa type, status badge, last updated date, confidence score (if evaluated)
  - "Create New Case" button (prominent)
  - Filter/sort controls
  - Empty state: "Create your first case to get started"
  - Quick actions on each card: View, Edit, Delete, Duplicate

- **Case Creation Screen**:
  - Jurisdiction selector (dropdown: UK, Canada, etc.)
  - "Create Case" button
  - Existing cases list (if any)
  - Quick start guide (optional tooltip)

- **Case Detail Screen**:
  - Tabbed interface:
    - **Overview Tab**: Case facts summary, status, timeline
    - **Eligibility Results Tab**: Results per visa type
    - **Documents Tab**: Document checklist and uploads
    - **Review Status Tab**: Review history and feedback
  - Edit button (only if status = draft)
  - "Run Eligibility Check" button (if facts updated)

### 1.4.2 Case Information Collection
**Priority**: P0 (Must Have)

**Functional Requirements**:
- Multi-step form to collect case facts
- Save progress (auto-save on blur, manual save)
- Field validation (real-time)
- Progress indicator
- Ability to go back to previous steps
- Help text for complex fields

**Screen Requirements**:
- **Multi-Step Form Screen**:
  - Progress indicator at top (Step X of Y)
  - Form fields per step:
    - **Step 1: Basic Info**
      - Nationality (dropdown/autocomplete)
      - Age (number input)
      - Date of Birth (date picker)
      - Country of Residence (dropdown)
    - **Step 2: Visa Interest**
      - Visa type checkboxes (Skilled Worker, Student, Family, etc.)
      - "Select All" option
    - **Step 3: Employment**
      - Salary (number input, currency selector)
      - Job Title (text input)
      - Has Sponsor (radio: Yes/No)
      - Sponsor Name (text input, conditional on has_sponsor = Yes)
    - **Step 4: Financials**
      - Savings Amount (number input, currency)
      - Number of Dependants (number input)
  - Navigation buttons:
    - "Back" button (disabled on step 1)
    - "Save & Continue" button
    - "Save & Exit" button
  - Field validation:
    - Required field indicators
    - Inline error messages
    - Success checkmarks (when valid)

### 1.4.3 Eligibility Check
**Priority**: P0 (Must Have)

**Functional Requirements**:
- Submit case facts for eligibility evaluation
- View eligibility results per visa type
- See confidence scores (0-100%)
- View "Why" explanations
- See source citations (clickable links to gov.uk)
- View missing requirements
- See risk flags
- Compare multiple visa types (if multiple selected)

**Screen Requirements**:
- **Eligibility Results Screen**:
  - Results summary section (overview)
  - Results cards per visa type:
    - Outcome badge (likely/possible/unlikely)
    - Confidence meter (visual indicator with percentage)
    - Key requirements checklist (✓ passed, ✗ failed, ? missing)
    - "View Details" expandable section
    - Citations section with clickable links
  - "Run Eligibility Check" button (if facts updated)
  - "Request Human Review" button (if low confidence < 60%)
  - Link to Document Checklist
  - Loading state during evaluation:
    - Progress indicator
    - Estimated time message
    - "This may take 30 seconds" message

- **Eligibility Detail View** (Expandable):
  - Full AI reasoning explanation
  - Rule evaluation breakdown:
    - Requirement name
    - Pass/fail indicator
    - Explanation
    - Facts used in evaluation
  - All citations list:
    - Source URL (clickable, opens in new tab)
    - Excerpt preview
    - Document version date
    - "View Source" button
  - Confidence breakdown (how confidence was calculated)
  - Risk flags list with explanations

### 1.4.4 Document Management
**Priority**: P0 (Must Have)

**Functional Requirements**:
- View document checklist (required vs optional)
- Upload documents (drag & drop or file picker)
- View document status (uploaded, verified, rejected)
- Delete documents (with confirmation)
- Download document checklist (PDF)
- See document validation results
- View uploaded documents
- Retry failed uploads

**Screen Requirements**:
- **Document Checklist Screen**:
  - Checklist view:
    - Document type name
    - Mandatory indicator (Required/Optional badge)
    - Status badge (Provided/Missing/Incomplete)
    - Upload button (if missing)
    - Progress percentage indicator
  - Upload interface:
    - Drag & drop zone (prominent)
    - File picker button (fallback)
    - File type indicator (PDF, JPG, PNG accepted)
    - File size limit indicator (10MB max)
    - Upload progress bar (during upload)
    - Success/error feedback messages
  - Document list (uploaded documents):
    - Thumbnail/icon preview
    - Document type name
    - Upload date
    - Validation status badge
    - Actions menu: View, Delete, Re-upload
  - "Download Checklist" button (PDF export)
  - Completion percentage indicator

- **Document Upload Modal**:
  - Drag & drop area
  - File picker button
  - File type and size validation
  - Upload progress indicator
  - Success confirmation
  - Error message with retry option

### 1.4.5 Human Review Request
**Priority**: P1 (Should Have)

**Functional Requirements**:
- Request human review button (when eligible)
- Add note/question with request
- View review status
- Receive reviewer feedback
- Track review progress
- Set priority (normal/urgent)

**Screen Requirements**:
- **Request Review Modal/Form**:
  - Text area for note/question (required)
  - Priority selector (radio: Normal/Urgent)
  - Estimated completion time display
  - "Submit Request" button
  - Cancel button

- **Review Status Indicator** (on Case Detail):
  - Status badge:
    - "Awaiting Assignment"
    - "In Progress"
    - "Completed"
  - Reviewer name (if assigned)
  - SLA deadline (if in progress)
  - Reviewer feedback section (when completed)

### 1.4.6 Explanation & Citations
**Priority**: P0 (Must Have)

**Functional Requirements**:
- View full AI reasoning (expandable)
- See all source citations
- Click citations to view source (opens in new tab)
- View rule evaluation details
- See confidence breakdown
- Understand why each requirement passed/failed

**Screen Requirements**:
- **Full Explanation Section** (Expandable):
  - "View Full Explanation" button/link
  - Expandable accordion or modal
  - Complete AI reasoning text
  - Structured breakdown of decision factors

- **Citations List**:
  - Citation cards showing:
    - Source URL (clickable, opens in new tab)
    - Excerpt preview (first 200 characters)
    - Document version date
    - "View Source" button
  - Grouped by relevance or visa type

- **Rule Evaluation Breakdown**:
  - Requirement cards:
    - Requirement name/code
    - Pass/fail indicator
    - Explanation text
    - Facts used (list)
    - Rule expression (if user wants technical details)

## 1.5 Screen Specifications

### Screen 1: Landing Page
**Purpose**: First impression, value proposition, call-to-action

**Required Elements**:
- Hero section with value proposition
- Key benefits (3-4 feature cards)
- How it works (3-step process visualization)
- Trust indicators (citations, compliance badges)
- Primary CTA: "Get Started" / "Check Eligibility"
- Footer: Legal disclaimers, privacy policy, terms of service

**Key Messages**:
- "Not Legal Advice" disclaimer (prominent)
- "Decision Support" positioning
- Trust and transparency emphasis

### Screen 2: Sign Up / Login
**Purpose**: User authentication

**Required Elements**:
- Email/password form
- "Forgot Password" link (on login)
- "Create Account" link (if on login page)
- Social login options (optional, future)
- Terms & Conditions checkbox (required)
- Privacy policy link
- "Already have account?" / "Don't have account?" toggle

**Validation**:
- Email format validation
- Password strength indicator
- Clear error messages
- Success confirmation

### Screen 3: Case Dashboard
**Purpose**: Overview of all user's cases

**Required Elements**:
- Case cards grid/list:
  - Case ID or name
  - Visa type(s)
  - Status badge
  - Last updated timestamp
  - Confidence score (if evaluated)
  - Quick actions: View, Edit, Delete
- "Create New Case" button (prominent)
- Filter controls:
  - Status filter (dropdown)
  - Visa type filter (multi-select)
  - Date range filter
- Sort options:
  - By date (newest/oldest)
  - By status
  - By confidence score
- Empty state (if no cases):
  - Illustration or icon
  - Message: "Create your first case to get started"
  - "Create Case" button

### Screen 4: Case Information Collection (Multi-Step Form)
**Purpose**: Collect all case facts

**Required Elements**:
- Progress indicator (top of page):
  - Step numbers (1, 2, 3, 4)
  - Current step highlighted
  - Completed steps marked
  - Progress bar
- Form fields (see Section 1.4.2 for details)
- Navigation:
  - "Back" button (disabled on step 1)
  - "Save & Continue" button
  - "Save & Exit" button (saves and returns to dashboard)
- Field validation:
  - Required field asterisk
  - Inline error messages
  - Success indicators
- Help text:
  - Info icons with tooltips
  - Contextual help links

### Screen 5: Eligibility Results
**Purpose**: Display eligibility outcomes

**Required Elements**:
- Results summary section:
  - Overview message
  - Number of visa types evaluated
  - Overall confidence indicator
- Results cards per visa type:
  - Visa type name
  - Outcome badge (likely/possible/unlikely)
  - Confidence meter (visual + percentage)
  - Key requirements checklist (top 3-5 requirements)
  - "View Details" expandable section
  - Citations section (top 3 citations)
- Action buttons:
  - "Run Eligibility Check Again" (if facts updated)
  - "Request Human Review" (if confidence < 60%)
  - "View Document Checklist"
- Comparison view (if multiple visa types):
  - Side-by-side comparison table
  - Highlight best option

### Screen 6: Document Checklist
**Purpose**: Show required documents and enable uploads

**Required Elements**:
- Checklist section:
  - Document type name
  - Mandatory indicator (Required/Optional)
  - Status badge (Provided/Missing/Incomplete)
  - Upload button (if missing)
  - Progress percentage
- Upload interface:
  - Drag & drop zone (large, prominent)
  - File picker button
  - Accepted file types indicator
  - File size limit (10MB)
  - Upload progress bar
- Document list (uploaded):
  - Thumbnail/icon
  - Document type
  - Upload date
  - Validation status
  - Actions: View, Delete
- "Download Checklist" button (PDF)

### Screen 7: Case Detail View
**Purpose**: Complete case information and management

**Required Elements**:
- Tabbed interface:
  - **Overview Tab**:
    - Case facts summary (key-value pairs)
    - Case status
    - Timeline of actions
    - Edit button (if draft)
  - **Eligibility Results Tab**:
    - All eligibility results
    - Full explanations
    - Citations
  - **Documents Tab**:
    - Document checklist
    - Uploaded documents
    - Upload interface
  - **Review Status Tab**:
    - Review request status
    - Reviewer feedback
    - Review history
- Action buttons:
  - "Edit Case" (if draft)
  - "Run Eligibility Check" (if facts updated)
  - "Request Review" (if eligible)

## 1.6 Interaction Patterns

### Form Interactions
- **Multi-Step Forms**: Progress indicator, save & continue, back navigation
- **Field Validation**: Real-time inline validation, clear error messages
- **Help Text**: Contextual help icons with tooltips
- **Auto-Save**: Save progress on blur, manual save option

### File Upload
- **Drag & Drop**: Visual drop zone with hover state
- **File Picker**: Fallback button for file selection
- **Progress Feedback**: Upload progress bar, success/error messages
- **Preview**: Thumbnail preview after upload

### Data Display
- **Cards**: Hover states, action buttons, status badges
- **Expandable Sections**: Accordion-style, smooth animations
- **Loading States**: Skeleton loaders, progress indicators
- **Empty States**: Helpful messages with CTAs

### Navigation
- **Breadcrumbs**: Show location in hierarchy
- **Tabs**: Clear active state, smooth transitions
- **Modals**: For confirmations, forms, detail views

## 1.7 Edge Cases & Error States

### Empty States
- **No Cases**: "Create your first case to get started"
- **No Documents**: "Upload your first document"
- **No Results**: "Run eligibility check to see results"

### Error States
- **Network Error**: "Connection lost. Please check your internet and try again."
- **Server Error**: "Something went wrong. Our team has been notified."
- **Validation Error**: "Please correct the errors below" (with field-specific errors)
- **File Upload Error**: "File upload failed. Please check file size and format."

### Loading States
- **Eligibility Check**: "Analyzing your case... This may take 30 seconds"
- **Document Processing**: "Processing document... Please wait"
- **Form Submission**: "Saving your information..."

### Partial Data States
- **Incomplete Case**: "Complete all steps to run eligibility check"
- **Missing Facts**: "Some information is missing. Please provide: [list]"
- **Low Confidence**: "Confidence is low. Consider requesting human review."

---

# Part 2: Reviewer Console System

## 2.1 System Purpose

The Reviewer Console enables licensed immigration advisers to:
- Review cases assigned for human review
- Verify AI recommendations
- Override AI decisions when needed
- Provide feedback to applicants
- Track review workload and SLA compliance

## 2.2 User Journey: Complete Review Flow

### Flow Diagram

```
1. Reviewer Dashboard
   - Assigned reviews list
   - SLA indicators
   - Priority flags
   ↓
2. Select Case to Review
   - Case summary card
   - Risk flags visible
   - AI confidence score
   ↓
3. Review Detail View
   - Case facts summary
   - AI eligibility results
   - Full AI reasoning (expandable)
   - Rule evaluation details
   - Uploaded documents
   - User notes/questions
   ↓
4. Reviewer Decision
   - Option A: Approve AI Decision
     → Mark complete, add note
   - Option B: Override Decision
     → Select new outcome, provide reason
   - Option C: Request More Info
     → Add note, notify user
   - Option D: Escalate
     → Reassign to senior reviewer
   ↓
5. Complete Review
   - Confirmation
   - Audit log entry
   - User notification sent
```

## 2.3 Information Architecture

```
Reviewer Console
├── Dashboard
│   ├── Review Queue Overview
│   ├── Metrics Cards
│   └── Quick Actions
├── Review Queue
│   ├── Assigned to Me
│   ├── Pending Assignment
│   └── Completed Reviews
├── Case Review
│   ├── Case Summary Tab
│   ├── AI Analysis Tab
│   ├── Documents Tab
│   └── History Tab
└── Settings
    ├── Notification Preferences
    └── Review History
```

## 2.4 Feature Requirements

### 2.4.1 Review Dashboard
**Priority**: P0 (Must Have)

**Functional Requirements**:
- View assigned reviews
- Filter by status (pending, in progress, completed)
- Sort by priority, SLA deadline, confidence score
- See review queue metrics
- Quick actions (start review, complete review)
- View overdue reviews
- See average completion time

**Screen Requirements**:
- **Reviewer Dashboard Screen**:
  - Metrics cards:
    - Total pending reviews
    - Assigned to me
    - Overdue reviews (with countdown)
    - Average completion time
  - Review cards list:
    - Case ID
    - Visa type
    - AI confidence score
    - Risk flags (badges)
    - SLA deadline (with countdown timer)
    - Time in queue
    - Quick action buttons: Start Review, View Details
  - Filters sidebar:
    - Status filter (dropdown)
    - Priority filter (dropdown)
    - Visa type filter (multi-select)
  - Sort options:
    - By SLA deadline (urgent first)
    - By confidence score
    - By date assigned

### 2.4.2 Case Review Interface
**Priority**: P0 (Must Have)

**Functional Requirements**:
- View complete case information
- See AI eligibility results
- View full AI reasoning
- See rule evaluation details
- View uploaded documents
- See user notes/questions
- Take review actions (approve, override, request info, escalate)
- Add review notes
- View review history

**Screen Requirements**:
- **Review Detail Screen**:
  - Tabbed interface:
    - **Tab 1: Case Summary**
      - Case facts (key-value pairs, organized by category)
      - User profile info (name, nationality, contact)
      - Case timeline (creation, updates, review requests)
    - **Tab 2: AI Analysis**
      - Eligibility results (all visa types)
      - Full AI reasoning (expandable)
      - Rule evaluation breakdown (per requirement)
      - Citations list (all sources)
      - Confidence breakdown (how calculated)
    - **Tab 3: Documents**
      - Document grid/list
      - Document viewer (click to view full document)
      - Validation results per document
      - Document status indicators
    - **Tab 4: History**
      - Previous reviews (if any)
      - Notes timeline
      - Override history
      - Status change history
  - Action panel (sticky, always visible):
    - "Approve AI Decision" button
    - "Override Decision" dropdown
    - "Request More Info" button
    - "Escalate" button
    - Notes text area
    - "Submit Review" button
  - Side-by-side comparison view:
    - AI outcome vs human decision (when override exists)
    - Confidence scores comparison
    - Reasoning comparison

### 2.4.3 Override Functionality
**Priority**: P0 (Must Have)

**Functional Requirements**:
- Override AI decision
- Select new outcome (likely/possible/unlikely)
- Provide reason for override (required)
- See override history
- View original AI result (preserved)
- Compare AI vs human decision

**Screen Requirements**:
- **Override Modal/Form**:
  - Outcome selector (radio buttons: likely/possible/unlikely)
  - Reason text area (required, minimum characters)
  - Preview of original AI result
  - Confirmation checkbox: "I understand this override will be logged"
  - "Submit Override" button
  - Cancel button

- **Override Indicator** (on results):
  - Badge: "Overridden by [Reviewer Name]"
  - Original outcome visible (strikethrough or muted)
  - New outcome prominent
  - Override reason visible (expandable)

- **Override History Timeline**:
  - All overrides listed chronologically
  - Reviewer name
  - Override reason
  - Timestamp
  - Original vs new outcome

### 2.4.4 Review Actions
**Priority**: P0 (Must Have)

**Functional Requirements**:
- Approve AI decision
- Override decision
- Request more information from user
- Escalate to senior reviewer
- Add review notes
- Complete review
- View review history

**Screen Requirements**:
- **Action Buttons** (in Review Detail):
  - "Approve" button:
    - Opens confirmation modal
    - Option to add note
    - "Confirm Approval" button
  - "Override" button:
    - Opens override form (see 2.4.3)
  - "Request Info" button:
    - Opens form:
      - Text area for information request
      - "Send Request" button
    - Updates case status to "awaiting_user_input"
  - "Escalate" button:
    - Opens escalation form:
      - Reason for escalation
      - Select senior reviewer (dropdown)
      - "Escalate" button

### 2.4.5 Review History & Audit Trail
**Priority**: P1 (Should Have)

**Functional Requirements**:
- View all reviews for a case
- See reviewer notes
- View override history
- Track status changes
- Export review history

**Screen Requirements**:
- **History Tab** (in Review Detail):
  - Timeline view:
    - Review creation
    - Reviewer assignment
    - Notes added
    - Overrides created
    - Review completion
  - Each entry shows:
    - Timestamp
    - Reviewer name
    - Action taken
    - Notes (if any)

## 2.5 Screen Specifications

### Screen 8: Reviewer Dashboard
**Purpose**: Review queue overview and management

**Required Elements**:
- Metrics cards row:
  - Total pending reviews
  - Assigned to me
  - Overdue reviews (with count)
  - Average completion time
- Review cards list:
  - Case ID
  - Visa type
  - AI confidence score (with indicator)
  - Risk flags (badges: low_confidence, rule_conflict, etc.)
  - SLA deadline (with countdown, color-coded)
  - Time in queue
  - Quick actions: Start Review, View Details
- Filters sidebar:
  - Status filter
  - Priority filter
  - Visa type filter
- Sort dropdown
- Empty state: "No reviews assigned"

### Screen 9: Review Detail View
**Purpose**: Complete case review interface

**Required Elements**:
- Tabbed interface (see 2.4.2 for tab details)
- Action panel (sticky):
  - All review action buttons
  - Notes text area
  - Submit button
- Case summary header:
  - Case ID
  - User name
  - Visa type
  - Current status
  - AI confidence score
- Comparison view (if override exists):
  - Side-by-side AI vs human
- Document viewer integration

## 2.6 Interaction Patterns

### Review Workflow
- **Quick Actions**: One-click actions for common decisions
- **Bulk Actions**: Select multiple reviews for batch operations (future)
- **Keyboard Shortcuts**: Quick navigation, approve/override shortcuts
- **Auto-Save Notes**: Save notes as reviewer types

### Data Display
- **Information Density**: Show all relevant info without overwhelming
- **Progressive Disclosure**: Expandable sections for detailed info
- **Comparison Views**: Side-by-side AI vs human decisions
- **Timeline Views**: Chronological history of actions

### Feedback
- **Confirmation Modals**: For all actions (approve, override, escalate)
- **Success Messages**: Toast notifications for completed actions
- **Error Handling**: Clear error messages with retry options

## 2.7 Edge Cases & Error States

### Empty States
- **No Reviews Assigned**: "No reviews assigned to you"
- **No Completed Reviews**: "You haven't completed any reviews yet"

### Error States
- **Case Not Found**: "Case not found or no longer available"
- **Review Already Completed**: "This review has already been completed"
- **Permission Denied**: "You don't have permission to review this case"

### Loading States
- **Loading Case Data**: "Loading case information..."
- **Submitting Review**: "Submitting your review..."

---

# Part 3: Admin Console System

## 3.1 System Purpose

The Admin Console enables platform administrators to:
- Validate AI-extracted immigration rules
- Monitor system health and performance
- Manage users and permissions
- View audit logs
- Manage data sources for ingestion

## 3.2 User Journey: Rule Validation Flow

### Flow Diagram

```
1. Admin Dashboard
   - System health metrics
   - Pending rule validations
   - Recent changes
   ↓
2. Rule Validation Queue
   - List of parsed rules awaiting approval
   - Change type indicators
   - Confidence scores
   ↓
3. Rule Validation Detail
   - Original source text
   - AI-extracted logic
   - Diff view (what changed)
   - Previous version comparison
   ↓
4. Admin Decision
   - Approve: Promote to production
   - Reject: Mark as rejected
   - Edit: Modify extracted logic
   ↓
5. Rule Published
   - Confirmation
   - Version history updated
   - Users notified (optional)
```

## 3.3 Information Architecture

```
Admin Console
├── Dashboard
│   ├── System Overview
│   ├── Health Metrics
│   └── Recent Activity
├── Rule Management
│   ├── Rule Validation Queue
│   ├── Active Rules
│   ├── Rule History
│   └── Data Sources
├── User Management
│   ├── Users List
│   ├── Reviewers
│   └── Permissions
└── Audit & Compliance
    ├── Audit Logs
    ├── Compliance Reports
    └── Data Exports
```

## 3.4 Feature Requirements

### 3.4.1 Rule Validation Interface
**Priority**: P1 (Should Have)

**Functional Requirements**:
- View pending rule validations
- See parsed rules with confidence scores
- Compare original text vs extracted logic
- View diff (what changed)
- Approve, reject, or edit rules
- See validation history
- Assign validations to reviewers
- Filter by change type, visa code, confidence

**Screen Requirements**:
- **Rule Validation Queue Screen**:
  - Validation queue table:
    - Rule ID
    - Visa code
    - Change type badge (requirement_change, fee_change, etc.)
    - Confidence score
    - Assigned reviewer
    - Created date
    - Actions: Review, Assign, Bulk Actions
  - Filters:
    - Status filter
    - Change type filter
    - Visa code filter
    - Confidence range filter
  - Search functionality
  - Sort options

- **Rule Validation Detail Screen**:
  - Split screen layout:
    - **Left Panel**: Original source text
      - Source URL
      - Document version date
      - Full text display
    - **Right Panel**: AI-extracted logic
      - Extracted requirements list
      - JSON Logic expressions
      - Confidence breakdown
  - Diff view (toggle):
    - Highlighted changes
    - Added/removed text
    - Changed values
  - Previous version comparison:
    - Side-by-side old vs new
    - Highlighted differences
    - Effective dates
  - Edit interface:
    - Editable JSON Logic expressions
    - Syntax validation
    - Preview of changes
  - Action buttons:
    - "Approve" button
    - "Reject" button
    - "Edit" button (opens edit mode)
    - "Save Changes" button
  - Reviewer notes section

### 3.4.2 System Monitoring
**Priority**: P2 (Nice to Have)

**Functional Requirements**:
- View system health metrics
- Monitor ingestion pipeline status
- See error rates
- View active cases count
- Monitor review queue metrics
- Track AI service status
- View performance metrics

**Screen Requirements**:
- **Admin Dashboard Screen**:
  - System health metrics cards:
    - Active cases count
    - Pending reviews count
    - Ingestion success rate
    - AI service status (up/down)
    - Error rate percentage
    - System uptime
  - Charts/graphs:
    - Cases over time (line chart)
    - Review completion time (bar chart)
    - Confidence score distribution (histogram)
    - Error rate over time
  - Alert indicators:
    - Failed ingestion sources (badge with count)
    - High error rates (warning badge)
    - SLA breaches (alert badge)
  - Recent activity feed:
    - Recent rule changes
    - Recent reviews
    - System events

### 3.4.3 User Management
**Priority**: P1 (Should Have)

**Functional Requirements**:
- View all users
- Manage user roles
- Activate/deactivate users
- View user activity
- Manage reviewer assignments
- View permissions

**Screen Requirements**:
- **User Management Screen**:
  - Users table:
    - User ID/Email
    - Name
    - Role
    - Status (active/inactive)
    - Last login
    - Actions: Edit, Deactivate, View Details
  - Filters:
    - Role filter
    - Status filter
  - "Add User" button
  - Bulk actions (activate/deactivate)

### 3.4.4 Data Source Management
**Priority**: P1 (Should Have)

**Functional Requirements**:
- View all data sources
- Add new data sources
- Edit data source configuration
- Activate/deactivate sources
- View ingestion history
- Monitor source health

**Screen Requirements**:
- **Data Sources Screen**:
  - Data sources table:
    - Source name
    - Base URL
    - Jurisdiction
    - Status (active/inactive)
    - Last fetched date
    - Success rate
    - Actions: Edit, Deactivate, View History
  - "Add Data Source" button
  - Source detail view:
    - Configuration
    - Ingestion history
    - Error log

### 3.4.5 Audit Logs
**Priority**: P1 (Should Have)

**Functional Requirements**:
- View audit logs
- Filter by actor, action, entity, date
- Export audit logs
- Search audit logs
- View detailed log entries

**Screen Requirements**:
- **Audit Logs Screen**:
  - Audit log table:
    - Timestamp
    - Actor (user name/ID)
    - Action
    - Entity type
    - Entity ID
    - Metadata (expandable)
  - Filters:
    - Date range picker
    - Actor filter
    - Action filter
    - Entity type filter
  - Search functionality
  - Export button (CSV/JSON)
  - Pagination

## 3.5 Screen Specifications

### Screen 10: Admin Dashboard
**Purpose**: System overview and health monitoring

**Required Elements**:
- System health metrics cards (see 3.4.2)
- Charts/graphs section
- Alert indicators
- Recent activity feed
- Quick actions:
  - "View Rule Queue"
  - "View Users"
  - "View Audit Logs"

### Screen 11: Rule Validation Queue
**Purpose**: Manage pending rule validations

**Required Elements**:
- Validation queue table (see 3.4.1)
- Filters sidebar
- Search bar
- Bulk actions toolbar
- "Assign Reviewer" button
- Empty state: "No pending validations"

### Screen 12: Rule Validation Detail
**Purpose**: Review and approve/reject rules

**Required Elements**:
- Split screen layout (see 3.4.1)
- Diff view toggle
- Edit interface
- Action buttons
- Version comparison
- Reviewer assignment

## 3.6 Interaction Patterns

### Rule Validation
- **Split Screen Comparison**: Side-by-side original vs extracted
- **Diff View**: Highlighted changes, toggle between views
- **Inline Editing**: Edit JSON Logic expressions directly
- **Bulk Actions**: Select multiple rules for batch approval/rejection

### Data Management
- **Table Views**: Sortable, filterable tables for data-heavy screens
- **Detail Drill-Down**: Click row to view details
- **Export Functionality**: Export data in various formats

### Monitoring
- **Real-Time Updates**: Auto-refresh for metrics
- **Alert Notifications**: Visual and/or audio alerts for critical issues
- **Historical Views**: Time-range selectors for charts

## 3.7 Edge Cases & Error States

### Empty States
- **No Pending Validations**: "No rules pending validation"
- **No Users**: "No users found"
- **No Audit Logs**: "No audit logs for selected filters"

### Error States
- **Rule Validation Failed**: "Could not validate rule. Please try again."
- **System Error**: "System error occurred. Please contact support."
- **Permission Denied**: "You don't have permission to perform this action"

### Loading States
- **Loading Rules**: "Loading rule validations..."
- **Processing Approval**: "Publishing rule to production..."

---

# 7. Shared Requirements

## 7.1 Authentication & Authorization

### Login/Logout
- Separate login portals for each system
- JWT token-based authentication
- Session management
- "Remember Me" option
- Password reset flow
- Account lockout after failed attempts

### Role-Based Access
- Applicants: Can only access Applicant Portal
- Reviewers: Can access Reviewer Console + own cases in Applicant Portal
- Admins: Can access Admin Console + all other systems

## 7.2 Design Principles

### Trust & Transparency
- **Show Sources**: Always display citations prominently
- **Explain AI**: Clear messaging about AI role and limitations
- **Show Confidence**: Visual confidence indicators
- **Disclaimers**: Clear "Not Legal Advice" messaging
- **Audit Trail**: Visible history of decisions

### Clarity & Simplicity
- **Plain Language**: Avoid legal jargon
- **Progressive Disclosure**: Show details on demand
- **Visual Hierarchy**: Important information prominent
- **Consistent Patterns**: Reuse interaction patterns
- **Clear CTAs**: Obvious next steps

### Empathy & Support
- **Reduce Anxiety**: Positive, supportive tone
- **Progress Indicators**: Show user progress
- **Help Available**: Easy access to help/support
- **Error Recovery**: Clear paths to fix errors
- **Celebrate Success**: Positive feedback for completed steps

### Compliance & Safety
- **Legal Disclaimers**: Prominent but not intrusive
- **Consent Flows**: Clear consent checkboxes
- **Privacy Controls**: Easy access to privacy settings
- **Data Transparency**: Show what data is collected
- **GDPR Compliance**: Right to erasure, data export

## 7.3 Accessibility Requirements

### WCAG 2.1 AA Compliance
- **Perceivable**: Text alternatives, adaptable content, distinguishable (4.5:1 contrast)
- **Operable**: Keyboard accessible, enough time, navigable
- **Understandable**: Readable, predictable, input assistance
- **Robust**: Compatible, valid HTML, proper ARIA labels

### Specific Requirements
- **Keyboard Navigation**: Full keyboard access, logical tab order, visible focus indicators
- **Screen Readers**: Proper ARIA labels, live regions, heading hierarchy
- **Visual Accessibility**: Color contrast, focus indicators, resizable text (up to 200%)
- **Cognitive Accessibility**: Clear language, consistent patterns, error prevention

## 7.4 Content Guidelines

### Tone of Voice
- **Professional but Approachable**: Not overly formal, but trustworthy
- **Clear and Direct**: Avoid jargon, use plain English
- **Supportive**: Empathetic to user's situation
- **Transparent**: Honest about limitations, clear about AI role

### Key Messages

**Disclaimers**:
- "This platform provides decision support and information interpretation, not legal advice."
- "AI recommendations are based on current immigration rules but may not cover all circumstances."
- "For regulated legal advice, please consult a qualified immigration adviser."

**Confidence Messages**:
- "Based on the information provided, you have a [X]% chance of meeting requirements."
- "This assessment is based on current rules as of [date]."
- "Rules may change. We recommend checking eligibility close to your application date."

**Error Messages**:
- "We couldn't process your request. Please try again or contact support."
- "Some information is missing. Please complete all required fields."
- "This document couldn't be processed. Please check the file and try again."

## 7.5 Common Interaction Patterns

### Forms
- **Multi-Step Forms**: Progress indicator, save & continue, back navigation
- **Field Validation**: Real-time inline validation, clear error messages
- **Help Text**: Contextual help icons with tooltips
- **Auto-Save**: Save progress automatically

### File Upload
- **Drag & Drop**: Visual drop zone with hover state
- **File Picker**: Fallback button
- **Progress**: Upload progress bar
- **Feedback**: Success/error messages

### Data Display
- **Cards**: Hover states, actions, status badges
- **Tables**: Sortable columns, filters, pagination
- **Expandable Sections**: Accordion-style, smooth animations
- **Loading States**: Skeleton loaders, progress indicators

### Navigation
- **Breadcrumbs**: Show location in hierarchy
- **Tabs**: Clear active state, smooth transitions
- **Modals**: For confirmations, forms, detail views

### Feedback
- **Loading States**: Skeleton loaders, progress bars, spinners
- **Success States**: Toast notifications, checkmarks, status updates
- **Error States**: Inline errors, error banners, retry actions

## 7.6 Common Edge Cases

### Empty States
- **No Data**: Helpful messages with CTAs
- **No Results**: "No results found. Try adjusting your filters."
- **No Access**: "You don't have access to this resource."

### Error States
- **Network Error**: "Connection lost. Please check your internet and try again."
- **Server Error**: "Something went wrong. Our team has been notified."
- **Validation Error**: "Please correct the errors below"
- **Permission Error**: "You don't have permission to perform this action"

### Loading States
- **Content Loading**: Skeleton loaders or spinners
- **Processing**: Progress indicators with estimated time
- **Submitting**: "Submitting..." with disabled form

---

# 8. Success Metrics

## 8.1 Applicant Portal Metrics

### Task Completion
- **Eligibility Check Completion Rate**: % of users who complete eligibility check
- **Document Upload Success Rate**: % of successful document uploads
- **Case Creation Rate**: % of users who create at least one case
- **Time to First Result**: Average time from case creation to eligibility result

### User Satisfaction
- **Net Promoter Score (NPS)**: User recommendation likelihood
- **User Satisfaction Score**: Post-task satisfaction surveys
- **Trust Score**: User trust in AI recommendations
- **Help Request Rate**: % of users requesting human review

### Engagement
- **Return User Rate**: % of users who return after first session
- **Cases per User**: Average number of cases created
- **Feature Adoption**: % of users using each feature
- **Session Duration**: Average time per session

## 8.2 Reviewer Console Metrics

### Efficiency
- **Review Completion Time**: Average time for reviewer to complete review
- **Reviews per Day**: Average number of reviews completed per reviewer
- **SLA Compliance**: % of reviews completed within SLA
- **Override Rate**: % of AI decisions overridden by reviewers

### Quality
- **Review Accuracy**: % of reviews that match final outcomes
- **Note Quality**: Average length and detail of reviewer notes
- **Escalation Rate**: % of reviews escalated to senior reviewer

## 8.3 Admin Console Metrics

### System Health
- **System Uptime**: % of time system is available
- **Error Rate**: % of failed operations
- **Ingestion Success Rate**: % of successful data source fetches
- **Rule Validation Time**: Average time to validate and publish rules

### Operational
- **Rule Publication Latency**: Time from change detection to rule publication
- **Validation Accuracy**: % of approved rules that are correct
- **User Management Efficiency**: Time to manage users

## 8.4 Business Metrics

### Conversion
- **Sign-up to Case Creation**: % of sign-ups who create case
- **Case to Eligibility Check**: % of cases that get evaluated
- **Eligibility to Document Upload**: % of users who upload documents

### Quality
- **AI Confidence Distribution**: Distribution of confidence scores
- **Human Review Rate**: % of cases requiring human review
- **Citation Click-through Rate**: % of citations clicked

---

# Document Version History

**Version 1.0** (2024)
- Initial PRD created from implementation.md
- Organized by system (Applicant, Reviewer, Admin)
- Functional requirements only (no visual design specs)
- Comprehensive feature requirements
- User journeys and flows
- Screen requirements
- Interaction patterns

---

**Status**: Ready for Design  
**Next Steps**: 
1. User research and validation
2. Wireframe creation
3. Visual design exploration (designer's choice on colors, typography, etc.)
4. Prototype development
5. Usability testing
