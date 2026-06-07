# Live Inference Flow

```mermaid
flowchart TD
  A["Login + Number Verification"] --> B["CameraX frame"]
  B --> C["Stream uplink"]
  C --> D["Edge preprocess"]
  D --> E["Scene / road context"]
  E --> F["Vehicle detection"]
  F --> G["Multi-vehicle tracking"]
  G --> H["Target/risky vehicle selection"]
  H --> I["Context-gated routing"]
  I --> J["Risk pre-score"]
  J --> K["Mobile overlay"]
```
