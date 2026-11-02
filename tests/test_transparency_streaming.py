"""Unit and integration coverage for Phase 5.5.2.I2 WebSocket streaming."""

from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, Mock

import pytest
from flask import Flask
from flask_socketio import SocketIO

from kicli_code_assist.agent.code_implementation import CodeImplementationAgent
from kicli_code_assist.agent.transparency_event_emitter import TransparencyEventEmitter
from kicli_code_assist.web import server_websocket
from kicli_code_assist.web.server_websocket import register_websocket


@pytest.fixture
def emitter():
    return TransparencyEventEmitter(Mock(), "exec-123")


def assert_common_event(emitter, call, event_name):
    name, data = call.args[:2]
    assert name == event_name
    assert data["execution_id"] == emitter.execution_id
    datetime.fromisoformat(data["timestamp"])
    assert call.kwargs == {
        "room": f"execution:{emitter.execution_id}",
        "skip_sid": False,
    }


class TestTransparencyEventEmitter:
    def test_decision_event_structure_and_room(self, emitter):
        emitter.emit_decision(["patch", "rewrite"], "patch", 1.4, "small change")
        call = emitter.socketio.emit.call_args
        assert_common_event(emitter, call, "agent:decision")
        assert call.args[1]["options_considered"] == ["patch", "rewrite"]
        assert call.args[1]["confidence_score"] == 1.0
        assert call.args[1]["reasoning"] == "small change"

    def test_execution_includes_non_negative_duration(self, emitter):
        emitter.emit_execution("file_write", "success", -5, {"path": "a.py"})
        data = emitter.socketio.emit.call_args.args[1]
        assert data["duration_ms"] == 0
        assert data["details"] == {"path": "a.py"}

    def test_error_includes_recovery_suggestion_and_empty_optional_id(self, emitter):
        emitter.emit_error("ValueError", "bad input", "Retry with valid input")
        data = emitter.socketio.emit.call_args.args[1]
        assert data["recovery_suggestion"] == "Retry with valid input"
        assert data["error_id"] == ""

    def test_llm_call_includes_cost_and_latency(self, emitter):
        emitter.emit_llm_call("gpt-4o", "generation", 10, 20, 30, 0.25, 125)
        data = emitter.socketio.emit.call_args.args[1]
        assert data["cost"] == 0.25
        assert data["latency_ms"] == 125
        assert data["total_tokens"] == 30

    def test_metric_update_batches_metrics_in_one_event(self, emitter):
        metrics = {"tokens": 30, "latency_ms": 125, "counters": {"files": 2}}
        emitter.emit_metric_update("generation", metrics)
        emitter.socketio.emit.assert_called_once()
        data = emitter.socketio.emit.call_args.args[1]
        assert data["phase"] == "generation"
        assert data["metrics"] is metrics

    def test_session_end_finalizes_event_and_preserves_trace_data(self, emitter):
        emitter.emit_session_end(True, 7, 500, "/tmp/trace.json", "done")
        data = emitter.socketio.emit.call_args.args[1]
        assert data["success"] is True
        assert data["total_events"] == 7
        assert data["trace_file"] == "/tmp/trace.json"
        assert emitter.event_count == 1

    @pytest.mark.parametrize(
        "method,args,event",
        [
            ("emit_decision", ([], "", 0, None), "agent:decision"),
            ("emit_execution", ("", "", None, None), "agent:execution"),
            ("emit_error", ("", "", None, None), "agent:error"),
            ("emit_metric_update", ("", None), "agent:metric_update"),
            ("emit_session_end", (False, 0, None, None, None), "agent:session_end"),
        ],
    )
    def test_all_events_have_metadata_and_target_room(self, emitter, method, args, event):
        getattr(emitter, method)(*args)
        assert_common_event(emitter, emitter.socketio.emit.call_args, event)

    def test_event_order_and_count_tracking(self, emitter):
        emitter.emit_decision(["a"], "a", 0.5)
        emitter.emit_execution("run", "success", 1)
        emitter.emit_session_end(True)
        assert [c.args[0] for c in emitter.socketio.emit.call_args_list] == [
            "agent:decision",
            "agent:execution",
            "agent:session_end",
        ]
        assert emitter.event_count == 3


@pytest.fixture
def websocket_server():
    app = Flask(__name__)
    app.config["TESTING"] = True
    socketio = SocketIO(app, async_mode="threading")
    server_websocket._EXECUTION_SUBSCRIPTIONS.clear()
    register_websocket(app, socketio)
    yield app, socketio
    server_websocket._EXECUTION_SUBSCRIPTIONS.clear()


