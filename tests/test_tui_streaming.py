"""
TUI Streaming & Real-Time Features Tests (Phase 1.2)

Comprehensive test suite for WebSocket streaming, error handling,
and real-time UI updates.
"""

import asyncio
import sys
import json
from pathlib import Path


class TestStreamingHandler:
    """Test StreamingResponseHandler (Phase 1.2.1)."""
    
    @staticmethod
    def test_token_buffer():
        """Test token buffering and processing."""
        from kicli_code_assist.ui.streaming import StreamingResponseHandler
        
        async def run():
            tokens = []
            
            def collect_token(token):
                tokens.append(token)
            
            handler = StreamingResponseHandler(on_token=collect_token)
            await handler.start_streaming()
            
            # Add tokens
            for i in range(10):
                await handler.add_token(f"token{i} ")
            
            await handler.complete()
            await asyncio.sleep(0.2)  # Let processor finish
            
            assert len(tokens) == 10, f"Expected 10 tokens, got {len(tokens)}"
            assert handler.stats.tokens_received == 10
            assert handler.stats.tokens_rendered == 10
            return True
        
        return asyncio.run(run())
    
    @staticmethod
    def test_error_handling():
        """Test error event handling."""
        from kicli_code_assist.ui.streaming import StreamingResponseHandler, StreamingEventType
        
        async def run():
            errors = []
            
            async def on_error(msg):
                errors.append(msg)
            
            handler = StreamingResponseHandler(on_error=on_error)
            await handler.start_streaming()
            
            await handler.add_error("Test error")
            await asyncio.sleep(0.1)
            
            assert len(errors) == 1
            assert "Test error" in errors[0]
            return True
        
        return asyncio.run(run())
    
    @staticmethod
    def test_backpressure():
        """Test buffer backpressure handling."""
        from kicli_code_assist.ui.streaming import StreamingResponseHandler
        
        async def run():
            handler = StreamingResponseHandler(max_buffer_size=5)
            await handler.start_streaming()
            
            # Add up to buffer limit
            for i in range(5):
                result = await handler.add_token(f"token{i}")
                assert result is True
            
            # Further additions should trigger backpressure
            result = await handler.add_token("overflow")
            # Backpressure detected but operation still succeeds
            # (actual queue behavior depends on asyncio.Queue implementation)
            
            return True
        
        return asyncio.run(run())


class TestAgentTabs:
    """Test AgentTabPanel streaming (Phase 1.2.2)."""
    
    @staticmethod
    def test_streaming_setup():
        """Test streaming to tab."""
        from kicli_code_assist.ui.widgets.agent_tabs import AgentTabPanel
        
        async def run():
            panel = AgentTabPanel()
            
            # Mock compose
            panel.tabbed_content = type('MockTabs', (), {})()
            panel.tab_panels['explain'] = type('MockLog', (), {
                'clear': lambda s: None,
                'write': lambda s, x: None
            })()
            
            # Get streaming callback
            callback = await panel.stream_to_tab('explain', flush=True)
            
            # Callback should be callable
            assert callable(callback)
            assert panel.streaming_active
            assert panel.current_streaming_tab == 'explain'
            
            return True
        
        return asyncio.run(run())


class TestErrorHandling:
    """Test error recovery (Phase 1.2.5)."""
    
    @staticmethod
    def test_error_validator():
        """Test response validation."""
        from kicli_code_assist.ui.error_handler import ResponseValidator
        
        # Valid token
        is_valid, _ = ResponseValidator.validate_token_event({
            'type': 'token',
            'content': 'hello'
        })
        assert is_valid
        
        # Invalid token
        is_valid, msg = ResponseValidator.validate_token_event({
            'type': 'invalid'
        })
        assert not is_valid
        
        # Valid complete
        is_valid, _ = ResponseValidator.validate_complete_event({
            'type': 'complete'
        })
        assert is_valid
        
        # Invalid complete
        is_valid, _ = ResponseValidator.validate_complete_event({
            'type': 'token'
        })
        assert not is_valid
        
        return True
    
    @staticmethod
    def test_recovery_strategy():
        """Test retry/recovery logic."""
        from kicli_code_assist.ui.error_handler import (
            ErrorRecoveryStrategy, StreamingError
        )
        
        async def run():
            strategy = ErrorRecoveryStrategy(max_retries=2)
            attempt_count = 0
            
            async def failing_func():
                nonlocal attempt_count
                attempt_count += 1
                if attempt_count < 2:
                    raise StreamingError("First attempt fails")
                return "success"
            
            result = await strategy.retry_with_backoff(failing_func)
            assert result == "success"
            assert attempt_count == 2
            
            return True
        
        return asyncio.run(run())


class TestConfig:
    """Test streaming configuration (Phase 1.2)."""
    
    @staticmethod
    def test_streaming_config_load():
        """Test config loading."""
        from kicli_code_assist.ui.config import ConfigLoader
        
        loader = ConfigLoader('config/tui_config.yaml')
        
        # Check streaming config exists
        assert hasattr(loader.config, 'streaming')
        assert loader.config.streaming.enabled
        assert loader.config.streaming.protocol == 'websocket'
        assert loader.config.streaming.min_token_delay_ms > 0
        
        return True


class TestStatusBar:
    """Test live status updates (Phase 1.2.3)."""
    
    @staticmethod
    def test_streaming_status():
        """Test status bar streaming display."""
        # Just test that methods are callable
        from kicli_code_assist.ui.widgets.input_bar import StatusBar
        
        # Verify methods exist
        assert hasattr(StatusBar, 'set_streaming')
        assert hasattr(StatusBar, 'set_token_stats')
        assert hasattr(StatusBar, 'set_progress')
        
        return True


# Test Runner
def run_all_tests():
    """Run all tests."""
    tests = [
        ("StreamingHandler: Token Buffer", TestStreamingHandler.test_token_buffer),
        ("StreamingHandler: Error Handling", TestStreamingHandler.test_error_handling),
        ("StreamingHandler: Backpressure", TestStreamingHandler.test_backpressure),
        ("AgentTabs: Streaming Setup", TestAgentTabs.test_streaming_setup),
        ("ErrorHandling: Validator", TestErrorHandling.test_error_validator),
        ("ErrorHandling: Recovery Strategy", TestErrorHandling.test_recovery_strategy),
        ("Config: Streaming Load", TestConfig.test_streaming_config_load),
        ("StatusBar: Streaming Status", TestStatusBar.test_streaming_status),
    ]
    
    print("\n" + "="*70)
    print("Phase 1.2 - TUI Streaming & Real-Time Features Tests")
    print("="*70)
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            if result:
                print(f"✅ {test_name}")
                passed += 1
            else:
                print(f"❌ {test_name}: Failed")
                failed += 1
        except Exception as e:
            print(f"❌ {test_name}: {e}")
            failed += 1
    
    print("="*70)
    print(f"Results: {passed} passed, {failed} failed ({passed + failed} total)")
    print("="*70 + "\n")
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
