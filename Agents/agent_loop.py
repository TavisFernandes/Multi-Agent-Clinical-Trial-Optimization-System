"""
Agent Loop Module
Implements multi-agent reasoning loop: Architect -> Critic -> Improve (3 iterations).
"""

import logging
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

from .retriever_agent import RetrieverAgent
from .architect_agent import ArchitectAgent
from .critic_agent import CriticAgent

logger = logging.getLogger(__name__)

# Type alias for logging callback
LogCallback = Optional[Callable[[Dict[str, Any]], None]]


@dataclass
class AgentState:
    """Container for agent loop state."""
    session_id: str
    iteration: int = 0
    report_draft: str = ""
    retrieved_docs: List[Dict[str, Any]] = field(default_factory=list)
    missing_fields: List[str] = field(default_factory=list)
    critic_approved: bool = False
    quality_scores: List[float] = field(default_factory=list)
    iteration_logs: List[str] = field(default_factory=list)


def emit_log(log_cb: LogCallback, payload: Dict[str, Any]) -> None:
    """Emit log event if callback provided."""
    if log_cb:
        # Keep backward-compatible streaming payload for existing frontend terminal.
        if payload.get("type") != "loop_complete":
            payload = {
                **payload,
                "type": "reasoning",
                "agent": payload.get("agent", "Orchestrator"),
            }
        log_cb(payload)


