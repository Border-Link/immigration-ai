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
4. [Module 1: Authentication & User Management](#module-1-authentication--user-management)
   - [4.1 User App Perspective](#41-user-app-perspective)
   - [4.2 Reviewer App Perspective](#42-reviewer-app-perspective)
   - [4.3 Admin App Perspective](#43-admin-app-perspective)
5. [Module 2: Case Management](#module-2-case-management)
   - [5.1 User App Perspective](#51-user-app-perspective)
   - [5.2 Reviewer App Perspective](#52-reviewer-app-perspective)
   - [5.3 Admin App Perspective](#53-admin-app-perspective)
6. [Module 3: Eligibility Checks & AI Decisions](#module-3-eligibility-checks--ai-decisions)
   - [6.1 User App Perspective](#61-user-app-perspective)
   - [6.2 Reviewer App Perspective](#62-reviewer-app-perspective)
   - [6.3 Admin App Perspective](#63-admin-app-perspective)
7. [Module 4: Document Management](#module-4-document-management)
   - [7.1 User App Perspective](#71-user-app-perspective)
   - [7.2 Reviewer App Perspective](#72-reviewer-app-perspective)
   - [7.3 Admin App Perspective](#73-admin-app-perspective)
8. [Module 5: AI Voice Calls](#module-5-ai-voice-calls)
   - [8.1 User App Perspective](#81-user-app-perspective)
   - [8.2 Reviewer App Perspective](#82-reviewer-app-perspective)
   - [8.3 Admin App Perspective](#83-admin-app-perspective)
9. [Module 6: Human Reviews](#module-6-human-reviews)
   - [9.1 User App Perspective](#91-user-app-perspective)
   - [9.2 Reviewer App Perspective](#92-reviewer-app-perspective)
   - [9.3 Admin App Perspective](#93-admin-app-perspective)
10. [Module 7: Payments](#module-7-payments)
    - [10.1 User App Perspective](#101-user-app-perspective)
    - [10.2 Reviewer App Perspective](#102-reviewer-app-perspective)
    - [10.3 Admin App Perspective](#103-admin-app-perspective)
11. [Module 8: Rules Knowledge & Data Ingestion](#module-8-rules-knowledge--data-ingestion)
    - [11.1 User App Perspective](#111-user-app-perspective)
    - [11.2 Reviewer App Perspective](#112-reviewer-app-perspective)
    - [11.3 Admin App Perspective](#113-admin-app-perspective)
12. [End-to-End Flows & Data Transitions](#12-end-to-end-flows--data-transitions)
13. [Shared Requirements](#13-shared-requirements)
14. [Success Metrics](#14-success-metrics)

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

The platform is a **single unified application** with role-based views:
1. **User View (Applicant Portal)**: For immigration applicants to check eligibility and manage cases
2. **Reviewer View (Reviewer Console)**: For human immigration advisers to review cases
3. **Admin View (Admin Console)**: For platform administrators to manage rules and system

All three views are part of the same application - users see different features and screens based on their role. The UI dynamically renders components based on user permissions.

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

## 3.1 Single System with Role-Based Views

The platform is a **single unified application** where users see different features and screens based on their role. All users share the same login portal and backend infrastructure, but the UI dynamically renders different views based on user permissions and role.

```
┌─────────────────────────────────────────────────────────┐
│                   USER APP (Applicant Portal)           │
│                                                          │
│  Module 1: Authentication & User Management            │
│  - Registration & Email Verification (OTP)              │
│  - Login with OTP/2FA                                    │
│  - Profile Management (GDPR-compliant)                   │
│  - User Settings & Security                              │
│  - Password Reset (3-step OTP process)                  │
│                                                          │
│  Module 2: Case Management                               │
│  - Create & Manage Immigration Cases                     │
│  - Collect Case Facts (Multi-step form)                  │
│  - View Case Timeline & Status                           │
│                                                          │
│  Module 3: Eligibility Checks & AI Decisions            │
│  - Run Eligibility Checks                               │
│  - View AI-Generated Results                            │
│  - See Confidence Scores & Explanations                  │
│  - View Citations & Rule Evaluations                     │
│                                                          │
│  Module 4: Document Management                          │
│  - Upload Documents (Drag & Drop)                       │
│  - View Document Checklist                              │
│  - Track Document Validation Status                     │
│  - View OCR Results & Classifications                    │
│                                                          │
│  Module 5: AI Voice Calls                               │
│  - Create & Start 30-Minute Voice Sessions              │
│  - Real-time Voice Conversations                        │
│  - View Call Transcripts & Summaries                    │
│                                                          │
│  Module 6: Human Reviews                                 │
│  - Request Human Review                                  │
│  - Track Review Status & SLA                             │
│  - Receive Reviewer Feedback                            │
│                                                          │
│  Module 7: Payments                                     │
│  - Make Payments (Stripe/PayPal)                        │
│  - View Payment History                                 │
│  - Download Receipts                                    │
│                                                          │
│  Module 8: Rules Knowledge (Read-Only)                  │
│  - View Rules in Eligibility Results                    │
│  - See Rule Versions & Effective Dates                  │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│              REVIEWER APP (Reviewer Console)             │
│                                                          │
│  Module 1: Authentication & User Management              │
│  - Login with OTP/2FA                                    │
│  - View Profile (Limited Editing)                       │
│                                                          │
│  Module 2: Case Management (Read-Only)                  │
│  - View Assigned Cases                                  │
│  - Access Case Facts & Timeline                         │
│                                                          │
│  Module 3: Eligibility Checks & AI Decisions            │
│  - View AI Results for Assigned Cases                   │
│  - Override AI Decisions                                │
│  - View Full AI Reasoning Logs                          │
│                                                          │
│  Module 4: Document Management                           │
│  - View Documents for Assigned Cases                    │
│  - Validate Document Classifications                    │
│  - Approve/Reject Documents                             │
│                                                          │
│  Module 5: AI Voice Calls (Read-Only)                   │
│  - View Call Sessions for Assigned Cases               │
│  - Review Call Transcripts                              │
│  - Analyze Guardrails Events                            │
│                                                          │
│  Module 6: Human Reviews                                 │
│  - Review Dashboard with Queue                          │
│  - Complete Reviews (Approve/Override/Escalate)        │
│  - Add Review Notes & Feedback                          │
│  - Track SLA Deadlines                                  │
│                                                          │
│  Module 7: Payments (Read-Only)                          │
│  - View Payments for Assigned Cases                     │
│                                                          │
│  Module 8: Rules Knowledge (Read-Only)                  │
│  - View Rules & Technical Details                       │
│  - See Rule History & Versions                          │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│                ADMIN APP (Admin Console)                 │
│                                                          │
│  Module 1: Authentication & User Management            │
│  - Full User CRUD Operations                            │
│  - User Role Management                                 │
│  - User Activation/Deactivation/Suspension               │
│  - User Analytics & Activity Tracking                   │
│  - Bulk User Operations                                 │
│                                                          │
│  Module 2: Case Management                              │
│  - View All Cases (Full Access)                         │
│  - Edit Any Case Facts                                 │
│  - Force Case Status Changes                            │
│  - Case Analytics & Statistics                          │
│                                                          │
│  Module 3: Eligibility Checks & AI Decisions            │
│  - View All Eligibility Results                         │
│  - Manage AI Reasoning Logs                            │
│  - View AI Citations                                    │
│  - AI Decisions Analytics                              │
│                                                          │
│  Module 4: Document Management                          │
│  - View All Documents                                   │
│  - Update Document Types & Status                       │
│  - Manage Document Checks                               │
│  - Document Analytics                                  │
│                                                          │
│  Module 5: AI Voice Calls                                │
│  - View All Call Sessions                               │
│  - Call Analytics & Statistics                          │
│  - Guardrail Analytics                                  │
│                                                          │
│  Module 6: Human Reviews                                 │
│  - View All Reviews                                     │
│  - Assign/Reassign Reviewers                           │
│  - Review Analytics & SLA Tracking                      │
│                                                          │
│  Module 7: Payments                                      │
│  - View All Payments                                    │
│  - Process Refunds                                      │
│  - Payment Analytics & Revenue Tracking                │
│                                                          │
│  Module 8: Rules Knowledge & Data Ingestion              │
│  - Rule Validation Queue                                │
│  - Approve/Reject/Edit Rules                            │
│  - Manage Data Sources                                  │
│  - Monitor Ingestion Pipeline                          │
│  - View Document Versions & Diffs                       │
│  - Ingestion Analytics                                  │
└─────────────────────────────────────────────────────────┘
```

## 3.2 User Access & Authentication

- **Single Unified System**: One application that renders different views based on user role
- **Single Login Portal**: All users (Users, Reviewers, Admins) use the same login portal
- **Role-Based UI Rendering**: After login, the UI dynamically renders based on `user.role`:
  - **User Role**: Sees applicant-focused features and screens
  - **Reviewer Role**: Sees reviewer-focused features and screens (created by Super Admin)
  - **Admin Role**: Sees admin-focused features and screens (created by Super Admin)
- **Same Backend, Different Views**: All roles share the same backend API, but UI components conditionally render based on permissions
- **User Registration**: Only regular users (applicants) can self-register
- **Reviewer & Admin Creation**: Reviewers and Admins are created by Super Admin only (no self-registration)
- **Role-Based Redirect**: After authentication, users are redirected to their role-appropriate dashboard view
- **Single Sign-On (Future)**: Optional SSO for organizations

---

# Module 1: Authentication & User Management

This module handles user registration, login, password management, and user profile management. All users (Users, Reviewers, Admins) use the same authentication system, but see different features based on their role.

## 4.1 User App Perspective

### 4.1.1 Registration & Login

**Screen Name**: `SignUpScreen`, `LoginScreen`

**User Journey**:
```
1. Landing Page → "Sign Up" button (Only for regular users/applicants)
2. Sign Up Screen → Fill form → Submit
3. Email verification → OTP input → Verify
4. Login Screen → Enter credentials → OTP/2FA verification → Role-based redirect
   - User Role → User App Dashboard
   - Reviewer Role → Reviewer App Dashboard (created by Super Admin)
   - Admin Role → Admin App Dashboard (created by Super Admin)
5. Forgot Password → OTP → Reset Password
```

**Note**: Only regular users (applicants) can self-register. Reviewers and Admins are created by Super Admin and cannot self-register.

**Sign Up Screen Specifications**:
- **Access**: Only available for regular users (applicants). Reviewers and Admins cannot self-register.
- **Fields**:
  - Email (text input, required, email validation, auto-lowercase)
  - Password (password input, required, strength indicator)
  - First Name (text input, required, max 255 chars)
  - Last Name (text input, required, max 255 chars)
  - Terms & Conditions checkbox (required)
  - Privacy Policy link (opens in new tab)
- **Validation**:
  - Real-time email format validation
  - Email uniqueness check (prevents duplicate registration)
  - Password strength validation (checks similarity to email)
  - Password strength meter (weak/medium/strong)
  - Terms checkbox must be checked
- **API Endpoint**: `POST /api/v1/auth/register/`
- **Request Parameters**:
  ```json
  {
    "email": "user@example.com",
    "password": "SecurePass123!",
    "first_name": "John",
    "last_name": "Doe"
  }
  ```
- **Response Data**:
  ```json
  {
    "message": "User created successfully. Please check your email for confirmation OTP",
    "data": {
      "user": {
        "id": "uuid",
        "email": "user@example.com",
        "is_verified": false
      },
      "endpoint_token": "unique_token_for_otp_verification"
    }
  }
  ```
- **UI Behavior**:
  - Show loading spinner during submission
  - Display success message with OTP verification prompt
  - Redirect to OTP verification screen (not login)
  - Show inline validation errors for each field
  - Email is automatically normalized (lowercase, trimmed)

**OTP Verification Screen** (Registration):
- **Screen Name**: `OTPVerificationScreen`
- **Fields**:
  - OTP Code (6-digit input, required)
  - Resend OTP button (with throttling)
- **API Endpoint**: `POST /api/v1/auth/register/verify/<endpoint_token>/`
- **Request Parameters**:
  ```json
  {
    "otp": "123456"
  }
  ```
- **Response Data**:
  ```json
  {
    "message": "Email verified successfully",
    "data": {
      "user": {
        "id": "uuid",
        "email": "user@example.com",
        "is_verified": true
      }
    }
  }
  ```
- **UI Behavior**:
  - Auto-focus on OTP input
  - Auto-submit when 6 digits entered
  - Show countdown timer for resend (throttling)
  - Display error if OTP invalid or expired
  - Redirect to login screen on success

**Login Screen Specifications**:
- **Access**: Single login portal for all users (Users, Reviewers, Admins)
- **Fields**:
  - Email (text input, required, auto-lowercase)
  - Password (password input, required)
  - "Forgot Password?" link
  - "Sign Up" link (only shown for regular users, not for Reviewers/Admins)
- **API Endpoint**: `POST /api/v1/auth/login/`
- **Request Parameters**:
  ```json
  {
    "email": "user@example.com",
    "password": "SecurePass123!"
  }
  ```
- **Response Data** (Initial Login - OTP/2FA Required):
  ```json
  {
    "message": "OTP sent to your email" or "Two-factor authentication is enabled. Please verify your identity.",
    "data": {
      "email": "user@example.com",
      "2fa_enabled": false, // or true if 2FA enabled
      "endpoint_token": "unique_token_for_verification"
    }
  }
  ```
- **UI Behavior**:
  - Show loading spinner during submission
  - If 2FA enabled: Redirect to 2FA verification screen
  - If 2FA not enabled: Redirect to OTP verification screen
  - Show error message for invalid credentials
  - All previous device sessions are automatically revoked on new login (security)
  - After successful login: Redirect based on user role:
    - User role → Dashboard (User view)
    - Reviewer role → Dashboard (Reviewer view)
    - Admin role → Dashboard (Admin view)
  - UI components conditionally render based on `user.role`

**OTP/2FA Verification Screen** (Login):
- **Screen Name**: `LoginVerificationScreen`
- **Fields**:
  - OTP Code (6-digit input, required) - if 2FA disabled
  - TOTP Code (6-digit input, required) - if 2FA enabled
  - Resend OTP button (if 2FA disabled, with throttling)
- **API Endpoint**: `POST /api/v1/auth/login/verify/<endpoint_token>/`
- **Request Parameters**:
  ```json
  {
    "otp": "123456",
    "is_2fa": false // true if using TOTP from authenticator app
  }
  ```
- **Response Data** (Successful Verification):
  ```json
  {
    "access_granted": true,
    "user": {
      "id": "uuid",
      "email": "user@example.com"
    }
  }
  ```
- **Cookies Set** (Multi-Cookie Authentication):
  - `access_token` (24-hour expiry)
  - `fingerprint` (device fingerprint hash)
  - `session_id` (Django session key)
  - `mfa_verified` (if 2FA used)
  - `last_active` (timestamp)
- **UI Behavior**:
  - Auto-focus on OTP/TOTP input
  - Auto-submit when 6 digits entered
  - Show countdown timer for resend (if applicable)
  - Display error if OTP/TOTP invalid
  - Redirect to Dashboard on success
  - Device session created automatically with fingerprint (IP + User-Agent hash)

### 4.1.2 Password Reset (3-Step Process)

**Screen Name**: `ForgotPasswordScreen`, `OTPVerificationScreen`, `ResetPasswordScreen`

**User Journey**:
```
1. Login Screen → "Forgot Password?" link
2. Forgot Password Screen → Enter email → Submit
3. OTP Verification Screen → Enter OTP → Verify
4. Reset Password Screen → Enter new password → Submit
5. Success message → Redirect to Login
```

**Step 1: Forgot Password Screen**:
- **Fields**: Email (text input, required)
- **API Endpoint**: `POST /api/v1/auth/forgot-password/`
- **Request Parameters**:
  ```json
  {
    "email": "user@example.com"
  }
  ```
- **Response Data**:
  ```json
  {
    "message": "OTP resent successfully",
    "data": {
      "email": "user@example.com",
      "endpoint_token": "unique_token_for_verification"
    }
  }
  ```
- **UI Behavior**: 
  - Show success message regardless of email existence (security)
  - Redirect to OTP verification screen
  - OTP sent via email automatically

**Step 2: OTP Verification Screen**:
- **Fields**:
  - OTP Code (6-digit input, required)
  - Resend OTP button (with throttling)
- **API Endpoint**: `POST /api/v1/auth/forgot-password/verify/<endpoint_token>/`
- **Request Parameters**:
  ```json
  {
    "otp": "123456"
  }
  ```
- **Response Data**:
  ```json
  {
    "message": "OTP verified successfully",
    "data": {
      "email": "user@example.com",
      "can_reset": true,
      "endpoint_token": "same_endpoint_token"
    }
  }
  ```
- **UI Behavior**: 
  - Auto-focus on OTP input
  - Auto-submit when 6 digits entered
  - Show countdown timer for resend
  - Redirect to password reset screen on success

**Step 3: Reset Password Screen**:
- **Fields**:
  - New Password (password input, required, strength indicator)
  - Confirm Password (password input, required, must match)
- **API Endpoint**: `POST /api/v1/auth/forgot-password/reset/<endpoint_token>/`
- **Request Parameters**:
  ```json
  {
    "new_password": "NewSecurePass123!",
    "email": "user@example.com"
  }
  ```
- **Response Data**:
  ```json
  {
    "message": "Password updated successfully.",
    "data": {
      "email": "user@example.com"
    }
  }
  ```
- **UI Behavior**: 
  - Validate password strength
  - Show password match indicator
  - Redirect to login screen on success
  - Password reset record created for audit trail

### 4.1.3 Profile Management

**Screen Name**: `ProfileScreen`

**User Journey**:
```
Dashboard → Account Settings → Profile
```

**Profile Screen Specifications**:
- **GDPR-Compliant Structure**:
  - **User Model**: Authentication only (email, password, role, permissions)
  - **UserProfile Model**: All PII data (names, DOB, nationality, consent)
  - Separation allows for easier right-to-erasure compliance
- **Viewable Fields** (read-only):
  - Email (display only, cannot change - stored in User model)
  - Registration Date (`created_at`)
  - Last Login Date (`last_login`)
  - Account Status (`is_active`, `is_verified`)
  - Profile Completion Percentage (calculated)
- **Editable Fields** (via UserProfile - GDPR-separated):
  - First Name (`first_name`)
  - Last Name (`last_name`)
  - Date of Birth (`date_of_birth`)
  - Nationality (`nationality` - Country FK)
  - State/Province (`state_province` - StateProvince FK, optional)
  - Avatar (`avatar` - image upload)
  - Consent Given (`consent_given` - boolean, GDPR compliance)
- **API Endpoint**: 
  - View: `GET /api/v1/auth/profile/`
  - Create: `POST /api/v1/auth/profile/` (auto-created via signal, but can be explicitly created)
  - Update: `PATCH /api/v1/auth/profile/` (supports partial updates)
- **Response Data** (View):
  ```json
  {
    "message": "Profile retrieved successfully.",
    "data": {
      "id": "uuid",
      "user_id": "uuid",
      "first_name": "John",
      "last_name": "Doe",
      "date_of_birth": "1990-01-15",
      "nationality": {
        "code": "US",
        "name": "United States"
      },
      "state_province": {
        "code": "CA",
        "name": "California"
      },
      "avatar": "https://...",
      "consent_given": true,
      "consent_timestamp": "2025-01-15T10:00:00Z",
      "created_at": "2025-01-01T08:00:00Z",
      "updated_at": "2025-01-15T10:00:00Z"
    }
  }
  ```
- **Request Parameters** (Update - Partial Updates Supported):
  ```json
  {
    "first_name": "John",
    "last_name": "Doe",
    "date_of_birth": "1990-01-15",
    "country_code": "US",
    "state_code": "CA",
    "avatar": "<file>",
    "consent_given": true
  }
  ```
- **UI Behavior**:
  - Show current profile data
  - Edit mode toggle
  - Save button (disabled until changes made)
  - Success toast notification on save
  - Profile auto-created on user registration (via Django signal)
  - Avatar can be removed via separate endpoint: `DELETE /api/v1/auth/profile/avatar/`

### 4.1.4 User Account Information

**Screen Name**: `UserAccountScreen`

**User Journey**:
```
Dashboard → Account Settings → Account Information
```

**Account Information Screen Specifications**:
- **Comprehensive Account View**:
  - Single endpoint returns all account-related data
- **API Endpoint**: `GET /api/v1/auth/user-account/`
- **Response Data Structure**:
  ```json
  {
    "message": "User account information retrieved successfully.",
    "data": {
      "profile": {
        "user_id": "uuid",
        "email": "user@example.com",
        "first_name": "John",
        "last_name": "Doe",
        "full_name": "John Doe",
        "avatar": "https://...",
        "date_of_birth": "1990-01-15",
        "nationality": "US",
        "nationality_name": "United States",
        "state_province": "CA",
        "state_province_name": "California",
        "email_verified": true,
        "consent_given": true,
        "consent_timestamp": "2025-01-15T10:00:00Z",
        "member_since": "2025-01-01 08:00:00",
        "profile_created_at": "2025-01-01 08:00:00",
        "profile_updated_at": "2025-01-15 10:00:00",
        "last_login": "2025-01-15 10:00:00",
        "profile_completion": 85
      },
      "account": {
        "user_id": "uuid",
        "role": "user",
        "is_active": true,
        "is_superuser": false,
        "is_staff": false,
        "account_created_at": "2025-01-01 08:00:00",
        "account_updated_at": "2025-01-15 10:00:00",
        "account_age_days": 14,
        "days_since_last_login": 0
      },
      "settings": {
        "two_factor_enabled": false,
        "language": "en",
        "timezone": "UTC",
        "dark_mode": false,
        "email_notifications": true,
        "sms_notifications": true,
        "push_notifications": true,
        "notify_case_status_updates": true,
        "notify_eligibility_results": true,
        "notify_document_status": true,
        "notify_missing_documents": true,
        "notify_rule_changes": false,
        "notify_review_updates": true,
        "data_sharing_consent": false,
        "marketing_emails": false
      },
      "security": {
        "two_factor_enabled": false,
        "account_active": true,
        "email_verified": true,
        "total_logins": 5,
        "has_usable_password": true,
        "security_score": {
          "score": 60,
          "max_score": 100,
          "percentage": 60,
          "level": "Moderate",
          "last_password_change": "2025-01-10 10:00:00"
        }
      }
    }
  }
  ```
- **Security Score Calculation**:
  - Email verified: +25 points
  - Has usable password: +25 points
  - 2FA enabled: +30 points
  - Password changed in last 90 days: +10 points
  - Has logged in before: +10 points
  - **Security Levels**:
    - High: 85-100 points
    - Moderate: 60-84 points
    - Low: 0-59 points
- **Profile Completion Calculation**:
  - Based on required fields: first_name, last_name, email, nationality, date_of_birth, consent_given
  - Percentage: (completed_fields / total_fields) * 100
- **UI Behavior**:
  - Display all information in organized sections/tabs
  - Show security score with visual indicator (progress bar)
  - Show profile completion percentage
  - Highlight areas needing attention (low security score, incomplete profile)

### 4.1.5 User Settings Management

**Screen Name**: `UserSettingsScreen`

**User Journey**:
```
Dashboard → Account Settings → Settings
```

**Settings Screen Specifications**:
- **View Settings**:
  - **API Endpoint**: `GET /api/v1/auth/settings/`
  - Returns all user settings
- **Update Individual Setting**:
  - **API Endpoint**: `PATCH /api/v1/auth/settings/<setting_name>/`
  - **Request Parameters**:
    ```json
    {
      "value": true // or false, or string value
    }
    ```
  - **Supported Settings**:
    - `two_factor_auth` (boolean)
    - `language` (string: 'en', 'fr', etc.)
    - `timezone` (string: 'UTC', 'America/New_York', etc.)
    - `dark_mode` (boolean)
    - `email_notifications` (boolean)
    - `sms_notifications` (boolean)
    - `push_notifications` (boolean)
    - `notify_case_status_updates` (boolean)
    - `notify_eligibility_results` (boolean)
    - `notify_document_status` (boolean)
    - `notify_missing_documents` (boolean)
    - `notify_rule_changes` (boolean)
    - `notify_review_updates` (boolean)
    - `data_sharing_consent` (boolean)
    - `marketing_emails` (boolean)
- **UI Behavior**:
  - Toggle switches for boolean settings
  - Dropdowns for language/timezone
  - Real-time updates (no page refresh needed)
  - Success toast notifications

**Enable 2FA Screen**:
- **Screen Name**: `Enable2FAScreen`
- **API Endpoint**: `POST /api/v1/auth/settings/enable-2fa/`
- **Response Data**:
  ```json
  {
    "message": "2FA enabled successfully.",
    "data": {
      "qr_code": "data:image/png;base64,..." // QR code for authenticator app
    }
  }
  ```
- **UI Behavior**:
  - Display QR code for scanning with authenticator app
  - Show instructions for setting up 2FA
  - User must verify TOTP on next login
  - TOTP secret stored securely in UserSettings

### 4.1.6 Logout

**Screen Name**: `LogoutAction` (triggered from header/menu)

**User Journey**:
```
Dashboard → User Menu → Logout
```

**Logout Flow**:
- **API Endpoints**:
  - `POST /api/v1/auth/logout/` - Logout current session
  - `POST /api/v1/auth/logoutall/` - Logout all sessions
- **Process**:
  1. All device sessions for user are revoked
  2. All AuthTokens (Knox tokens) are deleted
  3. All cookies are expired/cleared:
     - `access_token`
     - `fingerprint`
     - `session_id`
     - `mfa_verified`
     - `last_active`
  4. User redirected to login screen
- **UI Behavior**:
  - Confirmation dialog (optional, for logout all)
  - Success message
  - Redirect to login screen
  - All authentication state cleared

### 4.1.7 Device Session Management

**Screen Name**: `DeviceSessionsScreen` (Future Enhancement)

**Device Session Information**:
- **Purpose**: Track and manage active device sessions for security
- **Model**: `UserDeviceSession`
- **Tracks**:
  - Device fingerprint (SHA-256 hash of IP + User-Agent)
  - IP address and User-Agent
  - Device info (platform, browser, language)
  - Session ID (Django session key)
  - MFA verification status
  - Last active timestamp
  - Revocation status
- **Security Features**:
  - All previous sessions revoked on new login
  - One device session per fingerprint per user
  - Automatic cleanup of old sessions
  - Session revocation on logout
- **API Endpoints** (Future):
  - `GET /api/v1/auth/device-sessions/` - List active sessions
  - `DELETE /api/v1/auth/device-sessions/<id>/` - Revoke specific session

## 4.2 Reviewer App Perspective

### 4.2.1 Account Creation & Login

**Screen Name**: `ReviewerLoginScreen`

**User Journey**:
```
Super Admin creates Reviewer account → Reviewer receives credentials
→ Single Login Portal → Login → OTP/2FA verification → Reviewer Dashboard
```

**Account Creation**:
- **Process**: Reviewers are created by Super Admin only
- **No Self-Registration**: Reviewers cannot sign up themselves
- **Creation Method**: Super Admin uses Admin App to create reviewer accounts
- **Initial Credentials**: Super Admin sets initial password (reviewer must change on first login)
- **Notification**: Reviewer receives email with account details

**Login Screen Specifications**:
- **Access**: Uses the same single login portal as all users
- **Fields**: Same as User App (email, password)
- **API Endpoint**: `POST /api/v1/auth/login/` (same endpoint, role-based redirect)
- **Response Data**: Same structure as User App (OTP/2FA flow)
- **Verification Flow**: Same OTP/2FA verification as User App
- **UI Behavior**:
  - Same login flow as regular users (OTP/2FA required)
  - After verification, system detects `role: "reviewer"` and renders Reviewer view
  - UI components conditionally show reviewer-specific features
  - Show reviewer-specific welcome message
  - Display pending reviews count in header
  - All previous sessions revoked on login (security)
  - "Sign Up" link should not be visible (reviewers cannot self-register)

### 4.2.2 Profile View

**Screen Name**: `ReviewerProfileScreen`

**Profile Screen Specifications**:
- **Viewable Fields**:
  - Email
  - Name
  - Reviewer ID
  - License Number (if applicable)
  - Assigned Reviews Count
  - Completed Reviews Count
  - Average Review Time
- **Editable Fields**: Limited (name, phone, contact info only)
- **API Endpoint**: `GET /api/v1/auth/profile/`, `PATCH /api/v1/auth/profile/update/`
- **UI Behavior**: Read-only for most fields, limited editing capability

## 4.3 Admin App Perspective

### 4.3.1 Account Creation & Login

**Screen Name**: `AdminLoginScreen`

**User Journey**:
```
Super Admin creates Admin account → Admin receives credentials
→ Single Login Portal → Login → OTP/2FA verification → Admin Dashboard
```

**Account Creation**:
- **Process**: Admins are created by Super Admin only
- **No Self-Registration**: Admins cannot sign up themselves
- **Creation Method**: Super Admin uses Admin App to create admin accounts
- **Initial Credentials**: Super Admin sets initial password (admin must change on first login)
- **Notification**: Admin receives email with account details

**Login Screen Specifications**:
- **Access**: Uses the same single login portal as all users
- **Fields**: Same as User App (email, password)
- **API Endpoint**: `POST /api/v1/auth/login/` (same endpoint, role-based redirect)
- **Response Data**: Same structure as User App (OTP/2FA flow)
- **Verification Flow**: Same OTP/2FA verification as User App
- **UI Behavior**:
  - Same login flow as regular users (OTP/2FA required)
  - After verification, system detects `role: "admin"` and renders Admin view
  - UI components conditionally show admin-specific features
  - Show admin-specific welcome message
  - Display system metrics in header
  - All previous sessions revoked on login (security)
  - "Sign Up" link should not be visible (admins cannot self-register)

### 4.3.2 User Management

**Screen Name**: `UserManagementScreen`, `UserDetailScreen`, `UserCreateScreen`

**User Journey**:
```
Admin Dashboard → User Management → User List
→ [View User] / [Edit User] / [Create User]
```

**User List Screen Specifications**:
- **Table Columns**:
  - Email
  - Name
  - Role (badge: User/Reviewer/Staff/Admin)
  - Status (badge: Active/Inactive/Unverified)
  - Last Login
  - Created Date
  - Actions (View, Edit, Deactivate, Delete)
- **Filters**:
  - Role dropdown (User, Reviewer, Staff, Admin, All)
  - Status dropdown (Active, Inactive, Unverified, All)
  - Email search (text input)
  - Date range picker (created date)
- **API Endpoint**: `GET /api/v1/auth/admin/users/`
- **Query Parameters**:
  - `role` (optional)
  - `is_active` (optional, boolean)
  - `is_verified` (optional, boolean)
  - `email` (optional, search)
  - `date_from` (optional, ISO 8601)
  - `date_to` (optional, ISO 8601)
- **Response Data**:
  ```json
  {
    "message": "Users retrieved successfully",
    "data": [
      {
        "id": "uuid",
        "email": "user@example.com",
        "name": "John Doe",
        "role": "user",
        "is_active": true,
        "is_verified": true,
        "last_login": "2025-01-15T10:00:00Z",
        "created_at": "2025-01-01T08:00:00Z"
      }
    ],
    "status_code": 200
  }
  ```
- **UI Behavior**:
  - Pagination (20 users per page)
  - Sortable columns
  - Bulk selection checkbox
  - Export to CSV button
  - "Create User" button (prominent)

**User Detail Screen Specifications**:
- **Tabs**:
  - Overview (basic info, status, dates)
  - Activity (login history, actions)
  - Cases (linked cases count)
  - Reviews (if reviewer, shows review history)
- **Editable Fields**:
  - Role (dropdown: User, Reviewer, Staff, Admin)
  - Status (Active/Inactive toggle)
  - Verified status (checkbox)
  - Staff status (checkbox)
  - Superuser status (checkbox, superuser only)
- **API Endpoint**: 
  - View: `GET /api/v1/auth/admin/users/<id>/`
  - Update: `PATCH /api/v1/auth/admin/users/<id>/update/`
- **Request Parameters** (Update):
  ```json
  {
    "role": "reviewer",
    "is_active": true,
    "is_verified": true,
    "is_staff": false,
    "is_superuser": false
  }
  ```
- **UI Behavior**:
  - Confirmation modal for role changes
  - Warning for deactivating users
  - Success toast on update
  - Audit log entry created automatically

**User Create Screen Specifications**:
- **Fields**:
  - Email (required, validated)
  - Password (required, strength indicator)
  - Confirm Password (required)
  - Role (dropdown, required):
    - **User**: Regular applicant (can also self-register)
    - **Reviewer**: Immigration adviser (created by Super Admin only)
    - **Admin**: Platform administrator (created by Super Admin only)
  - First Name (optional)
  - Last Name (optional)
  - Send Verification Email (checkbox, default: true)
  - Send Welcome Email (checkbox, default: true)
- **API Endpoint**: `POST /api/v1/auth/admin/users/create/`
- **Request Parameters**:
  ```json
  {
    "email": "reviewer@example.com",
    "password": "SecurePass123!",
    "confirm_password": "SecurePass123!",
    "role": "reviewer",
    "first_name": "James",
    "last_name": "Smith",
    "send_verification_email": true,
    "send_welcome_email": true
  }
  ```
- **UI Behavior**:
  - Form validation before submission
  - Success message with user ID
  - Option to send welcome email with credentials
  - For Reviewers/Admins: Clear indication that they cannot self-register
  - User receives email with account details and initial password

### 4.3.2 Advanced User Management

**Screen Name**: `UserAdvancedManagementScreen`

**Features**:
- **Suspend User**: `POST /api/v1/auth/admin/users/<id>/suspend/`
  - Suspends user account temporarily
  - Shows suspension reason field
  - Sets suspension end date
- **Activate/Deactivate**: `POST /api/v1/auth/admin/users/<id>/activate/` or `/deactivate/`
- **Bulk Operations**: `POST /api/v1/auth/admin/users/bulk-operation/`
  - Bulk activate/deactivate
  - Bulk role assignment
  - Bulk delete
- **User Analytics**: `GET /api/v1/auth/admin/users/analytics/`
  - User registration trends
  - Active users count
  - Role distribution
  - Login frequency

### 4.3.3 Profile Management

**Screen Name**: `AdminProfileScreen`

**Profile Screen Specifications**:
- **Viewable Fields**: All user fields plus admin-specific:
  - Admin ID
  - Permissions List
  - System Access Level
- **Editable Fields**: Name, contact info, notification preferences
- **API Endpoint**: Same as User App, but with admin permissions

---

# Module 2: Case Management

This module handles immigration case creation, fact collection, case status management, and case lifecycle tracking.

## 5.1 User App Perspective

### 5.1.1 Case Creation & Management

**Screen Name**: `CaseListScreen`, `CaseCreateScreen`, `CaseDetailScreen`

**User Journey: Create Case**:
```
Dashboard → "Create New Case" button
→ Case Creation Screen → Select Jurisdiction → Create
→ Case Detail Screen → Add Facts → Save
```

**Case List Screen Specifications**:
- **Case Cards Display**:
  - Case ID (short format: ABC-123)
  - Jurisdiction badge (UK, US, CA, AU)
  - Status badge (Draft, Evaluated, Awaiting Review, Reviewed, Closed)
  - Last Updated timestamp
  - Confidence Score (if evaluated, visual meter)
  - Quick Actions: View, Edit, Delete, Duplicate
- **Filters**:
  - Status dropdown (All, Draft, Evaluated, etc.)
  - Jurisdiction multi-select
  - Date range picker
- **Sort Options**:
  - By date (newest/oldest)
  - By status
  - By confidence score
- **API Endpoint**: `GET /api/v1/imigration-cases/cases/`
- **Response Data**:
  ```json
  {
    "message": "Cases retrieved successfully",
    "data": [
      {
        "id": "uuid",
        "jurisdiction": "UK",
        "status": "evaluated",
        "created_at": "2025-01-15T10:00:00Z",
        "updated_at": "2025-01-15T11:00:00Z",
        "confidence_score": 0.85
      }
    ]
  }
  ```
- **UI Behavior**:
  - Empty state: "Create your first case to get started" with CTA
  - Loading skeleton while fetching
  - Hover effects on cards
  - Confirmation modal for delete action

**Case Create Screen Specifications**:
- **Fields**:
  - Jurisdiction (dropdown, required): UK, US, CA, AU
  - Case Name (optional, text input)
- **API Endpoint**: `POST /api/v1/imigration-cases/cases/create/`
- **Request Parameters**:
  ```json
  {
    "jurisdiction": "UK",
    "name": "My UK Visa Application" // optional
  }
  ```
- **Response Data**:
  ```json
  {
    "message": "Case created successfully",
    "data": {
      "id": "uuid",
      "jurisdiction": "UK",
      "status": "draft",
      "created_at": "2025-01-15T10:00:00Z"
    }
  }
  ```
- **UI Behavior**:
  - Redirect to Case Detail Screen after creation
  - Show success toast notification
  - Pre-fill jurisdiction if coming from jurisdiction selector

**Case Detail Screen Specifications**:
- **Tabbed Interface**:
  - **Overview Tab**:
    - Case facts summary (key-value pairs)
    - Case status badge
    - Timeline of actions (creation, updates, eligibility checks)
    - Edit button (only if status = "draft")
  - **Eligibility Results Tab**: (See Module 3)
  - **Documents Tab**: (See Module 4)
  - **Review Status Tab**: (See Module 6)
- **Action Buttons**:
  - "Edit Case" (only if draft)
  - "Run Eligibility Check" (if facts updated)
  - "Request Review" (if eligible)
  - "Delete Case" (with confirmation)
- **API Endpoint**: `GET /api/v1/imigration-cases/cases/<id>/`
- **UI Behavior**:
  - Auto-save case facts on blur
  - Show unsaved changes indicator
  - Disable edit if status != "draft"

### 5.1.2 Case Facts Collection

**Screen Name**: `CaseFactsFormScreen` (Multi-Step)

**User Journey: Add Facts**:
```
Case Detail → Overview Tab → "Add Facts" button
→ Multi-Step Form → Step 1: Basic Info → Continue
→ Step 2: Visa Interest → Continue
→ Step 3: Employment → Continue
→ Step 4: Financials → Save
```

**Multi-Step Form Screen Specifications**:
- **Progress Indicator**:
  - Step numbers (1, 2, 3, 4)
  - Current step highlighted
  - Completed steps marked with checkmark
  - Progress bar (0%, 25%, 50%, 75%, 100%)
- **Step 1: Basic Info**:
  - Nationality (dropdown/autocomplete, required)
  - Age (number input, required, 18-100)
  - Date of Birth (date picker, required)
  - Country of Residence (dropdown, required)
- **Step 2: Visa Interest**:
  - Visa Types (checkboxes, at least one required):
    - Skilled Worker Visa
    - Student Visa
    - Family Visa
    - Investor Visa
    - Other (text input if selected)
  - "Select All" checkbox
- **Step 3: Employment**:
  - Salary (number input, required, currency selector)
  - Job Title (text input, required)
  - Has Sponsor (radio: Yes/No, required)
  - Sponsor Name (text input, conditional, required if has_sponsor = Yes)
- **Step 4: Financials**:
  - Savings Amount (number input, currency)
  - Number of Dependants (number input, 0-10)
- **Navigation**:
  - "Back" button (disabled on step 1)
  - "Save & Continue" button
  - "Save & Exit" button (saves and returns to Case Detail)
- **API Endpoint**: `POST /api/v1/imigration-cases/case-facts/create/`
- **Request Parameters**:
  ```json
  {
    "case_id": "uuid",
    "fact_key": "nationality",
    "fact_value": "Nigerian",
    "source": "user"
  }
  ```
- **UI Behavior**:
  - Real-time field validation
  - Inline error messages
  - Success checkmarks when valid
  - Auto-save on blur (optional)
  - Help tooltips for complex fields

### 5.1.3 Case Status & Timeline

**Screen Name**: `CaseTimelineScreen` (within Case Detail)

**Timeline Display**:
- **Events Shown**:
  - Case Created (timestamp, user)
  - Facts Added (timestamp, count)
  - Eligibility Check Run (timestamp, results)
  - Documents Uploaded (timestamp, count)
  - Review Requested (timestamp, status)
  - Review Completed (timestamp, reviewer name)
- **API Endpoint**: `GET /api/v1/imigration-cases/cases/<id>/status-history/`
- **UI Behavior**:
  - Chronological timeline view
  - Expandable event details
  - Color-coded by event type

## 5.2 Reviewer App Perspective

### 5.2.1 Assigned Cases View

**Screen Name**: `ReviewerCaseListScreen`

**User Journey**:
```
Reviewer Dashboard → "Assigned Cases" → Case List
→ Select Case → Case Review Screen
```

**Case List Screen Specifications**:
- **Case Cards Display**:
  - Case ID
  - User Name/Email
  - Jurisdiction
  - Status
  - AI Confidence Score
  - Risk Flags (badges: low_confidence, missing_docs, etc.)
  - Time in Queue
  - SLA Deadline (countdown timer)
- **Filters**:
  - Status (Pending Review, In Progress, Completed)
  - Priority (Normal, Urgent)
  - Jurisdiction
  - Date Assigned
- **API Endpoint**: `GET /api/v1/imigration-cases/cases/` (filtered by reviewer assignment)
- **UI Behavior**:
  - Highlight overdue cases (red border)
  - Show SLA countdown prominently
  - Quick action: "Start Review" button

### 5.2.2 Case Review Access

**Screen Name**: `ReviewerCaseDetailScreen`

**Case Detail Screen Specifications**:
- **Same tabs as User App**, but with additional:
  - **Review Actions Panel** (sticky, always visible):
    - "Approve AI Decision" button
    - "Override Decision" button
    - "Request More Info" button
    - "Escalate" button
    - Notes text area
    - "Submit Review" button
- **Read-Only Access**:
  - Can view all case facts
  - Can view all documents
  - Can view eligibility results
  - Cannot edit case facts (read-only)
- **API Endpoint**: `GET /api/v1/imigration-cases/cases/<id>/` (same as user, but with reviewer context)
- **UI Behavior**:
  - Show reviewer-specific actions
  - Display review history
  - Show comparison view (AI vs Human decision if override exists)

## 5.3 Admin App Perspective

### 5.3.1 All Cases Management

**Screen Name**: `AdminCaseListScreen`, `AdminCaseDetailScreen`

**User Journey**:
```
Admin Dashboard → Case Management → All Cases
→ [View/Edit/Delete] Case
```

**Case List Screen Specifications**:
- **Table View** (instead of cards):
  - Case ID
  - User Email
  - Jurisdiction
  - Status
  - Created Date
  - Updated Date
  - Confidence Score
  - Actions (View, Edit, Delete, Bulk Actions)
- **Advanced Filters**:
  - User ID/Email
  - Jurisdiction
  - Status
  - Date range (created/updated)
  - Confidence score range
- **Bulk Operations**:
  - Bulk status update
  - Bulk delete
  - Bulk archive
- **API Endpoint**: `GET /api/v1/imigration-cases/admin/cases/`
- **Query Parameters**:
  - `user_id` (optional)
  - `jurisdiction` (optional)
  - `status` (optional)
  - `date_from` (optional)
  - `date_to` (optional)
  - `updated_date_from` (optional)
  - `updated_date_to` (optional)
- **Response Data**: Same structure as User App, but includes `user_email` field
- **UI Behavior**:
  - Export to CSV button
  - Pagination (50 cases per page)
  - Bulk selection with checkbox column
  - Advanced search bar

**Case Detail Screen Specifications**:
- **All tabs from User App**, plus:
  - **Admin Actions Tab**:
    - Force status change
    - Assign reviewer
    - View audit log
    - Export case data
- **Editable Fields**:
  - Status (dropdown, all statuses available)
  - Jurisdiction
  - Any case facts (full edit access)
- **API Endpoint**: 
  - View: `GET /api/v1/imigration-cases/admin/cases/<id>/`
  - Update: `PATCH /api/v1/imigration-cases/admin/cases/<id>/update/`
- **Request Parameters** (Update):
  ```json
  {
    "status": "reviewed",
    "jurisdiction": "UK"
  }
  ```
- **UI Behavior**:
  - Warning modal for status changes
  - Audit log entry on any update
  - Success toast notification

### 5.3.2 Case Facts Management

**Screen Name**: `AdminCaseFactsScreen`

**Case Facts Management**:
- **List View**:
  - Fact Key
  - Fact Value
  - Source (User, AI, Reviewer)
  - Created Date
  - Actions (Edit, Delete)
- **Filters**:
  - Case ID
  - Fact Key
  - Source
  - Date range
- **API Endpoint**: 
  - List: `GET /api/v1/imigration-cases/admin/case-facts/`
  - Update: `PATCH /api/v1/imigration-cases/admin/case-facts/<id>/update/`
  - Delete: `DELETE /api/v1/imigration-cases/admin/case-facts/<id>/delete/`
- **Bulk Operations**: `POST /api/v1/imigration-cases/admin/case-facts/bulk-operation/`

### 5.3.3 Case Analytics

**Screen Name**: `CaseAnalyticsScreen`

**Analytics Dashboard**:
- **Metrics Cards**:
  - Total Cases
  - Cases by Status (breakdown)
  - Cases by Jurisdiction (breakdown)
  - Cases by User (top 10)
- **Charts**:
  - Cases over time (line chart)
  - Status distribution (pie chart)
  - Jurisdiction distribution (bar chart)
- **API Endpoint**: `GET /api/v1/imigration-cases/admin/statistics/`
- **Query Parameters**: `date_from`, `date_to` (optional)
- **Response Data**:
  ```json
  {
    "message": "Immigration cases statistics retrieved successfully",
    "data": {
      "cases": {
        "total_cases": 150,
        "draft_cases": 20,
        "evaluated_cases": 50,
        "awaiting_review_cases": 30,
        "reviewed_cases": 40,
        "closed_cases": 10,
        "cases_by_status": {...},
        "cases_by_jurisdiction": {...},
        "cases_by_user": {...}
      },
      "case_facts": {
        "total_facts": 500,
        "facts_by_source": {...},
        "facts_by_key": {...}
      }
    }
  }
  ```
- **UI Behavior**:
  - Date range selector
  - Export charts as images
  - Drill-down on metrics

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

---

# Module 3: Eligibility Checks & AI Decisions

This module handles automated eligibility evaluation using AI reasoning and rule engine evaluation.

## 6.1 User App Perspective

### 6.1.1 Eligibility Check Request

**Screen Name**: `EligibilityCheckScreen`, `EligibilityResultsScreen`

**User Journey: Run Eligibility Check**:
```
Case Detail → Eligibility Results Tab → "Run Eligibility Check" button
→ Loading Screen → Results Display
```

**Eligibility Check Request**:
- **Trigger**: 
  - Manual: User clicks "Run Eligibility Check" button
  - Automatic: When case facts are updated and case is submitted
- **API Endpoint**: `POST /api/v1/imigration-cases/cases/<id>/eligibility`
- **Request Parameters**: None (uses case facts from database)
- **Response Data** (during processing):
  ```json
  {
    "message": "Eligibility check in progress",
    "data": {
      "status": "processing",
      "estimated_time_seconds": 30
    }
  }
  ```
- **UI Behavior**:
  - Show loading spinner
  - Display "Analyzing your case... This may take 30 seconds"
  - Progress indicator (estimated)
  - Disable button during processing

**Eligibility Results Screen Specifications**:
- **Results Summary Section**:
  - Overview message: "Based on your information, here are your eligibility results"
  - Number of visa types evaluated
  - Overall confidence indicator (if multiple visa types)
- **Results Cards per Visa Type**:
  - Visa Type Name (header)
  - Outcome Badge:
    - "Likely Eligible" (green, confidence >= 0.7)
    - "Possibly Eligible" (yellow, 0.4 <= confidence < 0.7)
    - "Unlikely Eligible" (red, confidence < 0.4)
  - Confidence Meter:
    - Visual progress bar (0-100%)
    - Percentage display
    - Color-coded (green/yellow/red)
  - Key Requirements Checklist (top 3-5):
    - ✓ Passed (green checkmark)
    - ✗ Failed (red X)
    - ? Missing Information (yellow question mark)
  - "View Details" expandable button
  - Citations Section (top 3 citations with preview)
- **Action Buttons**:
  - "Run Eligibility Check Again" (if facts updated)
  - "Request Human Review" (if confidence < 60%)
  - "View Document Checklist" (link)
- **API Endpoint**: `GET /api/v1/ai-decisions/eligibility-results/`
- **Query Parameters**: `case_id` (required)
- **Response Data**:
  ```json
  {
    "message": "Eligibility results retrieved successfully",
    "data": [
      {
        "id": "uuid",
        "case_id": "uuid",
        "visa_type_id": "uuid",
        "visa_type_name": "Skilled Worker Visa",
        "outcome": "eligible",
        "confidence": 0.85,
        "reasoning_summary": "Based on your salary and job title...",
        "missing_facts": ["sponsor_name"],
        "created_at": "2025-01-15T10:30:00Z"
      }
    ]
  }
  ```
- **UI Behavior**:
  - Expandable detail sections
  - Smooth animations
  - Comparison view if multiple visa types selected
  - Highlight best option

**Eligibility Detail View (Expandable)**:
- **Full AI Reasoning Section**:
  - Complete explanation text
  - Structured breakdown of decision factors
- **Rule Evaluation Breakdown**:
  - Requirement cards:
    - Requirement Name/Code
    - Pass/Fail indicator (visual)
    - Explanation text
    - Facts Used (list of case facts)
    - Rule Expression (collapsible, technical details)
- **All Citations List**:
  - Citation cards:
    - Source URL (clickable, opens in new tab)
    - Excerpt preview (first 200 characters)
    - Document version date
    - Relevance score (0-1)
    - "View Source" button
  - Grouped by relevance or visa type
- **Confidence Breakdown**:
  - How confidence was calculated
  - Factors contributing to confidence
  - Uncertainty indicators
- **Risk Flags List**:
  - Risk flag name
  - Severity (High/Medium/Low)
  - Explanation
  - Recommendation
- **API Endpoint**: `GET /api/v1/imigration-cases/cases/<id>/eligibility/<result_id>/explanation`
- **Response Data**:
  ```json
  {
    "message": "Eligibility explanation retrieved successfully",
    "data": {
      "eligibility_result": {...},
      "ai_reasoning_log": {
        "prompt": "...",
        "response": "...",
        "model_name": "gpt-4",
        "tokens_used": 1500
      },
      "ai_citations": [
        {
          "id": "uuid",
          "source_url": "https://www.gov.uk/...",
          "excerpt": "...",
          "relevance_score": 0.92,
          "document_version": {...}
        }
      ],
      "rule_evaluations": [
        {
          "requirement_name": "Minimum Salary",
          "passed": true,
          "explanation": "Your salary of £50,000 meets the requirement of £38,700",
          "facts_used": ["salary"],
          "rule_expression": "{...}"
        }
      ]
    }
  }
  ```
- **UI Behavior**:
  - Accordion-style expansion
  - Smooth scroll to sections
  - Copy citation link button
  - Print-friendly view option

### 6.1.2 Eligibility Results Management

**Screen Name**: `EligibilityResultsListScreen`

**User Journey**:
```
Case Detail → Eligibility Results Tab → View All Results
```

**Results List Screen**:
- **Display**: All eligibility results for the case
- **Filters**: Visa type, outcome, date range
- **API Endpoint**: `GET /api/v1/ai-decisions/eligibility-results/?case_id=<id>`
- **UI Behavior**:
  - Show latest result prominently
  - Allow comparison between results
  - Delete old results option

## 6.2 Reviewer App Perspective

### 6.2.1 View Eligibility Results for Assigned Cases

**Screen Name**: `ReviewerEligibilityResultsScreen`

**User Journey**:
```
Reviewer Case Detail → Eligibility Results Tab
```

**Eligibility Results Screen Specifications**:
- **Same display as User App**, plus:
  - **Review Actions Panel**:
    - "Approve AI Decision" button
    - "Override Decision" button (opens override modal)
    - "Request More Info" button
  - **AI Reasoning Log Access**:
    - Full prompt and response visible
    - Token usage displayed
    - Model information
  - **Comparison View**:
    - Side-by-side: AI Decision vs Human Decision (if override exists)
    - Highlight differences
- **API Endpoint**: Same as User App, but with reviewer context
- **UI Behavior**:
  - Show reviewer-specific actions
  - Display override history
  - Show confidence breakdown with reviewer notes

### 6.2.2 Override Eligibility Decision

**Screen Name**: `OverrideDecisionModal`

**User Journey**:
```
Eligibility Results → "Override Decision" button → Override Modal
→ Select New Outcome → Provide Reason → Submit
```

**Override Modal Specifications**:
- **Fields**:
  - Original Outcome (display only, read-only)
  - New Outcome (radio buttons):
    - Likely Eligible
    - Possibly Eligible
    - Unlikely Eligible
  - Reason for Override (text area, required, min 50 characters)
  - Confirmation checkbox: "I understand this override will be logged"
- **API Endpoint**: `POST /api/v1/human-reviews/reviews/<review_id>/override/`
- **Request Parameters**:
  ```json
  {
    "new_outcome": "eligible",
    "reason": "The AI did not consider the applicant's exceptional circumstances...",
    "confirm_override": true
  }
  ```
- **Response Data**:
  ```json
  {
    "message": "Decision override created successfully",
    "data": {
      "override_id": "uuid",
      "original_outcome": "unlikely",
      "new_outcome": "eligible",
      "reason": "...",
      "reviewer_name": "James Smith",
      "created_at": "2025-01-15T11:00:00Z"
    }
  }
  ```
- **UI Behavior**:
  - Preview original AI result
  - Character counter for reason field
  - Validation before submission
  - Success toast and refresh results

## 6.3 Admin App Perspective

### 6.3.1 Eligibility Results Management

**Screen Name**: `AdminEligibilityResultsScreen`

**User Journey**:
```
Admin Dashboard → AI Decisions → Eligibility Results
```

**Eligibility Results List Screen**:
- **Table View**:
  - Result ID
  - Case ID
  - User Email
  - Visa Type
  - Outcome
  - Confidence Score
  - Created Date
  - Actions (View, Update, Delete)
- **Advanced Filters**:
  - Case ID
  - Visa Type ID
  - Outcome (eligible/not_eligible/requires_review)
  - Min Confidence (0-1)
  - Date range
- **API Endpoint**: `GET /api/v1/ai-decisions/admin/eligibility-results/`
- **Query Parameters**:
  - `case_id` (optional)
  - `visa_type_id` (optional)
  - `outcome` (optional)
  - `min_confidence` (optional)
  - `date_from` (optional)
  - `date_to` (optional)
- **Bulk Operations**: 
  - Bulk delete
  - Bulk update outcome
- **API Endpoint**: `POST /api/v1/ai-decisions/admin/eligibility-results/bulk-operation/`

### 6.3.2 AI Reasoning Logs Management

**Screen Name**: `AdminAIReasoningLogsScreen`

**AI Reasoning Logs List**:
- **Table View**:
  - Log ID
  - Case ID
  - Model Name
  - Tokens Used
  - Created Date
  - Actions (View, Delete)
- **Filters**:
  - Case ID
  - Model Name
  - Min Tokens
  - Date range
- **API Endpoint**: `GET /api/v1/ai-decisions/admin/ai-reasoning-logs/`
- **Detail View**:
  - Full prompt text
  - Full response text
  - Model configuration
  - Token breakdown
  - Citations used
- **API Endpoint**: `GET /api/v1/ai-decisions/admin/ai-reasoning-logs/<id>/`

### 6.3.3 AI Citations Management

**Screen Name**: `AdminAICitationsScreen`

**AI Citations List**:
- **Table View**:
  - Citation ID
  - Reasoning Log ID
  - Source URL
  - Relevance Score
  - Created Date
- **Filters**:
  - Reasoning Log ID
  - Document Version ID
  - Min Relevance
  - Date range
- **API Endpoint**: `GET /api/v1/ai-decisions/admin/ai-citations/`
- **Update Capability**: Can update relevance score and excerpt

### 6.3.4 AI Decisions Analytics

**Screen Name**: `AdminAIDecisionsAnalyticsScreen`

**Analytics Dashboard**:
- **Metrics Cards**:
  - Total Eligibility Results
  - Results by Outcome
  - Average Confidence Score
  - Results Requiring Review
- **Charts**:
  - Confidence Score Distribution (histogram)
  - Outcomes over Time (line chart)
  - Token Usage Trends (line chart)
- **API Endpoint**: `GET /api/v1/ai-decisions/admin/statistics/`
- **Token Usage Analytics**: `GET /api/v1/ai-decisions/admin/token-usage/`
- **Citation Quality Analytics**: `GET /api/v1/ai-decisions/admin/citation-quality/`

---

# Module 4: Document Management

This module handles document upload, validation, classification, OCR processing, and document status tracking.

## 7.1 User App Perspective

### 7.1.1 Document Checklist & Upload

**Screen Name**: `DocumentChecklistScreen`, `DocumentUploadModal`

**User Journey: Upload Documents**:
```
Case Detail → Documents Tab → Document Checklist
→ Select Document Type → Upload Modal → Drag & Drop File
→ Upload Progress → Processing Status → Verification Complete
```

**Document Checklist Screen Specifications**:
- **Checklist View**:
  - Document Type Name (e.g., "Passport", "Bank Statement")
  - Mandatory Indicator (badge: Required/Optional)
  - Status Badge:
    - "Provided" (green, document uploaded and verified)
    - "Missing" (red, no document uploaded)
    - "Incomplete" (yellow, document uploaded but needs attention)
    - "Processing" (blue, document being processed)
  - Upload Button (if missing, opens upload modal)
  - Progress Percentage Indicator (e.g., "3 of 5 documents provided - 60%")
- **Upload Interface**:
  - Drag & Drop Zone (large, prominent):
    - Visual drop area with dashed border
    - "Drop files here" text
    - Hover state (highlighted border)
  - File Picker Button (fallback)
  - File Type Indicator: "Accepted: PDF, JPG, PNG, DOC, DOCX"
  - File Size Limit: "Maximum file size: 10MB"
  - Upload Progress Bar (during upload):
    - Percentage display
    - Animated progress
    - Cancel button
  - Success/Error Feedback Messages:
    - Success: Green toast "Document uploaded successfully"
    - Error: Red toast with error message and retry option
- **Document List (Uploaded Documents)**:
  - Thumbnail/Icon Preview:
    - PDF icon for PDFs
    - Image thumbnail for images
    - Document icon for other types
  - Document Type Name
  - File Name
  - Upload Date (relative: "2 hours ago")
  - Validation Status Badge:
    - "Verified" (green)
    - "Processing" (blue)
    - "Needs Attention" (yellow)
    - "Rejected" (red)
  - Actions Menu (three-dot menu):
    - View (opens document viewer)
    - Download
    - Delete (with confirmation)
    - Re-upload
- **Completion Percentage Indicator**:
  - Visual progress bar
  - "X of Y documents provided"
  - Percentage display
- **API Endpoint**: `POST /api/v1/document-handling/case-documents/`
- **Request Parameters** (multipart/form-data):
  ```
  case_id: uuid (required)
  document_type_id: uuid (optional, can be auto-detected)
  file: binary (required, max 10MB)
  ```
- **Response Data**:
  ```json
  {
    "message": "Document uploaded successfully",
    "data": {
      "id": "uuid",
      "case_id": "uuid",
      "document_type_name": "Passport",
      "file_name": "passport.pdf",
      "file_size": 1024000,
      "status": "processing",
      "classification_confidence": null,
      "uploaded_at": "2025-01-15T10:00:00Z"
    }
  }
  ```
- **UI Behavior**:
  - Real-time upload progress
  - Auto-refresh status after upload
  - Show processing indicator
  - Notification when processing completes
  - Error handling with retry option

**Document Upload Modal Specifications**:
- **Modal Layout**:
  - Header: "Upload Document - [Document Type]"
  - Drag & Drop Area (large, centered)
  - File Picker Button (below drop zone)
  - Selected File Display (if file selected):
    - File name
    - File size
    - File type icon
    - Remove button
  - Upload Button (disabled until file selected)
  - Cancel Button
- **Validation**:
  - File type validation (before upload)
  - File size validation (before upload)
  - Inline error messages
- **UI Behavior**:
  - Close on backdrop click
  - Show loading state during upload
  - Auto-close on success
  - Keep open on error (for retry)

### 7.1.2 Document Status & Validation

**Screen Name**: `DocumentStatusScreen` (within Case Detail)

**Document Status Display**:
- **Status Indicators**:
  - Processing: "Your document is being processed..."
  - Verified: "Document verified ✓"
  - Needs Attention: "Document needs review - [reason]"
  - Rejected: "Document rejected - [reason]"
- **Validation Results**:
  - OCR Status: "Text extracted successfully" or "OCR failed"
  - Classification Status: "Classified as [type] with [X]% confidence"
  - Validation Checks:
    - ✓ Passed checks (list)
    - ✗ Failed checks (list with reasons)
    - ⚠ Warning checks (list)
- **API Endpoint**: `GET /api/v1/document-handling/case-documents/<id>/`
- **Response Data**:
  ```json
  {
    "message": "Case document retrieved successfully",
    "data": {
      "id": "uuid",
      "file_name": "passport.pdf",
      "status": "verified",
      "classification_confidence": 0.95,
      "ocr_text": "PASSPORT\nUNITED KINGDOM...",
      "checks": [
        {
          "check_type": "ocr",
          "result": "passed",
          "details": {...}
        },
        {
          "check_type": "classification",
          "result": "passed",
          "details": {
            "confidence": 0.95,
            "reasoning": "..."
          }
        }
      ]
    }
  }
  ```
- **UI Behavior**:
  - Real-time status updates (polling or WebSocket)
  - Expandable validation details
  - Show OCR text preview (if available)
  - Download document option

### 7.1.3 Document Viewer

**Screen Name**: `DocumentViewerScreen`

**Document Viewer**:
- **Viewer Layout**:
  - Document preview (PDF viewer or image viewer)
  - Document metadata sidebar:
    - File name
    - Document type
    - Upload date
    - File size
    - Status
    - Validation results
  - Actions toolbar:
    - Download
    - Delete
    - Re-upload
- **API Endpoint**: `GET /api/v1/document-handling/case-documents/<id>/file/` (returns file URL or binary)
- **UI Behavior**:
  - Full-screen viewer option
  - Zoom controls
  - Print option
  - Close button

## 7.2 Reviewer App Perspective

### 7.2.1 View Documents for Assigned Cases

**Screen Name**: `ReviewerDocumentListScreen`

**User Journey**:
```
Reviewer Case Detail → Documents Tab
```

**Document List Screen Specifications**:
- **Same display as User App**, plus:
  - **Review Actions**:
    - "Validate Classification" button (if classification confidence < 0.7)
    - "Reclassify Document" button
    - "Approve Document" button
    - "Reject Document" button (with reason)
  - **Document Validation Panel**:
    - Override classification option
    - Add validation notes
    - Mark as verified/rejected
- **API Endpoint**: `GET /api/v1/document-handling/case-documents/?case_id=<id>`
- **UI Behavior**:
  - Show reviewer-specific actions
  - Display validation history
  - Show all document checks

### 7.2.2 Document Validation

**Screen Name**: `DocumentValidationModal`

**Validation Modal**:
- **Fields**:
  - Current Classification (display only)
  - New Classification (dropdown, if reclassifying)
  - Validation Notes (text area)
  - Action (radio):
    - Approve Document
    - Reject Document
  - Rejection Reason (text area, required if rejecting)
- **API Endpoint**: `POST /api/v1/document-handling/document-checks/create/`
- **Request Parameters**:
  ```json
  {
    "case_document_id": "uuid",
    "check_type": "validation",
    "result": "passed",
    "details": {
      "reviewer_notes": "Document verified manually",
      "classification_override": null
    },
    "performed_by": "Human Reviewer"
  }
  ```
- **UI Behavior**:
  - Show document preview
  - Confirmation before submission
  - Success notification

## 7.3 Admin App Perspective

### 7.3.1 All Documents Management

**Screen Name**: `AdminDocumentListScreen`, `AdminDocumentDetailScreen`

**Document List Screen**:
- **Table View**:
  - Document ID
  - Case ID
  - User Email
  - Document Type
  - File Name
  - File Size
  - Status
  - Classification Confidence
  - Has OCR Text (boolean)
  - Uploaded Date
  - Actions (View, Update, Delete)
- **Advanced Filters**:
  - Case ID
  - Document Type ID
  - Status
  - Has OCR Text (boolean)
  - Min Confidence (0-1)
  - MIME Type
  - Date range
- **API Endpoint**: `GET /api/v1/document-handling/admin/case-documents/`
- **Query Parameters**:
  - `case_id` (optional)
  - `document_type_id` (optional)
  - `status` (optional)
  - `has_ocr_text` (optional, boolean)
  - `min_confidence` (optional)
  - `mime_type` (optional)
  - `date_from` (optional)
  - `date_to` (optional)
- **Bulk Operations**:
  - Bulk delete
  - Bulk status update
  - Bulk reprocess OCR (future)
  - Bulk reprocess classification (future)

**Document Detail Screen**:
- **All information from User App**, plus:
  - **Admin Actions**:
    - Update document type
    - Update status
    - Update classification confidence
    - Update OCR text
    - Delete document (and file)
- **API Endpoint**: 
  - View: `GET /api/v1/document-handling/admin/case-documents/<id>/`
  - Update: `PUT /api/v1/document-handling/admin/case-documents/<id>/`
- **Request Parameters** (Update):
  ```json
  {
    "document_type_id": "uuid",
    "status": "verified",
    "classification_confidence": 0.95,
    "ocr_text": "Updated OCR text"
  }
  ```

### 7.3.2 Document Checks Management

**Screen Name**: `AdminDocumentChecksScreen`

**Document Checks List**:
- **Table View**:
  - Check ID
  - Document ID
  - Document File Name
  - Case ID
  - Check Type (OCR, Classification, Validation, Authenticity)
  - Result (Passed, Failed, Warning, Pending)
  - Performed By
  - Created Date
- **Filters**:
  - Case Document ID
  - Check Type
  - Result
  - Performed By
  - Date range
- **API Endpoint**: `GET /api/v1/document-handling/admin/document-checks/`
- **Update Capability**: Can update check results and details

### 7.3.3 Document Analytics

**Screen Name**: `AdminDocumentAnalyticsScreen`

**Analytics Dashboard**:
- **Metrics Cards**:
  - Total Documents
  - Documents by Status
  - Documents with OCR
  - Average Classification Confidence
  - Total File Size (MB)
- **Charts**:
  - Documents over Time (line chart)
  - Status Distribution (pie chart)
  - Document Type Distribution (bar chart)
  - Classification Confidence Distribution (histogram)
- **API Endpoint**: `GET /api/v1/document-handling/admin/statistics/`
- **Response Data**:
  ```json
  {
    "message": "Document handling statistics retrieved successfully",
    "data": {
      "case_documents": {
        "total": 10000,
        "by_status": [...],
        "with_ocr": 9500,
        "without_ocr": 500,
        "average_classification_confidence": 0.89,
        "total_file_size_bytes": 10737418240,
        "total_file_size_mb": 10240.0,
        "recent_activity": {
          "last_24_hours": 500,
          "last_7_days": 3000,
          "last_30_days": 10000
        },
        "by_document_type": [...]
      },
      "document_checks": {
        "total": 50000,
        "by_type": [...],
        "by_result": [...],
        "failed": 5000,
        "passed": 40000,
        "warning": 3000,
        "pending": 2000
      }
    }
  }
  ```

---

# Module 5: AI Voice Calls

This module enables 30-minute voice-based conversations between users and an AI agent about their specific immigration case.

## 8.1 User App Perspective

### 8.1.1 Call Session Creation

**Screen Name**: `CallSessionCreateScreen`, `CallSessionPrepareScreen`

**User Journey: Start AI Call**:
```
Case Detail → "Start AI Call" button
→ Call Session Create → Prepare Call → Start Call
→ Voice Interface → Conversation → End Call
```

**Call Session Create Screen**:
- **Fields**:
  - Case Selection (dropdown, pre-filled if from case detail)
  - Parent Session (optional, if retrying a call)
- **API Endpoint**: `POST /api/v1/ai-calls/sessions/`
- **Request Parameters**:
  ```json
  {
    "case_id": "uuid",
    "parent_session_id": "uuid" // optional, for retries
  }
  ```
- **Response Data**:
  ```json
  {
    "message": "Call session created successfully",
    "data": {
      "id": "uuid",
      "case_id": "uuid",
      "status": "created",
      "created_at": "2025-01-15T10:00:00Z"
    }
  }
  ```
- **UI Behavior**:
  - Show session creation confirmation
  - Redirect to prepare screen

**Call Session Prepare Screen**:
- **Loading State**:
  - "Preparing your call session..."
  - "Building case context..."
  - "Validating information..."
- **API Endpoint**: `POST /api/v1/ai-calls/sessions/<session_id>/prepare/`
- **Response Data**:
  ```json
  {
    "message": "Call session prepared successfully",
    "data": {
      "id": "uuid",
      "status": "ready",
      "context_version": 1,
      "context_hash": "sha256_hash",
      "ready_at": "2025-01-15T10:01:00Z"
    }
  }
  ```
- **UI Behavior**:
  - Show progress indicators
  - Auto-redirect to start screen when ready
  - Show error if preparation fails

### 8.1.2 Voice Call Interface

**Screen Name**: `VoiceCallScreen`

**Voice Call Interface**:
- **Call Header**:
  - Case Name/ID
  - Call Duration Timer (MM:SS format)
  - Time Remaining Indicator (with warnings at 5min and 1min)
  - End Call button
- **Conversation Area**:
  - Transcript Display (scrollable):
    - User messages (right-aligned, blue)
    - AI responses (left-aligned, gray)
    - Timestamps (small, muted)
    - Turn numbers
  - Current Speaking Indicator (animated)
- **Input Area**:
  - Microphone Button (large, prominent):
    - Press and hold to speak
    - Visual feedback (pulsing animation)
    - Release to send
  - Text Input (optional, for typing):
    - Text field
    - Send button
  - Audio Output Indicator (when AI is speaking)
- **Status Indicators**:
  - Connection Status (Connected/Disconnected)
  - Audio Status (Microphone/Speaker)
  - Guardrails Triggered (warning badge, if any)
- **API Endpoints**:
  - Start: `POST /api/v1/ai-calls/sessions/<session_id>/start/`
  - Speech: `POST /api/v1/ai-calls/sessions/<session_id>/speech/` (multipart/form-data with audio file)
  - Heartbeat: `POST /api/v1/ai-calls/sessions/<session_id>/heartbeat/`
  - End: `POST /api/v1/ai-calls/sessions/<session_id>/end/`
  - Terminate: `POST /api/v1/ai-calls/sessions/<session_id>/terminate/`
- **Speech Request Parameters**:
  ```
  audio: binary file (required, max 10MB)
  ```
- **Speech Response Data**:
  ```json
  {
    "message": "Speech processed successfully",
    "data": {
      "text": "What documents do I need?",
      "confidence": 0.92,
      "turn_id": "uuid",
      "ai_response": {
        "text": "Based on your case, you need...",
        "audio_url": "https://...",
        "turn_id": "uuid",
        "guardrails_triggered": false
      },
      "time_remaining_seconds": 1200,
      "warning_level": "none"
    }
  }
  ```
- **UI Behavior**:
  - Real-time transcript updates
  - Audio playback for AI responses
  - Visual feedback for speaking/listening states
  - Warning notifications at 5min and 1min remaining
  - Auto-end at 30 minutes
  - Confirmation modal before ending call

### 8.1.3 Call Transcript & Summary

**Screen Name**: `CallTranscriptScreen`, `CallSummaryScreen`

**Call Transcript Screen**:
- **Transcript Display**:
  - Full conversation transcript
  - Turn-by-turn display
  - Timestamps
  - Speaker labels (You / AI)
  - Guardrails indicators (if triggered)
- **API Endpoint**: `GET /api/v1/ai-calls/sessions/<session_id>/transcript/`
- **Response Data**:
  ```json
  {
    "message": "Transcript retrieved successfully",
    "data": {
      "session_id": "uuid",
      "transcripts": [
        {
          "turn_number": 1,
          "turn_type": "user",
          "text": "What documents do I need?",
          "timestamp": "2025-01-15T10:05:00Z",
          "duration_seconds": 3
        },
        {
          "turn_number": 2,
          "turn_type": "ai",
          "text": "Based on your case...",
          "timestamp": "2025-01-15T10:05:05Z",
          "duration_seconds": 8,
          "guardrails_triggered": false
        }
      ]
    }
  }
  ```
- **UI Behavior**:
  - Searchable transcript
  - Export to PDF option
  - Print-friendly view

**Call Summary Screen**:
- **Summary Display**:
  - Call Duration
  - Total Turns
  - Key Topics Discussed
  - Summary Text (AI-generated)
  - Attached to Case Timeline
- **API Endpoint**: `GET /api/v1/ai-calls/sessions/<session_id>/`
- **UI Behavior**:
  - Show summary card
  - Link to full transcript
  - Link to case detail

## 8.2 Reviewer App Perspective

### 8.2.1 View Call Sessions for Assigned Cases

**Screen Name**: `ReviewerCallSessionsScreen`

**User Journey**:
```
Reviewer Case Detail → Call Sessions Tab
```

**Call Sessions List**:
- **Session Cards**:
  - Session ID
  - Call Duration
  - Status (Completed, Terminated, Failed)
  - Date/Time
  - Guardrails Triggered Count
  - Warnings Count
  - Refusals Count
- **API Endpoint**: `GET /api/v1/ai-calls/sessions/?case_id=<id>` (filtered by reviewer access)
- **UI Behavior**:
  - Show all sessions for assigned cases
  - Link to transcript view
  - Filter by status

### 8.2.2 Call Transcript Review

**Screen Name**: `ReviewerCallTranscriptScreen`

**Transcript Review**:
- **Same display as User App**, plus:
  - **Review Actions**:
    - Flag for compliance review
    - Add review notes
    - Export transcript
- **Guardrails Analysis**:
  - Show all guardrails triggered
  - Review refusal messages
  - Check compliance
- **API Endpoint**: Same as User App
- **UI Behavior**:
  - Highlight guardrails events
  - Show full prompts (if stored)
  - Review context bundle

## 8.3 Admin App Perspective

### 8.3.1 All Call Sessions Management

**Screen Name**: `AdminCallSessionsScreen`

**Call Sessions List**:
- **Table View**:
  - Session ID
  - Case ID
  - User Email
  - Status
  - Duration
  - Guardrails Triggered
  - Warnings Count
  - Refusals Count
  - Created Date
  - Actions (View, Delete)
- **Advanced Filters**:
  - Case ID
  - User ID
  - Status
  - Date range
  - Guardrails triggered (boolean)
- **API Endpoint**: `GET /api/v1/ai-calls/admin/sessions/`
- **Query Parameters**:
  - `case_id` (optional)
  - `user_id` (optional)
  - `status` (optional)
  - `date_from` (optional)
  - `date_to` (optional)
  - `guardrails_triggered` (optional, boolean)

### 8.3.2 Call Analytics

**Screen Name**: `AdminCallAnalyticsScreen`

**Analytics Dashboard**:
- **Metrics Cards**:
  - Total Call Sessions
  - Average Call Duration
  - Guardrails Triggered Count
  - Refusals Count
  - Warnings Count
- **Charts**:
  - Calls over Time (line chart)
  - Duration Distribution (histogram)
  - Guardrails Events over Time (line chart)
  - Status Distribution (pie chart)
- **API Endpoint**: `GET /api/v1/ai-calls/admin/statistics/`
- **Guardrail Analytics**: `GET /api/v1/ai-calls/admin/guardrail-analytics/`
- **Response Data**:
  ```json
  {
    "message": "Call session statistics retrieved successfully",
    "data": {
      "total_sessions": 1000,
      "completed_sessions": 850,
      "terminated_sessions": 100,
      "failed_sessions": 50,
      "average_duration_seconds": 1200,
      "total_guardrails_triggered": 150,
      "total_warnings": 300,
      "total_refusals": 50
    }
  }
  ```

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

---

# Module 6: Human Reviews

This module handles human review requests, reviewer assignment, review actions, and review history tracking.

## 9.1 User App Perspective

### 9.1.1 Request Human Review

**Screen Name**: `RequestReviewModal`, `ReviewStatusScreen`

**User Journey: Request Review**:
```
Case Detail → "Request Human Review" button
→ Request Review Modal → Fill Form → Submit
→ Review Status Screen → Track Progress → Receive Feedback
```

**Request Review Modal Specifications**:
- **Fields**:
  - Note/Question (text area, required, min 20 characters):
    - Placeholder: "What would you like the reviewer to help with?"
    - Character counter
  - Priority (radio buttons, required):
    - Normal (default)
    - Urgent
  - Estimated Completion Time (display only):
    - Normal: "Within 2-3 business days"
    - Urgent: "Within 24 hours"
- **API Endpoint**: `POST /api/v1/human-reviews/reviews/create/`
- **Request Parameters**:
  ```json
  {
    "case_id": "uuid",
    "note": "I'm unsure about my salary requirement. Can you review?",
    "priority": "normal"
  }
  ```
- **Response Data**:
  ```json
  {
    "message": "Review request created successfully",
    "data": {
      "id": "uuid",
      "case_id": "uuid",
      "status": "pending_assignment",
      "priority": "normal",
      "created_at": "2025-01-15T10:00:00Z",
      "estimated_completion": "2025-01-17T10:00:00Z"
    }
  }
  ```
- **UI Behavior**:
  - Show validation errors inline
  - Disable submit until required fields filled
  - Success toast and close modal
  - Redirect to Review Status screen

**Review Status Screen Specifications**:
- **Status Badge**:
  - "Awaiting Assignment" (yellow)
  - "In Progress" (blue)
  - "Completed" (green)
  - "Requested More Info" (orange)
- **Status Details**:
  - Reviewer Name (if assigned): "Assigned to: [Name]"
  - SLA Deadline: "Expected completion: [Date]"
  - Time in Queue: "In queue for: [Duration]"
- **Reviewer Feedback Section** (when completed):
  - Reviewer Notes (text display)
  - Decision Summary
  - Recommendations
  - Next Steps
- **API Endpoint**: `GET /api/v1/human-reviews/reviews/<id>/`
- **Response Data**:
  ```json
  {
    "message": "Review retrieved successfully",
    "data": {
      "id": "uuid",
      "case_id": "uuid",
      "status": "completed",
      "priority": "normal",
      "note": "User's question...",
      "reviewer_name": "James Smith",
      "reviewer_notes": "After reviewing your case...",
      "completed_at": "2025-01-16T14:00:00Z",
      "sla_deadline": "2025-01-17T10:00:00Z"
    }
  }
  ```
- **UI Behavior**:
  - Real-time status updates (polling)
  - Show progress indicator
  - Notification when status changes
  - Link to case detail

### 9.1.2 Review History

**Screen Name**: `ReviewHistoryScreen` (within Case Detail)

**Review History Display**:
- **Timeline View**:
  - All reviews for the case (chronological)
  - Each review shows:
    - Request date
    - Status
    - Reviewer name (if assigned)
    - Completion date (if completed)
    - Quick preview of notes
- **API Endpoint**: `GET /api/v1/human-reviews/reviews/?case_id=<id>`
- **UI Behavior**:
  - Expandable review details
  - Filter by status
  - Sort by date

## 9.2 Reviewer App Perspective

### 9.2.1 Review Dashboard

**Screen Name**: `ReviewerDashboardScreen`

**User Journey**:
```
Reviewer Login → Dashboard → Review Queue
→ Select Review → Review Detail Screen
```

**Reviewer Dashboard Screen Specifications**:
- **Metrics Cards**:
  - Total Pending Reviews (number, badge)
  - Assigned to Me (number)
  - Overdue Reviews (number, red if > 0)
  - Average Completion Time (MM:SS format)
- **Review Cards List**:
  - Case ID
  - User Name/Email
  - Visa Type
  - AI Confidence Score (visual indicator)
  - Risk Flags (badges):
    - Low Confidence
    - Rule Conflict
    - Missing Documents
    - Other
  - SLA Deadline (countdown timer, color-coded):
    - Green: > 24 hours remaining
    - Yellow: 12-24 hours remaining
    - Red: < 12 hours remaining
  - Time in Queue (relative: "2 hours ago")
  - Quick Action Buttons:
    - "Start Review" (primary)
    - "View Details" (secondary)
- **Filters Sidebar**:
  - Status Filter (dropdown): All, Pending, In Progress, Completed
  - Priority Filter (dropdown): All, Normal, Urgent
  - Visa Type Filter (multi-select)
  - Date Assigned Filter (date range)
- **Sort Options** (dropdown):
  - By SLA Deadline (urgent first)
  - By Confidence Score (low first)
  - By Date Assigned (oldest first)
- **API Endpoint**: `GET /api/v1/human-reviews/reviews/assigned/`
- **Response Data**:
  ```json
  {
    "message": "Assigned reviews retrieved successfully",
    "data": [
      {
        "id": "uuid",
        "case_id": "uuid",
        "user_email": "user@example.com",
        "status": "pending",
        "priority": "normal",
        "ai_confidence": 0.55,
        "risk_flags": ["low_confidence"],
        "sla_deadline": "2025-01-17T10:00:00Z",
        "time_in_queue": "2 hours"
      }
    ]
  }
  ```
- **UI Behavior**:
  - Auto-refresh every 30 seconds
  - Highlight overdue reviews
  - Show empty state if no reviews
  - Quick filter chips

### 9.2.2 Review Detail Screen

**Screen Name**: `ReviewDetailScreen`

**User Journey**:
```
Review Queue → Select Review → Review Detail Screen
→ Review Case → Take Action → Submit Review
```

**Review Detail Screen Specifications**:
- **Tabbed Interface**:
  - **Tab 1: Case Summary**:
    - Case Facts (key-value pairs, organized by category)
    - User Profile Info (name, nationality, contact)
    - Case Timeline (creation, updates, review requests)
  - **Tab 2: AI Analysis**:
    - Eligibility Results (all visa types)
    - Full AI Reasoning (expandable)
    - Rule Evaluation Breakdown (per requirement)
    - Citations List (all sources)
    - Confidence Breakdown (how calculated)
  - **Tab 3: Documents**:
    - Document Grid/List
    - Document Viewer (click to view full document)
    - Validation Results per Document
    - Document Status Indicators
  - **Tab 4: History**:
    - Previous Reviews (if any)
    - Notes Timeline
    - Override History
    - Status Change History
- **Action Panel** (sticky, always visible):
  - "Approve AI Decision" Button:
    - Opens confirmation modal
    - Option to add note
    - "Confirm Approval" button
  - "Override Decision" Dropdown:
    - Opens override form (see Module 3)
  - "Request More Info" Button:
    - Opens form with text area
    - "Send Request" button
    - Updates case status to "awaiting_user_input"
  - "Escalate" Button:
    - Opens escalation form:
      - Reason for escalation (text area)
      - Select Senior Reviewer (dropdown)
      - "Escalate" button
  - Notes Text Area:
    - Placeholder: "Add review notes..."
    - Auto-save as typing
    - Character counter
  - "Submit Review" Button:
    - Disabled until action taken
    - Confirmation modal
- **Side-by-Side Comparison View** (if override exists):
  - AI Outcome vs Human Decision
  - Confidence Scores Comparison
  - Reasoning Comparison
- **API Endpoints**:
  - View: `GET /api/v1/human-reviews/reviews/<id>/`
  - Approve: `POST /api/v1/human-reviews/reviews/<id>/approve/`
  - Override: `POST /api/v1/human-reviews/reviews/<id>/override/`
  - Request Info: `POST /api/v1/human-reviews/reviews/<id>/request-info/`
  - Escalate: `POST /api/v1/human-reviews/reviews/<id>/escalate/`
  - Complete: `POST /api/v1/human-reviews/reviews/<id>/complete/`
- **Approve Request Parameters**:
  ```json
  {
    "notes": "AI decision is correct. Case looks good.",
    "confirm_approval": true
  }
  ```
- **Request Info Parameters**:
  ```json
  {
    "information_request": "Please provide your sponsor's license number."
  }
  ```
- **UI Behavior**:
  - Show all relevant case information
  - Highlight risk flags
  - Show SLA countdown
  - Auto-save notes
  - Confirmation modals for all actions
  - Success toast on completion
  - Redirect to dashboard after completion

### 9.2.3 Review History & Notes

**Screen Name**: `ReviewHistoryScreen`

**Review History**:
- **Completed Reviews List**:
  - Review ID
  - Case ID
  - User Email
  - Completion Date
  - Action Taken (Approved, Overridden, Escalated)
  - Quick View button
- **API Endpoint**: `GET /api/v1/human-reviews/reviews/completed/`
- **UI Behavior**:
  - Filter by date range
  - Search by case ID or user email
  - Export review history

## 9.3 Admin App Perspective

### 9.3.1 All Reviews Management

**Screen Name**: `AdminReviewsScreen`

**Reviews List**:
- **Table View**:
  - Review ID
  - Case ID
  - User Email
  - Reviewer Name
  - Status
  - Priority
  - Created Date
  - SLA Deadline
  - Actions (View, Reassign, Complete)
- **Advanced Filters**:
  - Case ID
  - User ID
  - Reviewer ID
  - Status
  - Priority
  - Date range
  - SLA Status (On Time, Overdue, Upcoming)
- **API Endpoint**: `GET /api/v1/human-reviews/admin/reviews/`
- **Bulk Operations**:
  - Bulk reassign reviewers
  - Bulk status update
  - Bulk priority update

### 9.3.2 Reviewer Assignment

**Screen Name**: `ReviewerAssignmentScreen`

**Assignment Management**:
- **Assign Review**:
  - Select Review (from list)
  - Select Reviewer (dropdown with availability)
  - Assign button
- **Reassign Review**:
  - Current reviewer (display)
  - New reviewer (dropdown)
  - Reason (text area)
  - Reassign button
- **API Endpoint**: 
  - Assign: `POST /api/v1/human-reviews/admin/reviews/<id>/assign/`
  - Reassign: `POST /api/v1/human-reviews/admin/reviews/<id>/reassign/`
- **Request Parameters** (Assign):
  ```json
  {
    "reviewer_id": "uuid",
    "priority": "normal"
  }
  ```
- **UI Behavior**:
  - Show reviewer workload
  - Round-robin assignment option
  - Auto-assign based on availability

### 9.3.3 Review Analytics

**Screen Name**: `AdminReviewAnalyticsScreen`

**Analytics Dashboard**:
- **Metrics Cards**:
  - Total Reviews
  - Pending Reviews
  - Completed Reviews
  - Average Completion Time
  - SLA Compliance Rate
  - Override Rate
- **Charts**:
  - Reviews over Time (line chart)
  - Completion Time Distribution (histogram)
  - Reviewer Performance (bar chart)
  - Status Distribution (pie chart)
- **API Endpoint**: `GET /api/v1/human-reviews/admin/analytics/`
- **Response Data**:
  ```json
  {
    "message": "Review analytics retrieved successfully",
    "data": {
      "total_reviews": 500,
      "pending_reviews": 50,
      "completed_reviews": 400,
      "average_completion_time_seconds": 3600,
      "sla_compliance_rate": 0.92,
      "override_rate": 0.15,
      "reviews_by_status": {...},
      "reviews_by_reviewer": {...}
    }
  }
  ```

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

---

# Module 7: Payments

This module handles payment creation, processing, gateway integration, and payment history tracking.

## 10.1 User App Perspective

### 10.1.1 Payment Creation & Processing

**Screen Name**: `PaymentScreen`, `PaymentProcessingScreen`

**User Journey: Make Payment**:
```
Case Detail → "Make Payment" button
→ Payment Screen → Select Amount → Select Payment Method
→ Payment Processing → Gateway Redirect → Payment Verification
→ Payment Confirmation
```

**Payment Screen Specifications**:
- **Payment Details**:
  - Case Information (display only):
    - Case ID
    - Jurisdiction
    - Service Type (Eligibility Check, Document Review, etc.)
  - Amount (display, with currency):
    - Amount: £99.00
    - Currency: GBP (display only)
  - Payment Method Selection (radio buttons):
    - Stripe (Credit/Debit Card)
    - PayPal
    - Bank Transfer (if enabled)
- **API Endpoint**: `POST /api/v1/payments/create/`
- **Request Parameters**:
  ```json
  {
    "case_id": "uuid",
    "amount": 99.00,
    "currency": "GBP",
    "payment_provider": "stripe"
  }
  ```
- **Response Data**:
  ```json
  {
    "message": "Payment created successfully",
    "data": {
      "id": "uuid",
      "case_id": "uuid",
      "amount": "99.00",
      "currency": "GBP",
      "status": "pending",
      "payment_provider": "stripe",
      "created_at": "2025-01-15T10:00:00Z"
    }
  }
  ```
- **UI Behavior**:
  - Show payment amount prominently
  - Display currency selector (if multiple currencies)
  - Show payment method icons
  - Redirect to payment gateway on "Pay Now"

**Payment Processing Screen**:
- **Gateway Integration**:
  - Stripe: Embedded payment form or redirect
  - PayPal: Redirect to PayPal
  - Bank Transfer: Show bank details
- **API Endpoint**: `POST /api/v1/payments/<id>/initiate/`
- **Response Data** (Stripe):
  ```json
  {
    "message": "Payment initiated",
    "data": {
      "payment_intent_id": "pi_...",
      "client_secret": "pi_..._secret_...",
      "redirect_url": null // for embedded
    }
  }
  ```
- **UI Behavior**:
  - Show loading state
  - Handle gateway redirects
  - Show payment form (if embedded)
  - Auto-verify payment after gateway callback

**Payment Verification**:
- **API Endpoint**: `POST /api/v1/payments/<id>/verify/`
- **UI Behavior**:
  - Auto-verify after gateway redirect
  - Show success/error message
  - Redirect to payment confirmation

**Payment Confirmation Screen**:
- **Confirmation Details**:
  - Payment ID
  - Amount Paid
  - Payment Date
  - Payment Method
  - Transaction ID
  - Status (Completed)
- **Next Steps**:
  - "View Case" button
  - "Download Receipt" button
- **API Endpoint**: `GET /api/v1/payments/<id>/`
- **UI Behavior**:
  - Show success message
  - Display receipt
  - Link to case detail

### 10.1.2 Payment History

**Screen Name**: `PaymentHistoryScreen`

**Payment History Display**:
- **Payment List**:
  - Payment ID
  - Amount
  - Currency
  - Status Badge:
    - Completed (green)
    - Pending (yellow)
    - Failed (red)
    - Refunded (gray)
  - Payment Date
  - Payment Method
  - Actions (View, Download Receipt)
- **Filters**:
  - Status
  - Date range
  - Case ID
- **API Endpoint**: `GET /api/v1/payments/<id>/history/`
- **UI Behavior**:
  - Show all payments for user
  - Filter and sort options
  - Export to PDF option

## 10.2 Reviewer App Perspective

### 10.2.1 View Payments for Assigned Cases

**Screen Name**: `ReviewerPaymentListScreen`

**Payment List**:
- **Same display as User App**, but:
  - Shows payments for assigned cases only
  - Read-only access
  - Cannot process payments
- **API Endpoint**: `GET /api/v1/payments/?case_id=<id>` (filtered by reviewer access)
- **UI Behavior**:
  - Show payment status
  - Link to case detail
  - View payment details

## 10.3 Admin App Perspective

### 10.3.1 All Payments Management

**Screen Name**: `AdminPaymentListScreen`, `AdminPaymentDetailScreen`

**Payment List**:
- **Table View**:
  - Payment ID
  - Case ID
  - User Email
  - Amount
  - Currency
  - Status
  - Payment Provider
  - Transaction ID
  - Created Date
  - Actions (View, Refund, Update)
- **Advanced Filters**:
  - Case ID
  - User ID
  - Status
  - Payment Provider
  - Date range
  - Amount range
- **API Endpoint**: `GET /api/v1/payments/admin/payments/`
- **Bulk Operations**:
  - Bulk refund
  - Bulk status update

**Payment Detail Screen**:
- **All payment information**, plus:
  - **Admin Actions**:
    - Refund Payment
    - Update Status
    - View Gateway Logs
    - Retry Payment (if failed)
- **API Endpoint**: 
  - View: `GET /api/v1/payments/admin/payments/<id>/`
  - Refund: `POST /api/v1/payments/<id>/refund/`
  - Update: `PATCH /api/v1/payments/admin/payments/<id>/update/`

### 10.3.2 Payment Analytics

**Screen Name**: `AdminPaymentAnalyticsScreen`

**Analytics Dashboard**:
- **Metrics Cards**:
  - Total Payments
  - Total Revenue
  - Successful Payments
  - Failed Payments
  - Refunded Payments
  - Average Payment Amount
- **Charts**:
  - Revenue over Time (line chart)
  - Payment Status Distribution (pie chart)
  - Payment Method Distribution (bar chart)
  - Revenue by Currency (bar chart)
- **API Endpoint**: `GET /api/v1/payments/admin/statistics/`

---

# Module 8: Rules Knowledge & Data Ingestion

This module handles immigration rule extraction, validation, publishing, and data source management. **Note**: Users and Reviewers have read-only access to rules. Only Admins can manage rules and data sources.

## 11.1 User App Perspective

### 11.1.1 View Rules (Read-Only)

**Screen Name**: `RulesViewScreen` (within Eligibility Results)

**Rules Display**:
- **Rule Information** (displayed in eligibility results):
  - Rule Name
  - Rule Description
  - Applicable Visa Types
  - Effective Date
  - Source Document
- **API Endpoint**: Rules are embedded in eligibility results (see Module 3)
- **UI Behavior**:
  - Read-only display
  - Link to source document
  - Show rule version

## 11.2 Reviewer App Perspective

### 11.2.1 View Rules (Read-Only)

**Screen Name**: `ReviewerRulesViewScreen`

**Rules Display**:
- **Same as User App**, plus:
  - Rule Expression (JSON Logic, technical view)
  - Rule History (version changes)
  - Validation Status
- **API Endpoint**: `GET /api/v1/rules-knowledge/rules/<id>/`
- **UI Behavior**:
  - Read-only access
  - Can view technical details
  - Cannot edit or publish rules

## 11.3 Admin App Perspective

### 11.3.1 Rule Validation Queue

**Screen Name**: `RuleValidationQueueScreen`, `RuleValidationDetailScreen`

**User Journey: Validate Rules**:
```
Admin Dashboard → Rule Management → Validation Queue
→ Select Rule → Validation Detail → Review → Approve/Reject/Edit
```

**Rule Validation Queue Screen**:
- **Table View**:
  - Rule ID
  - Visa Code
  - Change Type Badge:
    - Requirement Change
    - Fee Change
    - Document Change
    - Other
  - Confidence Score (0-1, visual indicator)
  - Assigned Reviewer (if assigned)
  - Created Date
  - Actions (Review, Assign, Bulk Actions)
- **Filters**:
  - Status (Pending, Approved, Rejected, In Progress)
  - Change Type
  - Visa Code
  - Confidence Range (slider)
  - Assigned Reviewer
- **API Endpoint**: `GET /api/v1/data-ingestion/parsed-rules/pending/`
- **Response Data**:
  ```json
  {
    "message": "Pending parsed rules retrieved successfully",
    "data": [
      {
        "id": "uuid",
        "visa_code": "SWV",
        "change_type": "requirement_change",
        "confidence": 0.85,
        "assigned_reviewer": null,
        "created_at": "2025-01-15T10:00:00Z"
      }
    ]
  }
  ```
- **UI Behavior**:
  - Highlight low confidence rules
  - Show assignment status
  - Bulk selection for batch operations
  - Sort by confidence or date

**Rule Validation Detail Screen**:
- **Split Screen Layout**:
  - **Left Panel: Original Source Text**:
    - Source URL (clickable)
    - Document Version Date
    - Full Text Display (scrollable)
    - Highlight relevant sections
  - **Right Panel: AI-Extracted Logic**:
    - Extracted Requirements List:
      - Requirement Name
      - Requirement Value
      - Confidence Score
    - JSON Logic Expressions:
      - Editable code editor
      - Syntax highlighting
      - Validation errors
    - Confidence Breakdown:
      - How confidence was calculated
      - Factors contributing to confidence
- **Diff View Toggle**:
  - Show highlighted changes
  - Added text (green)
  - Removed text (red)
  - Changed values (yellow)
- **Previous Version Comparison**:
  - Side-by-side old vs new
  - Highlighted differences
  - Effective dates
- **Edit Interface**:
  - Editable JSON Logic expressions
  - Syntax validation (real-time)
  - Preview of changes
  - Save draft option
- **Action Buttons**:
  - "Approve" Button:
    - Opens confirmation modal
    - "Confirm Approval" button
    - Promotes rule to production
  - "Reject" Button:
    - Opens rejection form:
      - Reason (text area, required)
      - "Confirm Rejection" button
  - "Edit" Button:
    - Opens edit mode
    - Enables JSON Logic editing
  - "Save Changes" Button (in edit mode)
  - "Assign Reviewer" Button:
    - Opens assignment modal
    - Select reviewer dropdown
- **Reviewer Notes Section**:
  - Display existing notes
  - Add new note (if assigned reviewer)
- **API Endpoints**:
  - View: `GET /api/v1/data-ingestion/parsed-rules/<id>/`
  - Update: `PATCH /api/v1/data-ingestion/parsed-rules/<id>/update/`
  - Approve: `POST /api/v1/data-ingestion/parsed-rules/<id>/status/` (status: "approved")
  - Reject: `POST /api/v1/data-ingestion/parsed-rules/<id>/status/` (status: "rejected")
  - Assign: `POST /api/v1/data-ingestion/rule-validation-tasks/<id>/assign/`
- **Request Parameters** (Update):
  ```json
  {
    "json_logic": {
      "and": [
        {"<": [{"var": "age"}, 65]},
        {">=": [{"var": "salary"}, 38700]}
      ]
    },
    "confidence": 0.90
  }
  ```
- **UI Behavior**:
  - Auto-save draft edits
  - Show validation errors
  - Confirmation modals for approve/reject
  - Success toast notifications
  - Version history display

### 11.3.2 Data Source Management

**Screen Name**: `DataSourceManagementScreen`, `DataSourceDetailScreen`

**Data Sources List**:
- **Table View**:
  - Source Name
  - Base URL
  - Jurisdiction
  - Status (Active/Inactive badge)
  - Last Fetched Date
  - Success Rate (percentage)
  - Actions (Edit, Deactivate, View History, Trigger Ingestion)
- **API Endpoint**: `GET /api/v1/data-ingestion/data-sources/`
- **Response Data**:
  ```json
  {
    "message": "Data sources retrieved successfully",
    "data": [
      {
        "id": "uuid",
        "name": "UK Government Immigration Rules",
        "base_url": "https://www.gov.uk/...",
        "jurisdiction": "UK",
        "status": "active",
        "last_fetched_at": "2025-01-15T08:00:00Z",
        "success_rate": 0.95
      }
    ]
  }
  ```
- **UI Behavior**:
  - Show health indicators (green/yellow/red)
  - Highlight failed sources
  - Quick actions for common operations

**Data Source Detail Screen**:
- **Configuration Tab**:
  - Source Name
  - Base URL
  - Jurisdiction
  - Status Toggle
  - Fetch Schedule (cron expression)
  - Selectors (CSS/XPath)
- **Ingestion History Tab**:
  - History table:
    - Fetch Date
    - Status (Success/Failed)
    - Documents Found
    - Rules Extracted
    - Errors (if any)
  - Filters: Date range, status
- **Error Log Tab**:
  - Error messages
  - Stack traces
  - Retry options
- **API Endpoints**:
  - View: `GET /api/v1/data-ingestion/data-sources/<id>/`
  - Update: `PATCH /api/v1/data-ingestion/data-sources/<id>/update/`
  - Trigger: `POST /api/v1/data-ingestion/data-sources/<id>/ingest/`
- **UI Behavior**:
  - Show real-time ingestion status
  - Display error details
  - Retry failed ingestions

### 11.3.3 Document Versions & Diffs

**Screen Name**: `DocumentVersionsScreen`, `DocumentDiffScreen`

**Document Versions List**:
- **Table View**:
  - Version ID
  - Source Document
  - Version Date
  - Status (Current/Archived)
  - Changes Detected (boolean)
  - Actions (View, Compare, Archive)
- **API Endpoint**: `GET /api/v1/data-ingestion/document-versions/`
- **Filters**: Source document, date range, has changes

**Document Diff Screen**:
- **Split View**:
  - Left: Previous Version
  - Right: Current Version
  - Diff Highlighting:
    - Added (green)
    - Removed (red)
    - Changed (yellow)
- **API Endpoint**: `GET /api/v1/data-ingestion/document-diffs/<id>/`
- **UI Behavior**:
  - Side-by-side comparison
  - Line-by-line diff
  - Navigate between changes

### 11.3.4 Ingestion Analytics

**Screen Name**: `IngestionAnalyticsScreen`

**Analytics Dashboard**:
- **Metrics Cards**:
  - Total Data Sources
  - Active Sources
  - Total Documents Fetched
  - Total Rules Extracted
  - Pending Validations
  - Ingestion Success Rate
- **Charts**:
  - Ingestion Activity over Time (line chart)
  - Success Rate by Source (bar chart)
  - Rules Extracted over Time (line chart)
  - Validation Queue Size (line chart)
- **API Endpoint**: `GET /api/v1/data-ingestion/admin/statistics/`

---

# 12. End-to-End Flows & Data Transitions

This section describes complete user journeys across all three applications, showing how data flows between User, Reviewer, and Admin roles.

## 12.1 Complete Case Lifecycle Flow

### Flow: User Creates Case → Eligibility Check → Document Upload → Review → Completion

```
USER APP:
1. User creates case
   → POST /api/v1/imigration-cases/cases/create/
   → Case created with status: "draft"
   → Data: Case record created in database

2. User adds case facts
   → POST /api/v1/imigration-cases/case-facts/create/
   → Multiple fact records created
   → Case status remains "draft"

3. User runs eligibility check
   → POST /api/v1/imigration-cases/cases/<id>/eligibility
   → System automatically:
     a. Evaluates rules (Rule Engine)
     b. Runs AI reasoning (RAG)
     c. Creates EligibilityResult
     d. Creates AIReasoningLog
     e. Creates AICitations
   → Case status: "draft" → "evaluated"
   → Data: EligibilityResult linked to Case

4. User uploads documents
   → POST /api/v1/document-handling/case-documents/
   → Document uploaded, status: "uploaded"
   → Async processing:
     a. OCR extraction
     b. Document classification
     c. Validation checks
   → Document status: "uploaded" → "processing" → "verified"
   → Data: CaseDocument and DocumentCheck records created

5. User requests human review (if confidence < 60% or user chooses)
   → POST /api/v1/human-reviews/reviews/create/
   → Review created, status: "pending_assignment"
   → Case status: "evaluated" → "awaiting_review"
   → Data: Review record created, notification sent

REVIEWER APP:
6. Reviewer sees review in queue
   → GET /api/v1/human-reviews/reviews/assigned/
   → Review appears in Reviewer Dashboard

7. Reviewer starts review
   → GET /api/v1/human-reviews/reviews/<id>/
   → Review status: "pending_assignment" → "in_progress"
   → Data: Review assigned to reviewer, SLA deadline set

8. Reviewer reviews case
   → Views case facts, eligibility results, documents
   → GET /api/v1/imigration-cases/cases/<id>/
   → GET /api/v1/ai-decisions/eligibility-results/?case_id=<id>
   → GET /api/v1/document-handling/case-documents/?case_id=<id>

9. Reviewer takes action:
   Option A: Approve AI Decision
   → POST /api/v1/human-reviews/reviews/<id>/approve/
   → Review status: "in_progress" → "completed"
   → Case status: "awaiting_review" → "reviewed"
   → Data: Review completed, notification sent to user

   Option B: Override Decision
   → POST /api/v1/human-reviews/reviews/<id>/override/
   → DecisionOverride created
   → Review status: "in_progress" → "completed"
   → Case status: "awaiting_review" → "reviewed"
   → Data: Override record created, original AI result preserved

   Option C: Request More Info
   → POST /api/v1/human-reviews/reviews/<id>/request-info/
   → Review status: "in_progress" → "awaiting_user_input"
   → Case status: "awaiting_review" → "awaiting_user_input"
   → Data: Review note added, notification sent to user

USER APP:
10. User receives notification
    → GET /api/v1/human-reviews/reviews/<id>/
    → Sees reviewer feedback
    → If more info requested: Updates case facts
    → Review cycle continues

ADMIN APP:
11. Admin monitors system
    → GET /api/v1/immigration-cases/admin/statistics/
    → GET /api/v1/human-reviews/admin/analytics/
    → Views all cases, reviews, payments
    → Can intervene if needed (reassign, escalate)
```

## 12.2 AI Call Session Flow

### Flow: User Starts Call → Conversation → Summary

```
USER APP:
1. User creates call session
   → POST /api/v1/ai-calls/sessions/
   → CallSession created, status: "created"
   → Data: CallSession record created

2. User prepares call
   → POST /api/v1/ai-calls/sessions/<id>/prepare/
   → System builds context bundle:
     a. Case facts
     b. Documents summary
     c. AI decisions
     d. Rules knowledge
   → CallSession status: "created" → "ready"
   → Data: Context bundle stored, versioned, hashed

3. User starts call
   → POST /api/v1/ai-calls/sessions/<id>/start/
   → CallSession status: "ready" → "in_progress"
   → Timebox task scheduled (30 minutes)
   → Data: Timebox task ID stored, started_at timestamp set

4. User speaks (turn-by-turn)
   → POST /api/v1/ai-calls/sessions/<id>/speech/ (with audio file)
   → System processes:
     a. Audio validation (voice_utils)
     b. Speech-to-text (external service)
     c. Guardrails pre-prompt validation
     d. AI response generation (LLM)
     e. Guardrails post-response validation
     f. Text-to-speech (external service)
   → CallTranscript records created (user turn + AI turn)
   → Data: Transcripts stored, guardrails events logged

5. User ends call (or timebox expires)
   → POST /api/v1/ai-calls/sessions/<id>/end/
   → CallSession status: "in_progress" → "completed"
   → Timebox task cancelled
   → Post-call summary generated
   → Data: CallSummary created, attached to case timeline

REVIEWER APP:
6. Reviewer views call session (if case is assigned)
   → GET /api/v1/ai-calls/sessions/?case_id=<id>
   → Sees call transcript
   → Can review guardrails events
   → Data: Read-only access to call data

ADMIN APP:
7. Admin views call analytics
   → GET /api/v1/ai-calls/admin/statistics/
   → GET /api/v1/ai-calls/admin/guardrail-analytics/
   → Sees system-wide call metrics
   → Data: Analytics aggregated
```

## 12.3 Rule Validation & Publishing Flow

### Flow: Rule Change Detected → Validation → Publishing

```
SYSTEM (Automatic):
1. Data ingestion runs (scheduled)
   → Fetches source documents
   → Compares with previous versions
   → Detects changes
   → Data: DocumentVersion and DocumentDiff created

2. Rule parsing (automatic)
   → LLM extracts rules from changed text
   → Creates ParsedRule records
   → Status: "pending_validation"
   → Data: ParsedRule with JSON Logic, confidence score

ADMIN APP:
3. Admin sees pending validations
   → GET /api/v1/data-ingestion/parsed-rules/pending/
   → Validation queue populated

4. Admin reviews rule
   → GET /api/v1/data-ingestion/parsed-rules/<id>/
   → Views original text vs extracted logic
   → Compares with previous version

5. Admin takes action:
   Option A: Approve
   → POST /api/v1/data-ingestion/parsed-rules/<id>/status/ (status: "approved")
   → ParsedRule status: "pending_validation" → "approved"
   → Rule published to production
   → Data: Rule becomes active, used in eligibility checks

   Option B: Reject
   → POST /api/v1/data-ingestion/parsed-rules/<id>/status/ (status: "rejected")
   → ParsedRule status: "pending_validation" → "rejected"
   → Rule not published
   → Data: Rule marked as rejected, reason stored

   Option C: Edit
   → PATCH /api/v1/data-ingestion/parsed-rules/<id>/update/
   → Edits JSON Logic expression
   → Saves draft
   → Can approve edited version later
   → Data: ParsedRule updated, version incremented

6. Approved rules take effect
   → Next eligibility check uses new rules
   → Users see updated results
   → Data: Rules applied in real-time
```

## 12.4 Payment & Service Activation Flow

### Flow: User Makes Payment → Service Activated

```
USER APP:
1. User initiates payment
   → POST /api/v1/payments/create/
   → Payment created, status: "pending"
   → Data: Payment record created

2. User selects payment method
   → POST /api/v1/payments/<id>/initiate/
   → Redirected to payment gateway (Stripe/PayPal)
   → Data: Payment provider transaction initiated

3. Payment processed
   → Gateway callback → POST /api/v1/payments/<id>/verify/
   → Payment status: "pending" → "completed"
   → Data: Payment verified, transaction ID stored

SYSTEM (Automatic):
4. Payment completion triggers services
   → Signal handler detects payment completion
   → Automatically triggers eligibility check (if not done)
   → Enables document upload (if restricted)
   → Data: Case status updated, services activated

USER APP:
5. User sees payment confirmation
   → GET /api/v1/payments/<id>/
   → Payment confirmed
   → Can now access paid services
   → Data: User can proceed with case
```

## 12.5 Data Flow Summary

### Key Data Transitions:

1. **Case Creation** (User → System):
   - User creates case → Case record in database
   - User adds facts → CaseFact records linked to Case
   - Case status: "draft"

2. **Eligibility Evaluation** (System → User):
   - System evaluates case → EligibilityResult created
   - AI reasoning → AIReasoningLog and AICitations created
   - Case status: "draft" → "evaluated"
   - User views results

3. **Document Processing** (User → System → User):
   - User uploads document → CaseDocument created
   - System processes (OCR, classification) → DocumentCheck records
   - Document status: "uploaded" → "processing" → "verified"
   - User sees validation results

4. **Review Request** (User → Reviewer):
   - User requests review → Review created
   - System assigns reviewer → Review linked to Reviewer
   - Case status: "evaluated" → "awaiting_review"
   - Reviewer sees in queue

5. **Review Completion** (Reviewer → User):
   - Reviewer completes review → Review status: "completed"
   - Override created (if applicable) → DecisionOverride record
   - Case status: "awaiting_review" → "reviewed"
   - User receives notification and feedback

6. **Rule Updates** (Admin → System → All Users):
   - Admin approves rule → Rule published
   - Rule becomes active → Used in next eligibility check
   - All users benefit from updated rules
   - No user action required

7. **Call Sessions** (User → System → Case):
   - User creates call → CallSession created
   - Conversation occurs → CallTranscript records created
   - Call ends → CallSummary created and attached to Case
   - Reviewer/Admin can view transcript

## 12.6 Cross-Role Data Visibility

### What Each Role Can See:

**User Role**:
- Own cases only
- Own eligibility results
- Own documents
- Own payments
- Own call sessions
- Own review requests and feedback

**Reviewer Role**:
- Assigned cases (read-only)
- Eligibility results for assigned cases
- Documents for assigned cases
- Review requests assigned to them
- Call sessions for assigned cases (read-only)
- Cannot see: Other users' data, payment details, admin functions

**Admin Role**:
- All cases (full access)
- All eligibility results
- All documents
- All payments
- All call sessions
- All reviews
- All rules and data sources
- All users
- System analytics and metrics

---

# 13. Shared Requirements

## 13.1 Authentication & Authorization

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

## 13.2 Design Principles

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

## 13.3 Accessibility Requirements

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

## 13.4 Content Guidelines

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

## 13.5 Common Interaction Patterns

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

## 13.6 Common Edge Cases

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

# 14. Success Metrics

## 14.1 User App Metrics

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

## 14.2 Reviewer App Metrics

### Efficiency
- **Review Completion Time**: Average time for reviewer to complete review
- **Reviews per Day**: Average number of reviews completed per reviewer
- **SLA Compliance**: % of reviews completed within SLA
- **Override Rate**: % of AI decisions overridden by reviewers

### Quality
- **Review Accuracy**: % of reviews that match final outcomes
- **Note Quality**: Average length and detail of reviewer notes
- **Escalation Rate**: % of reviews escalated to senior reviewer

## 14.3 Admin App Metrics

### System Health
- **System Uptime**: % of time system is available
- **Error Rate**: % of failed operations
- **Ingestion Success Rate**: % of successful data source fetches
- **Rule Validation Time**: Average time to validate and publish rules

### Operational
- **Rule Publication Latency**: Time from change detection to rule publication
- **Validation Accuracy**: % of approved rules that are correct
- **User Management Efficiency**: Time to manage users

## 14.4 Business Metrics

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
