# WhatsApp Bot Setup Guide - Meta WhatsApp Business API

## Overview

The WhatsApp bot now uses Meta (Facebook) WhatsApp Business API instead of Twilio for better integration and lower costs.

## Prerequisites

1. **Meta Developer Account**: Create at account https://developers.facebook.com
2. **WhatsApp Business App**: Create a WhatsApp Business App in Meta Developer Console
3. **Phone Number**: Add and verify a phone number for WhatsApp Business

## Setup Steps

### 1. Create WhatsApp Business App

1. Go to [Meta Developers](https://developers.facebook.com)
2. Click "My Apps" → "Create App"
3. Select "Business" type
4. Enter app name and contact email
5. Add "WhatsApp" product to your app

### 2. Get Your Credentials

From the WhatsApp Business API dashboard, get:

**Phone Number ID**:
- Go to WhatsApp → API Setup
- Copy the "Phone number ID" (starts with numbers, e.g., `109876543210987`)

**Access Token**:
- Go to WhatsApp → API Setup
- Generate a permanent access token (expires in 60 days or never)
- Or use System User token for production (recommended)

**Create a Verify Token**:
- This is a custom string you create for webhook verification
- Example: `my_custom_verify_token_12345`

### 3. Configure Environment Variables

Add to your `.env` file:

```env
# Meta WhatsApp Business API
META_ACCESS_TOKEN=your_permanent_access_token_here
META_PHONE_NUMBER_ID=109876543210987
META_VERIFY_TOKEN=my_custom_verify_token_12345
```

### 4. Update Django Settings

Add to `settings.py`:

```python
# Meta WhatsApp Configuration
META_ACCESS_TOKEN = os.getenv('META_ACCESS_TOKEN')
META_PHONE_NUMBER_ID = os.getenv('META_PHONE_NUMBER_ID')
META_VERIFY_TOKEN = os.getenv('META_VERIFY_TOKEN')
```

### 5. Configure Webhook

1. In Meta Developer Console, go to WhatsApp → Configuration
2. Click "Edit" under Webhook
3. Enter your webhook URL:
   ```
   https://api.pluggedspace.org/api/whatsapp/webhook
   ```
4. Enter your **Verify Token** (same as `META_VERIFY_TOKEN` in .env)
5. Click "Verify and Save"
6. Subscribe to **messages** field

### 6. Test the Integration

Send a message to your WhatsApp Business number:
```
/start
```

You should receive the welcome message with all available commands.

## Important Notes

### Message Format
- Phone numbers should be in international format without `+` or `whatsapp:` prefix
- Example: `234801234567` for Nigeria

### Rate Limits
- Free tier: 1,000 conversations per month
- Conversations last 24 hours from last message
- After 24 hours, you need user to initiate

### Message Templates
- Template messages required to initiate conversations after 24 hours
- Interactive messages require approval

### Costs
- **Free tier**: 1,000 conversations/month
- **Paid**: ~$0.005 - $0.10 per conversation (varies by country)
- Much cheaper than Twilio for high volume

## API Differences from Twilio

| Feature | Twilio | Meta |
|---------|--------|------|
| Phone Format | `whatsapp:+1234567890` | `1234567890` |
| Authentication | Account SID + Auth Token | Access Token |
| Webhook | TwiML format | JSON |
| Pricing | Per message | Per conversation (24h) |
| Message Types | Text, Media | Text, Media, Templates, Interactive |

## Troubleshooting

### Webhook Not Receiving Messages

1. Check webhook URL is HTTPS
2. Verify token matches exactly
3. Check webhook subscriptions include "messages"
4. View webhook logs in Meta Developer Console

### Can't Send Messages

1. Verify access token is valid
2. Check phone number ID is correct
3. Ensure phone number is verified in Meta
4. Check rate limits haven't been exceeded

### Messages Not Delivered

1. User must message first (for first contact)
2. 24-hour window may have expired
3. Use template messages for expired windows
4. Check message status in Meta dashboard

## Production Recommendations

1. **Use System User Token**: More secure than user access tokens
2. **Set up Business Manager**: Better account management
3. **Enable Two-Factor Auth**: On your Meta/Facebook account
4. **Monitor Webhooks**: Use Meta's webhook testing tools
5. **Handle Errors**: Implement retry logic for failed messages
6. **Rate Limiting**: Implement backoff for API calls

## Testing Commands

Test all features:
```
/start - Welcome message
/findjobs python - Search jobs
/careerpath developer - Career paths
/upskill data scientist - Learning plan
/quota - Check limits
/link - Generate link code
/account - Account info
```

Premium features (requires subscription):
```
/cv_review - AI CV review
/coverletter Software Engineer | Google - Generate cover letter
/practice - Mock interview
```

## Resources

- [Meta WhatsApp Business API Documentation](https://developers.facebook.com/docs/whatsapp/cloud-api)
- [Getting Started Guide](https://developers.facebook.com/docs/whatsapp/cloud-api/get-started)
- [Webhook Setup](https://developers.facebook.com/docs/graph-api/webhooks)
- [Message Templates](https://developers.facebook.com/docs/whatsapp/message-templates)

## Migration from Twilio

If migrating from Twilio:
1. Export user data (phone numbers)
2. Update environment variables
3. Test webhook in sandbox first
4. Switch production webhook URL
5. Monitor for 24-48 hours
6. Remove Twilio credentials after successful migration
