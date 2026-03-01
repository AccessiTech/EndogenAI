"""
EndogenAI Sensory / Input Layer.

Provides multi-modal signal ingestion, normalisation, timestamping, and upward
dispatch for the brAIn framework.  All output conforms to
shared/types/signal.schema.json.
"""

from endogenai_sensory_input.ingestion import SignalIngestor
from endogenai_sensory_input.models import Modality, RawInput, Signal

__all__ = ["SignalIngestor", "RawInput", "Signal", "Modality"]
