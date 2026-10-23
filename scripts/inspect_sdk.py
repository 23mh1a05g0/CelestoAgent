"""Inspect the installed Celesto SDK to discover actual API surface."""
import sys
import inspect

try:
    import celesto
    print(f"celesto version: {celesto.__version__}")
    print(f"celesto location: {celesto.__file__}")
    print(f"celesto dir: {[x for x in dir(celesto) if not x.startswith('_')]}")
except Exception as e:
    print(f"ERROR importing celesto: {e}")
    sys.exit(1)

print("\n--- Inspecting celesto.Computer ---")
try:
    from celesto import Computer
    print(f"Computer class: {Computer}")
    sig = inspect.signature(Computer.__init__)
    print(f"Computer.__init__ signature: {sig}")
    print(f"Computer methods: {[m for m in dir(Computer) if not m.startswith('_')]}")
    
    # Check for run method signature
    if hasattr(Computer, 'run'):
        run_sig = inspect.signature(Computer.run)
        print(f"Computer.run signature: {run_sig}")
    
    # Check for delete method
    if hasattr(Computer, 'delete'):
        del_sig = inspect.signature(Computer.delete)
        print(f"Computer.delete signature: {del_sig}")

    # Check for upload/download file methods
    for method_name in ['upload', 'download', 'upload_file', 'download_file', 
                        'write_file', 'read_file', 'file_write', 'file_read',
                        'files', 'filesystem']:
        if hasattr(Computer, method_name):
            m = getattr(Computer, method_name)
            try:
                msig = inspect.signature(m)
                print(f"Computer.{method_name} signature: {msig}")
            except:
                print(f"Computer.{method_name} exists (not inspectable)")
except Exception as e:
    print(f"ERROR inspecting Computer: {e}")

print("\n--- Inspecting celesto.NetworkPolicy ---")
try:
    from celesto import NetworkPolicy
    print(f"NetworkPolicy class: {NetworkPolicy}")
    sig = inspect.signature(NetworkPolicy.__init__)
    print(f"NetworkPolicy.__init__ signature: {sig}")
    print(f"NetworkPolicy dir: {[m for m in dir(NetworkPolicy) if not m.startswith('_')]}")
except ImportError:
    print("NetworkPolicy not found as a top-level export")
    # Try to find it
    for attr_name in dir(celesto):
        attr = getattr(celesto, attr_name)
        if isinstance(attr, type) and 'network' in attr_name.lower():
            print(f"  Found: celesto.{attr_name}")

print("\n--- Checking for other key classes ---")
for name in ['Celesto', 'Sandbox', 'SandboxConfig', 'Session', 'Client']:
    if hasattr(celesto, name):
        cls = getattr(celesto, name)
        try:
            sig = inspect.signature(cls.__init__)
            print(f"celesto.{name}.__init__: {sig}")
            print(f"  methods: {[m for m in dir(cls) if not m.startswith('_')]}")
        except:
            print(f"celesto.{name} exists")

print("\n--- Checking for async variants ---")
for name in dir(celesto):
    obj = getattr(celesto, name)
    if inspect.isclass(obj) or inspect.isfunction(obj):
        if 'async' in name.lower() or 'aio' in name.lower():
            print(f"  Async: celesto.{name}")

print("\n--- Source of Computer class ---")
try:
    source_file = inspect.getfile(Computer)
    print(f"Source file: {source_file}")
    # Print first 100 lines of source
    source = inspect.getsource(Computer)
    lines = source.split('\n')
    for i, line in enumerate(lines[:150]):
        print(f"  {i+1}: {line}")
    if len(lines) > 150:
        print(f"  ... ({len(lines) - 150} more lines)")
except Exception as e:
    print(f"Could not get source: {e}")
