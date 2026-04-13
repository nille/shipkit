# Import compilers so their @register_compiler decorators run
from shipkit.compilers.claude import ClaudeCodeCompiler  # noqa: F401
from shipkit.compilers.kiro import KiroCompiler  # noqa: F401
from shipkit.compilers.gemini import GeminiCliCompiler  # noqa: F401
from shipkit.compilers.opencode import OpenCodeCompiler  # noqa: F401
