# IMP-037 & IMP-101 Implementation Strategy: Next.js Bundle Analysis & Jest Snapshot Testing

This document outlines the investigation findings and implementation strategy for setting up **Next.js Bundle Analysis** (`@next/bundle-analyzer`) and **Frontend Jest Snapshot Tests** within the JobHunt Pro Next.js (TypeScript) frontend.

---

## 1. Executive Summary

- **IMP-037 (Bundle Analysis)**: Enables visual analysis of chunk sizes to identify large dependencies and optimize loading speeds. We recommend integrating `@next/bundle-analyzer` into the native `next.config.ts`, utilizing `cross-env` to ensure cross-platform compatibility for Windows environments.
- **IMP-101 (Jest Snapshot Tests)**: Prevents UI regressions by snapshotting key presentation components and pages. We propose a fast SWC-based Jest runner using `next/jest`, configure ES modules with `jest.config.mjs`, and handle frontend mocks (WebSockets, window.matchMedia, and WebAssembly SQLite) to ensure tests run reliably in JSDOM.

---

## 2. Next.js Bundle Analysis Setup (IMP-037)

### A. Core Package Installations
We need to install the bundle analyzer and a utility to support cross-platform environment variables:
```bash
cd frontend
npm install --save-dev @next/bundle-analyzer @types/next__bundle-analyzer cross-env
```
*Note: `cross-env` is required because setting `ANALYZE=true` directly in standard package scripts fails in Windows command prompt (`cmd.exe`) and PowerShell.*

### B. Configuration of `next.config.ts`
The current `next.config.ts` wraps the Next configuration with `withPWA` (which is loaded via `require`). We will import `withBundleAnalyzer` and wrap the configuration cleanly.

**Proposed `next.config.ts`**:
```typescript
import withBundleAnalyzer from '@next/bundle-analyzer';

const withPWA = require('next-pwa')({
  dest: 'public',
  disable: process.env.NODE_ENV === 'development',
  register: true,
  skipWaiting: true,
});

/** @type {import('next').NextConfig} */
const nextConfig = {
  // Comment out output: "export" to deploy to Vercel and use full Next.js SSR & Image Optimization
  output: "export",
  trailingSlash: true,
  images: {
    // Enable WebP & AVIF for smaller image sizes on supported browsers
    formats: ['image/avif', 'image/webp'],
    unoptimized: true,
  },
};

const withBundleAnalyzerConfig = withBundleAnalyzer({
  enabled: process.env.ANALYZE === 'true',
});

export default withBundleAnalyzerConfig(withPWA(nextConfig));
```

### C. Scripts in `package.json`
We will add an `analyze` command to compile and generate reports:
```json
"scripts": {
  ...
  "analyze": "cross-env ANALYZE=true npm run build"
}
```
Running `npm run analyze` will trigger the Webpack build (specified by `--webpack` in `npm run build`), generating visual HTML reports inside `.next/analyze/` (e.g., `client.html`, `server.html`, and `edge.html`). These files are already gitignored because the `/frontend/.gitignore` ignores the `/.next/` folder.

---

## 3. Jest Snapshot Testing Setup (IMP-101)

Since the frontend is built using Next.js 16.2 and React 19.2, Jest setup must use compatible versions. Using Next.js's built-in `next/jest` compiler allows Jest to use Next's Rust-based compiler (SWC) to transform files, which respects `tsconfig.json` path mappings out of the box and is significantly faster than using `ts-jest` or Babel.

### A. Dependencies
Install the required testing packages as devDependencies:
```bash
cd frontend
npm install --save-dev jest jest-environment-jsdom @testing-library/react @testing-library/jest-dom @testing-library/dom @types/jest
```
*Note: `jest-environment-jsdom` is package-scoped in Jest 28+ and must be installed explicitly.*

### B. Configuration Files

#### 1. `frontend/jest.config.mjs`
We write the configuration with the `.mjs` extension to run Jest with ESM support natively, bypassing the need for `ts-node` to compile config files.
```javascript
import nextJest from 'next/jest.js';

const createJestConfig = nextJest({
  // Provide the path to your Next.js app to load next.config.ts and .env files
  dir: './',
});

/** @type {import('jest').Config} */
const config = {
  coverageProvider: 'v8',
  testEnvironment: 'jest-environment-jsdom',
  setupFilesAfterEnv: ['<rootDir>/jest.setup.ts'],
};

export default createJestConfig(config);
```

