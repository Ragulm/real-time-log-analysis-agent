# PowerShell script to build and deploy worker via Google Cloud Build
# This avoids local Docker push network issues by leveraging Cloud Build's infrastructure
# Usage: .\scripts\cloud-build-worker.ps1 -BuildId "v1" -SkipDeploy $false

param(
    [string]$BuildId = "latest",
    [switch]$SkipDeploy,
    [string]$ConfigFile = "cloudbuild-worker.yaml"
)

$projectId = "project-294f73a2-90e4-4430-b84"
$region = "us-central1"
$registry = "us-central1-docker.pkg.dev"
$repo = "realtime-agent-repo"
$imageName = "realtime-agent"

Write-Host "🏗️ Cloud Build: Building and pushing worker image..." -ForegroundColor Cyan

# Check if cloudbuild.yaml exists
if (-not (Test-Path $ConfigFile)) {
    Write-Host "❌ Error: $ConfigFile not found in current directory" -ForegroundColor Red
    exit 1
}

try {
    # Submit build to Google Cloud Build
    Write-Host "📤 Submitting build to Cloud Build..." -ForegroundColor Yellow
    $buildOutput = gcloud builds submit `
        --config=$ConfigFile `
        --project=$projectId `
        2>&1

    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Cloud Build submit failed:" -ForegroundColor Red
        Write-Host $buildOutput
        exit 1
    }

    # Extract build ID from gcloud output
    $buildId = $buildOutput | Select-String -Pattern "ID: ([a-f0-9\-]+)" | ForEach-Object { $_.Matches.Groups[1].Value }
    
    Write-Host "✅ Build submitted successfully!" -ForegroundColor Green
    Write-Host "   Build ID: $buildId" -ForegroundColor Green
    Write-Host "   View logs: https://console.cloud.google.com/cloud-build/builds/$buildId?project=$projectId" -ForegroundColor Green

    if (-not $SkipDeploy) {
        Write-Host "" 
        Write-Host "⏳ Monitoring build progress..." -ForegroundColor Cyan
        
        # Wait for build to complete
        do {
            Start-Sleep -Seconds 10
            $status = gcloud builds log $buildId --project=$projectId --tail=1 2>&1
        } while ($status -like "*QUEUED*" -or $status -like "*WORKING*")

        Write-Host "✅ Build completed!" -ForegroundColor Green
    }

} catch {
    Write-Host "❌ Error: $_" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "🎉 Cloud Build worker deployment prepared!" -ForegroundColor Green
