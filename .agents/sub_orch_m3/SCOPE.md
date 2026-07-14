# Scope: Milestone 3: Frontend Improvements & Onboarding

## Architecture
- Next.js frontend code optimization, ISR integration, user onboarding flow, and Jest testing.

## Work Items
1. **IMP-037**: Next.js bundle analysis (@next/bundle-analyzer to find large chunks).
2. **IMP-038**: Next.js ISR for static job pages (getStaticProps + revalidate:300 for job listing pages).
3. **IMP-187**: User onboarding wizard (Multi-step: upload CV → preferences → email pool → test run).
4. **IMP-243**: Streaming cover letter preview (Word-by-word streaming preview in frontend dashboard).
5. **IMP-101**: Frontend snapshot tests (Jest toMatchSnapshot() for key React components).

## Interface Contracts
- Onboarding wizard components and routing.
- Server-sent events or websockets or streaming endpoints for cover letter preview.
