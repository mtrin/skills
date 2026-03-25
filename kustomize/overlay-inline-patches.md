# Overlay Inline Patches

## When to Use

A Kubernetes resource (e.g. HTTPRoute + WAF CRD) needs environment-specific values but the structure is identical. Instead of duplicating the file per overlay, keep **one copy in base** (prod values) and **patch in lower overlays**.

## Pattern

### Base

The resource file lives in base with prod values. Base `kustomization.yaml` references it:

```yaml
# base/kustomization.yaml
resources:
- httproute-suncorp-ingest.yaml
```

### Prod overlay

Inherits from base — no httproute reference needed:

```yaml
# overlays/plt-shared-prod/kustomization.yaml
resources:
- ../../base
```

### Lower overlay

Uses `op: replace` at `/spec` level to override the entire spec in one shot. Use `patch: |- #yaml` for IDE syntax highlighting:

```yaml
# overlays/plt-shared-lower/kustomization.yaml
resources:
- ../../base
patches:
  - target:
      kind: HTTPRoute
      name: loki-suncorp-ingest
    patch: |- #yaml
      - op: replace
        path: /spec
        value:
          parentRefs:
          - name: lower-gateway
            namespace: cluster-resources-agc
            sectionName: https-listener
          hostnames:
          - platform-loki-ingest.dev.finitytech.com.au
          rules:
          - matches:
            - path:
                type: PathPrefix
                value: /loki/api/v1/push
            backendRefs:
            - name: loki-gateway
              port: 80
  - target:
      kind: WebApplicationFirewallPolicy
      name: waf-suncorp-alloy-loki-ingest
    patch: |- #yaml
      - op: replace
        path: /spec
        value:
          targetRef:
            group: gateway.networking.k8s.io
            kind: HTTPRoute
            name: loki-suncorp-ingest
            namespace: plt-shared
          webApplicationFirewall:
            # created in plt_tf_platform/layers/waf/
            id: /subscriptions/.../waf-lower-suncorp-alloy-ingest-02
```

## Key Principles

- **One `op: replace` at `/spec`** — replaces the whole spec cleanly, avoids fragile array-index paths like `/spec/parentRefs/0/name`
- **`patch: |- #yaml`** — the `#yaml` comment enables YAML syntax highlighting in IDEs for the inline block
- **Base = prod** — prod overlay just inherits, lower overlay patches
- **Multi-document YAML** — when the base file has `---` separators (e.g. HTTPRoute + WAF CRD), each document becomes a separate resource; target each by `kind` + `name`
