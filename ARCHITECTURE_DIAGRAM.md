# The Negotiator - System Architecture

## Class Diagram (Mermaid)

```mermaid
classDiagram
    %% Backend Models
    class JobSpec {
        +str origin
        +str destination
        +float distance_miles
        +date move_date
        +HomeInfo home
        +Inventory inventory
        +bool confirmed_by_user
        +datetime confirmed_at
        +model_validate(data) JobSpec
        +model_dump(mode) dict
        +is_binding_ready(required) bool
        +missing_binding_fields(required) list
        +merge(spec1, spec2) JobSpec
    }
    
    class HomeInfo {
        +int bedrooms
        +int bathrooms
        +bool stairs
        +str special_access
    }
    
    class Inventory {
        +list~str~ large_items
        +list~str~ special_items
    }
    
    class Quote {
        +str vendor_id
        +str vendor_name
        +str negotiation_style
        +list~LineItem~ line_items
        +float total
        +QuoteOutcome outcome
        +str transcript_url
        +model_validate(data) Quote
        +model_dump(mode) dict
    }
    
    class LineItem {
        +str fee_type
        +str description
        +float amount
    }
    
    class JobRecord {
        +str id
        +str status
        +get_json_field(key) Any
        +set_json_field(key, value) void
    }
    
    class QuoteOutcome {
        <<enumeration>>
        COMPLETED
        CALLBACK
        NO_ANSWER
    }
    
    %% Backend Services
    class ElevenLabsClient {
        +str api_key
        +str base_url
        +bool use_real_api
        +str ngrok_url
        +start_intake_session(job_id, webhook_url) dict
        +start_counterparty_session(job_id, vendor_id, vendor_name, style, webhook_url) dict
        +parse_voice_transcript(transcript) JobSpec
        -_get_webhook_url() str
        -_mock_start_session(job_id) dict
        -_mock_parse_transcript(transcript) JobSpec
    }
    
    class CallerService {
        +VerticalConfig config
        +CallListService call_list
        +QuoteBuilder quote_builder
        +gather_quotes(spec) list~Quote~
        -_call_counterparty(counterparty, spec) Quote
    }
    
    class CloserService {
        +VerticalConfig config
        +negotiate(quotes, spec) tuple~list~Quote~~, list~Negotiation~~
    }
    
    class DocumentIntakeService {
        +parse_text_content(text) JobSpec
        +parse_upload(filename, content) JobSpec
    }
    
    class CallListService {
        +VerticalConfig config
        +get_counterparties() list~Counterparty~
        +build_call_list(origin) list~str~
    }
    
    class QuoteBuilder {
        +VerticalConfig config
        +build_quote(counterparty, spec) Quote
    }
    
    class VerticalConfig {
        +str vertical
        +str display_name
        +dict job_spec
        +dict benchmarks
        +list~Counterparty~ counterparties
    }
    
    class Counterparty {
        +str id
        +str name
        +str phone
        +str negotiation_style
        +float base_multiplier
        +list~HiddenFee~ hidden_fees
        +list~UpsellFee~ upsell_fees
    }
    
    %% Backend API Routes
    class JobsRouter {
        +POST / - create_job() CreateJobResponse
        +GET /{job_id}/voice/session - get_voice_session() dict
        +POST /{job_id}/voice - submit_voice_intake() dict
        +POST /{job_id}/documents - upload_document() dict
        +GET /{job_id}/spec - get_spec() dict
        +PATCH /{job_id}/spec - update_spec() dict
        +POST /{job_id}/confirm - confirm_spec() dict
        +POST /{job_id}/calls - start_calls() dict
        +GET /{job_id}/calls - get_calls() dict
        +POST /{job_id}/negotiate - run_negotiation() dict
    }
    
    class WebhookRouter {
        +POST /elevenlabs - elevenlabs_webhook() dict
        +POST /call-result - call_result_webhook() dict
        +GET /transcript/{job_id}/{vendor_id} - get_transcript() dict
        +GET /ngrok-url - get_ngrok_url() dict
    }
    
    class PagesRouter {
        +GET / - index() HTMLResponse
        +GET /intake/voice - voice_intake() HTMLResponse
        +GET /intake/documents - documents() HTMLResponse
        +GET /intake/confirm - confirm() HTMLResponse
        +GET /calls - calls() HTMLResponse
        +GET /negotiate - negotiate() HTMLResponse
        +GET /report - report() HTMLResponse
    }
    
    class ReportsRouter {
        +GET /{job_id}/report - get_report() dict
    }
    
    %% Frontend Components
    class VoiceIntakePage {
        +string transcript
        +boolean loading
        +string error
        +any session
        +string jobId
        +string voiceText
        +handleSubmit() void
        +handleVoiceCommand() void
        +useEffect() void
    }
    
    class CallsPage {
        +boolean loading
        +string error
        +Quote[] quotes
        +boolean started
        +string voiceText
        +handleStartCalls() void
        +handleVoiceCommand() void
    }
    
    class NegotiatePage {
        +boolean loading
        +string error
        +Negotiation[] negotiations
        +boolean done
        +string voiceText
        +handleNegotiate() void
        +handleVoiceCommand() void
    }
    
    class ReportPage {
        +string jobId
        +JobSpec spec
        +Quote[] quotes
        +Negotiation[] negotiations
        +useEffect() void
    }
    
    class ConfirmPage {
        +string jobId
        +JobSpec spec
        +boolean loading
        +handleConfirm() void
    }
    
    class DocumentsPage {
        +string jobId
        +boolean loading
        +handleUpload() void
    }
    
    class VoiceButton {
        +function onCommand
        +string label
        +string className
        +handleClick() void
    }
    
    class ProgressStepper {
        +int currentStep
        +render() JSX
    }
    
    class VoiceFeedback {
        +string text
        +render() JSX
    }
    
    class useVoiceControl {
        +string transcript
        +boolean isListening
        +startListening() void
        +stopListening() void
    }
    
    %% Relationships
    JobSpec --> HomeInfo
    JobSpec --> Inventory
    Quote --> LineItem
    JobRecord --> JobSpec
    JobRecord --> Quote
    
    ElevenLabsClient ..> JobSpec : creates
    CallerService ..> Quote : creates
    CallerService ..> JobSpec : uses
    CloserService ..> Quote : uses
    DocumentIntakeService ..> JobSpec : creates
    
    JobsRouter ..> ElevenLabsClient : uses
    JobsRouter ..> CallerService : uses
    JobsRouter ..> CloserService : uses
    JobsRouter ..> DocumentIntakeService : uses
    JobsRouter ..> JobRecord : uses
    
    WebhookRouter ..> JobRecord : uses
    WebhookRouter ..> Quote : creates
    
    VoiceIntakePage ..> useVoiceControl : uses
    VoiceIntakePage ..> VoiceButton : uses
    VoiceIntakePage ..> ProgressStepper : uses
    VoiceIntakePage ..> VoiceFeedback : uses
    
    CallsPage ..> VoiceButton : uses
    CallsPage ..> ProgressStepper : uses
    CallsPage ..> VoiceFeedback : uses
    
    NegotiatePage ..> VoiceButton : uses
    NegotiatePage ..> ProgressStepper : uses
    NegotiatePage ..> VoiceFeedback : uses
    
    ReportPage ..> ProgressStepper : uses
    ConfirmPage ..> ProgressStepper : uses
    DocumentsPage ..> ProgressStepper : uses
```

