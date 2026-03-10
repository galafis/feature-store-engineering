# Feature Store Engineering

<div align="center">

![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)

</div>

**[English](#english)** | **[Portugues (BR)](#portugues-br)**

---

## English

### Overview

A feature store implementation providing feature registry with versioning, online/offline stores, point-in-time lookups, feature computation pipelines, and a metadata catalog. Built in pure Python for ML feature management.

### Architecture

```mermaid
graph TD
    A[Raw Data Sources] --> B[Feature Compute Pipeline]
    B --> C[Feature Registry]
    C --> D[Online Store]
    C --> E[Offline Store]
    D --> F[Real-time Serving]
    E --> G[Point-in-Time Lookup]
    E --> H[Training Data Generation]
    C --> I[Metadata Catalog]
    I --> J[Feature Discovery]
    I --> K[Lineage Tracking]
```

### Data Flow

```mermaid
flowchart LR
    subgraph Ingestion
        A1[Raw Events] --> A2[Transform Functions]
        A2 --> A3[Computed Features]
    end
    subgraph Storage
        A3 --> B1[Online Store - Latest]
        A3 --> B2[Offline Store - Historical]
    end
    subgraph Serving
        B1 --> C1[Real-time Predictions]
        B2 --> C2[Training Datasets]
    end
```

### Features

- **Feature Registry**: Register, version, list, and filter feature definitions
- **Online Store**: Low-latency key-value store for latest feature values
- **Offline Store**: Historical feature storage with point-in-time lookups
- **Compute Pipeline**: Chain transform functions to derive features from raw data
- **Metadata Catalog**: Searchable catalog with feature descriptions and lineage

### Running Tests

```bash
pytest tests/ -v
```

### Author

**Gabriel Demetrios Lafis** - [GitHub](https://github.com/galafis)

---

## Portugues BR

### Visao Geral

Uma implementacao de feature store fornecendo registro de features com versionamento, stores online/offline, consultas point-in-time, pipelines de computacao de features e catalogo de metadados. Construido em Python puro para gerenciamento de features de ML.

### Arquitetura

```mermaid
graph TD
    A[Fontes de Dados] --> B[Pipeline de Computacao]
    B --> C[Registro de Features]
    C --> D[Store Online]
    C --> E[Store Offline]
    D --> F[Servico em Tempo Real]
    E --> G[Consulta Point-in-Time]
    C --> H[Catalogo de Metadados]
```

### Funcionalidades

- **Registro de Features**: Registrar, versionar e filtrar definicoes
- **Store Online**: Armazenamento chave-valor para valores mais recentes
- **Store Offline**: Armazenamento historico com consultas point-in-time
- **Pipeline de Computacao**: Encadear funcoes de transformacao
- **Catalogo de Metadados**: Catalogo pesquisavel com descricoes e linhagem

---

## License

MIT License - see [LICENSE](LICENSE) for details.
