# Production Architecture Blueprint: AI Mental Health Support System

## 1) Clean, Modular Project Structure

```text
mh-ai/
├── app/
│   └── main.py                         # Streamlit entrypoint
├── src/
│   ├── domain/
│   │   ├── entities.py                 # Core business entities
│   │   └── value_objects.py            # Domain value constraints
│   ├── application/
│   │   ├── services/
│   │   │   ├── nlp_service.py
│   │   │   ├── risk_service.py
│   │   │   ├── personalization_service.py
│   │   │   └── scoring_service.py
│   │   └── use_cases/
│   │       ├── analyze_message.py
│   │       ├── process_session.py
│   │       └── generate_response.py
│   ├── infrastructure/
│   │   ├── db/
│   │   │   ├── models.py
│   │   │   ├── repositories.py
│   │   │   └── session.py
│   │   ├── ml/
│   │   │   ├── hf_pipeline.py
│   │   │   ├── model_registry.py
│   │   │   └── tokenizer_loader.py
│   │   ├── auth/
│   │   │   ├── jwt_auth.py
│   │   │   └── password_policy.py
│   │   ├── cache/
│   │   │   └── memory_store.py         # Redis-backed conversation memory
│   │   ├── alerts/
│   │   │   └── notifier.py             # Email/SMS/Slack escalation
│   │   ├── logging/
│   │   │   └── logger.py
│   │   └── monitoring/
│   │       └── metrics.py
│   ├── interfaces/
│   │   ├── streamlit_ui/
│   │   │   ├── pages.py
│   │   │   └── components.py
│   │   └── api/
│   │       └── routers.py              # Optional FastAPI backend
│   └── config/
│       ├── settings.py
│       └── constants.py
├── ml/
│   ├── training/
│   │   ├── finetune_multilabel.py
│   │   ├── evaluate.py
│   │   └── dataset_builder.py
│   ├── inference/
│   │   └── predict.py
│   └── explainability/
│       ├── shap_explainer.py
│       └── attention_viz.py
├── scripts/
│   ├── seed_data.py
│   └── migrate.py
├── tests/
│   ├── unit/
│   ├── integration/
│   └── e2e/
├── docker-compose.yml
├── Dockerfile
├── .github/workflows/ci.yml
└── pyproject.toml
```

---

## 2) System Architecture (High-Level)

**Presentation Layer**
- Streamlit UI for end-users and admin dashboards.
- Optional REST API gateway (FastAPI) for external integrations/mobile.

**Application Layer**
- Orchestrates use-cases:
  - Analyze incoming message
  - Update conversation state
  - Run risk assessment
  - Generate personalized response
  - Persist analytics

**Domain Layer**
- Core entities: `User`, `Session`, `Message`, `EmotionResult`, `RiskAssessment`, `MentalHealthScore`.
- Business rules: threshold policies, escalation logic, role restrictions.

**Infrastructure Layer**
- DB: PostgreSQL (prod), SQLite (dev fallback).
- Redis for context memory + rate limiting.
- HuggingFace model serving components.
- Logging, metrics, alert adapters.

---

## 3) NLP/ML Stack

### 3.1 Transformer-based multi-label emotion classification
- Base model: `distilbert-base-uncased` (fast) or `bert-base-uncased` (higher capacity).
- Head: sigmoid multi-label classification (`BCEWithLogitsLoss`).
- Output labels example:
  - `joy, sadness, anger, fear, anxiety, guilt, loneliness, hope`.

### 3.2 Sentiment + stress analysis
- Sentiment:
  - Option A: dedicated model (`cardiffnlp/twitter-roberta-base-sentiment-latest`).
  - Option B: derive sentiment from emotion logits.
- Stress estimation:
  - Auxiliary classifier (`low`, `moderate`, `high`) or regression score `[0,1]`.

### 3.3 Risk (self-harm / crisis) detection
- Dedicated binary classifier + rules:
  - `risk_prob >= 0.80` => `HIGH`
  - `0.55 <= risk_prob < 0.80` => `MODERATE`
  - else `LOW`
- Rule boosts:
  - Escalate one level if crisis keywords occur repeatedly in rolling window.
  - Escalate one level if high-risk pattern frequency > threshold over 7 days.

### 3.4 Mental health score (regression)
- Gradient Boosting/XGBoost regressor (feature-level):
  - rolling stress mean
  - sentiment volatility
  - sleep/activity proxies (if available)
  - session frequency and linguistic markers
- Output normalized score `0–100` + confidence band.

### 3.5 Behavioral pattern detection
- Time-series features over last N sessions:
  - trend in negative affect
  - abrupt change points
  - disengagement (drop in response rate)
