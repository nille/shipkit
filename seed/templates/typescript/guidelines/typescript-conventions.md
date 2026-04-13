# TypeScript Conventions

## Language Version
- Target ES2022+ with strict TypeScript (`"strict": true` in tsconfig.json)
- Prefer `const` over `let`; never use `var`

## Code Style
- Use the project's configured formatter (prettier, biome, etc.)
- Prefer named exports over default exports
- Use explicit return types on public functions
- Prefer `interface` over `type` for object shapes (unless unions/intersections are needed)

## Project Structure
- Follow the existing directory convention (feature-based, layer-based, etc.)
- Co-locate related files: component + test + styles in the same directory
- Use barrel files (`index.ts`) sparingly — they can cause circular dependencies

## Testing
- Use the project's test runner (vitest, jest, node:test)
- Co-locate test files as `*.test.ts` or `*.spec.ts`
- Prefer `describe`/`it` blocks for behavior-driven organization
- Mock only external boundaries (APIs, databases) — not internal modules

## Error Handling
- Use typed errors: extend `Error` with specific error classes
- Prefer returning `Result` types or throwing — not both in the same module
- Always handle promise rejections — never leave `.catch()` empty

## Common Patterns
- Use `Map`/`Set` over plain objects for dynamic keys
- Prefer `Array.prototype` methods (`.map`, `.filter`, `.reduce`) over loops
- Use `satisfies` for type checking without widening
- For async operations, use `async/await` — avoid raw `.then()` chains
- Use `zod` or similar for runtime validation at system boundaries

## React (if applicable)
- Prefer functional components with hooks
- Use server components by default (Next.js 13+); client components only for interactivity
- Co-locate hooks in the component file unless shared
- Use `React.Suspense` for async data loading patterns
