# Infrastructure as Code - Fly.io Deployment

This directory contains all infrastructure configuration for deploying the GM Chatbot to Fly.io using a monolithic architecture with GitOps.

## Directory Structure

```
infrastructure/
├── Dockerfile          # Container image definition
├── .dockerignore       # Docker build exclusions
├── fly.toml            # Fly.io application configuration
├── fly.toml.example    # Example configuration template
└── README.md           # This file
```

## Prerequisites

1. **Fly.io CLI**: Install from https://fly.io/docs/getting-started/installing-flyctl/
   ```bash
   curl -L https://fly.io/install.sh | sh
   ```

2. **Fly.io Account**: Sign up at https://fly.io/app/sign-up

3. **GitHub Repository**: For GitOps deployments via GitHub Actions

## Initial Setup

### 1. Authenticate with Fly.io

```bash
flyctl auth login
```

### 2. Create Fly.io Application

```bash
cd infrastructure
flyctl apps create roll20-chatbot
```

**Note**: If the app name `roll20-chatbot` is taken, choose a different name and update `fly.toml` accordingly.

### 3. Configure Application

Copy the example configuration and customize:

```bash
cp fly.toml.example fly.toml
```

Edit `fly.toml` and update:
- `app` - Your app name (if different)
- `primary_region` - Choose closest to your users (see https://fly.io/docs/reference/regions/)

### 4. Set Secrets

Set sensitive configuration as Fly.io secrets:

```bash
# Required: OpenAI API key (if using AI features)
flyctl secrets set OPENAI_API_KEY=your-api-key-here

# Optional: Override default model
flyctl secrets set LLM_MODEL=gpt-4o-mini

# Optional: Set log level
flyctl secrets set LOG_LEVEL=INFO
```

**Important**: Never commit secrets to git. Always use `flyctl secrets set`.

### 5. Configure GitHub Actions

1. Go to your GitHub repository
2. Navigate to Settings → Secrets and variables → Actions
3. Add secret: `FLY_API_TOKEN`
4. Get your token: `flyctl auth token`

## Deployment

### Automated Deployment (GitOps)

Deployments happen automatically via GitHub Actions when you push to `main` or `master` branch.

**Manual trigger**: Go to Actions tab → "Deploy to Fly.io" → "Run workflow"

### Manual Deployment

Deploy manually from the infrastructure directory:

```bash
cd infrastructure
flyctl deploy
```

### Verify Deployment

```bash
# Check app status
flyctl status --app roll20-chatbot

# View logs
flyctl logs --app roll20-chatbot

# Check app info
flyctl info --app roll20-chatbot
```

## Configuration

### Environment Variables

The application uses these environment variables (set via Fly.io secrets or `fly.toml`):

- `OPENAI_API_KEY` - OpenAI API key (required for AI features)
- `LLM_MODEL` - LLM model name (default: `gpt-4o-mini`)
- `WS_ADDRESS` - WebSocket bind address (default: `0.0.0.0` for Fly.io)
- `PORT` - Port number (automatically set by Fly.io)
- `LOG_LEVEL` - Logging level (default: `INFO`)

### Resource Limits

Default configuration in `fly.toml`:
- CPU: 1 shared CPU
- Memory: 256 MB

To adjust, edit `fly.toml`:

```toml
[vm]
  cpu_kind = "shared"  # or "performance"
  cpus = 1
  memory_mb = 512      # Increase if needed
```

### Scaling

To scale the application:

```bash
# Scale to multiple instances
flyctl scale count 2 --app roll20-chatbot

# Scale resources
flyctl scale vm shared-cpu-1x --memory 512 --app roll20-chatbot
```

## Client Configuration

After deployment, update the Tampermonkey script (`chat_connector.js`) to use your Fly.io app URL:

1. Get your app URL: `flyctl status --app roll20-chatbot`
2. Update `chat_connector.js` WebSocket address:
   ```javascript
   // For HTTPS Roll20 pages, use wss://
   return "wss://roll20-chatbot.fly.dev";
   ```
3. Or configure at runtime via browser console:
   ```javascript
   localStorage.setItem('roll20_chatbot_ws_url', 'wss://roll20-chatbot.fly.dev');
   ```

## Monitoring & Logs

### View Logs

```bash
# Stream logs
flyctl logs --app roll20-chatbot

# Follow logs
flyctl logs --app roll20-chatbot --follow

# Filter logs
flyctl logs --app roll20-chatbot | grep ERROR
```

### Metrics

View metrics in Fly.io dashboard:
```bash
flyctl dashboard --app roll20-chatbot
```

## Troubleshooting

### Deployment Fails

1. **Check build logs**:
   ```bash
   flyctl logs --app roll20-chatbot
   ```

2. **Verify Dockerfile**:
   ```bash
   docker build -f infrastructure/Dockerfile -t test-image .
   ```

3. **Check configuration**:
   ```bash
   flyctl config validate --app roll20-chatbot
   ```

### WebSocket Connection Issues

1. **Verify app is running**:
   ```bash
   flyctl status --app roll20-chatbot
   ```

2. **Check WebSocket URL**:
   - Use `wss://` (not `ws://`) for HTTPS pages
   - Verify app URL is correct

3. **Test connection**:
   ```bash
   # Test WebSocket endpoint
   curl -i -N -H "Connection: Upgrade" -H "Upgrade: websocket" \
     https://roll20-chatbot.fly.dev
   ```

### Health Check Failures

Fly.io uses TCP health checks for WebSocket services. If health checks fail:

1. Check if app is listening on correct port
2. Verify firewall/security group settings
3. Review application logs for errors

### High Memory Usage

If experiencing memory issues:

1. Increase memory allocation:
   ```bash
   flyctl scale vm shared-cpu-1x --memory 512 --app roll20-chatbot
   ```

2. Check for memory leaks in application logs

## Rollback

### View Release History

```bash
flyctl releases --app roll20-chatbot
```

### Rollback to Previous Release

```bash
flyctl releases rollback <release-id> --app roll20-chatbot
```

Or rollback to previous release:
```bash
flyctl releases rollback --app roll20-chatbot
```

## Security Best Practices

1. **Never commit secrets**: Always use `flyctl secrets set`
2. **Use HTTPS/WSS**: Always use secure WebSocket (`wss://`) in production
3. **Regular updates**: Keep dependencies updated
4. **Monitor logs**: Regularly check logs for suspicious activity
5. **Limit access**: Use Fly.io's access controls

## Cost Optimization

1. **Auto-stop machines**: Enable in `fly.toml` for development
2. **Right-size resources**: Start with minimum required resources
3. **Monitor usage**: Use Fly.io dashboard to track usage
4. **Use shared CPUs**: Sufficient for most workloads

## Additional Resources

- [Fly.io Documentation](https://fly.io/docs/)
- [Fly.io Configuration Reference](https://fly.io/docs/reference/configuration/)
- [Fly.io Regions](https://fly.io/docs/reference/regions/)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)

## Support

For issues:
1. Check application logs: `flyctl logs --app roll20-chatbot`
2. Review Fly.io status: https://status.fly.io
3. Consult Fly.io documentation
4. Check GitHub Issues for known problems

