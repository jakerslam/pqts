"""External I/O adapter layer for canonical PQTS architecture."""

from adapters.market_data import load_adapter_module
from adapters.prediction_market_client import (
    APICredentials,
    AuthContext,
    ClientStateError,
    PredictionMarketClientContract,
)
from adapters.prediction_market_settlement import (
    TypedOrder,
    evaluate_settlement_invariants,
    validate_deployment_registry,
    validate_typed_order,
    verify_fee_symmetry,
)
from adapters.prediction_market_streaming import (
    BuilderScope,
    LocalSigner,
    RemoteSigner,
    SignRequest,
    StreamHealthTracker,
)
from adapters.provider_contracts import (
    ProviderErrorEnvelope,
    ProviderResponseEnvelope,
    call_with_envelope,
)
from adapters.registry import AdapterDescriptor, adapters_by_kind, default_adapter_descriptors
from adapters.retrieval_surface import (
    MultiSourceRetrievalSurface,
    RetrievalRecord,
    merge_retrieval_sources,
)

__all__ = [
    "AdapterDescriptor",
    "APICredentials",
    "AuthContext",
    "ClientStateError",
    "BuilderScope",
    "LocalSigner",
    "MultiSourceRetrievalSurface",
    "RemoteSigner",
    "SignRequest",
    "StreamHealthTracker",
    "TypedOrder",
    "PredictionMarketClientContract",
    "ProviderErrorEnvelope",
    "ProviderResponseEnvelope",
    "RetrievalRecord",
    "adapters_by_kind",
    "call_with_envelope",
    "default_adapter_descriptors",
    "evaluate_settlement_invariants",
    "load_adapter_module",
    "merge_retrieval_sources",
    "validate_deployment_registry",
    "validate_typed_order",
    "verify_fee_symmetry",
]
