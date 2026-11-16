# Checklist t02
Source: hidden tests at f8949ec: backend/tests/application/test_account_settings_service.py

1. Updating the profile trims whitespace from the display name, and the account view reports email-verified, overall-verified and phone-verified status correctly.
2. Requesting an email change normalizes the new address (lower-cases it) and sends a verification code to the new address.
3. Confirming the email change with the correct code updates the account's email, marks it verified, and sends a notice to the old address that mentions the new address.
4. Requesting an email change to an address already used by another account is rejected as "email already used".
5. A verification code issued for one account's email change cannot be used by a different account to claim that address (rejected as an invalid code).
6. Requesting a phone change to a number already verified on another account is rejected as "phone already used"; local formats like "0987654321" are normalized to E.164 (+84...) for the comparison.
7. Requesting and confirming a phone change with the SMS code (phone input given in local format with or without spaces) sets the phone number in E.164 form and marks it verified.
8. Changing the password when one is already set requires the correct current password; a wrong or missing current password is rejected, and the correct one stores the new (hashed) password.
9. An account that has no password yet (e.g. phone-only signup) can set a first password without providing a current one, after which the account shows a password as set.
10. Unlinking Google is refused when Google is the account's only sign-in method; when another method (password) exists, unlinking succeeds and the account shows Google as not linked.
11. Listing sessions marks exactly the caller's current session as current, and exposed session ids do not contain the raw session token.
12. Revoking a session by its id works once; revoking the same session again is reported as "session not found".
13. Revoking all other sessions keeps only the current one and returns how many sessions were revoked.
14. Looking up an unknown account id is reported as "account not found".
