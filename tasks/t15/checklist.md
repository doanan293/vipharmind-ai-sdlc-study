# Checklist t15
Source: hidden tests at 0a6b1f0: backend/tests/infrastructure/test_notifications.py

1. A Gmail API email sender exchanges its OAuth refresh token for an access token at https://oauth2.googleapis.com/token using a form with grant_type=refresh_token and the configured refresh token (plus client id/secret).
2. The access token is cached and reused while valid: sending two emails performs only one token request.
3. Emails are sent by POSTing to https://gmail.googleapis.com/gmail/v1/users/me/messages/send with an "Authorization: Bearer <access token>" header.
4. The send request body is JSON with a "raw" field containing the base64url-encoded RFC 822 message.
5. The encoded message has the right To and From headers (From is the configured sender, e.g. "ViPharMind <an@gmail.com>") and is multipart/alternative carrying both text and HTML parts.
6. A token-endpoint failure (e.g. 400 invalid_grant) is reported as a delivery error whose message includes the Google error (invalid_grant).
7. A failure from the Gmail send endpoint (e.g. 403) is reported as a delivery error whose message includes the status code.
8. Choosing the "gmail" email provider in settings with client id, client secret and refresh token builds the Gmail API sender. [exact]
9. Choosing "gmail" without the credentials fails at build time with an error naming the missing setting (GMAIL_REFRESH_TOKEN). [exact]
