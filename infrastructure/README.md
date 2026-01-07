# Infrastructure as Code - Fly.io Deployment

This directory contains all infrastructure configuration for deploying the GM Chatbot to Fly.io using a monolithic architecture with GitOps.

## Directory Structure

```
infrastructure/
├── Dockerfile          # Container image definition
├── .dockerignore       # Docker build exclusions
├── fly.toml            # Fly.io application configuration
├── fly.toml.example    # Example configuration template
├── fly.toml            # Fly.io application and volume configuration
├── manage-volumes.sh   # Volume management script
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
flyctl apps create roll20-chatbot
```

**Note**: If the app name `roll20-chatbot` is taken, choose a different name and update `infrastructure/fly.toml` accordingly.

**Important**: For deployment, `fly.toml` must be in the project root (not in `infrastructure/`) because Fly.io uses the directory containing `fly.toml` as the build context. The source of truth is `infrastructure/fly.toml`, which should be copied to the project root before deployment.

### 3. Configure Application

Copy the example configuration and customize:

```bash
cd infrastructure
cp fly.toml.example fly.toml
cd ..
```

Edit `infrastructure/fly.toml` and update:

- `app` - Your app name (if different)
- `primary_region` - Choose closest to your users (see https://fly.io/docs/reference/regions/)

### 4. Create Persistent Volume

Create a persistent volume for campaign data and rules:

```bash
# Create volume (10GB is a good starting size)
flyctl volumes create chatbot_data --size 10 --app roll20-chatbot

# Verify volume was created
flyctl volumes list --app roll20-chatbot
```

**Note**: The volume will be mounted at `/data` and will contain both `/data/campaigns` and `/data/rules` directories.

### 5. Set Secrets

Set sensitive configuration as Fly.io secrets:

```bash
# Required: OpenAI API key (if using AI features)
flyctl secrets set OPENAI_API_KEY=your-api-key-here

# Optional: Override default model
flyctl secrets set LLM_MODEL=gpt-4o-mini

# Optional: Set log level
flyctl secrets set LOG_LEVEL=INFO

# Optional: Override storage paths (defaults shown)
flyctl secrets set CAMPAIGNS_DIR=/data/campaigns
flyctl secrets set RULES_DIR=/data/rules
```

**Important**: Never commit secrets to git. Always use `flyctl secrets set`.

### 6. Configure GitHub Actions

1. Go to your GitHub repository
2. Navigate to Settings → Secrets and variables → Actions
3. Add secret: `FLY_API_TOKEN`
4. Get your token: `flyctl auth token`

## Deployment

### Automated Deployment (GitOps)

Deployments happen automatically via GitHub Actions when you push to `main` or `master` branch.

**Manual trigger**: Go to Actions tab → "Deploy to Fly.io" → "Run workflow"

### Manual Deployment

Deploy manually from the project root:

```bash
# From project root directory
# Copy infrastructure/fly.toml to root (build context must be project root)
cp infrastructure/fly.toml fly.toml
flyctl deploy
```

**Note**:

- `infrastructure/fly.toml` is the source of truth (version controlled)
- `fly.toml` in project root is for deployment only (gitignored)
- Fly.io uses the directory containing `fly.toml` as the build context
- The Dockerfile references `infrastructure/Dockerfile` but builds from project root

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

**Application Configuration:**

- `OPENAI_API_KEY` - OpenAI API key (required for AI features)
- `LLM_MODEL` - LLM model name (default: `gpt-4o-mini`)
- `WS_ADDRESS` - WebSocket bind address (default: `0.0.0.0` for Fly.io)
- `PORT` - Port number (automatically set by Fly.io)
- `LOG_LEVEL` - Logging level (default: `INFO`)

**Storage Configuration:**

- `CAMPAIGNS_DIR` - Directory for campaign artifacts (default: `/data/campaigns`)
- `RULES_DIR` - Directory for game rules YAML files (default: `/data/rules`)

**Note**: Storage directories default to `/data/campaigns` and `/data/rules` which are mounted from the persistent volume. These can be overridden for testing or custom deployments.

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
   localStorage.setItem(
     "roll20_chatbot_ws_url",
     "wss://roll20-chatbot.fly.dev"
   );
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

## Volume Management

Volumes are managed as Infrastructure as Code using the `[volumes]` section in `infrastructure/fly.toml` and the `manage-volumes.sh` script. This ensures volumes are automatically provisioned during deployment.

### Volume Configuration

Volume specifications are defined in the `[volumes]` section of `infrastructure/fly.toml`:

```toml
[volumes.chatbot_data]
name = "chatbot_data"
size_gb = 10
region = "iad"  # Must match primary_region in fly.toml
app = "gm-chatbot"
description = "Persistent storage for campaigns, characters, and rules"
required = true  # If true, deployment fails if volume doesn't exist
```

**Configuration Fields:**

- `name` - Volume name (required)
- `size_gb` - Volume size in GB (required)
- `region` - Fly.io region code, must match `primary_region` in `fly.toml` (required)
- `app` - Application name, must match `app` in `fly.toml` (required)
- `description` - Human-readable description (optional)
- `required` - If `true`, deployment fails if volume creation fails (default: `true`)

### Volume Management Script

The `infrastructure/manage-volumes.sh` script provides idempotent volume operations:

**Ensure Volumes (Idempotent):**

```bash
# Ensure all volumes from fly.toml exist (creates if missing)
./infrastructure/manage-volumes.sh ensure
```

**List Volumes:**

```bash
# List all volumes for app (auto-detects app from fly.toml)
./infrastructure/manage-volumes.sh list

# List volumes for specific app
./infrastructure/manage-volumes.sh list gm-chatbot
```

**Extend Volume:**

```bash
# Extend volume to new size
./infrastructure/manage-volumes.sh extend chatbot_data 20
```

**Dry Run:**

```bash
# Test volume operations without making changes
DRY_RUN=true ./infrastructure/manage-volumes.sh ensure
```

### Automated Volume Provisioning

Volumes are automatically provisioned during CI/CD deployment:

1. **GitHub Actions** runs `manage-volumes.sh ensure` before deployment
2. Script checks if volumes exist (idempotent)
3. Creates volumes if they don't exist
4. Deployment proceeds only if volume provisioning succeeds

**No manual intervention required** - volumes are created automatically on first deployment.

### Manual Volume Operations

For advanced operations, you can use `flyctl` directly:

```bash
# List volumes
flyctl volumes list --app gm-chatbot

# Create additional volume (if needed)
flyctl volumes create chatbot_data_2 --size 10 --app gm-chatbot

# Extend volume size
flyctl volumes extend chatbot_data --size 20 --app gm-chatbot

# Delete volume (WARNING: This will delete all data!)
flyctl volumes destroy chatbot_data --app gm-chatbot
```

**Note:** For standard operations, use `manage-volumes.sh` which is idempotent and configuration-driven.

### Volume Storage Structure

The application uses a persistent volume mounted at `/data` to store:

- Campaign artifacts (`/data/campaigns/`)
- Game rules (`/data/rules/`)

### Rules Management

Game rules are stored in `/data/rules/` and can be updated without redeploying:

1. **Initial Setup**: Copy default rules to volume on first deployment
2. **Update Rules**: SSH into the machine and edit YAML files directly, or use volume snapshots
3. **Hot Reload**: Rules are cached in memory - restart the app to reload

```bash
# SSH into machine
flyctl ssh console --app gm-chatbot

# Edit rules (example)
cd /data/rules/shadowdark
vi core.yaml

# Restart app to reload rules
flyctl apps restart gm-chatbot
```

### Character Sheet Import/Export

Players can export and import their character sheets via the API:

**Export Character:**

```bash
# Get character sheet as YAML
curl -X GET \
  "https://gm-chatbot.fly.dev/api/v1/campaigns/{campaign_id}/characters/{character_id}/export" \
  -H "Accept: application/x-yaml" \
  -o character.yaml
```

**Import Character:**

```bash
# Import character sheet from YAML
curl -X POST \
  "https://gm-chatbot.fly.dev/api/v1/campaigns/{campaign_id}/characters/import" \
  -H "Content-Type: application/x-yaml" \
  --data-binary @character.yaml
```

**Use Cases:**

- Backup character sheets
- Share characters between campaigns
- Import characters from external tools
- Restore lost character data

## Troubleshooting

### Volume Issues

**Volume Not Found During Deployment:**

- Check that `fly.toml` exists and is properly formatted with `[volumes]` sections
- Verify volume configuration matches `fly.toml` (app name, region)
- Check Fly.io API token has proper permissions
- Review GitHub Actions logs for volume creation errors

**Volume Creation Fails:**

- Verify app exists: `flyctl apps list`
- Check region is valid: `flyctl regions list`
- Ensure sufficient Fly.io quota for volume creation
- Check volume name doesn't conflict with existing volumes

**Volume Mount Issues:**

- Verify volume exists: `flyctl volumes list --app gm-chatbot`
- Check volume is in same region as app
- Verify `fly.toml` has correct mount configuration
- Restart app after volume creation: `flyctl apps restart gm-chatbot`

**Script Execution Issues:**

- Ensure script is executable: `chmod +x infrastructure/manage-volumes.sh`
- Verify `jq` is installed (required for JSON parsing)
- Check TOML file syntax is valid
- Test script locally with `DRY_RUN=true` flag

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