def run_agent_loop(
    pipeline_result: Any,
    log_cb: LogCallback = None,
    max_iterations: int = 3
) -> Dict[str, Any]:
    """
    Run multi-agent reasoning loop.

    Flow: Retriever -> Architect -> Critic -> (repeat if needed)

    Args:
        pipeline_result: Output from main pipeline
        log_cb: Optional callback for logging events
        max_iterations: Maximum refinement iterations

    Returns:
        Dictionary with final report and metadata
    """
    # Initialize agents
    retriever = RetrieverAgent()
    architect = ArchitectAgent()
    critic = CriticAgent()

    # Initialize state
    state = AgentState(session_id=str(uuid.uuid4()))

    emit_log(
        log_cb,
        {
            'type': 'loop_start',
            'session_id': state.session_id,
            'max_iterations': max_iterations,
            'message': f'Starting multi-agent reasoning loop ({max_iterations} iterations max)'
        }
    )

    # Main loop
    for iteration in range(1, max_iterations + 1):
        state.iteration = iteration

        emit_log(
            log_cb,
            {
                'type': 'iteration_start',
                'iteration': iteration,
                'message': f'Beginning iteration {iteration}/{max_iterations}'
            }
        )

        # Step 1: Retriever fetches relevant documents
        emit_log(
            log_cb,
            {
                'type': 'agent_action',
                'agent': 'Retriever',
                'iteration': iteration,
                'message': 'Searching clinical trial database for relevant documents...'
            }
        )

        entities = getattr(pipeline_result, 'ner_entities', [])
        text_preview = getattr(pipeline_result, 'raw_input_preview', '')
        retrieved_docs = retriever.search(text_preview, entities, top_k=5)

        state.retrieved_docs = retrieved_docs

        ent_log = [
            f"{e.get('text', '')}[{e.get('label', '')}]"
            for e in (entities or [])
            if isinstance(e, dict)
        ]
        trial_titles = [str(d.get("title", ""))[:120] for d in retrieved_docs[:5]]
        logger.info(
            "Retriever result: iteration=%s entity_spans=%s trial_titles=%s",
            iteration,
            ent_log[:15],
            trial_titles,
        )

        emit_log(
            log_cb,
            {
                'type': 'agent_complete',
                'agent': 'Retriever',
                'iteration': iteration,
                'docs_found': len(retrieved_docs),
                'message': f'Retrieved {len(retrieved_docs)} structured records: {"; ".join(trial_titles) or "(none)"}'
            }
        )

        # Step 2: Architect generates/improves report
        emit_log(
            log_cb,
            {
                'type': 'agent_action',
                'agent': 'Architect',
                'iteration': iteration,
                'message': 'Synthesizing structured clinical report...'
            }
        )

        if iteration == 1:
            # First iteration: generate new report
            report = architect.generate_report(
                pipeline_result=pipeline_result,
                retrieved_docs=retrieved_docs,
                missing_fields=[],
                iteration=iteration
            )
        else:
            # Subsequent iterations: improve with missing fields
            report = architect.generate_report(
                pipeline_result=pipeline_result,
                retrieved_docs=retrieved_docs,
                missing_fields=state.missing_fields,
                iteration=iteration
            )

        state.report_draft = report

        logger.info(
            "Architect: iteration=%s report_chars=%s sections= synopsis+evidence+interpretation",
            iteration,
            len(report),
        )

        emit_log(
            log_cb,
            {
                'type': 'agent_complete',
                'agent': 'Architect',
                'iteration': iteration,
                'report_length': len(report),
                'message': f'Generated grounded report ({len(report)} characters)'
            }
        )

        # Step 3: Critic reviews report
        emit_log(
            log_cb,
            {
                'type': 'agent_action',
                'agent': 'Critic',
                'iteration': iteration,
                'message': 'Reviewing report for completeness and quality...'
            }
        )

        approved, missing_fields, quality_metrics = critic.review(report, iteration)

        state.missing_fields = missing_fields
        state.critic_approved = approved

        # Store quality score
        total_checks = quality_metrics.get('checks_passed', 0) + quality_metrics.get('checks_failed', 0)
        if total_checks > 0:
            quality_score = quality_metrics.get('checks_passed', 0) / total_checks
            state.quality_scores.append(quality_score)

        emit_log(
            log_cb,
            {
                'type': 'agent_complete',
                'agent': 'Critic',
                'iteration': iteration,
                'approved': approved,
                'missing_fields': missing_fields,
                'message': critic.get_feedback_message(approved, missing_fields, quality_metrics)
            }
        )

        state.iteration_logs.append(
            f"Iteration {iteration}: retriever={len(retrieved_docs)} docs; "
            f"critic_approved={approved}; missing={missing_fields or 'none'}"
        )

        # Check if we should stop
        if approved:
            emit_log(
                log_cb,
                {
                    'type': 'loop_complete',
                    'session_id': state.session_id,
                    'iterations_used': iteration,
                    'approved': True,
                    'critic_approved': True,
                    'message': f'Report approved at iteration {iteration}/{max_iterations}'
                }
            )
            break

        # If not approved and more iterations available, continue
        if iteration < max_iterations and missing_fields:
            emit_log(
                log_cb,
                {
                    'type': 'feedback',
                    'iteration': iteration,
                    'missing_fields': missing_fields,
                    'message': f'Feedback: Architect will address {missing_fields} in next iteration'
                }
            )

    # Final iteration check
    if not state.critic_approved:
        emit_log(
            log_cb,
            {
                'type': 'loop_complete',
                'session_id': state.session_id,
                'iterations_used': max_iterations,
                'approved': False,
                'critic_approved': False,
                'remaining_issues': state.missing_fields,
                'message': f'Max iterations ({max_iterations}) reached. Report may be incomplete.'
            }
        )

    # Build final result (agent_iterations = iteration log strings for API clarity)
    quality_rows = [
        {
            "iteration": i + 1,
            "quality_score": state.quality_scores[i]
            if i < len(state.quality_scores)
            else None,
        }
        for i in range(state.iteration)
    ]
    normalized_output = {
        "input_type": getattr(pipeline_result, "route", "unknown"),
        "entities": getattr(pipeline_result, "ner_entities", []),
        "analysis": getattr(pipeline_result, "analysis", ""),
        "retrieved_trials": state.retrieved_docs,
        "agent_iterations": state.iteration_logs,
        "agent_iteration_quality": quality_rows,
        "final_report": state.report_draft,
    }

    return {
        'session_id': state.session_id,
        'report': state.report_draft,
        'critic_approved': state.critic_approved,
        'missing_fields': state.missing_fields,
        'iterations_used': state.iteration,
        'max_iterations': max_iterations,
        'retrieved_docs': state.retrieved_docs,
        'quality_scores': state.quality_scores,
        'pipeline': {
            'route': getattr(pipeline_result, 'route', 'unknown'),
            'model_outputs': getattr(pipeline_result, 'model_outputs', {}),
            'ner_entities': getattr(pipeline_result, 'ner_entities', []),
            'warnings': getattr(pipeline_result, 'warnings', [])
        },
        **normalized_output,
    }


def run_simple(
    pipeline_result: Any,
    max_iterations: int = 3
) -> Dict[str, Any]:
    """
    Run agent loop without logging callback.

    Args:
        pipeline_result: Pipeline output
        max_iterations: Maximum iterations

    Returns:
        Final result dictionary
    """
    return run_agent_loop(pipeline_result, log_cb=None, max_iterations=max_iterations)


# Example usage
if __name__ == "__main__":
    print("=== Agent Loop Test ===")

    # Mock pipeline result
    class MockResult:
        route = 'text'
        ner_entities = [
            {'text': 'stage II', 'label': 'DISEASE'},
            {'text': 'chemotherapy', 'label': 'THERAPY'},
            {'text': 'Phase 2', 'label': 'TRIAL'}
        ]
        model_outputs = {'lstm_source': 'mock_lstm'}
        warnings = []
        raw_input_preview = 'Patient with stage II cancer receiving treatment'

    # Simple run without logging
    result = run_simple(MockResult(), max_iterations=2)

    print(f"Session ID: {result['session_id']}")
    print(f"Iterations used: {result['iterations_used']}")
    print(f"Critic approved: {result['critic_approved']}")
    print(f"Missing fields: {result['missing_fields']}")
    print(f"\nReport preview (first 500 chars):")
    print(result['report'][:500])