#### 2. `frontend/jest.setup.ts`
This setup file extends Jest with DOM assertions and mocks browser-only APIs that are missing or incomplete in JSDOM:
```typescript
import '@testing-library/jest-dom';

// 1. Mock window.matchMedia (commonly invoked by layout packages/responsive grids)
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: jest.fn().mockImplementation((query) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: jest.fn(), // Deprecated
    removeListener: jest.fn(), // Deprecated
    addEventListener: jest.fn(),
    removeEventListener: jest.fn(),
    dispatchEvent: jest.fn(),
  })),
});

// 2. Mock WebSocket class (Required since frontend/src/app/page.tsx instantiates a WebSocket on mount)
global.WebSocket = jest.fn().mockImplementation(() => ({
  close: jest.fn(),
  send: jest.fn(),
  addEventListener: jest.fn(),
  removeEventListener: jest.fn(),
})) as any;
```

### C. tsconfig.json Support
No configuration changes are required in `frontend/tsconfig.json` because:
1. `tsconfig.json` already includes `"**/*.ts"` and `"**/*.tsx"`, meaning test files and `jest.setup.ts` are covered.
2. The alias `"@/*": ["./src/*"]` is automatically mapped by `next/jest` using the Next compiler under the hood, ensuring paths like `@/components/SkeletonLoader` resolve perfectly in tests.
3. Installing `@types/jest` enables IDE and type-safety auto-complete for Jest globals (`describe`, `test`, `expect`, `jest`, etc.).

---

## 4. Proposed Test Cases & Snapshot Implementations

### A. Presentation Component: `SkeletonLoader`
*Path: `frontend/src/components/__tests__/SkeletonLoader.test.tsx`*
```typescript
import React from 'react';
import { render } from '@testing-library/react';
import { SkeletonLoader, SkeletonProfile, SkeletonCard } from '../SkeletonLoader';

describe('SkeletonLoader Components', () => {
  it('renders SkeletonLoader default layout correctly', () => {
    const { container } = render(<SkeletonLoader />);
    expect(container).toMatchSnapshot();
  });

  it('renders SkeletonProfile layout correctly', () => {
    const { container } = render(<SkeletonProfile />);
    expect(container).toMatchSnapshot();
  });

  it('renders SkeletonCard layout correctly', () => {
    const { container } = render(<SkeletonCard />);
    expect(container).toMatchSnapshot();
  });
});
```

### B. Core Page: `Home` (`app/page.tsx`)
*Path: `frontend/src/app/__tests__/page.test.tsx`*
The Home page depends on `LocaleProvider` context (via `useLocale`) and initiates a WebSocket connection on mount. The WebSocket is globally mocked in `jest.setup.ts`. We must wrap the component inside the `LocaleProvider`.
```typescript
import React from 'react';
import { render } from '@testing-library/react';
import Home from '../page';
import { LocaleProvider } from '../locale-context';

describe('Home Page Snapshot', () => {
  it('renders in default locale (Arabic) and matches snapshot', () => {
    const { container } = render(
      <LocaleProvider>
        <Home />
      </LocaleProvider>
    );
    expect(container).toMatchSnapshot();
  });
});
```

### C. Client Database Page: `Dashboard` (`app/dashboard/page.tsx`)
*Path: `frontend/src/app/dashboard/__tests__/page.test.tsx`*
The Dashboard calls `runLocalQuery` on mount, which accesses SQLite WebAssembly, downloads SQL.js from a CDN script tag, and calls browser OPFS filesystem handles. This will fail under testing environments. We must mock the Wasm database module (`@/app/db/wasm-db`) to return mock results.
```typescript
import React from 'react';
import { render, act } from '@testing-library/react';
import Dashboard from '../page';
import { LocaleProvider } from '../../locale-context';

// Mock the browser SQLite Wasm client
jest.mock('@/app/db/wasm-db', () => ({
  runLocalQuery: jest.fn().mockResolvedValue([
    {
      columns: ['id', 'campaign_id', 'status', 'total_companies', 'sent_count', 'created_at'],
      values: [
        [1, 'camp_1', 'completed', 50, 45, '2026-07-03 12:00:00']
      ]
    }
  ]),
}));

describe('Dashboard Page Snapshot', () => {
  it('renders Dashboard correctly and matches snapshot', async () => {
    let renderResult: any;
    
    await act(async () => {
      renderResult = render(
        <LocaleProvider>
          <Dashboard />
        </LocaleProvider>
      );
    });

    expect(renderResult.container).toMatchSnapshot();
  });
});
```

---

## 5. Script Support in `package.json`

Add testing scripts to `frontend/package.json`:
```json
"scripts": {
  ...
  "test": "jest",
  "test:watch": "jest --watch",
  "test:coverage": "jest --coverage",
  "test:update": "jest -u"
}
```

### Running the Setup
- To run tests: `npm run test`
- To run and watch: `npm run test:watch`
- To update snapshots: `npm run test:update` (or `npm run test -- -u`)