## Data Flow Diagram

```mermaid
flowchart TD
    subgraph Frontend["Frontend (Next.js)"]
        A[VoiceIntakePage] -->|GET /api/jobs/{id}/voice/session| B[JobsRouter]
        A -->|POST /api/jobs/{id}/voice| B
        C[CallsPage] -->|POST /api/jobs/{id}/calls| B
        D[NegotiatePage] -->|POST /api/jobs/{id}/negotiate| B
        E[ReportPage] -->|GET /api/jobs/{id}/calls| B
        E -->|GET /api/jobs/{id}/report| F[ReportsRouter]
    end
    
    subgraph Backend["Backend (FastAPI)"]
        B --> G[ElevenLabsClient]
        B --> H[CallerService]
        B --> I[CloserService]
        B --> J[DocumentIntakeService]
        H --> K[CallListService]
        H --> L[QuoteBuilder]
        G -->|webhook| M[WebhookRouter]
        M -->|store quote| B
    end
    
    subgraph Database["Database (SQLite)"]
        N[JobRecord]
    end
    
    subgraph External["External Services"]
        O[ElevenLabs API]
        P[OpenAI API]
    end
    
    B <--> N
    G <--> O
    G <--> P
    
    style Frontend fill:#e1f5fe
    style Backend fill:#f3e5f5
    style Database fill:#fff3e0
    style External fill:#e8f5e8
```

## Agent Interaction Flow

```mermaid
sequenceDiagram
    participant U as User
    participant N as Neogitatera (Main Agent)
    participant B as Backend
    participant C as Carolina Haulers
    participant BM as Budget Move Express
    participant P as Premium Relocation Co
    
    U->>N: Voice conversation (collects move details)
    N->>B: Webhook callback with transcript
    B->>B: Parse and store JobSpec
    
    U->>B: POST /api/jobs/{id}/confirm
    B->>U: Job confirmed
    
    U->>B: POST /api/jobs/{id}/calls
    B->>C: Call counterparty agent
    B->>BM: Call counterparty agent
    B->>P: Call counterparty agent
    
    C->>B: Webhook: /api/webhook/call-result
    BM->>B: Webhook: /api/webhook/call-result
    P->>B: Webhook: /api/webhook/call-result
    
    B->>U: Quotes received
    
    U->>B: POST /api/jobs/{id}/negotiate
    B->>U: Negotiated quotes
    
    U->>B: GET /api/jobs/{id}/report
    B->>U: Final report