- Techniques:
  - rolling z-score anomaly detection
  - change-point algorithms

---

## 4) Real-Time Conversation Memory + Personalization

- Short-term memory:
  - Last K turns in Redis (`session:{id}:context`).
- Long-term profile:
  - Persisted user preferences, triggers, recurring concerns in PostgreSQL.
- Response generation:
  - Prompt template conditions on:
    - current emotions + stress + risk level
    - historical user context
    - safety policy constraints

**Safety response policy**
1. If `HIGH` risk, switch to crisis-safe script + immediate escalation.
2. Avoid diagnostic/medical claims.
3. Encourage professional help and emergency contacts by locale.

---

## 5) Authentication + RBAC

- Auth:
  - JWT access + refresh tokens.
  - Password hashing: Argon2 or bcrypt.
- Roles:
  - `user`: chat, personal dashboard.
  - `admin`: aggregate analytics, risk queue, intervention logs.
- Security controls:
  - audit logs for admin actions
  - brute-force lockout
  - encrypted secrets via environment/secret manager

---

## 6) Database Design

### Core tables
- `users(id, email, password_hash, role, created_at)`
- `sessions(id, user_id, started_at, ended_at)`
- `messages(id, session_id, sender, text, ts)`
- `emotion_predictions(id, message_id, labels_json, confidences_json)`
- `risk_assessments(id, message_id, risk_prob, risk_level, triggered_rules_json)`
- `mental_health_scores(id, user_id, score, confidence, ts)`
- `alerts(id, user_id, risk_level, status, created_at, resolved_at)`
- `interventions(id, alert_id, admin_id, notes, ts)`

**Storage strategy**
- Dev: SQLite
- Production: PostgreSQL + read replica (optional at scale)

---

## 7) Logging, Monitoring, Observability

- Structured logs (JSON): request_id, user_id (hashed), model_version, latency_ms.
- Metrics (Prometheus/OpenTelemetry):
  - inference latency p50/p95
  - model confidence drift
  - risk alert rate
  - auth failures
- Dashboards (Grafana/CloudWatch/Azure Monitor).
- Error tracking: Sentry.

---

## 8) Explainability

- SHAP on regression/classification features for dashboard-level transparency.
- Attention visualization for transformer outputs in admin diagnostics.
- Store explanation artifacts by prediction id for auditability.

---

## 9) Fine-Tuning Pipeline (HuggingFace)

1. Dataset curation + annotation (multi-label emotion, risk tags).
2. Train/val/test split with stratification.
3. Fine-tune DistilBERT/BERT via `Trainer`.
4. Evaluate metrics:
   - F1 micro/macro
   - PR-AUC (risk)
   - calibration error
5. Register versioned model in model registry (`mlflow` or simple registry table).
6. Promote to staging/prod after gate checks.

---

## 10) CI/CD Ready Setup

### CI (GitHub Actions)
- Lint (`ruff`), type-check (`mypy`), tests (`pytest`).
- Security scan (`bandit`, `pip-audit`).
- Build Docker image.

### CD
- Staging deploy on `develop`.
- Production deploy on version tags.
- Blue/green or rolling deployment strategy.

---

## 11) Docker + Deployment

### Containers
- `web`: Streamlit/FastAPI app
- `worker`: background jobs (alerts, scheduled scoring)
- `db`: PostgreSQL
- `redis`: memory/cache
- `nginx`: TLS termination/reverse proxy

### Cloud architecture (AWS example)
- ECS Fargate (app + worker)
- RDS PostgreSQL
- ElastiCache Redis
- ECR image registry
- CloudWatch logs/metrics
- Secrets Manager for secrets
- SNS/SES for alert notifications

### Azure equivalent
- Azure Container Apps / AKS
- Azure Database for PostgreSQL
- Azure Cache for Redis
- Azure Monitor + Key Vault

---

## 12) Risk Escalation Flow (Operational)

1. User sends message.
2. NLP inference pipeline computes emotions, sentiment, stress, risk probability.
3. Rule engine determines `LOW/MODERATE/HIGH`.
4. If `HIGH`:
   - immediate safe-response template
   - create alert record
   - notify admin/on-call channel
5. Admin dashboard shows active risk queue with explanation panel.
6. Intervention notes stored for compliance and model feedback loop.

---

## 13) Professional Extras for Portfolio Impact

- A/B testing for response strategies.
- Offline evaluation notebook + error analysis report.
- Drift detection job + retraining trigger.
- Data retention/privacy policy and anonymization pipeline.
- Synthetic data generator for safe demo environments.

This design gives you a genuinely production-grade, portfolio-strong system that blends ML rigor, safety, and software engineering best practices.
