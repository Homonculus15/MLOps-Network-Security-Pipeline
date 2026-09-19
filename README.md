# MLOps Network Security Pipeline

An end-to-end machine learning system for network security / phishing-website detection, built with production MLOps practices — automated data ingestion, experiment tracking, containerized inference, and a full CI/CD pipeline deploying to AWS EC2.

**Repo:** [github.com/Homonculus15/MLOps-Network-Security-Pipeline](https://github.com/Homonculus15/MLOps-Network-Security-Pipeline)
**Live demo:** `http://<your-ec2-public-ip>:8080/docs`

---

## Overview

This project takes a network-security dataset (features derived from URLs/website characteristics) from raw ingestion all the way to a served, containerized prediction API. It's built as a modular pipeline rather than a single script — each stage (ingestion, validation, transformation, training) is a separate component, wired together and tracked end-to-end.

## Architecture

```
Training pipeline:
MongoDB Atlas → Data Ingestion → Data Validation → Data Transformation → Model Training → MLflow/DagsHub Tracking

Inference pipeline (this deployment):
CSV Upload → FastAPI /predict → Preprocessor → Trained Model → Predictions (HTML table)

CI/CD:
GitHub push → GitHub Actions (build) → Push image to Amazon ECR → Self-hosted runner on EC2 pulls & redeploys
```

## Tech Stack

| Layer | Tools |
|---|---|
| Data storage | MongoDB Atlas |
| Experiment tracking | MLflow, DagsHub |
| Model serving | FastAPI, Uvicorn |
| Containerization | Docker |
| Container registry | Amazon ECR |
| Compute | AWS EC2 |
| CI/CD | GitHub Actions (self-hosted runner) |
| ML | scikit-learn / pandas (preprocessing + model, pickled) |

## Project Structure

```
.
├── app.py                          # FastAPI app — /train and /predict routes
├── NetworkSecurity/
│   ├── components/                 # Data ingestion, validation, transformation, trainer
│   ├── pipeline/                   # TrainingPipeline orchestration
│   ├── utils/
│   │   ├── main_utils/utils.py     # load_object / save_object helpers
│   │   └── ml_utils/model/estimator.py  # NetworkModel wrapper class
│   ├── exception/                  # Custom NetworkSecurityException
│   └── logging/                    # Logging setup
├── final_model/
│   ├── model.pkl                   # Trained model artifact
│   └── preprocessing.pkl           # Fitted preprocessing pipeline
├── templates/
│   └── table.html                  # Jinja2 template for rendering predictions
├── Dockerfile
├── requirements.txt
└── .github/workflows/main.yaml     # CI/CD pipeline definition
```

## Prerequisites

- Python 3.10
- Docker
- MongoDB Atlas cluster + connection string
- AWS account with ECR repository and an EC2 instance
- DagsHub account (for MLflow tracking) + a long-lived access token
- GitHub repo secrets configured (see below)

## Environment Variables

Set these as GitHub Actions secrets (used by the CI/CD workflow) and/or in a local `.env` file for local runs:

| Variable | Purpose |
|---|---|
| `MONGODB_URL_KEY` | MongoDB Atlas connection string |
| `AWS_ACCESS_KEY_ID` | AWS credentials for ECR/EC2 access |
| `AWS_SECRET_ACCESS_KEY` | AWS credentials |
| `AWS_REGION` | AWS region (e.g. `us-east-1`) |
| `AWS_ECR_LOGIN_URI` | ECR registry URI |
| `ECR_REPOSITORY_NAME` | ECR repo name |
| `DAGSHUB_USER_TOKEN` | DagsHub long-lived access token (required for non-interactive/headless MLflow auth in CI) |

## Running Locally

```bash
git clone https://github.com/Homonculus15/MLOps-Network-Security-Pipeline.git
cd MLOps-Network-Security-Pipeline
pip install -r requirements.txt

# create a .env file with MONGODB_URL_KEY and DagsHub token as needed
python app.py
```

App runs at `http://localhost:8000`. Visit `/docs` for the interactive Swagger UI.

## Running with Docker

```bash
docker build -t network-security-app .

docker run -d \
  -p 8080:8000 \
  --ipc="host" \
  --name=nsimage \
  -e AWS_ACCESS_KEY_ID=<value> \
  -e AWS_SECRET_ACCESS_KEY=<value> \
  -e AWS_REGION=<value> \
  -e DAGSHUB_USER_TOKEN=<value> \
  network-security-app
```

**Note:** the app listens on port `8000` internally — the Docker port mapping (`-p 8080:8000`) must match this, or the container will run "successfully" while being completely unreachable on the host port.

## API Endpoints

| Route | Method | Description |
|---|---|---|
| `/` | GET | Redirects to `/docs` |
| `/train` | GET | Triggers the full training pipeline |
| `/predict` | POST | Accepts a CSV file upload, returns predictions as an HTML table |
| `/docs` | GET | Interactive Swagger UI |

### Using `/predict`

Upload a CSV of feature columns matching the training schema. **Do not include the target/label column** (e.g. `Result`) in the upload — the endpoint expects raw feature data only; including the label column will cause a feature-mismatch error at inference time.

## CI/CD Pipeline

On every push to `main`, GitHub Actions:
1. Builds the Docker image.
2. Pushes it to Amazon ECR.
3. A **self-hosted runner on the EC2 instance** pulls the new image, stops/removes the previous container, and starts the new one.

### Self-hosted runner setup

The GitHub Actions runner on EC2 is installed as a **systemd service**, not run manually via `./run.sh` in a foreground SSH session — this keeps it alive across reboots and SSH disconnects:

```bash
cd ~/actions-runner
sudo ./svc.sh install
sudo ./svc.sh start
sudo ./svc.sh status
```

### Deploy step ordering

The deploy step always stops and removes the previous container **before** starting a new one (prevents `Conflict: container name already in use` on every redeploy):

```yaml
- name: Stop and remove old container
  run: |
    docker stop nsimage || true
    docker rm nsimage || true

- name: Run Docker Image to serve users
  run: |
    docker run -d \
      -p 8080:8000 \
      --ipc="host" \
      --name=nsimage \
      -e AWS_ACCESS_KEY_ID=${{ secrets.AWS_ACCESS_KEY_ID }} \
      -e AWS_SECRET_ACCESS_KEY=${{ secrets.AWS_SECRET_ACCESS_KEY }} \
      -e AWS_REGION=${{ secrets.AWS_REGION }} \
      -e DAGSHUB_USER_TOKEN=${{ secrets.DAGSHUB_USER_TOKEN }} \
      ${{ secrets.AWS_ECR_LOGIN_URI }}/${{ secrets.ECR_REPOSITORY_NAME }}:latest

- name: Clean up old/dangling images
  run: |
    docker image prune -f
```

## Infrastructure Notes

- **EC2 root volume:** provisioned at 20GB (resized up from the default 8GB, which fills up fast with Docker image layers + runner logs on repeated CI/CD deploys). Monitor with `df -h /`; run `docker image prune -f` regularly.
- **Security group:** inbound rules required for ports `22` (SSH), `80`/`443` (if fronting with a reverse proxy later), and `8080` (app access), all currently open to `0.0.0.0/0` for development — lock this down before any real production use.
- **DagsHub/MLflow authentication:** the client defaults to an interactive OAuth browser flow, which fails in headless containers. Authentication is done non-interactively via the `DAGSHUB_USER_TOKEN` environment variable instead.

## Known Limitations / Next Steps

- [ ] Restrict security group inbound rules to specific IPs before any production exposure.
- [ ] Move `dagshub.init()` out of module-level import in the trainer so the serving container doesn't require tracking-service connectivity just to boot.
- [ ] Add automated tests for the `/predict` schema validation (reject uploads with unexpected columns instead of erroring mid-inference).
- [ ] Consider an Elastic IP for the EC2 instance so the public address doesn't change across reboots.

## License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

## Acknowledgments

This project was built while following a Network Security MLOps course. The core architecture and pipeline design follow the course curriculum; implementation, debugging, deployment, and infrastructure troubleshooting (CI/CD, containerization, cloud deployment) were done independently.
