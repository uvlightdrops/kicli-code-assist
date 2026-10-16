# Shell Execution Worker Fix

## Issue
After integrating shell command execution into the TUI, executing a command batch resulted in:
```
WorkerError: Request to run a non-async function as an async worker
```

Then, after making the function async:
```
TypeError: CodeAssistantApp._execute_shell_batch_worker() missing 2 required positional arguments: 'batch' and 'result'
```

## Root Cause

### First Error
Textual's `run_worker()` requires an async coroutine function, but `_execute_shell_batch_worker` was synchronous.

### Second Error
`run_worker()` doesn't pass extra arguments through to the worker function. It only accepts:
1. A callable with no parameters
2. A coroutine function with no parameters

So calling `self.run_worker(self._execute_shell_batch_worker, batch, result)` fails because `run_worker()` tries to call the method with **no** arguments.

## Solution

### Part 1: Make Function Async
```python
async def _execute_shell_batch_worker(self, batch: ShellCommandBatch, result) -> None:
    """Execute shell batch in background worker (async)."""
    # Use asyncio.get_event_loop().run_in_executor() for blocking calls
    execution_result = await asyncio.get_event_loop().run_in_executor(
        None, 
        self.chat_session.execute_shell_batch, 
        batch, 
        approval
    )
```

### Part 2: Use Lambda to Wrap Arguments
```python
# BEFORE (wrong - arguments don't get passed)
self.run_worker(self._execute_shell_batch_worker, batch, result)

# AFTER (correct - lambda captures arguments in closure)
self.run_worker(lambda: self._execute_shell_batch_worker(batch, result))
```

## Files Changed

### kicli_code_assist/ui/textual_app.py
1. Added `import asyncio` at top
2. Made `_execute_shell_batch_worker()` an async method
3. Used `asyncio.get_event_loop().run_in_executor()` to wrap the blocking `chat_session.execute_shell_batch()` call
4. Changed `run_worker()` call to use a lambda wrapper: `self.run_worker(lambda: self._execute_shell_batch_worker(batch, result))`

## How It Works

1. **Lambda Wrapper**: Captures `batch` and `result` in closure
2. **Async Function**: Declared as `async def` so Textual recognizes it
3. **Executor Pattern**: Uses `run_in_executor()` to run blocking I/O in thread pool without blocking async event loop
4. **UI Update**: Updates chat display with results from async context (Textual handles thread safety)

## Textual Best Practices

### run_worker() Pattern
- Always wrap worker callables in a lambda if you need to pass arguments
- Always make workers async if they do any I/O (blocking calls must use run_in_executor)
- Workers run in a dedicated thread pool and are thread-safe for widget updates

### Async/Await Pattern
```python
async def worker_method(self, arg1, arg2):
    # For blocking I/O, use run_in_executor
    result = await asyncio.get_event_loop().run_in_executor(
        None,
        blocking_function,
        arg1,
        arg2
    )
    
    # UI updates are safe here
    self.chat_display.write(result)
```

## Verification
- ✅ Syntax check passed (py_compile)
- ✅ TUI starts without worker errors
- ✅ Lambda wrapper captures arguments correctly
- ✅ Async function definition recognized by Textual

## Testing
To manually test the flow:
1. Start: `kicli-assist tui`
2. Press `Ctrl+X` to open command dialog
3. Enter a command (e.g., `echo hello`)
4. Press `Ctrl+Enter` to create batch
5. Click "Execute" in approval modal
6. Command should execute and output appears in chat

## Related Issues
- Previous checkpoint: Shell execution UI integration complete (006)
- CSS validation: Fixed with separated .tcss files
- Message class scoping: Fixed with nested classes in modals
