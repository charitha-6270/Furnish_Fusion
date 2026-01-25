# PowerShell script to push Furnish Fusion AWS to GitHub
# Run this script: .\push_to_github.ps1

Write-Host "🚀 Setting up Git and pushing to GitHub..." -ForegroundColor Cyan
Write-Host ""

# Navigate to project directory
$projectPath = "c:\Users\Sai Charitha\OneDrive\Desktop\Furnish_Fusion_AWS"
Set-Location $projectPath

# Remove git lock file if it exists
if (Test-Path ".git\config.lock") {
    Write-Host "⚠️  Removing git lock file..." -ForegroundColor Yellow
    Remove-Item ".git\config.lock" -Force
}

# Initialize git if not already done
if (-not (Test-Path ".git")) {
    Write-Host "📦 Initializing Git repository..." -ForegroundColor Cyan
    git init
} else {
    Write-Host "✅ Git repository already initialized" -ForegroundColor Green
}

# Configure git user if not set
$gitUser = git config user.name
if (-not $gitUser) {
    Write-Host ""
    Write-Host "⚙️  Git Configuration" -ForegroundColor Cyan
    $userName = Read-Host "Enter your Git user name"
    $userEmail = Read-Host "Enter your Git email"
    git config user.name $userName
    git config user.email $userEmail
}

# Add all files
Write-Host ""
Write-Host "📝 Adding files to staging area..." -ForegroundColor Cyan
git add .

# Check if there are changes to commit
$status = git status --porcelain
if ($status) {
    Write-Host ""
    Write-Host "💾 Creating commit..." -ForegroundColor Cyan
    git commit -m "Initial commit: Furnish Fusion AWS application with admin login system and modern UI"
    Write-Host "✅ Files committed successfully!" -ForegroundColor Green
} else {
    Write-Host "ℹ️  No changes to commit" -ForegroundColor Yellow
}

# Check if remote exists
$remoteExists = git remote | Select-String -Pattern "origin"
if (-not $remoteExists) {
    Write-Host ""
    Write-Host "🔗 Setting up GitHub remote..." -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Please create a repository on GitHub first:" -ForegroundColor Yellow
    Write-Host "1. Go to https://github.com/new" -ForegroundColor White
    Write-Host "2. Repository name: Furnish_Fusion_AWS" -ForegroundColor White
    Write-Host "3. Choose Public or Private" -ForegroundColor White
    Write-Host "4. DO NOT initialize with README" -ForegroundColor White
    Write-Host "5. Click 'Create repository'" -ForegroundColor White
    Write-Host ""
    
    $repoUrl = Read-Host "Enter your GitHub repository URL (e.g., https://github.com/username/Furnish_Fusion_AWS.git)"
    
    if ($repoUrl) {
        git remote add origin $repoUrl
        Write-Host "✅ Remote added successfully!" -ForegroundColor Green
    }
} else {
    Write-Host "✅ Remote 'origin' already exists" -ForegroundColor Green
    $currentRemote = git remote get-url origin
    Write-Host "   Current remote: $currentRemote" -ForegroundColor Gray
}

# Rename branch to main
Write-Host ""
Write-Host "🌿 Setting branch to main..." -ForegroundColor Cyan
git branch -M main

# Push to GitHub
Write-Host ""
Write-Host "📤 Pushing to GitHub..." -ForegroundColor Cyan
Write-Host "You may be prompted for your GitHub credentials." -ForegroundColor Yellow
Write-Host "If using HTTPS, use a Personal Access Token instead of password." -ForegroundColor Yellow
Write-Host "Create one at: https://github.com/settings/tokens" -ForegroundColor Yellow
Write-Host ""

try {
    git push -u origin main
    Write-Host ""
    Write-Host "✅ Successfully pushed to GitHub!" -ForegroundColor Green
    $repoUrl = git remote get-url origin
    Write-Host "Visit your repository at: $repoUrl" -ForegroundColor Cyan
} catch {
    Write-Host ""
    Write-Host "❌ Push failed. Please check:" -ForegroundColor Red
    Write-Host "1. Repository URL is correct" -ForegroundColor White
    Write-Host "2. You have access to the repository" -ForegroundColor White
    Write-Host "3. Your GitHub credentials are correct" -ForegroundColor White
    Write-Host ""
    Write-Host "Try running manually:" -ForegroundColor Yellow
    Write-Host "  git push -u origin main" -ForegroundColor Cyan
}
