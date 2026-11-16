# Checklist f14
Source: hidden tests at 11079ab: backend/tests/api/test_openapi.py, backend/tests/api/test_organizations_api_postgres.py, backend/tests/application/test_account_settings_service.py, backend/tests/application/test_audit_service.py, backend/tests/application/test_invitation_messages.py, backend/tests/application/test_invitation_service.py, backend/tests/infrastructure/test_superadmin_cli.py

1. An owner (or editor) inviting an email address normalizes it (trim, lower-case), creates an invitation in "sent" status, and emails the invitee a link of the form <frontend_url>/invitations/<token>. [exact]
2. Anyone holding the token can preview the invitation without signing in: organization name, offered role, and a masked email hint keeping only the first letter of the local part (e.g. "n**@example.com").
3. A signed-in user whose verified email equals the invited address can accept: they join with the offered role, a "member joined" audit event is recorded, and accepting again is refused as no longer pending.
4. Accepting with a different email, or with the right email but unverified, is refused as an email mismatch.
5. Invitations expire after 7 days: accepting is refused as expired and the preview reports not found.
6. An invitation made by a plain member waits for approval (pending-approval status, no email sent); members cannot approve it; an editor or owner approving it sends the email (status "sent") and records an "invitation approved" audit event.
7. A pending invitation can be rejected (status rejected), after which it can no longer be approved.
8. Inviters can only grant roles up to their own level: an editor cannot invite an owner, a member cannot invite an editor; a non-member inviting gets "organization not found".
9. Inviting an existing member (email compared case-insensitively) or an address with an open invitation is refused.
10. An invitation stays valid after its inviter leaves the organization.
11. Resending issues a new token (the old one stops working) and emails it again; revoking closes the invitation and its token no longer previews.
12. The invitee can decline, which marks the invitation declined.
13. Owners/editors see all of the organization's invitations; plain members see only the ones they created.
14. Invitation emails to the same address are rate limited (a 6th send within the hour is refused; allowed again after an hour).
15. The invitation email exists in Vietnamese ("Lời mời tham gia <org> trên ViPharMind", role named e.g. "biên tập viên") and English ("Join <org> on ViPharMind", "editor"), includes the link in the text, and HTML-escapes the link in the HTML part. [exact]
16. The organization audit log is readable by owners/editors, paged newest first with a cursor, and each entry shows the actor's name/email; plain members get a role error and outsiders get "not found".
17. A user's own audit log lists only events about them; the full audit log is superadmin-only.
18. The account view lists the user's organization memberships (id, name, role), plus whether the user is superadmin and whether phone sign-in is enabled.
19. When SMS is disabled, phone login codes and phone-change codes are refused (no SMS sent) and the account view reports phone sign-in disabled.
20. HTTP API (cookie auth + CSRF): POST /api/v1/organizations creates an org (201, role "owner", member_count 1); GET /api/v1/organizations lists the caller's orgs with role; invitations are created under /api/v1/organizations/{id}/invitations (201, status "sent"); preview at GET /api/v1/invitations/{token} without auth; accept at POST /api/v1/invitations/{token}/accept. [exact]
21. Over HTTP a member renaming the org gets 403 FORBIDDEN_ROLE and cannot read the org audit (403), but can list members; the owner's org audit (GET .../audit, {"items": [...]}) includes "member.joined".
22. Outsiders get 404 on every organization route (get, rename, delete, members, invitations list/create, audit, leave).
23. Over HTTP the last owner leaving gets 409 LAST_OWNER; DELETE with a wrong confirm_name gets 422; with the exact name 204 and the org disappears from the list; the user's account audit (GET /api/v1/account/audit) is then empty. [exact]
24. The OpenAPI document has unique operation ids for the new routes (organizations:list/create/get/rename/delete, members list/set_role/remove, leave, invitations list/create/approve/reject/revoke/resend/preview/accept/decline, audit:organization, audit:mine). [exact]
25. A "superadmin" CLI can grant (email matched case-insensitively), list, and revoke superadmin for a user; granting an unknown email exits with code 1. [exact]
