# GitHub Token Setup for Automated Releases

## Overview
To allow the manual stable release workflow to bypass branch protection rules, you need to create a Personal Access Token (PAT) with elevated permissions.

## Option 1: Personal Access Token (Recommended - Simpler)

### Step 1: Create Personal Access Token
1. **Go to GitHub Settings**
   - Navigate to: https://github.com/settings/tokens
   - Click "Generate new token" → "Generate new token (classic)"

2. **Token Configuration**
   - **Note**: `libdyson-rest-release-token`
   - **Expiration**: 1 year (or your preference)
   - **Scopes** (check these boxes):
     - ✅ `repo` (Full control of private repositories)
     - ✅ `workflow` (Update GitHub Action workflows)

3. **Generate and Copy Token**
   - Click "Generate token"
   - **IMPORTANT**: Copy the token immediately - you won't see it again!

### Step 2: Add Token as Repository Secret
1. **Go to Repository Secrets**
   - Navigate to: https://github.com/cmgrayb/libdyson-rest/settings/secrets/actions
   - Click "New repository secret"

2. **Add Secret**
   - **Name**: `RELEASE_TOKEN`
   - **Secret**: Paste the PAT you copied
   - Click "Add secret"

### Step 3: Test the Setup
1. **Run Manual Stable Release**
   - Go to Actions → "Manual Release: Stable"
   - Click "Run workflow"
   - Enter version and type "CONFIRM"
   - Should now work without branch protection errors!

---

## Option 2: GitHub App (More Complex but More Secure)

If you prefer a GitHub App approach for better security and audit trails:

### Step 1: Create GitHub App
1. **Go to GitHub Settings**
   - Navigate to: https://github.com/settings/apps
   - Click "New GitHub App"

2. **Basic Information**
   - **GitHub App name**: `libdyson-rest-release-bot`
   - **Description**: `Automated release bot for libdyson-rest`
   - **Homepage URL**: `https://github.com/cmgrayb/libdyson-rest`
   - **Webhook**: Uncheck "Active"

3. **Permissions (Repository permissions)**
   - **Contents**: Read and write
   - **Metadata**: Read
   - **Pull requests**: Write
   - **Actions**: Read

4. **Install App**
   - After creation, install on your repository
   - Note the App ID and Installation ID

### Step 2: Generate Private Key & Add Secrets
1. **Generate private key** in app settings
2. **Add these secrets** to your repository:
   - `APP_ID`: Your GitHub App ID
   - `APP_PRIVATE_KEY`: Contents of the .pem file
   - `APP_INSTALLATION_ID`: Installation ID

### Step 3: Update Workflow (If Using GitHub App)
Add this step before checkout in `manual-release-stable.yml`:

```yaml
      - name: "🔑 Generate GitHub App Token"
        id: generate_token
        uses: actions/create-github-app-token@v1
        with:
          app-id: ${{ secrets.APP_ID }}
          private-key: ${{ secrets.APP_PRIVATE_KEY }}
```

And change the token reference to: `${{ steps.generate_token.outputs.token }}`

---

## Security Comparison

| Method | Pros | Cons |
|--------|------|------|
| **PAT** | Simple setup, works immediately | Tied to your personal account, broader permissions |
| **GitHub App** | Scoped permissions, better audit trail | More complex setup, additional steps |

## Recommendation
**Start with the PAT approach** - it's simpler and works well for personal/small team projects. You can always upgrade to a GitHub App later if needed.
