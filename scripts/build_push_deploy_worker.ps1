param(
    [string]$project = "project-294f73a2-90e4-4430-b84",
    [string]$region = "us-central1",
    [string]$repo = "realtime-agent-repo",
    [string]$image_name = "realtime-agent",
    [string]$tag = $(Get-Date -Format yyyyMMddHHmmss)
)

$full_image = "{0}-docker.pkg.dev/{1}/{2}/{3}:{4}" -f $region, $project, $repo, $image_name, $tag
Write-Output "Building image $full_image (no cache)..."
docker build --no-cache -t $full_image .
if ($LASTEXITCODE -ne 0) { throw "docker build failed" }

Write-Output "Pushing image..."
docker push $full_image
if ($LASTEXITCODE -ne 0) { throw "docker push failed" }

Write-Output "Deploying to Cloud Run (service: realtime-agent-worker)..."
gcloud run deploy "realtime-agent-worker" --image=$full_image --region=$region --platform=managed --memory=1Gi --cpu=1 --timeout=3600 --max-instances=10 --set-env-vars="ROLE=worker,TEMPORAL_ADDRESS=temporal.example.com:7233" --no-allow-unauthenticated --project=$project

Write-Output "Done. Deployed image: $full_image"