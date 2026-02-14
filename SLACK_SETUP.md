# Slack Setup Guide for CostGuard AI

To enable real-time cost alerts and approval notifications, follow these steps to set up a Slack Bot.

## 1. Create your Slack App
1. Go to [api.slack.com/apps](https://api.slack.com/apps).
2. Click **Create New App** -> **From scratch**.
3. **App Name**: `CostGuard Bot`
4. **Workspace**: Select your target workspace.

## 2. Configure Scopes
1. In the left sidebar, go to **OAuth & Permissions**.
2. Scroll down to **Scopes** -> **Bot Token Scopes**.
3. Add the following scope:
   - `chat:write` (Allows the bot to post messages).
   - `chat:write.public` (Allows posting to public channels without being invited).

## 3. Install App
1. Scroll back up to the top of **OAuth & Permissions**.
2. Click **Install to [Workspace Name]**.
3. Click **Allow**.
4. Copy the **Bot User OAuth Token** (starts with `xoxb-`).

### OR Option B: Simplified Webhooks (Recommended)
1. In your Slack App settings, go to **Incoming Webhooks**.
2. Toggle to **On**.
3. Click **Add New Webhook to Workspace**.
4. Select a channel and click **Allow** (You may need Admin approval).
5. Copy the **Webhook URL** and add it to your `.env`:
   ```bash
   SLACK_WEBHOOK_URL=https://hooks.slack.com/services/T.../B.../...
   ```

## 4. Update `.env`
Update your `.env` file with the token and your desired channels:
```bash
SLACK_BOT_TOKEN=xoxb-your-token-here
SLACK_CHANNEL_ALERTS=#cost-alerts
SLACK_CHANNEL_APPROVALS=#cost-approvals
```

## 5. (Optional) Invite Bot to Private Channels
If your channels are private, you must invite the bot manually:
1. Open the channel in Slack.
2. Type: `/invite @CostGuard Bot`.

## 6. Restart Backend
Restart your Docker container to apply the new `.env` settings:
```bash
docker-compose up -d backend
```
