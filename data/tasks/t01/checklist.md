# Checklist t01
Source: hidden tests at c293590: backend/tests/application/test_organization_service.py

1. Creating an organization trims surrounding whitespace from the name and makes the creator its first and only owner (member count 1).
2. A newly created organization appears in the creator's own list of organizations.
3. Creating an organization records an "organization created" audit event.
4. An organization name that is empty or whitespace-only is rejected as invalid.
5. A user who is not a member (or an unknown organization id) gets a "not found" result when viewing the organization, not a permission error.
6. A plain member can view the organization (seeing their own role) but is refused with a permission/role error when trying to rename it.
7. A superadmin can view any organization without being a member; the view shows no role for them and the correct member count.
8. An owner can change another member's role; the change is persisted and audited as a "member role changed" event that names the affected user and records the old and new role (e.g. from "member" to "editor").
9. An owner can remove a member; the removal is persisted and audited as a "member removed" event; removing someone who is no longer a member is reported as "member not found".
10. The last remaining owner cannot be demoted, removed, or leave the organization; once another owner exists, the owner may leave and a "member left" audit event is recorded.
11. A non-member trying to leave an organization gets a "not found" result.
12. Deleting an organization requires re-entering its exact current name (case-sensitive); a mismatch is rejected and nothing is deleted.
13. A successful delete removes the organization and records an "organization deleted" audit event carrying the organization id and its name.
14. If a change fails in storage partway (e.g. rename raises), no audit event for that change is recorded (audit and change happen atomically).
15. Members can list the organization's members (user and role); non-members get "not found".