def received(client, event):
    return [item["args"][0] for item in client.get_received("/agent/execution")
            if item["name"] == event]


class TestExecutionWebSocketHandlers:
    def test_namespace_connection_works(self, websocket_server):
        app, socketio = websocket_server
        client = socketio.test_client(app, namespace="/agent/execution")
        assert client.is_connected("/agent/execution")

    def test_subscribe_and_unsubscribe_track_sid_and_emit_ack(self, websocket_server):
        app, socketio = websocket_server
        client = socketio.test_client(app, namespace="/agent/execution")
        client.get_received("/agent/execution")
        client.emit("subscribe:execution", {"execution_id": "run-1"},
                    namespace="/agent/execution")
        assert "run-1" in server_websocket._EXECUTION_SUBSCRIPTIONS
        # The server records the Socket.IO SID (the test client intentionally
        # does not expose it), and exactly one client is subscribed.
        assert len(server_websocket._EXECUTION_SUBSCRIPTIONS["run-1"]) == 1
        assert received(client, "agent:subscribed")[-1]["status"] == "subscribed"
        client.emit("unsubscribe:execution", {"execution_id": "run-1"},
                    namespace="/agent/execution")
        assert "run-1" not in server_websocket._EXECUTION_SUBSCRIPTIONS
        assert received(client, "agent:unsubscribed")[-1]["status"] == "unsubscribed"

    def test_status_returns_status_object(self, websocket_server):
        app, socketio = websocket_server
        client = socketio.test_client(app, namespace="/agent/execution")
        client.emit("subscribe:execution", {"execution_id": "run-2"},
                    namespace="/agent/execution")
        client.get_received("/agent/execution")
        client.emit("get:execution_status", {"execution_id": "run-2"},
                    namespace="/agent/execution")
        status = received(client, "agent:status")[-1]
        assert status == {
            "execution_id": "run-2",
            "status": "running",
            "total_events": 0,
            "active_subscribers": 1,
        }

    def test_invalid_subscription_and_status_are_rejected(self, websocket_server):
        app, socketio = websocket_server
        client = socketio.test_client(app, namespace="/agent/execution")
        client.emit("subscribe:execution", {}, namespace="/agent/execution")
        client.emit("get:execution_status", {}, namespace="/agent/execution")
        errors = received(client, "error")
        assert len(errors) == 2
        assert all(error["message"] == "execution_id required" for error in errors)

    def test_disconnect_cleans_all_subscriptions(self, websocket_server):
        app, socketio = websocket_server
        client = socketio.test_client(app, namespace="/agent/execution")
        for execution_id in ("one", "two"):
            client.emit("subscribe:execution", {"execution_id": execution_id},
                        namespace="/agent/execution")
        assert set(server_websocket._EXECUTION_SUBSCRIPTIONS) == {"one", "two"}
        client.disconnect(namespace="/agent/execution")
        assert server_websocket._EXECUTION_SUBSCRIPTIONS == {}


class TestCodeImplementationAgentStreaming:
    def test_constructor_accepts_socketio_and_execution_id(self, tmp_path):
        socketio = Mock()
        agent = CodeImplementationAgent(str(tmp_path), socketio=socketio,
                                        execution_id="exec-1")
        assert agent.socketio is socketio
        assert agent.execution_id == "exec-1"
        assert isinstance(agent.event_emitter, TransparencyEventEmitter)

    def test_emitter_is_none_without_socketio_or_id(self, tmp_path):
        assert CodeImplementationAgent(str(tmp_path), execution_id="x").event_emitter is None
        assert CodeImplementationAgent(str(tmp_path), socketio=Mock()).event_emitter is None

    def test_emitter_is_none_when_transparency_disabled(self, tmp_path):
        agent = CodeImplementationAgent(str(tmp_path), enable_transparency=False,
                                        socketio=Mock(), execution_id="x")
        assert agent.event_emitter is None

    def test_event_emission_is_safe_when_socketio_is_none(self, tmp_path):
        agent = CodeImplementationAgent(str(tmp_path), execution_id="x")
        assert agent.event_emitter is None
        # The optional transport is not required for transparency initialization.
        assert agent.tracer is not None

    def test_transparency_response_fields_are_available_when_enabled(self, tmp_path):
        agent = CodeImplementationAgent(str(tmp_path), execution_id="exec-9")
        assert agent.enable_transparency
        assert agent.tracer is not None
        assert agent.metrics is not None
        assert agent.tracker is not None
